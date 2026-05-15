import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../lib/api'
import { StatusBadge, PriorityBadge } from '../components/Badges.jsx'
import { formatDate, slaCountdown } from '../lib/helpers'

export default function Escalations() {
  const [esc, setEsc] = useState([])
  const [breached, setBreached] = useState([])

  useEffect(() => {
    api.get('/complaints?status=Escalated').then((r) => setEsc(r.data))
    api.get('/complaints?sla_breached=true').then((r) => setBreached(r.data))
  }, [])

  function Section({ title, rows, accent }) {
    return (
      <div className="card p-0 overflow-x-auto">
        <div className={`px-4 py-3 border-b ${accent}`}>
          <h3 className="font-semibold">{title} ({rows.length})</h3>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr><th className="py-2 px-4 text-left">#</th><th className="text-left">Subject</th>
              <th>Customer</th><th>Agent</th><th>Priority</th><th>Status</th><th>SLA</th><th>Created</th></tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr><td colSpan={8} className="py-4 text-center text-slate-500">None right now.</td></tr>
            ) : rows.map((c) => {
              const sla = slaCountdown(c.sla_due_at)
              return (
                <tr key={c.id} className="border-t hover:bg-slate-50">
                  <td className="px-4 py-2"><Link to={`/complaints/${c.id}`} className="text-brand-600 font-mono text-xs hover:underline">{c.complaint_number}</Link></td>
                  <td className="truncate max-w-[260px]">{c.subject}</td>
                  <td className="text-xs">{c.customer_name}</td>
                  <td className="text-xs">{c.assigned_agent_name || '—'}</td>
                  <td className="text-center"><PriorityBadge priority={c.priority} /></td>
                  <td className="text-center"><StatusBadge status={c.status} /></td>
                  <td className={`text-xs text-center ${sla.breached ? 'text-rose-700 font-medium' : 'text-emerald-700'}`}>{sla.label}</td>
                  <td className="text-xs text-slate-500 text-center">{formatDate(c.created_at)}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-semibold text-slate-800">Escalations &amp; SLA Breaches</h1>
      <Section title="Escalated Complaints" rows={esc} accent="bg-rose-50 text-rose-700" />
      <Section title="SLA Breached Complaints" rows={breached} accent="bg-amber-50 text-amber-700" />
    </div>
  )
}
