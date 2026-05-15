import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../lib/api'
import { useAuth } from '../context/AuthContext'
import { StatusBadge, PriorityBadge } from '../components/Badges.jsx'
import { formatDate, slaCountdown } from '../lib/helpers'

export default function AgentQueue() {
  const { user } = useAuth()
  const [rows, setRows] = useState([])

  useEffect(() => {
    if (!user) return
    api.get(`/complaints?assigned_agent_id=${user.id}`).then((r) => setRows(r.data))
  }, [user])

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-slate-800">My Work Queue</h1>
      <p className="text-sm text-slate-500">Complaints currently assigned to you.</p>

      <div className="card p-0 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr><th className="py-3 px-4 text-left">Complaint</th><th className="text-left">Subject</th>
              <th>Priority</th><th>Status</th><th>SLA</th><th>Created</th></tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr><td colSpan={6} className="py-6 text-center text-slate-500">No complaints assigned to you.</td></tr>
            ) : rows.map((c) => {
              const sla = slaCountdown(c.sla_due_at)
              return (
                <tr key={c.id} className="border-t hover:bg-slate-50">
                  <td className="px-4 py-2"><Link to={`/complaints/${c.id}`} className="text-brand-600 font-mono text-xs hover:underline">{c.complaint_number}</Link></td>
                  <td className="truncate max-w-[300px]">{c.subject}</td>
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
    </div>
  )
}
