// Shared UI helpers — formatters and badge palettes.

export const STATUS_COLORS = {
  'Open':                       'bg-blue-100 text-blue-800',
  'Assigned':                   'bg-indigo-100 text-indigo-800',
  'In Progress':                'bg-amber-100 text-amber-800',
  'Pending Customer Response':  'bg-orange-100 text-orange-800',
  'Escalated':                  'bg-rose-100 text-rose-800',
  'Resolved':                   'bg-emerald-100 text-emerald-800',
  'Closed':                     'bg-slate-200 text-slate-700',
  'Reopened':                   'bg-purple-100 text-purple-800',
}

export const PRIORITY_COLORS = {
  'Low':      'bg-slate-100 text-slate-700',
  'Medium':   'bg-sky-100 text-sky-800',
  'High':     'bg-amber-100 text-amber-800',
  'Critical': 'bg-rose-100 text-rose-800',
}

export const STATUS_OPTIONS = [
  'Open', 'Assigned', 'In Progress', 'Pending Customer Response',
  'Escalated', 'Resolved', 'Closed', 'Reopened',
]

export const PRIORITY_OPTIONS = ['Low', 'Medium', 'High', 'Critical']

export function formatDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

export function timeAgo(iso) {
  if (!iso) return ''
  const diff = Date.now() - new Date(iso).getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

export function slaCountdown(dueIso) {
  const diffMs = new Date(dueIso).getTime() - Date.now()
  if (diffMs < 0) {
    const hours = Math.floor(-diffMs / 3600000)
    return { label: `Breached by ${hours}h`, breached: true }
  }
  const hours = Math.floor(diffMs / 3600000)
  const mins = Math.floor((diffMs % 3600000) / 60000)
  return { label: hours > 0 ? `${hours}h ${mins}m left` : `${mins}m left`, breached: false }
}
