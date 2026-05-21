import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../lib/api'

// Role → menu definitions. Each item: { path, label, icon }
const NAV = {
  Customer: [
    { path: '/dashboard',         label: 'Dashboard' },
    { path: '/complaints',        label: 'My Complaints' },
    { path: '/complaints/new',    label: 'New Complaint' },
    { path: '/notifications',     label: 'Notifications' },
  ],
  SupportAgent: [
    { path: '/dashboard',         label: 'Dashboard' },
    { path: '/complaints',        label: 'All Complaints' },
    { path: '/my-queue',          label: 'My Queue' },
    { path: '/notifications',     label: 'Notifications' },
  ],
  Supervisor: [
    { path: '/dashboard',         label: 'Dashboard' },
    { path: '/complaints',        label: 'Complaints' },
    { path: '/escalations',       label: 'Escalations' },
    { path: '/reports',           label: 'Reports' },
    { path: '/analytics',         label: 'Analytics' },
    { path: '/notifications',     label: 'Notifications' },
  ],
  Admin: [
    { path: '/dashboard',         label: 'Dashboard' },
    { path: '/complaints',        label: 'Complaints' },
    { path: '/escalations',       label: 'Escalations' },
    { path: '/reports',           label: 'Reports' },
    { path: '/analytics',         label: 'Analytics' },
    { path: '/users',             label: 'Users' },
    { path: '/categories',        label: 'Categories' },
    { path: '/notifications',     label: 'Notifications' },
  ],
}

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const nav = useNavigate()
  const [unread, setUnread] = useState(0)

  useEffect(() => {
    if (!user) return
    api.get('/notifications/unread-count')
       .then((r) => setUnread(r.data.unread))
       .catch(() => {})
    const id = setInterval(() => {
      api.get('/notifications/unread-count').then((r) => setUnread(r.data.unread)).catch(() => {})
    }, 30000)
    return () => clearInterval(id)
  }, [user])

  const menuItems = NAV[user?.role?.name] || []

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-brand-700 text-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link to="/dashboard" className="flex items-center gap-3">
            <div className="w-9 h-9 bg-white text-brand-700 rounded font-bold flex items-center justify-center">
              C
            </div>
            <div>
              <div className="font-semibold leading-none">CCRTS</div>
              <div className="text-xs text-brand-100">Complaint Tracking</div>
            </div>
          </Link>
          <div className="flex items-center gap-4 text-sm">
            <Link to="/notifications" className="relative">
              Notifications
              {unread > 0 && (
                <span className="absolute -top-2 -right-4 bg-rose-500 text-white rounded-full text-[10px] px-1.5 py-0.5">
                  {unread}
                </span>
              )}
            </Link>
            <span className="hidden md:inline text-brand-100">
              {user?.name} <span className="text-brand-200">({user?.role?.name})</span>
            </span>
            <button
              onClick={() => { logout(); nav('/login') }}
              className="bg-brand-900 hover:bg-brand-600 px-3 py-1 rounded text-xs"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      <div className="flex-1 max-w-7xl mx-auto w-full px-4 py-6 flex gap-6">
        <aside className="w-56 shrink-0 hidden md:block">
          <nav className="bg-white rounded-lg shadow-sm border border-slate-200 p-2">
            {menuItems.map((m) => (
              <NavLink
                key={m.path}
                to={m.path}
                className={({ isActive }) =>
                  'block px-3 py-2 rounded text-sm ' +
                  (isActive
                    ? 'bg-brand-50 text-brand-700 font-semibold'
                    : 'text-slate-700 hover:bg-slate-100')
                }
              >
                {m.label}
              </NavLink>
            ))}
          </nav>
        </aside>

        <main className="flex-1 min-w-0">{children}</main>
      </div>

      <footer className="bg-white border-t border-slate-200 py-4 text-center text-xs text-slate-500">
        CCRTS · Capstone Phase 1 · {new Date().getFullYear()}
      </footer>
    </div>
  )
}
