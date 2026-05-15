import { useEffect, useState } from 'react'
import api from '../lib/api'
import { formatDate } from '../lib/helpers'

export default function Users() {
  const [users, setUsers] = useState([])
  const [roles, setRoles] = useState([])
  const [showNew, setShowNew] = useState(false)
  const [form, setForm] = useState({ name: '', email: '', phone: '', password: '', role_id: '' })
  const [filter, setFilter] = useState({ role: '', q: '' })
  const [err, setErr] = useState('')

  const load = () => {
    const params = {}
    if (filter.role) params.role = filter.role
    if (filter.q) params.q = filter.q
    api.get('/users', { params }).then((r) => setUsers(r.data)).catch(() => {})
  }
  useEffect(() => { load() // eslint-disable-next-line react-hooks/exhaustive-deps
                  }, [])
  useEffect(() => {
    api.get('/users/roles').then((r) => setRoles(r.data))
  }, [])

  async function create(e) {
    e.preventDefault(); setErr('')
    try {
      await api.post('/users', { ...form, role_id: Number(form.role_id) })
      setShowNew(false); setForm({ name: '', email: '', phone: '', password: '', role_id: '' })
      load()
    } catch (e) {
      setErr(e?.response?.data?.detail || 'Failed')
    }
  }

  async function deactivate(id) {
    if (!confirm('Deactivate this user?')) return
    await api.delete(`/users/${id}`); load()
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-800">User Management</h1>
        <button className="btn-primary" onClick={() => setShowNew(true)}>+ New User</button>
      </div>

      <div className="card flex gap-3">
        <input className="input flex-1" placeholder="Search name or email"
               value={filter.q} onChange={(e) => setFilter({ ...filter, q: e.target.value })} />
        <select className="input max-w-xs" value={filter.role}
                onChange={(e) => setFilter({ ...filter, role: e.target.value })}>
          <option value="">All roles</option>
          {roles.map((r) => <option key={r.id} value={r.name}>{r.name}</option>)}
        </select>
        <button className="btn-secondary" onClick={load}>Search</button>
      </div>

      <div className="card p-0 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr><th className="py-3 px-4 text-left">Name</th><th className="text-left">Email</th>
              <th className="text-left">Phone</th><th>Role</th><th>Active</th><th>Created</th><th></th></tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-t hover:bg-slate-50">
                <td className="px-4 py-2">{u.name}</td><td>{u.email}</td>
                <td className="text-xs">{u.phone || '—'}</td>
                <td className="text-center"><span className="badge bg-slate-100 text-slate-700">{u.role.name}</span></td>
                <td className="text-center">{u.is_active ? '✅' : '🚫'}</td>
                <td className="text-xs text-slate-500 text-center">{formatDate(u.created_at)}</td>
                <td>{u.is_active &&
                  <button className="text-xs text-rose-600 hover:underline" onClick={() => deactivate(u.id)}>
                    Deactivate
                  </button>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showNew && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <form onSubmit={create} className="bg-white rounded-lg p-6 w-full max-w-md space-y-3">
            <h3 className="text-lg font-semibold">Create user</h3>
            {err && <div className="text-sm bg-rose-50 text-rose-700 px-3 py-2 rounded">{err}</div>}
            <div><label className="label">Name</label>
              <input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required /></div>
            <div><label className="label">Email</label>
              <input className="input" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required /></div>
            <div><label className="label">Phone</label>
              <input className="input" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></div>
            <div><label className="label">Password</label>
              <input className="input" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required minLength={6} /></div>
            <div><label className="label">Role</label>
              <select className="input" value={form.role_id} onChange={(e) => setForm({ ...form, role_id: e.target.value })} required>
                <option value="">Select…</option>
                {roles.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
              </select></div>
            <div className="flex gap-2 justify-end pt-2">
              <button type="button" className="btn-secondary" onClick={() => setShowNew(false)}>Cancel</button>
              <button className="btn-primary">Create</button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}
