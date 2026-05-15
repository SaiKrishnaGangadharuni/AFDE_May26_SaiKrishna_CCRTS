import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../lib/api'
import { useAuth } from '../context/AuthContext'
import { StatusBadge, PriorityBadge, SlaBadge } from '../components/Badges.jsx'
import { formatDate, slaCountdown } from '../lib/helpers'

export default function ComplaintDetail() {
  const { id } = useParams()
  const nav = useNavigate()
  const { user, hasRole } = useAuth()
  const [c, setC] = useState(null)
  const [history, setHistory] = useState([])
  const [agents, setAgents] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [files, setFiles] = useState([])

  // Action modal state
  const [action, setAction] = useState(null) // 'assign' | 'resolve' | 'escalate' | 'reopen' | 'status' | 'feedback'
  const [actionData, setActionData] = useState({})

  const load = () => {
    setError('')
    api.get(`/complaints/${id}`).then((r) => setC(r.data))
       .catch((e) => setError(e?.response?.data?.detail || 'Failed to load complaint'))
    api.get(`/complaints/${id}/history`).then((r) => setHistory(r.data)).catch(() => {})
  }

  useEffect(() => { load() // eslint-disable-next-line react-hooks/exhaustive-deps
                  }, [id])

  useEffect(() => {
    if (hasRole('Admin', 'Supervisor')) {
      api.get('/users/agents').then((r) => setAgents(r.data)).catch(() => {})
    }
  }, [hasRole])

  if (error) return <div className="card text-rose-600">{error}</div>
  if (!c) return <div className="text-sm text-slate-500">Loading…</div>

  const sla = slaCountdown(c.sla_due_at)
  const role = user?.role?.name
  const isOwner = c.customer.id === user?.id
  const isAssignedAgent = c.assigned_agent?.id === user?.id

  const canAssign = (role === 'Admin' || role === 'Supervisor') &&
                    !['Closed'].includes(c.status)
  const canResolve = (role === 'Admin' || role === 'Supervisor' ||
                      (role === 'SupportAgent' && isAssignedAgent)) &&
                    !['Resolved', 'Closed'].includes(c.status)
  const canEscalate = role !== 'Customer' &&
                      !['Closed', 'Resolved', 'Escalated'].includes(c.status)
  const canReopen = ['Resolved', 'Closed'].includes(c.status) && (isOwner || role !== 'Customer')
  const canCloseAsCustomer = isOwner && c.status === 'Resolved'
  const canChangeStatus = !['Customer'].includes(role) &&
                          (role === 'Admin' || role === 'Supervisor' || isAssignedAgent)
  const canSubmitFeedback = isOwner && ['Resolved', 'Closed'].includes(c.status) && !c.feedback

  async function performAction() {
    setBusy(true)
    try {
      if (action === 'assign') {
        await api.post(`/complaints/${id}/assign`, { agent_id: Number(actionData.agent_id) })
      } else if (action === 'status') {
        await api.post(`/complaints/${id}/status`, { status: actionData.status, comment: actionData.comment })
      } else if (action === 'escalate') {
        await api.post(`/complaints/${id}/escalate`, { reason: actionData.reason })
      } else if (action === 'resolve') {
        await api.post(`/complaints/${id}/resolve`, { resolution_notes: actionData.resolution_notes })
      } else if (action === 'reopen') {
        await api.post(`/complaints/${id}/reopen`, { reason: actionData.reason })
      } else if (action === 'close') {
        await api.post(`/complaints/${id}/status`, { status: 'Closed', comment: 'Closed by customer' })
      } else if (action === 'feedback') {
        await api.post(`/complaints/${id}/feedback`, {
          rating: Number(actionData.rating), comments: actionData.comments,
        })
      }
      setAction(null); setActionData({}); load()
    } catch (e) {
      alert(e?.response?.data?.detail || 'Action failed')
    } finally {
      setBusy(false)
    }
  }

  async function uploadAttachments() {
    if (files.length === 0) return
    setBusy(true)
    try {
      for (const f of files) {
        const fd = new FormData()
        fd.append('file', f)
        await api.post(`/complaints/${id}/attachments`, fd,
                       { headers: { 'Content-Type': 'multipart/form-data' } })
      }
      setFiles([]); load()
    } catch (e) {
      alert(e?.response?.data?.detail || 'Upload failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-4">
      <button onClick={() => nav('/complaints')} className="text-sm text-brand-600 hover:underline">← Back to list</button>

      <div className="card">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <div className="text-xs font-mono text-slate-500">{c.complaint_number}</div>
            <h1 className="text-2xl font-semibold text-slate-800 mt-1">{c.subject}</h1>
            <div className="flex flex-wrap gap-2 mt-3">
              <StatusBadge status={c.status} />
              <PriorityBadge priority={c.priority} />
              <SlaBadge breached={c.sla_breached} />
              <span className="badge bg-slate-100 text-slate-700">{c.category.name}</span>
            </div>
          </div>
          <div className="text-right text-xs text-slate-500 space-y-1">
            <div>Created: {formatDate(c.created_at)}</div>
            <div>SLA due: {formatDate(c.sla_due_at)} <span className={sla.breached ? 'text-rose-600 font-medium' : 'text-emerald-700 font-medium'}>({sla.label})</span></div>
            {c.resolved_at && <div>Resolved: {formatDate(c.resolved_at)}</div>}
            {c.closed_at && <div>Closed: {formatDate(c.closed_at)}</div>}
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-4 mt-5 text-sm">
          <div><div className="text-xs uppercase text-slate-500">Customer</div>
               <div>{c.customer.name}</div><div className="text-xs text-slate-500">{c.customer.email}</div></div>
          <div><div className="text-xs uppercase text-slate-500">Assigned Agent</div>
               <div>{c.assigned_agent?.name || <span className="text-slate-400">Unassigned</span>}</div>
               {c.assigned_agent?.email && <div className="text-xs text-slate-500">{c.assigned_agent.email}</div>}</div>
          <div><div className="text-xs uppercase text-slate-500">Category</div>
               <div>{c.category.name}</div></div>
        </div>

        <div className="mt-5">
          <div className="text-xs uppercase text-slate-500">Description</div>
          <p className="text-sm text-slate-700 whitespace-pre-wrap mt-1">{c.description}</p>
        </div>

        {c.resolution_notes && (
          <div className="mt-5 p-3 bg-emerald-50 rounded border border-emerald-200">
            <div className="text-xs uppercase text-emerald-700 font-semibold">Resolution</div>
            <p className="text-sm text-emerald-900 whitespace-pre-wrap mt-1">{c.resolution_notes}</p>
          </div>
        )}
        {c.escalation_reason && (
          <div className="mt-3 p-3 bg-rose-50 rounded border border-rose-200">
            <div className="text-xs uppercase text-rose-700 font-semibold">Escalation Reason</div>
            <p className="text-sm text-rose-900 whitespace-pre-wrap mt-1">{c.escalation_reason}</p>
          </div>
        )}
      </div>

      {/* Action toolbar */}
      <div className="card">
        <h3 className="font-semibold text-slate-800 mb-2">Actions</h3>
        <div className="flex flex-wrap gap-2">
          {canAssign && <button className="btn-primary" onClick={() => setAction('assign')}>Assign Agent</button>}
          {canChangeStatus && <button className="btn-secondary" onClick={() => setAction('status')}>Update Status</button>}
          {canResolve && <button className="btn-primary" onClick={() => setAction('resolve')}>Mark Resolved</button>}
          {canEscalate && <button className="btn-danger" onClick={() => setAction('escalate')}>Escalate</button>}
          {canCloseAsCustomer && <button className="btn-primary" onClick={() => { setActionData({ status: 'Closed' }); setAction('close') }}>Confirm Resolution & Close</button>}
          {canReopen && <button className="btn-secondary" onClick={() => setAction('reopen')}>Reopen</button>}
          {canSubmitFeedback && <button className="btn-primary" onClick={() => setAction('feedback')}>Submit Feedback</button>}
        </div>
      </div>

      {/* Attachments */}
      <div className="card">
        <h3 className="font-semibold text-slate-800 mb-3">Attachments ({c.attachments.length})</h3>
        {c.attachments.length === 0 && <div className="text-sm text-slate-500 mb-3">No attachments yet.</div>}
        <ul className="space-y-1 text-sm">
          {c.attachments.map((a) => (
            <li key={a.id} className="flex items-center justify-between border-b border-slate-100 py-2">
              <span>{a.file_name} <span className="text-xs text-slate-400">({Math.round((a.size_bytes || 0) / 1024)} KB)</span></span>
              <a className="text-brand-600 hover:underline text-xs"
                 href={`/api/complaints/${id}/attachments/${a.id}/download`} target="_blank" rel="noreferrer">
                Download
              </a>
            </li>
          ))}
        </ul>
        <div className="mt-4 flex items-center gap-2">
          <input type="file" multiple className="input" onChange={(e) => setFiles([...e.target.files])} />
          <button className="btn-secondary" disabled={busy || files.length === 0} onClick={uploadAttachments}>Upload</button>
        </div>
      </div>

      {/* Feedback */}
      {c.feedback && (
        <div className="card">
          <h3 className="font-semibold text-slate-800 mb-2">Customer Feedback</h3>
          <div className="text-amber-600 text-lg">{'★'.repeat(c.feedback.rating)}{'☆'.repeat(5 - c.feedback.rating)}</div>
          {c.feedback.comments && <p className="text-sm text-slate-700 mt-2">{c.feedback.comments}</p>}
          <div className="text-xs text-slate-500 mt-2">Submitted {formatDate(c.feedback.submitted_at)}</div>
        </div>
      )}

      {/* History timeline */}
      <div className="card">
        <h3 className="font-semibold text-slate-800 mb-3">Audit Trail / History</h3>
        {history.length === 0 ? (
          <div className="text-sm text-slate-500">No history.</div>
        ) : (
          <ol className="space-y-3">
            {history.map((h) => (
              <li key={h.id} className="border-l-2 border-brand-200 pl-3 pb-1">
                <div className="flex items-baseline justify-between gap-2 flex-wrap">
                  <div className="text-sm font-medium text-slate-800">
                    {h.action.replace('_', ' ')}
                    {h.old_status && h.new_status && (
                      <span className="text-xs text-slate-500 ml-2">
                        {h.old_status} → {h.new_status}
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate-400">{formatDate(h.updated_at)}</div>
                </div>
                {h.comment && <p className="text-sm text-slate-600 mt-1">{h.comment}</p>}
                {h.updated_by_user && (
                  <div className="text-xs text-slate-500 mt-1">
                    by {h.updated_by_user.name} ({h.updated_by_user.role.name})
                  </div>
                )}
              </li>
            ))}
          </ol>
        )}
      </div>

      {/* Action Modal */}
      {action && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">
              {action === 'assign' && 'Assign to Agent'}
              {action === 'status' && 'Change Status'}
              {action === 'escalate' && 'Escalate Complaint'}
              {action === 'resolve' && 'Mark as Resolved'}
              {action === 'reopen' && 'Reopen Complaint'}
              {action === 'close' && 'Confirm and Close'}
              {action === 'feedback' && 'Submit Feedback'}
            </h3>

            {action === 'assign' && (
              <div><label className="label">Agent</label>
                <select className="input" value={actionData.agent_id || ''}
                        onChange={(e) => setActionData({ agent_id: e.target.value })}>
                  <option value="">Select…</option>
                  {agents.map((a) => <option key={a.id} value={a.id}>{a.name} ({a.email})</option>)}
                </select>
              </div>
            )}
            {action === 'status' && (
              <div className="space-y-3">
                <div><label className="label">New Status</label>
                  <select className="input" value={actionData.status || ''}
                          onChange={(e) => setActionData({ ...actionData, status: e.target.value })}>
                    <option value="">Select…</option>
                    {['Assigned','In Progress','Pending Customer Response','Resolved','Closed'].map((s) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>
                <div><label className="label">Comment</label>
                  <textarea className="input" rows={3} value={actionData.comment || ''}
                            onChange={(e) => setActionData({ ...actionData, comment: e.target.value })} />
                </div>
              </div>
            )}
            {action === 'escalate' && (
              <div><label className="label">Reason for escalation</label>
                <textarea className="input" rows={4} value={actionData.reason || ''}
                          onChange={(e) => setActionData({ reason: e.target.value })} required />
              </div>
            )}
            {action === 'resolve' && (
              <div><label className="label">Resolution notes</label>
                <textarea className="input" rows={4} value={actionData.resolution_notes || ''}
                          onChange={(e) => setActionData({ resolution_notes: e.target.value })} required />
              </div>
            )}
            {action === 'reopen' && (
              <div><label className="label">Reason to reopen</label>
                <textarea className="input" rows={3} value={actionData.reason || ''}
                          onChange={(e) => setActionData({ reason: e.target.value })} required />
              </div>
            )}
            {action === 'feedback' && (
              <div className="space-y-3">
                <div><label className="label">Rating (1–5)</label>
                  <select className="input" value={actionData.rating || ''}
                          onChange={(e) => setActionData({ ...actionData, rating: e.target.value })}>
                    <option value="">Select…</option>
                    {[1,2,3,4,5].map((n) => <option key={n} value={n}>{n} – {'★'.repeat(n)}</option>)}
                  </select>
                </div>
                <div><label className="label">Comments</label>
                  <textarea className="input" rows={3} value={actionData.comments || ''}
                            onChange={(e) => setActionData({ ...actionData, comments: e.target.value })} />
                </div>
              </div>
            )}

            <div className="mt-5 flex gap-2 justify-end">
              <button className="btn-secondary" onClick={() => { setAction(null); setActionData({}) }} disabled={busy}>Cancel</button>
              <button className="btn-primary" onClick={performAction} disabled={busy}>
                {busy ? 'Working…' : 'Confirm'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
