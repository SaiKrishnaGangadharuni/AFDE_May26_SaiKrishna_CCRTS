import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import api from '../lib/api'
import { useAuth } from '../context/AuthContext'
import { StatusBadge, PriorityBadge } from '../components/Badges.jsx'
import { formatDate, slaCountdown } from '../lib/helpers'

const PIE_COLORS = ['#3b82f6', '#6366f1', '#f59e0b', '#fb923c', '#f43f5e', '#10b981', '#94a3b8', '#a855f7']

function StatCard({ label, value, accent }) {
  return (
    <div className="card">
      <div className="text-xs uppercase text-slate-500 tracking-wide">{label}</div>
      <div className={`text-3xl font-semibold mt-1 ${accent || 'text-slate-800'}`}>{value}</div>
    </div>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState(null)
  const [recent, setRecent] = useState([])
  const [byCategory, setByCategory] = useState([])
  const [trends, setTrends] = useState([])

  useEffect(() => {
    api.get('/dashboard/stats').then((r) => setStats(r.data)).catch(() => {})
    api.get('/complaints?page_size=8').then((r) => setRecent(r.data)).catch(() => {})
    api.get('/dashboard/category-breakdown').then((r) => setByCategory(r.data.filter((c) => c.total > 0))).catch(() => {})
    api.get('/dashboard/trends?months=6').then((r) => setTrends(r.data)).catch(() => {})
  }, [])

  if (!stats) return <div className="text-sm text-slate-500">Loading dashboard…</div>

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-800">Welcome back, {user?.name?.split(' ')[0]}</h1>
        <p className="text-sm text-slate-500">Here's the current state of complaints in the system.</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total" value={stats.total_complaints} />
        <StatCard label="Open + In Progress"
                  value={stats.open + stats.in_progress + stats.pending_customer} accent="text-amber-600" />
        <StatCard label="Escalated" value={stats.escalated} accent="text-rose-600" />
        <StatCard label="SLA Breaches" value={stats.sla_breaches} accent="text-rose-700" />
        <StatCard label="Resolved" value={stats.resolved} accent="text-emerald-600" />
        <StatCard label="Closed" value={stats.closed} accent="text-slate-600" />
        <StatCard label="Reopened" value={stats.reopened} accent="text-purple-600" />
        <StatCard label="Avg Resolution (hrs)"
                  value={stats.avg_resolution_hours ?? '—'} accent="text-brand-700" />
      </div>

      {(byCategory.length > 0 || trends.length > 0) && (
        <div className="grid lg:grid-cols-2 gap-4">
          <div className="card">
            <h3 className="font-semibold mb-2 text-slate-800">Complaints by Category</h3>
            <div style={{ width: '100%', height: 260 }}>
              <ResponsiveContainer>
                <PieChart>
                  <Pie data={byCategory} dataKey="total" nameKey="category_name" label
                       outerRadius={80} innerRadius={40}>
                    {byCategory.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                  </Pie>
                  <Tooltip />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="card">
            <h3 className="font-semibold mb-2 text-slate-800">Monthly Trend</h3>
            <div style={{ width: '100%', height: 260 }}>
              <ResponsiveContainer>
                <BarChart data={trends}>
                  <XAxis dataKey="period" fontSize={11} />
                  <YAxis fontSize={11} />
                  <Tooltip />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Bar dataKey="total" fill="#3b82f6" name="Total" />
                  <Bar dataKey="resolved" fill="#10b981" name="Resolved" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      <div className="card">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-slate-800">Recent Complaints</h3>
          <Link to="/complaints" className="text-sm text-brand-600 hover:underline">View all →</Link>
        </div>
        {recent.length === 0 ? (
          <div className="text-sm text-slate-500">No complaints to show.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-xs uppercase text-slate-500 border-b">
                <tr><th className="py-2 text-left">Number</th><th className="text-left">Subject</th>
                    <th className="text-left">Priority</th><th className="text-left">Status</th>
                    <th className="text-left">SLA</th><th className="text-left">Created</th></tr>
              </thead>
              <tbody>
                {recent.map((c) => {
                  const sla = slaCountdown(c.sla_due_at)
                  return (
                    <tr key={c.id} className="border-b last:border-0 hover:bg-slate-50">
                      <td className="py-2"><Link to={`/complaints/${c.id}`} className="text-brand-600 hover:underline font-mono text-xs">{c.complaint_number}</Link></td>
                      <td className="max-w-[300px] truncate" title={c.subject}>{c.subject}</td>
                      <td><PriorityBadge priority={c.priority} /></td>
                      <td><StatusBadge status={c.status} /></td>
                      <td className={sla.breached ? 'text-rose-700 font-medium text-xs' : 'text-emerald-700 text-xs'}>
                        {sla.label}
                      </td>
                      <td className="text-xs text-slate-500">{formatDate(c.created_at)}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
