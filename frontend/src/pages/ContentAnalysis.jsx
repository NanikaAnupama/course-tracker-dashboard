import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ReferenceLine, LabelList, Cell,
} from 'recharts'
import { useApi, Loading, ErrorState, Card, ChartTip, Legend } from '../components/ui'
import { CONTENT_COLORS, GRID, AXIS } from '../theme'
import { fmtInt, truncate } from '../utils'

export default function ContentAnalysis() {
  const overview = useApi('/api/overview')
  const courses = useApi('/api/courses')

  if (overview.loading || courses.loading) return <Loading />
  if (overview.error) return <ErrorState error={overview.error} />
  if (courses.error) return <ErrorState error={courses.error} />

  // NB: keep `fill` out of the row objects — recharts lets a datum's own
  // `fill` override the per-series color, which breaks the stacked chart.
  const ct = overview.data.contentTypes

  const gaps = courses.data
    .map((c) => ({
      name: c.name,
      units: c.units,
      videosGap: c.videosPending,
      podcastsGap: c.podcastsPending,
      guidesGap: c.guidesPending,
      totalGap: c.videosPending + c.podcastsPending + c.guidesPending,
    }))
    .filter((c) => c.totalGap > 0)
    .sort((a, b) => b.totalGap - a.totalGap)

  return (
    <>
      <div className="grid two-col">
        <Card title="Completed vs Pending per Content Type" sub="Stacked totals across all courses">
          <ResponsiveContainer width="100%" height={340}>
            <BarChart data={ct} margin={{ top: 8, right: 8 }} barSize={64}>
              <CartesianGrid vertical={false} stroke={GRID} />
              <XAxis dataKey="name" tick={{ fill: '#47536b', fontSize: 13 }} axisLine={{ stroke: GRID }} tickLine={false} />
              <YAxis tick={{ fill: AXIS, fontSize: 12 }} axisLine={false} tickLine={false} />
              <Tooltip cursor={{ fill: '#f4f6fa' }} content={<ChartTip total />} />
              <Bar isAnimationActive={false} dataKey="done" name="Completed" stackId="a" fill="#059669" />
              <Bar isAnimationActive={false} dataKey="pending" name="Still Pending" stackId="a" fill="#dc2626" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <Legend items={[{ name: 'Completed', color: '#059669' }, { name: 'Still Pending', color: '#dc2626' }]} />
        </Card>

        <Card title="Completion Rate per Content Type" sub="Which content type is closest to — or farthest from — 100%?">
          <ResponsiveContainer width="100%" height={340}>
            <BarChart data={ct} layout="vertical" margin={{ left: 8, right: 48, top: 8 }} barSize={26}>
              <CartesianGrid horizontal={false} stroke={GRID} />
              <XAxis type="number" domain={[0, 100]} tick={{ fill: AXIS, fontSize: 12 }}
                tickFormatter={(v) => `${v}%`} axisLine={{ stroke: GRID }} tickLine={false} />
              <YAxis type="category" dataKey="name" width={98} tick={{ fill: '#47536b', fontSize: 13 }}
                axisLine={false} tickLine={false} />
              <Tooltip cursor={{ fill: '#f4f6fa' }} content={({ active, payload, label }) => {
                if (!active || !payload?.length) return null
                const d = payload[0].payload
                return (
                  <div className="tip">
                    <div className="tip-title">{label}</div>
                    <div className="tip-row">Completion <span className="v">{d.pct}%</span></div>
                    <div className="tip-row">Done <span className="v">{fmtInt(d.done)}</span></div>
                    <div className="tip-row">Pending <span className="v">{fmtInt(d.pending)}</span></div>
                  </div>
                )
              }} />
              <ReferenceLine x={100} stroke={AXIS} strokeDasharray="4 4" />
              <Bar isAnimationActive={false} dataKey="pct" name="Completion %" radius={[0, 4, 4, 0]}>
                {ct.map((c) => <Cell key={c.name} fill={CONTENT_COLORS[c.name]} />)}
                <LabelList dataKey="pct" position="right" formatter={(v) => `${v}%`}
                  style={{ fill: '#0f172a', fontSize: 12, fontWeight: 700 }} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <Card className="section-gap"
        title="Top 15 Courses — Most Content Still Missing"
        sub="Sorted by total AI Videos, Podcasts, and Study Guides still needed"
      >
        <div className="table-wrap scroll-y">
          <table className="data">
            <thead>
              <tr>
                <th>Course Name</th>
                <th className="num">Units</th>
                <th className="num">AI Videos Needed</th>
                <th className="num">Podcasts Needed</th>
                <th className="num">Study Guides Needed</th>
                <th className="num">Total Needed</th>
              </tr>
            </thead>
            <tbody>
              {gaps.slice(0, 15).map((c) => (
                <tr key={c.name}>
                  <td title={c.name}>{truncate(c.name, 70)}</td>
                  <td className="num">{c.units}</td>
                  <td className="num">{c.videosGap}</td>
                  <td className="num">{c.podcastsGap}</td>
                  <td className="num">{c.guidesGap}</td>
                  <td className="num"><b>{c.totalGap}</b></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  )
}
