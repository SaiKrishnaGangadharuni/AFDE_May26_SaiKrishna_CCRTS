import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import api from '../lib/api'

export default function Reports() {
  const [agents, setAgents] = useState([])
  const [cats, setCats] = useState([])
  const [trends, setTrends] = useState([])
  const [csat, setCsat] = useState(null)

  useEffect(() => {
    api.get('/dashboard/agent-performance').then((r) => setAgents(r.data)).catch(() => {})
    api.get('/dashboard/category-breakdown').then((r) => setCats(r.data.filter((c) => c.total > 0))).catch(() => {})
    api.get('/dashboard/trends?months=12').then((r) => setTrends(r.data)).catch(() => {})
    api.get('/dashboard/customer-satisfaction').then((r) => setCsat(r.data)).catch(() => {})
  }, [])

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-semibold text-slate-800">Reports &amp; Analytics</h1>

      <div className="card">
        <h3 className="font-semibold text-slate-800 mb-3">Agent Performance</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-xs uppercase text-slate-500 border-b">
              <tr><th className="py-2 text-left">Agent</th>
                  <th className="text-right">Assigned</th>
                  <th className="text-right">Resolved</th>
                  <th className="text-right">Avg Hrs to Resolve</th>
                  <th className="text-right">SLA Breaches</th></tr>
            </thead>
            <tbody>
              {agents.length === 0 ? (
                <tr><td colSpan={5} className="py-4 text-center text-slate-500">No data.</td></tr>
              ) : agents.map((a) => (
                <tr key={a.agent_id} className="border-b last:border-0">
                  <td className="py-2">{a.agent_name}</td>
                  <td className="text-right">{a.total_assigned}</td>
                  <td className="text-right text-emerald-700">{a.resolved}</td>
                  <td className="text-right">{a.avg_resolution_hours ?? '—'}</td>
                  <td className="text-right text-rose-700">{a.sla_breaches}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        <div className="card">
          <h3 className="font-semibold text-slate-800 mb-3">Category Distribution</h3>
          <div style={{ width: '100%', height: 280 }}>
            <ResponsiveContainer>
              <BarChart data={cats} layout="vertical" margin={{ left: 80 }}>
                <XAxis type="number" fontSize={11} />
                <YAxis dataKey="category_name" type="category" fontSize={11} width={150} />
                <Tooltip />
                <Bar dataKey="total" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <h3 className="font-semibold text-slate-800 mb-3">12-Month Trend</h3>
          <div style={{ width: '100%', height: 280 }}>
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

      {csat && (
        <div className="card">
          <h3 className="font-semibold text-slate-800 mb-3">Customer Satisfaction</h3>
          <div className="flex flex-wrap gap-6 items-baseline">
            <div>
              <div className="text-xs uppercase text-slate-500">Avg Rating</div>
              <div className="text-3xl font-semibold text-amber-600">{csat.average_rating ?? '—'} <span className="text-base text-slate-500">/ 5</span></div>
            </div>
            <div>
              <div className="text-xs uppercase text-slate-500">Responses</div>
              <div className="text-2xl font-semibold">{csat.total_responses}</div>
            </div>
            <div className="text-sm">
              <div className="text-xs uppercase text-slate-500 mb-1">Distribution</div>
              {[5,4,3,2,1].map((r) => (
                <div key={r}>{'★'.repeat(r)} — {csat.distribution[r] || 0}</div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
