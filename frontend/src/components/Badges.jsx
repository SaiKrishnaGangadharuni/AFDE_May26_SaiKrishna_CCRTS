import { STATUS_COLORS, PRIORITY_COLORS } from '../lib/helpers'

export function StatusBadge({ status }) {
  return <span className={`badge ${STATUS_COLORS[status] || 'bg-slate-100 text-slate-700'}`}>{status}</span>
}

export function PriorityBadge({ priority }) {
  return <span className={`badge ${PRIORITY_COLORS[priority] || 'bg-slate-100 text-slate-700'}`}>{priority}</span>
}

export function SlaBadge({ breached }) {
  if (breached) return <span className="badge bg-rose-100 text-rose-800">SLA Breached</span>
  return <span className="badge bg-emerald-100 text-emerald-800">On Track</span>
}
