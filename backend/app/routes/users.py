"""User management endpoints — admin-only CRUD + agent listing."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.security import hash_password
from ..core.deps import require_roles, get_current_user
from ..models import User, Role
from ..schemas.schemas import UserOut, UserCreate, UserUpdate, RoleOut


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=List[UserOut])
def list_users(
    role: Optional[str] = Query(default=None, description="Filter by role name (Admin, Supervisor, ...)"),
    q: Optional[str] = Query(default=None, description="Search by name or email"),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Admin", "Supervisor")),
):
    qry = db.query(User)
    if role:
        qry = qry.join(Role).filter(Role.name == role)
    if q:
        like = f"%{q.lower()}%"
        qry = qry.filter((User.name.ilike(like)) | (User.email.ilike(like)))
    return qry.order_by(User.created_at.desc()).all()


@router.get("/agents", response_model=List[UserOut])
def list_agents(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Admin", "Supervisor")),
):
    """Convenience endpoint for the assignment dropdown."""
    return (
        db.query(User)
        .join(Role)
        .filter(Role.name == "SupportAgent", User.is_active == True)  # noqa: E712
        .all()
    )


@router.post("", response_model=UserOut, status_code=201)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Admin")),
):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(400, "Email already in use")
    if not db.query(Role).filter(Role.id == payload.role_id).first():
        raise HTTPException(400, "Invalid role_id")
    user = User(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role_id=payload.role_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Admin")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=204)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_roles("Admin")),
):
    """Soft-delete by deactivating, never hard-delete (preserves audit trail)."""
    if user_id == current.id:
        raise HTTPException(400, "Cannot deactivate yourself")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    user.is_active = False
    db.commit()


@router.get("/roles", response_model=List[RoleOut])
def list_roles(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return db.query(Role).order_by(Role.id).all()
