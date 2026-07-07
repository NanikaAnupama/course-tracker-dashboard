import { useState } from 'react'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  LabelList, Cell,
} from 'recharts'
import { useApi, Loading, ErrorState, Card, SubTabs, ChartTip, PctBar, Legend } from '../components/ui'
import { CONTENT_COLORS, GRID, AXIS } from '../theme'
import { fmtInt } from '../utils'

const TABS = ['By Subject Area', 'By Course Level']

// Red→amber→green by completion, mirroring the original colourscale.
function pctColor(pct) {
  if (pct < 35) return '#dc2626'
  if (pct < 60) return '#d97706'
  if (pct < 85) return '#10b981'
  return '#047857'
}

const PENDING_KEYS = [
  { key: 'videosPending', name: 'AI Videos', color: CONTENT_COLORS['AI Videos'] },
  { key: 'podcastsPending', name: 'Podcasts', color: CONTENT_COLORS['Podcasts'] },
  { key: 'guidesPending', name: 'Study Guides', color: CONTENT_COLORS['Study Guides'] },
]

export default function SubjectLevel() {
  const [tab, setTab] = useState(TABS[0])
  const subjects = useApi('/api/subjects')
  const levels = useApi('/api/levels')

  if (subjects.loading || levels.loading) return <Loading />
  if (subjects.error) return <ErrorState error={subjects.error} />
  if (levels.error) return <ErrorState error={levels.error} />

  const isSubjects = tab === TABS[0]
  // Original app hides one-course subject areas from the subject charts.
  const rows = isSubjects
    ? subjects.data.filter((s) => s.courses >= 2).sort((a, b) => a.avgPct - b.avgPct)
    : levels.data

  const dims = isSubjects ? 'Subject Area' : 'Course Level'

  return (
    <>
      <SubTabs tabs={TABS} active={tab} onChange={setTab} />

      <div className="grid two-col">
        <Card title={`Average Completion by ${dims}`} sub="How close each group is to finishing all content">
          <ResponsiveContainer width="100%" height={Math.max(300, rows.length * 46)}>
            <BarChart data={rows} layout="vertical" margin={{ left: 8, right: 52, top: 4 }} barSize={20}>
              <CartesianGrid horizontal={false} stroke={GRID} />
              <XAxis type="number" domain={[0, 100]} tick={{ fill: AXIS, fontSize: 12 }}
                tickFormatter={(v) => `${v}%`} axisLine={{ stroke: GRID }} tickLine={false} />
              <YAxis type="category" dataKey="name" width={150} tick={{ fill: '#47536b', fontSize: 12 }}
                axisLine={false} tickLine={false} />
              <Tooltip cursor={{ fill: '#f4f6fa' }} content={({ active, payload, label }) => {
                if (!active || !payload?.length) return null
                const d = payload[0].payload
                return (
                  <div className="tip">
                    <div className="tip-title">{label}</div>
                    <div className="tip-row">Avg completion <span className="v">{d.avgPct}%</span></div>
                    <div className="tip-row">Courses <span className="v">{d.courses}</span></div>
                    <div className="tip-row">Units <span className="v">{d.units}</span></div>
                    <div className="tip-row">Items pending <span className="v">{fmtInt(d.pending)}</span></div>
                  </div>
                )
              }} />
              <Bar isAnimationActive={false} dataKey="avgPct" name="Avg Completion %" radius={[0, 4, 4, 0]}>
                {rows.map((r) => <Cell key={r.name} fill={pctColor(r.avgPct)} />)}
                <LabelList dataKey="avgPct" position="right" formatter={(v) => `${v}%`}
                  style={{ fill: '#0f172a', fontSize: 11.5, fontWeight: 700 }} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card title={`Pending Items by ${dims}`} sub="AI Videos, Podcasts & Study Guides still needed — hover for exact values">
          <ResponsiveContainer width="100%" height={Math.max(300, rows.length * 46)}>
            <BarChart data={rows} layout="vertical" margin={{ left: 8, right: 40, top: 4 }} barSize={20}>
              <CartesianGrid horizontal={false} stroke={GRID} />
              <XAxis type="number" domain={[0, 'dataMax']} allowDataOverflow
                tick={{ fill: AXIS, fontSize: 12 }} axisLine={{ stroke: GRID }} tickLine={false} />
              <YAxis type="category" dataKey="name" width={150} tick={{ fill: '#47536b', fontSize: 12 }}
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
      </div>

      <Card className="section-gap" title={`${dims} Details`}>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>{dims}</th>
                <th className="num">Courses</th>
                <th className="num">Total Units</th>
                <th className="num">Content Completed</th>
                <th className="num">Content Pending</th>
                <th>Avg Progress</th>
              </tr>
            </thead>
            <tbody>
              {[...rows].sort((a, b) => b.avgPct - a.avgPct).map((r) => (
                <tr key={r.name}>
                  <td>{r.name}</td>
                  <td className="num">{r.courses}</td>
                  <td className="num">{fmtInt(r.units)}</td>
                  <td className="num">{fmtInt(r.completed)}</td>
                  <td className="num">{fmtInt(r.pending)}</td>
                  <td><PctBar pct={r.avgPct} color={pctColor(r.avgPct)} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  )
}
