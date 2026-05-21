// Phase 2 — Analytics dashboard fed by the ETL pipeline.
import { useEffect, useState } from 'react'
import api from '../lib/api'
import {
  BarChart, Bar,
  LineChart, Line,
  PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, Legend,
  CartesianGrid, ResponsiveContainer,
} from 'recharts'

const PIE_COLORS = ['#6366f1','#10b981','#f59e0b','#ef4444','#0ea5e9','#a855f7','#ec4899','#14b8a6','#f97316','#84cc16']

function StatCard({ label, value, hint }) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
      <div className="text-xs text-slate-500 uppercase tracking-wide">{label}</div>
      <div className="mt-1 text-3xl font-semibold text-slate-800">{value}</div>
      {hint && <div className="text-xs text-slate-500 mt-1">{hint}</div>}
    </div>
  )
}

export default function Analytics() {
  const [summary, setSummary] = useState(null)
  const [sla, setSla] = useState([])
  const [cats, setCats] = useState([])
  const [trends, setTrends] = useState([])
  const [agents, setAgents] = useState([])
  const [latestRun, setLatestRun] = useState(null)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')

  async function loadAll() {
    try {
      const [s, b, c, t, a, lr] = await Promise.all([
        api.get('/analytics/summary'),
        api.get('/analytics/sla-breaches'),
        api.get('/analytics/categories'),
        api.get('/analytics/resolution-trends'),
        api.get('/analytics/agents'),
        api.get('/etl/latest').catch(() => ({ data: null })),
      ])
      setSummary(s.data)
      setSla(b.data)
      setCats(c.data)
      setTrends(t.data)
      setAgents(a.data)
      setLatestRun(lr.data)
      setError('')
    } catch (e) {
      setError(e?.response?.data?.detail || e.message)
    }
  }

  useEffect(() => { loadAll() }, [])

  async function runEtl() {
    setRunning(true)
    setError('')
    try {
      const r = await api.post('/etl/run')
      setLatestRun(r.data)
      await loadAll()
    } catch (e) {
      setError(e?.response?.data?.detail || e.message)
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-800">Analytics & ETL</h1>
          <p className="text-sm text-slate-500">
            Phase 2 — Pandas ETL pipeline ingests <code>datasets/complaints_dataset.csv</code> into analytics tables.
          </p>
        </div>
        <button
          onClick={runEtl}
          disabled={running}
          className="bg-brand-700 hover:bg-brand-600 disabled:opacity-50 text-white px-4 py-2 rounded text-sm font-medium"
        >
          {running ? 'Running ETL…' : 'Run ETL'}
        </button>
      </div>

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 px-4 py-2 rounded text-sm">
          {error}
        </div>
      )}

      {latestRun && (
        <div className="bg-slate-50 border border-slate-200 rounded p-3 text-xs text-slate-600 flex flex-wrap gap-x-6 gap-y-1">
          <span>Last run: <b>{latestRun.status}</b></span>
          <span>Extracted: <b>{latestRun.rows_extracted}</b></span>
          <span>Cleaned: <b>{latestRun.rows_after_clean}</b></span>
          <span>Loaded: <b>{latestRun.rows_loaded}</b></span>
          <span>Duplicates dropped: <b>{latestRun.duplicates_dropped}</b></span>
          <span>Null rows dropped: <b>{latestRun.null_rows_dropped}</b></span>
          {latestRun.finished_at && (
            <span>Finished: <b>{new Date(latestRun.finished_at).toLocaleString()}</b></span>
          )}
        </div>
      )}

      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <StatCard label="Total complaints" value={summary.total_complaints} />
          <StatCard label="Resolved" value={summary.total_resolved} />
          <StatCard label="SLA breaches" value={summary.total_breaches} />
          <StatCard label="Breach rate" value={summary.overall_breach_rate_pct + '%'} />
          <StatCard label="Avg resolution"
            value={summary.avg_resolution_hours != null ? summary.avg_resolution_hours + 'h' : '—'} />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* SLA breaches by priority */}
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
          <h2 className="font-semibold text-slate-700 mb-3">SLA breaches by priority</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={sla}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="priority" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="total_complaints" fill="#94a3b8" name="Total" />
              <Bar dataKey="breach_count" fill="#ef4444" name="Breaches" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Category distribution */}
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
          <h2 className="font-semibold text-slate-700 mb-3">Complaints by category</h2>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={cats}
                dataKey="total_complaints"
                nameKey="category"
                cx="50%"
                cy="50%"
                outerRadius={90}
                label={(e) => e.category}
              >
                {cats.map((_, i) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Resolution trends */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
        <h2 className="font-semibold text-slate-700 mb-3">Monthly resolution-time trend</h2>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={trends}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Line yAxisId="left"  type="monotone" dataKey="resolved_count"        stroke="#10b981" name="Resolved" />
            <Line yAxisId="right" type="monotone" dataKey="avg_resolution_hours"  stroke="#6366f1" name="Avg resolution (h)" />
            <Line yAxisId="left"  type="monotone" dataKey="breach_count"          stroke="#ef4444" name="Breaches" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Agent performance */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
        <h2 className="font-semibold text-slate-700 mb-3">Agent performance</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-600 text-left">
              <tr>
                <th className="px-3 py-2">Agent</th>
                <th className="px-3 py-2 text-right">Handled</th>
                <th className="px-3 py-2 text-right">Resolved</th>
                <th className="px-3 py-2 text-right">Breaches</th>
                <th className="px-3 py-2 text-right">Avg resolution (h)</th>
              </tr>
            </thead>
            <tbody>
              {agents.map((a) => (
                <tr key={a.agent_name} className="border-t border-slate-100">
                  <td className="px-3 py-2 font-medium">{a.agent_name}</td>
                  <td className="px-3 py-2 text-right">{a.handled_count}</td>
                  <td className="px-3 py-2 text-right text-emerald-700">{a.resolved_count}</td>
                  <td className="px-3 py-2 text-right text-rose-700">{a.breach_count}</td>
                  <td className="px-3 py-2 text-right">
                    {a.avg_resolution_hours != null ? a.avg_resolution_hours.toFixed(1) : '—'}
                  </td>
                </tr>
              ))}
              {agents.length === 0 && (
                <tr><td colSpan={5} className="px-3 py-4 text-center text-slate-500">
                  No agent data yet — run the ETL pipeline.
                </td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
