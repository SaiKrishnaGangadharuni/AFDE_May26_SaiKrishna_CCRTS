import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login, loading } = useAuth()
  const nav = useNavigate()
  const loc = useLocation()
  const [email, setEmail] = useState('admin@example.com')
  const [password, setPassword] = useState('Admin@123')
  const [err, setErr] = useState('')

  async function submit(e) {
    e.preventDefault()
    setErr('')
    try {
      await login(email, password)
      const dest = loc.state?.from?.pathname || '/dashboard'
      nav(dest, { replace: true })
    } catch (e) {
      setErr(e?.response?.data?.detail || 'Login failed')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-gradient-to-br from-brand-50 to-slate-100">
      <div className="w-full max-w-md">
        <div className="text-center mb-6">
          <div className="w-14 h-14 mx-auto bg-brand-600 text-white rounded-lg flex items-center justify-center text-2xl font-bold">C</div>
          <h1 className="mt-3 text-2xl font-semibold text-slate-800">Sign in to CCRTS</h1>
          <p className="text-sm text-slate-500">Customer Complaint &amp; Resolution Tracking</p>
        </div>

        <form onSubmit={submit} className="card space-y-4">
          {err && <div className="text-sm bg-rose-50 text-rose-700 px-3 py-2 rounded">{err}</div>}
          <div>
            <label className="label">Email</label>
            <input className="input" type="email" value={email}
                   onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div>
            <label className="label">Password</label>
            <input className="input" type="password" value={password}
                   onChange={(e) => setPassword(e.target.value)} required />
          </div>
          <button type="submit" className="btn-primary w-full" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
          <div className="text-xs text-center text-slate-500">
            <Link to="/forgot-password" className="text-brand-600 hover:underline">Forgot password?</Link>
            <span className="mx-2">·</span>
            <Link to="/register" className="text-brand-600 hover:underline">Create an account</Link>
          </div>
        </form>

        <div className="mt-6 text-xs text-slate-600 bg-white rounded-lg p-4 border border-slate-200">
          <div className="font-semibold mb-2 text-slate-700">Demo credentials</div>
          <div className="space-y-1 font-mono">
            <div>admin@example.com / Admin@123</div>
            <div>supervisor@example.com / Super@123</div>
            <div>agent1@example.com / Agent@123</div>
            <div>customer1@example.com / Customer@123</div>
          </div>
        </div>
      </div>
    </div>
  )
}
