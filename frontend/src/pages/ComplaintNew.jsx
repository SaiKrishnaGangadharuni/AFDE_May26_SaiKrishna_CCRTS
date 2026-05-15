import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../lib/api'
import { PRIORITY_OPTIONS } from '../lib/helpers'

export default function ComplaintNew() {
  const nav = useNavigate()
  const [categories, setCategories] = useState([])
  const [form, setForm] = useState({ subject: '', description: '', category_id: '', priority: 'Medium' })
  const [files, setFiles] = useState([])
  const [submitting, setSubmitting] = useState(false)
  const [err, setErr] = useState('')

  useEffect(() => {
    api.get('/categories').then((r) => setCategories(r.data)).catch(() => {})
  }, [])

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  async function submit(e) {
    e.preventDefault()
    setErr(''); setSubmitting(true)
    try {
      const payload = { ...form, category_id: Number(form.category_id) }
      const { data } = await api.post('/complaints', payload)
      // Upload attachments (if any)
      for (const f of files) {
        const fd = new FormData()
        fd.append('file', f)
        await api.post(`/complaints/${data.id}/attachments`, fd,
                       { headers: { 'Content-Type': 'multipart/form-data' } })
      }
      nav(`/complaints/${data.id}`)
    } catch (e) {
      setErr(e?.response?.data?.detail || 'Failed to create complaint')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-semibold text-slate-800 mb-4">Register a new complaint</h1>
      <form onSubmit={submit} className="card space-y-4">
        {err && <div className="text-sm bg-rose-50 text-rose-700 px-3 py-2 rounded">{err}</div>}
        <div>
          <label className="label">Subject *</label>
          <input className="input" value={form.subject} onChange={set('subject')} required minLength={3} maxLength={200} />
        </div>
        <div>
          <label className="label">Description *</label>
          <textarea className="input" rows={5} value={form.description} onChange={set('description')} required minLength={5} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Category *</label>
            <select className="input" value={form.category_id} onChange={set('category_id')} required>
              <option value="">Select a category</option>
              {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Priority *</label>
            <select className="input" value={form.priority} onChange={set('priority')}>
              {PRIORITY_OPTIONS.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
        </div>
        <div>
          <label className="label">Attachments (optional, max 10 MB each)</label>
          <input className="input" type="file" multiple onChange={(e) => setFiles([...e.target.files])} />
          {files.length > 0 && (
            <ul className="mt-2 text-xs text-slate-600 space-y-1">
              {files.map((f, i) => <li key={i}>• {f.name} ({Math.round(f.size / 1024)} KB)</li>)}
            </ul>
          )}
        </div>
        <div className="flex gap-2">
          <button className="btn-primary" disabled={submitting}>
            {submitting ? 'Submitting…' : 'Submit Complaint'}
          </button>
          <button type="button" className="btn-secondary" onClick={() => nav(-1)}>Cancel</button>
        </div>
      </form>
    </div>
  )
}
