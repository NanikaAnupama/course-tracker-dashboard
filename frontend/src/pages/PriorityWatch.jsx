import { useState } from 'react'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ReferenceLine, LabelList,
} from 'recharts'
import { useApi, Loading, ErrorState, Card, KpiCard, SubTabs, ChartTip, PctBar, Legend } from '../components/ui'
import { CONTENT_COLORS, GRID, AXIS } from '../theme'
import { fmtInt, truncate } from '../utils'

const TABS = ['High Risk Courses', 'Not Started']

const PENDING_KEYS = [
  { key: 'videosPending', name: 'AI Videos', color: CONTENT_COLORS['AI Videos'] },
  { key: 'podcastsPending', name: 'Podcasts', color: CONTENT_COLORS['Podcasts'] },
  { key: 'guidesPending', name: 'Study Guides', color: CONTENT_COLORS['Study Guides'] },
]

const SIZE_ORDER = ['Small (1-3 units)', 'Medium (4-7 units)', 'Large (8-12 units)', 'Very Large (13+ units)']

export default function PriorityWatch() {
  const [tab, setTab] = useState(TABS[0])
  const { data, error, loading } = useApi('/api/courses')
  if (loading) return <Loading />
  if (error) return <ErrorState error={error} />

  return (
    <>
      <SubTabs tabs={TABS} active={tab} onChange={setTab} />
      {tab === TABS[0] ? <HighRisk courses={data} /> : <NotStarted courses={data} />}
    </>
  )
}

function HighRisk({ courses }) {
  const pc = courses.filter((c) => c.units >= 5 && c.pct < 50).sort((a, b) => b.priorityScore - a.priorityScore)
  if (pc.length === 0) {
    return <div className="state"><h3>All clear</h3><p>No large courses are critically behind.</p></div>
  }
  const totalPending = pc.reduce((a, c) => a + c.pending, 0)
  const avgPct = pc.reduce((a, c) => a + c.pct, 0) / pc.length
  const top10 = pc.slice(0, 10)
  const byPending = [...top10].sort((a, b) => a.pending - b.pending).map((c) => ({ ...c, shortName: truncate(c.name, 38) }))
  const byPct = [...top10].sort((a, b) => a.pct - b.pct).map((c) => ({ ...c, shortName: truncate(c.name, 38) }))

  return (
    <>
      <div className="grid kpi-grid">
        <KpiCard icon="⚠️" tint="#dc2626" label="High Risk Courses" value={pc.length} />
        <KpiCard icon="📦" tint="#d97706" label="Content Pending" value={fmtInt(totalPending)} />
        <KpiCard icon="📉" tint="#2563eb" label="Avg Completion" value={`${avgPct.toFixed(1)}%`} />
      </div>

      <div className="grid two-col section-gap">
        <Card title="What Each At-Risk Course Still Needs" sub="Longer bars = more remaining. Hover for details.">
          <ResponsiveContainer width="100%" height={Math.max(340, byPending.length * 44)}>
            <BarChart data={byPending} layout="vertical" margin={{ left: 8, right: 34, top: 4 }} barSize={17}>
              <CartesianGrid horizontal={false} stroke={GRID} />
              <XAxis type="number" domain={[0, 'dataMax']} allowDataOverflow
                tick={{ fill: AXIS, fontSize: 12 }} axisLine={{ stroke: GRID }} tickLine={false} allowDecimals={false} />
              <YAxis type="category" dataKey="shortName" width={240} tick={{ fill: '#47536b', fontSize: 11.5 }}
                axisLine={false} tickLine={false} />
              <Tooltip cursor={{ fill: '#f4f6fa' }} content={<ChartTip total />} />
              {PENDING_KEYS.map((k, i) => (
                <Bar isAnimationActive={false} key={k.key} dataKey={k.key} name={k.name} stackId="p" fill={k.color}
                  radius={i === PENDING_KEYS.length - 1 ? [0, 4, 4, 0] : 0} />
              ))}
            </BarChart>
          </ResponsiveContainer>
          <Legend items={PENDING_KEYS.map((k) => ({ name: k.name, color: k.color }))} />
        </Card>

        <Card title="How Far Behind Are These Top 10 Courses?" sub="All below 50% — far from the finish line">
          <ResponsiveContainer width="100%" height={Math.max(340, byPct.length * 44)}>
            <BarChart data={byPct} layout="vertical" margin={{ left: 8, right: 60, top: 4 }} barSize={17}>
              <CartesianGrid horizontal={false} stroke={GRID} />
              <XAxis type="number" domain={[0, 100]} tick={{ fill: AXIS, fontSize: 12 }}
                tickFormatter={(v) => `${v}%`} axisLine={{ stroke: GRID }} tickLine={false} />
              <YAxis type="category" dataKey="shortName" width={240} tick={{ fill: '#47536b', fontSize: 11.5 }}
                axisLine={false} tickLine={false} />
              <Tooltip cursor={{ fill: '#f4f6fa' }} content={({ active, payload }) => {
                if (!active || !payload?.length) return null
                const d = payload[0].payload
                return (
                  <div className="tip">
                    <div className="tip-title">{d.name}</div>
                    <div className="tip-row">Completion <span className="v">{d.pct}%</span></div>
                    <div className="tip-row">Units <span className="v">{d.units}</span></div>
                    <div className="tip-row">Items pending <span className="v">{d.pending}</span></div>
                  </div>
                )
              }} />
              <ReferenceLine x={50} stroke="#d97706" strokeDasharray="4 4" />
              <Bar isAnimationActive={false} dataKey="pct" name="Completion %" fill="#dc2626" radius={[0, 4, 4, 0]}>
                <LabelList dataKey="pct" position="right" formatter={(v) => `${v}%`}
                  style={{ fill: '#0f172a', fontSize: 11.5, fontWeight: 700 }} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <Card className="section-gap" title="High Risk Courses — Full Details">
        <div className="table-wrap scroll-y">
          <table className="data">
            <thead>
              <tr>
                <th>Course Name</th>
                <th>Level</th>
                <th>Subject Area</th>
                <th className="num">Units</th>
                <th>Progress</th>
                <th className="num">Items Pending</th>
              </tr>
            </thead>
            <tbody>
              {pc.map((c) => (
                <tr key={c.name}>
                  <td title={c.name}>{truncate(c.name, 60)}</td>
                  <td>{c.level}</td>
                  <td>{c.subject}</td>
                  <td className="num">{c.units}</td>
                  <td><PctBar pct={c.pct} color="#dc2626" /></td>
                  <td className="num"><b>{c.pending}</b></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  )
}

function NotStarted({ courses }) {
  const ns = courses.filter((c) => c.pct === 0).sort((a, b) => b.units - a.units)
  if (ns.length === 0) {
    return <div className="state"><h3>All courses have started</h3><p>Nothing is sitting at 0%.</p></div>
  }
  const totalNeeded = ns.reduce((a, c) => a + c.required, 0)
  const avgSize = ns.reduce((a, c) => a + c.units, 0) / ns.length

  const bySubject = Object.values(ns.reduce((acc, c) => {
    acc[c.subject] = acc[c.subject] || { name: c.subject, courses: 0, needed: 0 }
    acc[c.subject].courses += 1
    acc[c.subject].needed += c.required
    return acc
  }, {})).sort((a, b) => b.needed - a.needed)

  const bySize = SIZE_ORDER.map((size) => {
    const rows = ns.filter((c) => c.size === size)
    return { name: size, courses: rows.length, needed: rows.reduce((a, c) => a + c.required, 0) }
  }).filter((r) => r.courses > 0)

  return (
    <>
      <div className="grid kpi-grid">
        <KpiCard icon="⭕" tint="#dc2626" label="Courses Not Started" value={ns.length} />
        <KpiCard icon="📦" tint="#d97706" label="Total Content Needed" value={fmtInt(totalNeeded)} />
        <KpiCard icon="📐" tint="#2563eb" label="Avg Course Size" value={`${avgSize.toFixed(1)} units`} />
      </div>

      <div className="grid two-col section-gap">
        <Card title="Unstarted Courses by Subject Area" sub="Which departments have the most courses waiting?">
          <ResponsiveContainer width="100%" height={Math.max(300, bySubject.length * 48)}>
            <BarChart data={bySubject} layout="vertical" margin={{ left: 8, right: 40, top: 4 }} barSize={20}>
              <CartesianGrid horizontal={false} stroke={GRID} />
              <XAxis type="number" tick={{ fill: AXIS, fontSize: 12 }} axisLine={{ stroke: GRID }} tickLine={false} allowDecimals={false} />
              <YAxis type="category" dataKey="name" width={160} tick={{ fill: '#47536b', fontSize: 12 }}
                axisLine={false} tickLine={false} />
              <Tooltip cursor={{ fill: '#f4f6fa' }} content={({ active, payload, label }) => {
                if (!active || !payload?.length) return null
                const d = payload[0].payload
                return (
                  <div className="tip">
                    <div className="tip-title">{label}</div>
                    <div className="tip-row">Items needed <span className="v">{fmtInt(d.needed)}</span></div>
                    <div className="tip-row">Courses <span className="v">{d.courses}</span></div>
                  </div>
                )
              }} />
              <Bar isAnimationActive={false} dataKey="needed" name="Items Needed" fill="#dc2626" radius={[0, 4, 4, 0]}>
                <LabelList dataKey="needed" position="right" style={{ fill: '#0f172a', fontSize: 11.5, fontWeight: 700 }} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Unstarted Courses by Size" sub="Start with the smallest for quick momentum">
          <ResponsiveContainer width="100%" height={Math.max(260, bySize.length * 56)}>
            <BarChart data={bySize} layout="vertical" margin={{ left: 8, right: 40, top: 4 }} barSize={24}>
              <CartesianGrid horizontal={false} stroke={GRID} />
              <XAxis type="number" tick={{ fill: AXIS, fontSize: 12 }} axisLine={{ stroke: GRID }} tickLine={false} allowDecimals={false} />
              <YAxis type="category" dataKey="name" width={160} tick={{ fill: '#47536b', fontSize: 12 }}
                axisLine={false} tickLine={false} />
              <Tooltip cursor={{ fill: '#f4f6fa' }} content={({ active, payload, label }) => {
                if (!active || !payload?.length) return null
                const d = payload[0].payload
                return (
                  <div className="tip">
                    <div className="tip-title">{label}</div>
                    <div className="tip-row">Items needed <span className="v">{fmtInt(d.needed)}</span></div>
                    <div className="tip-row">Courses <span className="v">{d.courses}</span></div>
                  </div>
                )
              }} />
              <Bar isAnimationActive={false} dataKey="needed" name="Content Needed" fill="#d97706" radius={[0, 4, 4, 0]}>
                <LabelList dataKey="needed" position="right" style={{ fill: '#0f172a', fontSize: 11.5, fontWeight: 700 }} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <Card className="section-gap" title="Not Started — Full List">
        <div className="table-wrap scroll-y">
          <table className="data">
            <thead>
              <tr>
                <th>Course Name</th>
                <th>Subject Area</th>
                <th className="num">Units</th>
                <th className="num">Items Needed</th>
              </tr>
            </thead>
            <tbody>
              {ns.map((c) => (
                <tr key={c.name}>
                  <td title={c.name}>{truncate(c.name, 70)}</td>
                  <td>{c.subject}</td>
                  <td className="num">{c.units}</td>
                  <td className="num"><b>{c.required}</b></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  )
}
