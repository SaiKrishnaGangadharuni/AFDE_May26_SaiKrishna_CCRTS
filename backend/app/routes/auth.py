"""Authentication endpoints: register, login, forgot-password, /me."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.security import hash_password, verify_password, create_access_token
from ..core.deps import get_current_user
from ..models import User, Role
from ..schemas.schemas import (
    UserRegister, UserOut, LoginRequest, TokenResponse,
    PasswordResetConfirm,
)


router = APIRouter(prefix="/auth", tags=["Authentication"])


def _build_token(user: User) -> TokenResponse:
    token = create_access_token(subject=user.email, role=user.role.name, user_id=user.id)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    """Public self-registration — always creates a Customer."""
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    role = db.query(Role).filter(Role.name == "Customer").first()
    if not role:
        raise HTTPException(status_code=500, detail="Customer role not seeded; run seed.py first")

    user = User(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role_id=role.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _build_token(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")
    return _build_token(user)


@router.post("/login/form", response_model=TokenResponse, include_in_schema=False)
def login_form(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 password-flow compatible endpoint — used by Swagger 'Authorize' UI."""
    return login(LoginRequest(email=form.username, password=form.password), db)


@router.post("/forgot-password")
def forgot_password(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    """Simplified reset — in production this would email a one-time link.
    For Phase 1, the user supplies their email + a new password directly."""
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        # Don't reveal whether email exists — return success either way.
        return {"message": "If the email is registered, the password has been reset."}
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password updated successfully"}


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
