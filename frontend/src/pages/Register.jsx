import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Register() {
  const { register, loading } = useAuth()
  const nav = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', phone: '', password: '' })
  const [err, setErr] = useState('')

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  async function submit(e) {
    e.preventDefault()
    setErr('')
    try {
      await register(form)
      nav('/dashboard', { replace: true })
    } catch (e) {
      setErr(e?.response?.data?.detail || 'Registration failed')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-gradient-to-br from-brand-50 to-slate-100">
      <div className="w-full max-w-md">
        <h1 className="text-center text-2xl font-semibold text-slate-800 mb-4">Create customer account</h1>
        <form onSubmit={submit} className="card space-y-4">
          {err && <div className="text-sm bg-rose-50 text-rose-700 px-3 py-2 rounded">{err}</div>}
          <div><label className="label">Full name</label>
            <input className="input" value={form.name} onChange={set('name')} required minLength={2} /></div>
          <div><label className="label">Email</label>
            <input className="input" type="email" value={form.email} onChange={set('email')} required /></div>
          <div><label className="label">Phone</label>
            <input className="input" value={form.phone} onChange={set('phone')} /></div>
          <div><label className="label">Password</label>
            <input className="input" type="password" value={form.password} onChange={set('password')} required minLength={6} /></div>
          <button type="submit" className="btn-primary w-full" disabled={loading}>
            {loading ? 'Creating account…' : 'Sign up'}
          </button>
          <div className="text-xs text-center text-slate-500">
            Already have an account? <Link to="/login" className="text-brand-600 hover:underline">Sign in</Link>
          </div>
        </form>
      </div>
    </div>
  )
}
