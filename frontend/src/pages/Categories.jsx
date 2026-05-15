import { useEffect, useState } from 'react'
import api from '../lib/api'

export default function Categories() {
  const [items, setItems] = useState([])
  const [form, setForm] = useState({ name: '', description: '' })
  const [err, setErr] = useState('')

  const load = () => api.get('/categories').then((r) => setItems(r.data))
  useEffect(() => { load() }, [])

  async function create(e) {
    e.preventDefault(); setErr('')
    try {
      await api.post('/categories', form)
      setForm({ name: '', description: '' }); load()
    } catch (e) {
      setErr(e?.response?.data?.detail || 'Failed')
    }
  }
  async function remove(id) {
    if (!confirm('Deactivate this category?')) return
    await api.delete(`/categories/${id}`); load()
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-slate-800">Complaint Categories</h1>

      <form onSubmit={create} className="card grid md:grid-cols-3 gap-3 items-end">
        <div><label className="label">Name</label>
          <input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required minLength={2} /></div>
        <div><label className="label">Description</label>
          <input className="input" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></div>
        <button className="btn-primary">Add Category</button>
        {err && <div className="md:col-span-3 text-sm bg-rose-50 text-rose-700 px-3 py-2 rounded">{err}</div>}
      </form>

      <div className="card p-0 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr><th className="py-3 px-4 text-left">Name</th><th className="text-left">Description</th><th></th></tr>
          </thead>
          <tbody>
            {items.map((c) => (
              <tr key={c.id} className="border-t hover:bg-slate-50">
                <td className="px-4 py-2 font-medium">{c.name}</td>
                <td className="text-slate-600">{c.description}</td>
                <td><button className="text-xs text-rose-600 hover:underline" onClick={() => remove(c.id)}>Deactivate</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
