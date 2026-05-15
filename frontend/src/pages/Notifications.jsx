import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../lib/api'
import { timeAgo } from '../lib/helpers'

export default function Notifications() {
  const [items, setItems] = useState([])
  const [unreadOnly, setUnreadOnly] = useState(false)

  const load = () => {
    api.get('/notifications', { params: unreadOnly ? { unread_only: true } : {} })
       .then((r) => setItems(r.data))
  }
  useEffect(() => { load() // eslint-disable-next-line react-hooks/exhaustive-deps
                  }, [unreadOnly])

  async function markRead(id) {
    await api.post(`/notifications/${id}/read`); load()
  }
  async function markAll() {
    await api.post('/notifications/read-all'); load()
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-800">Notifications</h1>
        <div className="flex gap-2">
          <label className="flex items-center text-sm gap-2">
            <input type="checkbox" checked={unreadOnly} onChange={(e) => setUnreadOnly(e.target.checked)} />
            Unread only
          </label>
          <button className="btn-secondary" onClick={markAll}>Mark all read</button>
        </div>
      </div>

      <div className="card p-0">
        {items.length === 0 ? (
          <div className="p-6 text-center text-slate-500 text-sm">No notifications.</div>
        ) : items.map((n) => (
          <div key={n.id}
               className={`flex items-start justify-between px-4 py-3 border-b last:border-0 ${n.is_read ? '' : 'bg-brand-50/50'}`}>
            <div>
              <div className="font-medium text-slate-800">{n.title}</div>
              <div className="text-sm text-slate-600">{n.message}</div>
              <div className="text-xs text-slate-500 mt-1">
                {timeAgo(n.created_at)}
                {n.complaint_id && <> · <Link to={`/complaints/${n.complaint_id}`} className="text-brand-600 hover:underline">View complaint</Link></>}
              </div>
            </div>
            {!n.is_read && (
              <button className="btn-secondary text-xs" onClick={() => markRead(n.id)}>Mark read</button>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
