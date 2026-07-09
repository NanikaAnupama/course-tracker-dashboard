import { useMemo } from 'react'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  PieChart, Pie, Cell, AreaChart, Area, ReferenceLine, LabelList,
} from 'recharts'
import { useApi, Loading, ErrorState, Card, KpiCard, ChartTip, Legend } from '../components/ui'
import { CONTENT_COLORS, STATUS_COLORS, GRID, AXIS, ACCENT } from '../theme'
import { fmtInt, weekStartISO, weekLabel } from '../utils'

export default function Overview() {
  const { data, error, loading } = useApi('/api/overview')
  const log = useApi('/api/video-log')

  if (loading) return <Loading />
  if (error) return <ErrorState error={error} />

  const contentBars = data.contentTypes.map((c) => ({ ...c, fill: CONTENT_COLORS[c.name] }))
  const statusData = data.statusBreakdown.map((s) => ({ ...s, fill: STATUS_COLORS[s.status] }))

  return (
    <>
      <DataQualityBanner dq={data.dataQuality} />
      <div className="grid kpi-grid">
        <KpiCard icon="📚" tint="#2563eb" label="Total Courses" value={fmtInt(data.totalCourses)}
          note={`${fmtInt(data.totalUnits)} units in total`} />
        <KpiCard icon="🎯" tint="#7c3aed" label="Overall Completion" value={`${data.overallCompletion}%`}
          note={`${fmtInt(data.totalCompleted)} of ${fmtInt(data.totalRequired)} items`} />
        <KpiCard icon="🎬" tint="#d97706" label="AI Videos Completed" value={fmtInt(data.videosDone)}
          suffix={`/ ${fmtInt(data.totalUnits)}`} />
        <KpiCard icon="🎙️" tint="#0284c7" label="Podcasts Completed" value={fmtInt(data.podcastsDone)}
          suffix={`/ ${fmtInt(data.totalUnits)}`} />
        <KpiCard icon="📖" tint="#059669" label="Study Guides Completed" value={fmtInt(data.guidesDone)}
          suffix={`/ ${fmtInt(data.totalUnits)}`} />
        <KpiCard icon="🧩" tint="#e11d48" label="H5P Quizzes Completed" value={fmtInt(data.h5pDone)}
          suffix={`/ ${fmtInt(data.totalUnits)}`} />
        <KpiCard icon="✅" tint="#047857" label="Courses Fully Done" value={fmtInt(data.completeCourses)} />
        <KpiCard icon="⭕" tint="#dc2626" label="Courses Not Started" value={fmtInt(data.notStartedCourses)} />
      </div>

      <div className="grid two-col section-gap">
        <Card
          title="Progress by Content Type"
          sub="How far each content type has progressed toward one item per unit"
        >
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={contentBars} layout="vertical" margin={{ left: 8, right: 44, top: 4 }} barSize={22}>
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
                    <div className="tip-row">Completed <span className="v">{fmtInt(d.done)}</span></div>
                    <div className="tip-row">Pending <span className="v">{fmtInt(d.pending)}</span></div>
                    <div className="tip-foot"><span>Completion</span><span>{d.pct}%</span></div>
                  </div>
                )
              }} />
              <ReferenceLine x={100} stroke={AXIS} strokeDasharray="4 4" />
              <Bar isAnimationActive={false} dataKey="pct" radius={[0, 4, 4, 0]} name="Completion %">
                {contentBars.map((c) => <Cell key={c.name} fill={c.fill} />)}
                <LabelList dataKey="pct" position="right" formatter={(v) => `${v}%`}
                  style={{ fill: '#0f172a', fontSize: 12, fontWeight: 700 }} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <Legend items={contentBars.map((c) => ({ name: `${c.name} — ${fmtInt(c.done)} done, ${fmtInt(c.pending)} pending`, color: c.fill }))} />
        </Card>

        <Card title="Course Status Breakdown" sub={`${fmtInt(data.totalCourses)} courses by production stage`}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 18, flexWrap: 'wrap' }}>
            <div style={{ position: 'relative', width: 230, height: 230 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie isAnimationActive={false} data={statusData} dataKey="count" nameKey="status" innerRadius={68} outerRadius={100}
                    paddingAngle={2} strokeWidth={2} stroke="#ffffff">
                    {statusData.map((s) => <Cell key={s.status} fill={s.fill} />)}
                  </Pie>
                  <Tooltip content={<ChartTip />} />
                </PieChart>
              </ResponsiveContainer>
              <div style={{
                position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
                alignItems: 'center', justifyContent: 'center', pointerEvents: 'none',
              }}>
                <div style={{ fontSize: 26, fontWeight: 750 }}>{fmtInt(data.totalCourses)}</div>
                <div style={{ fontSize: 12, color: 'var(--muted)' }}>Total Courses</div>
              </div>
            </div>
            <div style={{ flex: 1, minWidth: 180 }}>
              {statusData.map((s) => (
                <div key={s.status} className="tip-row" style={{ padding: '5px 0', fontSize: 13 }}>
                  <span className="dot" style={{ background: s.fill }} />
                  {s.status}
                  <span className="v">{s.count} ({Math.round((s.count / data.totalCourses) * 100)}%)</span>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>

      <div className="section-gap">
        <ProductionOverTime log={log} />
      </div>

      <Card className="section-gap" title="Content Snapshot" sub="Completed vs required per content type">
        <div className="grid kpi-grid">
          {contentBars.map((c) => (
            <div key={c.name} style={{
              border: '1px solid var(--border)', borderRadius: 12, padding: '14px 16px',
            }}>
              <div className="legend-item" style={{ marginBottom: 8 }}>
                <span className="dot" style={{ background: c.fill }} />
                <b>{c.name}</b>
              </div>
              <div style={{ fontSize: 21, fontWeight: 750 }}>
                {fmtInt(c.done)} <small style={{ fontSize: 13, color: 'var(--muted)', fontWeight: 600 }}>of {fmtInt(c.required)}</small>
              </div>
              <div className="pbar" style={{ marginTop: 8 }}>
                <div className="pbar-track"><div className="pbar-fill" style={{ width: `${c.pct}%`, background: c.fill }} /></div>
                <span className="pbar-num">{c.pct}%</span>
              </div>
            </div>
          ))}
          <div style={{ border: '1px solid var(--border)', borderRadius: 12, padding: '14px 16px' }}>
            <div className="legend-item" style={{ marginBottom: 8 }}>
              <span className="dot" style={{ background: '#e11d48' }} />
              <b>H5P Quizzes</b>
            </div>
            <div style={{ fontSize: 21, fontWeight: 750 }}>
              {fmtInt(data.h5pDone)} <small style={{ fontSize: 13, color: 'var(--muted)', fontWeight: 600 }}>of {fmtInt(data.totalUnits)}</small>
            </div>
            <div className="pbar" style={{ marginTop: 8 }}>
              <div className="pbar-track">
                <div className="pbar-fill" style={{
                  width: `${Math.min(100, (data.h5pDone / data.totalUnits) * 100)}%`, background: '#e11d48',
                }} />
              </div>
              <span className="pbar-num">{((data.h5pDone / data.totalUnits) * 100).toFixed(1)}%</span>
            </div>
          </div>
        </div>
      </Card>
    </>
  )
}

// Surfaces tracker-sheet problems (blank names/units, totals drifting from the
// sheet's own SUM row) so bad rows are fixed at the source instead of silently
// skewing every figure below.
function DataQualityBanner({ dq }) {
  if (!dq || dq.ok) return null
  return (
    <div style={{
      border: '1px solid #f0c36d', background: 'rgba(245, 190, 80, 0.12)',
      borderRadius: 12, padding: '12px 16px', marginBottom: 16, fontSize: 13.5,
    }}>
      <b>⚠️ Tracker sheet needs attention</b>
      <ul style={{ margin: '6px 0 0', paddingLeft: 20 }}>
        {dq.issues.map((i, k) => (
          <li key={`i${k}`}><b>{i.course}</b> — {i.issue}</li>
        ))}
        {dq.totalsMismatches.map((m, k) => (
          <li key={`m${k}`}>
            {m.metric}: dashboard total {fmtInt(m.dashboard)} differs from the sheet&apos;s own total {fmtInt(m.sheet)}
          </li>
        ))}
      </ul>
      <div style={{ marginTop: 6, color: 'var(--muted)' }}>
        Numbers below already include the affected rows where possible — fix the highlighted cells in the SharePoint sheet to clear this.
      </div>
    </div>
  )
}

// Weekly cumulative AI-video output from the chapter-wise log (added context chart).
function ProductionOverTime({ log }) {
  const series = useMemo(() => {
    if (!log.data) return null
    const byWeek = new Map()
    for (const r of log.data.notebooklm || []) {
      const wk = weekStartISO(r.date)
      byWeek.set(wk, (byWeek.get(wk) || 0) + r.videos)
    }
    const weeks = [...byWeek.keys()].sort()
    let cum = 0
    return weeks.map((wk) => {
      cum += byWeek.get(wk)
      return { week: weekLabel(wk), weekly: byWeek.get(wk), cumulative: cum }
    })
  }, [log.data])

  if (log.loading || !series || series.length === 0) return null

  return (
    <Card
      title="AI Video Production Over Time"
      sub="Cumulative chapter-wise AI videos created (NotebookLM log), grouped by week"
    >
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={series} margin={{ left: 0, right: 16, top: 8 }}>
          <defs>
            <linearGradient id="cumFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={ACCENT} stopOpacity={0.22} />
              <stop offset="100%" stopColor={ACCENT} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid vertical={false} stroke={GRID} />
          <XAxis dataKey="week" tick={{ fill: AXIS, fontSize: 11.5 }} axisLine={{ stroke: GRID }}
            tickLine={false} interval="preserveStartEnd" minTickGap={24} />
          <YAxis tick={{ fill: AXIS, fontSize: 12 }} axisLine={false} tickLine={false} />
          <Tooltip content={({ active, payload, label }) => {
            if (!active || !payload?.length) return null
            const d = payload[0].payload
            return (
              <div className="tip">
                <div className="tip-title">{label}</div>
                <div className="tip-row">Videos that week <span className="v">{fmtInt(d.weekly)}</span></div>
                <div className="tip-row">Cumulative total <span className="v">{fmtInt(d.cumulative)}</span></div>
              </div>
            )
          }} />
          <Area isAnimationActive={false} type="monotone" dataKey="cumulative" name="Cumulative videos" stroke={ACCENT}
            strokeWidth={2} fill="url(#cumFill)" dot={false} activeDot={{ r: 5 }} />
        </AreaChart>
      </ResponsiveContainer>
    </Card>
  )
}
