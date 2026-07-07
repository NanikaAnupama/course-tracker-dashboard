import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ReferenceLine, LabelList,
} from 'recharts'
import { useApi, Loading, ErrorState, Card, KpiCard, ChartTip, PctBar, StatusChip, Legend } from '../components/ui'
import { CONTENT_COLORS, GRID, AXIS } from '../theme'
import { fmtInt, truncate } from '../utils'

const PENDING_KEYS = [
  { key: 'videosPending', name: 'AI Videos Needed', color: CONTENT_COLORS['AI Videos'] },
  { key: 'podcastsPending', name: 'Podcasts Needed', color: CONTENT_COLORS['Podcasts'] },
  { key: 'guidesPending', name: 'Study Guides Needed', color: CONTENT_COLORS['Study Guides'] },
]

export default function QuickWins() {
  const { data, error, loading } = useApi('/api/courses')
  if (loading) return <Loading />
  if (error) return <ErrorState error={error} />

  const qw = data.filter((c) => c.pct >= 75 && c.pct < 100).sort((a, b) => b.pct - a.pct)
  if (qw.length === 0) {
    return <div className="state"><h3>No quick wins right now</h3><p>No courses are currently in the 75–99% range.</p></div>
  }

  const totalPending = qw.reduce((a, c) => a + c.pending, 0)
  const avgPct = qw.reduce((a, c) => a + c.pct, 0) / qw.length
  const byPending = [...qw].sort((a, b) => a.pending - b.pending).slice(0, 12)
    .map((c) => ({ ...c, shortName: truncate(c.name, 38) }))
  const byPct = [...qw].slice(0, 12).sort((a, b) => a.pct - b.pct)
    .map((c) => ({ ...c, shortName: truncate(c.name, 38) }))

  return (
    <>
      <div className="grid kpi-grid">
        <KpiCard icon="🏁" tint="#047857" label="Quick Win Courses" value={qw.length} />
        <KpiCard icon="📦" tint="#d97706" label="Total Content Needed" value={fmtInt(totalPending)} />
        <KpiCard icon="📈" tint="#2563eb" label="Average Completion" value={`${avgPct.toFixed(1)}%`} />
      </div>

      <div className="grid two-col section-gap">
        <Card title="What Each Quick Win Course Still Needs" sub="Short bars = easiest to finish first. Hover for details.">
          <ResponsiveContainer width="100%" height={Math.max(340, byPending.length * 42)}>
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

        <Card title="Current Completion of Quick Win Courses" sub="All 75%+ done — just a final push needed">
          <ResponsiveContainer width="100%" height={Math.max(340, byPct.length * 42)}>
            <BarChart data={byPct} layout="vertical" margin={{ left: 8, right: 52, top: 4 }} barSize={17}>
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
                    <div className="tip-row">Items left <span className="v">{d.pending}</span></div>
                  </div>
                )
              }} />
              <ReferenceLine x={100} stroke={AXIS} strokeDasharray="4 4" />
              <Bar isAnimationActive={false} dataKey="pct" name="Completion %" fill="#059669" radius={[0, 4, 4, 0]}>
                <LabelList dataKey="pct" position="right" formatter={(v) => `${v}%`}
                  style={{ fill: '#0f172a', fontSize: 11.5, fontWeight: 700 }} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <Card className="section-gap" title="Quick Win Courses — Full Details">
        <div className="table-wrap scroll-y">
          <table className="data">
            <thead>
              <tr>
                <th>Course Name</th>
                <th>Subject Area</th>
                <th className="num">Units</th>
                <th>Progress</th>
                <th className="num">AI Videos ✓</th>
                <th className="num">Podcasts ✓</th>
                <th className="num">Study Guides ✓</th>
                <th className="num">To Complete</th>
              </tr>
            </thead>
            <tbody>
              {qw.map((c) => (
                <tr key={c.name}>
                  <td title={c.name}>{truncate(c.name, 60)}</td>
                  <td>{c.subject}</td>
                  <td className="num">{c.units}</td>
                  <td><PctBar pct={c.pct} color="#059669" /></td>
                  <td className="num">{c.videosDone}</td>
                  <td className="num">{c.podcastsDone}</td>
                  <td className="num">{c.guidesDone}</td>
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
