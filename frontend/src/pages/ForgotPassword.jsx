import { useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../lib/api'

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [pwd, setPwd] = useState('')
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')

  async function submit(e) {
    e.preventDefault()
    setMsg(''); setErr('')
    try {
      const { data } = await api.post('/auth/forgot-password', { email, new_password: pwd })
      setMsg(data.message)
    } catch (e) {
      setErr(e?.response?.data?.detail || 'Failed')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-gradient-to-br from-brand-50 to-slate-100">
      <form onSubmit={submit} className="card w-full max-w-md space-y-4">
        <h1 className="text-xl font-semibold text-slate-800">Reset password</h1>
        <p className="text-sm text-slate-500">
          Phase 1 simplified flow — supply your email and a new password to reset.
        </p>
        {msg && <div className="text-sm bg-emerald-50 text-emerald-700 px-3 py-2 rounded">{msg}</div>}
        {err && <div className="text-sm bg-rose-50 text-rose-700 px-3 py-2 rounded">{err}</div>}
        <div><label className="label">Email</label>
          <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></div>
        <div><label className="label">New password</label>
          <input className="input" type="password" value={pwd} onChange={(e) => setPwd(e.target.value)} required minLength={6} /></div>
        <button className="btn-primary w-full">Update password</button>
        <div className="text-xs text-center"><Link to="/login" className="text-brand-600 hover:underline">Back to sign in</Link></div>
      </form>
    </div>
  )
}
