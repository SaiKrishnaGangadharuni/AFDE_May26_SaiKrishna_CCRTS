import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../lib/api'
import { PriorityBadge, StatusBadge } from '../components/Badges.jsx'
import { STATUS_OPTIONS, PRIORITY_OPTIONS, formatDate, slaCountdown } from '../lib/helpers'
import { useAuth } from '../context/AuthContext'

export default function ComplaintList() {
  const { hasRole } = useAuth()
  const [rows, setRows] = useState([])
  const [categories, setCategories] = useState([])
  const [filters, setFilters] = useState({
    q: '', status: '', priority: '', category_id: '', sla_breached: '',
  })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.get('/categories').then((r) => setCategories(r.data)).catch(() => {})
  }, [])

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function load() {
    setLoading(true)
    const params = {}
    for (const [k, v] of Object.entries(filters)) if (v !== '') params[k] = v
    try {
      const { data } = await api.get('/complaints', { params })
      setRows(data)
    } finally {
      setLoading(false)
    }
  }

  const set = (k) => (e) => setFilters({ ...filters, [k]: e.target.value })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-800">Complaints</h1>
        {hasRole('Customer', 'Admin', 'Supervisor') && (
          <Link to="/complaints/new" className="btn-primary">+ New Complaint</Link>
        )}
      </div>

      <div className="card">
        <div className="grid md:grid-cols-6 gap-3">
          <div className="md:col-span-2">
            <label className="label">Search</label>
            <input className="input" placeholder="Subject / description / number"
                   value={filters.q} onChange={set('q')}
                   onKeyDown={(e) => e.key === 'Enter' && load()} />
          </div>
          <div>
            <label className="label">Status</label>
            <select className="input" value={filters.status} onChange={set('status')}>
              <option value="">All</option>
              {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Priority</label>
            <select className="input" value={filters.priority} onChange={set('priority')}>
              <option value="">All</option>
              {PRIORITY_OPTIONS.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Category</label>
            <select className="input" value={filters.category_id} onChange={set('category_id')}>
              <option value="">All</option>
              {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div>
            <label className="label">SLA</label>
            <select className="input" value={filters.sla_breached} onChange={set('sla_breached')}>
              <option value="">Any</option>
              <option value="true">Breached</option>
              <option value="false">On Track</option>
            </select>
          </div>
        </div>
        <div className="mt-3 flex gap-2">
          <button className="btn-primary" onClick={load}>Apply Filters</button>
          <button className="btn-secondary" onClick={() => { setFilters({ q: '', status: '', priority: '', category_id: '', sla_breached: '' }); setTimeout(load, 0) }}>Clear</button>
        </div>
      </div>

      <div className="card overflow-x-auto p-0">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="py-3 px-4 text-left">Complaint #</th>
              <th className="text-left">Subject</th>
              <th className="text-left">Category</th>
              <th className="text-left">Customer</th>
              <th className="text-left">Agent</th>
              <th className="text-left">Priority</th>
              <th className="text-left">Status</th>
              <th className="text-left">SLA</th>
              <th className="text-left">Created</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={9} className="py-6 text-center text-slate-500">Loading…</td></tr>
            ) : rows.length === 0 ? (
              <tr><td colSpan={9} className="py-6 text-center text-slate-500">No complaints match your filters.</td></tr>
            ) : rows.map((c) => {
              const sla = slaCountdown(c.sla_due_at)
              return (
                <tr key={c.id} className="border-t hover:bg-slate-50">
                  <td className="py-2 px-4"><Link to={`/complaints/${c.id}`} className="text-brand-600 font-mono text-xs hover:underline">{c.complaint_number}</Link></td>
                  <td className="max-w-[260px] truncate" title={c.subject}>{c.subject}</td>
                  <td className="text-xs">{c.category_name}</td>
                  <td className="text-xs">{c.customer_name}</td>
                  <td className="text-xs">{c.assigned_agent_name || '—'}</td>
                  <td><PriorityBadge priority={c.priority} /></td>
                  <td><StatusBadge status={c.status} /></td>
                  <td className={sla.breached ? 'text-rose-700 font-medium text-xs' : 'text-emerald-700 text-xs'}>{sla.label}</td>
                  <td className="text-xs text-slate-500">{formatDate(c.created_at)}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
