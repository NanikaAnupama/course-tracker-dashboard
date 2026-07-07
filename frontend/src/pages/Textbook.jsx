import { useMemo, useState } from 'react'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  PieChart, Pie, Cell,
} from 'recharts'
import { useApi, Loading, ErrorState, Card, KpiCard, SubTabs, ChartTip, StatusChip, Legend } from '../components/ui'
import { TEXTBOOK_COLORS, GRID, AXIS } from '../theme'
import { fmtInt, fmtGBP, truncate } from '../utils'

const TABS = ['Executive Overview', 'Course Explorer', 'Course Details']
const STATUS_ORDER = ['Textbook Ready', 'In Progress', 'No Textbook']

export default function Textbook() {
  const [tab, setTab] = useState(TABS[0])
  const { data, error, loading } = useApi('/api/textbooks')
  if (loading) return <Loading />
  if (error) return <ErrorState error={error} />

  return (
    <>
      <SubTabs tabs={TABS} active={tab} onChange={setTab} />
      {tab === TABS[0] && <ExecOverview rows={data} />}
      {tab === TABS[1] && <Explorer rows={data} />}
      {tab === TABS[2] && <Details rows={data} />}
    </>
  )
}

function ExecOverview({ rows }) {
  const total = rows.length
  const ready = rows.filter((r) => r.status === 'Textbook Ready').length
  const none = rows.filter((r) => r.status === 'No Textbook').length
  const inProg = rows.filter((r) => r.status === 'In Progress').length
  const pct = total ? (ready / total) * 100 : 0

  const byLevel = useMemo(() => {
    const levels = [...new Set(rows.filter((r) => r.level != null).map((r) => r.level))].sort((a, b) => a - b)
    return levels.map((lvl) => {
      const g = rows.filter((r) => r.level === lvl)
      const row = { name: `Level ${lvl}` }
      for (const s of STATUS_ORDER) row[s] = g.filter((r) => r.status === s).length
      return row
    })
  }, [rows])

  const byQual = useMemo(() => {
    const quals = [...new Set(rows.map((r) => r.qualification))]
    return quals.map((q) => {
      const g = rows.filter((r) => r.qualification === q)
      const row = { name: q }
      for (const s of STATUS_ORDER) row[s] = g.filter((r) => r.status === s).length
      return row
    })
  }, [rows])

  const pieData = STATUS_ORDER
    .map((s) => ({ status: s, count: rows.filter((r) => r.status === s).length }))
    .filter((d) => d.count > 0)

  return (
    <>
      <div className="grid kpi-grid">
        <KpiCard icon="📚" tint="#2563eb" label="Total Courses" value={fmtInt(total)} />
        <KpiCard icon="✅" tint="#059669" label="Textbook Ready" value={fmtInt(ready)} />
        <KpiCard icon="⚠️" tint="#d97706" label="No Textbook" value={fmtInt(none)} />
        <KpiCard icon="🔄" tint="#7c3aed" label="In Progress" value={fmtInt(inProg)} />
        <KpiCard icon="🎯" tint="#047857" label="Completion Rate" value={`${pct.toFixed(1)}%`} />
      </div>

      <div className="grid two-col section-gap">
        <Card title="Textbook Status by Course Level" sub="Stacked count of courses at each level">
          <ResponsiveContainer width="100%" height={340}>
            <BarChart data={byLevel} margin={{ top: 8, right: 8 }} barSize={34}>
              <CartesianGrid vertical={false} stroke={GRID} />
              <XAxis dataKey="name" tick={{ fill: '#47536b', fontSize: 12.5 }} axisLine={{ stroke: GRID }} tickLine={false} />
              <YAxis tick={{ fill: AXIS, fontSize: 12 }} axisLine={false} tickLine={false} allowDecimals={false} />
              <Tooltip cursor={{ fill: '#f4f6fa' }} content={<ChartTip total />} />
              {STATUS_ORDER.map((s, i) => (
                <Bar isAnimationActive={false} key={s} dataKey={s} name={s} stackId="a" fill={TEXTBOOK_COLORS[s]}
                  radius={i === STATUS_ORDER.length - 1 ? [4, 4, 0, 0] : 0} />
              ))}
            </BarChart>
          </ResponsiveContainer>
          <Legend items={STATUS_ORDER.map((s) => ({ name: s, color: TEXTBOOK_COLORS[s] }))} />
        </Card>

        <Card title="Overall Textbook Coverage" sub="Share of courses with a finished textbook">
          <div style={{ display: 'flex', alignItems: 'center', gap: 18, flexWrap: 'wrap' }}>
            <div style={{ position: 'relative', width: 240, height: 240 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie isAnimationActive={false} data={pieData} dataKey="count" nameKey="status" innerRadius={72} outerRadius={104}
                    paddingAngle={2} strokeWidth={2} stroke="#ffffff">
                    {pieData.map((d) => <Cell key={d.status} fill={TEXTBOOK_COLORS[d.status]} />)}
                  </Pie>
                  <Tooltip content={<ChartTip />} />
                </PieChart>
              </ResponsiveContainer>
              <div style={{
                position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
                alignItems: 'center', justifyContent: 'center', pointerEvents: 'none',
              }}>
                <div style={{ fontSize: 28, fontWeight: 750 }}>{pct.toFixed(0)}%</div>
                <div style={{ fontSize: 12, color: 'var(--muted)' }}>Complete</div>
              </div>
            </div>
            <div style={{ flex: 1, minWidth: 170 }}>
              {pieData.map((d) => (
                <div key={d.status} className="tip-row" style={{ padding: '5px 0', fontSize: 13 }}>
                  <span className="dot" style={{ background: TEXTBOOK_COLORS[d.status] }} />
                  {d.status}
                  <span className="v">{d.count}</span>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>

      <Card className="section-gap" title="Textbook Status by Qualification Type" sub="Grouped count per qualification">
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={byQual} margin={{ top: 8, right: 8 }} barSize={20} barGap={3}>
            <CartesianGrid vertical={false} stroke={GRID} />
            <XAxis dataKey="name" tick={{ fill: '#47536b', fontSize: 12.5 }} axisLine={{ stroke: GRID }} tickLine={false} />
            <YAxis tick={{ fill: AXIS, fontSize: 12 }} axisLine={false} tickLine={false} allowDecimals={false} />
            <Tooltip cursor={{ fill: '#f4f6fa' }} content={<ChartTip />} />
            {STATUS_ORDER.map((s) => (
              <Bar isAnimationActive={false} key={s} dataKey={s} name={s} fill={TEXTBOOK_COLORS[s]} radius={[4, 4, 0, 0]} />
            ))}
          </BarChart>
        </ResponsiveContainer>
        <Legend items={STATUS_ORDER.map((s) => ({ name: s, color: TEXTBOOK_COLORS[s] }))} />
      </Card>
    </>
  )
}

function Explorer({ rows }) {
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('All')
  const [level, setLevel] = useState('All')
  const [qual, setQual] = useState('All')

  const levels = [...new Set(rows.filter((r) => r.level != null).map((r) => r.level))].sort((a, b) => a - b)
  const quals = [...new Set(rows.map((r) => r.qualification))].sort()

  const filtered = rows.filter((r) =>
    (!search || r.name.toLowerCase().includes(search.toLowerCase()))
    && (status === 'All' || r.status === status)
    && (level === 'All' || r.level === Number(level))
    && (qual === 'All' || r.qualification === qual))

  return (
    <>
      <div className="filters">
        <input className="control" style={{ minWidth: 220 }} placeholder="Search course name…"
          value={search} onChange={(e) => setSearch(e.target.value)} />
        <span className="filter-label">Status</span>
        <select className="control" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option>All</option>
          {STATUS_ORDER.map((s) => <option key={s}>{s}</option>)}
        </select>
        <span className="filter-label">Level</span>
        <select className="control" value={level} onChange={(e) => setLevel(e.target.value)}>
          <option>All</option>
          {levels.map((l) => <option key={l} value={l}>Level {l}</option>)}
        </select>
        <span className="filter-label">Qualification</span>
        <select className="control" value={qual} onChange={(e) => setQual(e.target.value)}>
          <option>All</option>
          {quals.map((q) => <option key={q}>{q}</option>)}
        </select>
        <span className="filter-label" style={{ marginLeft: 'auto' }}>Showing {filtered.length} courses</span>
      </div>

      {filtered.length === 0 ? (
        <div className="state"><h3>No courses match your filters</h3><p>Try adjusting the filters above.</p></div>
      ) : (
        <Card>
          <div className="table-wrap" style={{ maxHeight: 560, overflowY: 'auto' }}>
            <table className="data">
              <thead>
                <tr>
                  <th>Course Name</th>
                  <th>Qualification</th>
                  <th>Level</th>
                  <th className="num">Units</th>
                  <th className="num">Pages</th>
                  <th className="num">Cost to Print</th>
                  <th className="num">Price</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((r) => (
                  <tr key={r.name}>
                    <td title={r.name}>{truncate(r.name, 62)}</td>
                    <td>{r.qualification}</td>
                    <td>{r.level != null ? `Level ${r.level}` : '—'}</td>
                    <td className="num">{fmtInt(r.units)}</td>
                    <td className="num">{fmtInt(r.pages)}</td>
                    <td className="num">{fmtGBP(r.costToPrint)}</td>
                    <td className="num">{fmtGBP(r.price)}</td>
                    <td><StatusChip status={r.status} colors={TEXTBOOK_COLORS} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </>
  )
}

function Details({ rows }) {
  const [quick, setQuick] = useState('All')
  const list = quick === 'All' ? rows : rows.filter((r) => r.status === quick)
  const [selected, setSelected] = useState('')
  const row = list.find((r) => r.name === selected) || list[0]

  return (
    <>
      <div className="filters">
        <span className="filter-label">Quick filter</span>
        <div className="seg">
          {['All', ...STATUS_ORDER].map((s) => (
            <button key={s} className={quick === s ? 'active' : ''} onClick={() => { setQuick(s); setSelected('') }}>{s}</button>
          ))}
        </div>
        <select className="control" style={{ minWidth: 320, maxWidth: '100%' }}
          value={row?.name || ''} onChange={(e) => setSelected(e.target.value)}>
          {list.map((r) => <option key={r.name}>{r.name}</option>)}
        </select>
      </div>

      {!row ? (
        <div className="state"><h3>No courses available</h3><p>Adjust the quick filter above.</p></div>
      ) : (
        <Card>
          <h2 style={{ margin: '0 0 8px', fontSize: 19 }}>{row.name}</h2>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 18 }}>
            <StatusChip status={row.status} colors={TEXTBOOK_COLORS} />
            <span className="chip" style={{ background: '#eaf1fe', color: '#2563eb' }}>🎓 {row.qualification}</span>
            <span className="chip" style={{ background: '#eaf1fe', color: '#2563eb' }}>
              📘 {row.level != null ? `Level ${row.level}` : 'Level —'}
            </span>
          </div>
          <div className="grid kpi-grid">
            {[
              ['Number of Units', fmtInt(row.units)],
              ['Page Count', fmtInt(row.pages)],
              ['Cost to Print', fmtGBP(row.costToPrint)],
              ['Selling Price', fmtGBP(row.price)],
            ].map(([label, value]) => (
              <div key={label} style={{ border: '1px solid var(--border)', borderRadius: 12, padding: '14px 16px', textAlign: 'center' }}>
                <div className="kpi-label">{label}</div>
                <div style={{ fontSize: 20, fontWeight: 750, marginTop: 4 }}>{value}</div>
              </div>
            ))}
          </div>
          {row.link && (
            <p style={{ marginTop: 16, fontSize: 13 }}>
              🔗 <b>Course page:</b>{' '}
              <a href={row.link} target="_blank" rel="noreferrer" style={{ color: 'var(--accent)' }}>
                {truncate(row.link, 80)}
              </a>
            </p>
          )}
        </Card>
      )}
    </>
  )
}
