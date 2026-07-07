import { useMemo, useState } from 'react'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  LineChart, Line, PieChart, Pie, Cell, LabelList, AreaChart, Area,
} from 'recharts'
import { Card, KpiCard, ChartTip, Legend } from './ui'
import { personColor, GRID, AXIS } from '../theme'
import { fmtInt, shortDate, monthKey, monthLabel, weekStartISO, weekLabel, parseDate } from '../utils'

// ── Shared period filter (month dropdown + daily/weekly toggle) ──

export function useMonths(dates) {
  return useMemo(() => [...new Set(dates.map(monthKey))].sort(), [dates])
}

export function PeriodControls({ months, month, setMonth, gran, setGran }) {
  return (
    <div className="filters">
      <span className="filter-label">View</span>
      <div className="seg">
        <button className={gran === 'daily' ? 'active' : ''} onClick={() => setGran('daily')}>Daily</button>
        <button className={gran === 'weekly' ? 'active' : ''} onClick={() => setGran('weekly')}>Weekly</button>
      </div>
      <span className="filter-label">Period</span>
      <select className="control" value={month} onChange={(e) => setMonth(e.target.value)}>
        <option value="all">All time</option>
        <option value="last4w">Last 4 weeks</option>
        {months.map((m) => <option key={m} value={m}>{monthLabel(m)}</option>)}
      </select>
    </div>
  )
}

export function filterByPeriod(rows, month) {
  if (month === 'all') return rows
  if (month === 'last4w') {
    const dates = rows.map((r) => r.date).sort()
    if (!dates.length) return rows
    const last = parseDate(dates[dates.length - 1])
    last.setDate(last.getDate() - 27)
    const cutoff = `${last.getFullYear()}-${String(last.getMonth() + 1).padStart(2, '0')}-${String(last.getDate()).padStart(2, '0')}`
    return rows.filter((r) => r.date >= cutoff)
  }
  return rows.filter((r) => monthKey(r.date) === month)
}

// ── Per-person production dashboard section ──────────────────────
// rows: [{ date: 'YYYY-MM-DD', person: string, count: number }]
// unit: plural noun for the produced item ("videos", "courses", "items")

export default function ProductionSection({ rows, unit = 'items', totalLabel = 'Total Completed', emptyMsg = 'No data yet.', showCumulative = false }) {
  const [month, setMonth] = useState('all')
  const [gran, setGran] = useState('daily')

  const months = useMonths((rows || []).map((r) => r.date))

  const view = useMemo(() => {
    if (!rows || !rows.length) return null
    const filtered = filterByPeriod(rows, month)
    const persons = [...new Set(rows.map((r) => r.person))].sort()

    const bucketOf = gran === 'weekly' ? (d) => weekStartISO(d) : (d) => d
    const labelOf = gran === 'weekly' ? weekLabel : shortDate
    const buckets = new Map()
    for (const r of filtered) {
      const b = bucketOf(r.date)
      if (!buckets.has(b)) buckets.set(b, { key: b, label: labelOf(b), total: 0 })
      const row = buckets.get(b)
      row[r.person] = (row[r.person] || 0) + r.count
      row.total += r.count
    }
    const series = [...buckets.values()].sort((a, b) => a.key.localeCompare(b.key))

    let cum = 0
    series.forEach((row, i) => {
      cum += row.total
      row.cumulative = cum
      row.change = i > 0 && series[i - 1].total > 0
        ? ((row.total - series[i - 1].total) / series[i - 1].total) * 100
        : null
    })

    const totals = persons
      .map((p) => ({ person: p, count: filtered.filter((r) => r.person === p).reduce((a, r) => a + r.count, 0) }))
      .sort((a, b) => b.count - a.count)
    const activeTotals = totals.filter((t) => t.count > 0)

    const activeDays = new Set(filtered.filter((r) => r.count > 0).map((r) => r.date)).size
    const grandTotal = filtered.reduce((a, r) => a + r.count, 0)

    const dayKeys = [...new Set(filtered.map((r) => r.date))].sort()
    const tableRows = dayKeys.map((d) => {
      const row = { date: d }
      let t = 0
      for (const r of filtered) {
        if (r.date === d) { row[r.person] = (row[r.person] || 0) + r.count; t += r.count }
      }
      row.total = t
      return row
    })

    return {
      series,
      persons: totals.map((t) => t.person),
      totals,
      activeTotals,
      activeDays,
      grandTotal,
      tableRows,
    }
  }, [rows, month, gran])

  if (!view) return <div className="state"><h3>No data yet</h3><p>{emptyMsg}</p></div>

  const { series, persons, totals, activeTotals, activeDays, grandTotal, tableRows } = view
  const colorOf = (p) => personColor(p, persons.indexOf(p))
  const latest = series[series.length - 1]
  const unitCap = unit.charAt(0).toUpperCase() + unit.slice(1)
  const periodNote = month === 'all' ? 'All time' : month === 'last4w' ? 'Last 4 weeks' : monthLabel(month)

  return (
    <>
      <PeriodControls months={months} month={month} setMonth={setMonth} gran={gran} setGran={setGran} />

      <div className="grid kpi-grid">
        <KpiCard icon="✅" tint="#2563eb" label={totalLabel} value={fmtInt(grandTotal)} note={periodNote} />
        <KpiCard icon="📅" tint="#7c3aed" label="Active Days" value={fmtInt(activeDays)} />
        {gran === 'weekly' && latest && latest.change != null && (
          <KpiCard icon={latest.change >= 0 ? '📈' : '📉'} tint={latest.change >= 0 ? '#047857' : '#dc2626'}
            label="Latest Week vs Previous" value={`${latest.change >= 0 ? '+' : ''}${latest.change.toFixed(0)}%`}
            note={`${fmtInt(latest.total)} ${unit} in ${latest.label}`}
            dir={latest.change >= 0 ? 'up' : 'down'} />
        )}
        {totals.map((t) => (
          <KpiCard key={t.person} icon="👤" tint={colorOf(t.person)}
            label={`${t.person} — Total`} value={fmtInt(t.count)} />
        ))}
      </div>

      <Card className="section-gap"
        title={gran === 'weekly' ? `Weekly ${unitCap} Completed by Person` : `Daily ${unitCap} Completed by Person`}
        sub={gran === 'weekly'
          ? `Each bar is one week (Mon–Sun), broken down by person — tooltip shows week-on-week change`
          : `Each bar shows total ${unit} completed per day, broken down by person`}
      >
        <ResponsiveContainer width="100%" height={380}>
          <BarChart data={series} margin={{ top: 22, right: 8 }} barCategoryGap="24%">
            <CartesianGrid vertical={false} stroke={GRID} />
            <XAxis dataKey="label" tick={{ fill: AXIS, fontSize: 11 }} axisLine={{ stroke: GRID }}
              tickLine={false} angle={-35} textAnchor="end" height={62} interval="preserveStartEnd"
              minTickGap={gran === 'weekly' ? 8 : 14} />
            <YAxis tick={{ fill: AXIS, fontSize: 12 }} axisLine={false} tickLine={false} allowDecimals={false} />
            <Tooltip cursor={{ fill: '#f4f6fa' }} content={({ active, payload, label }) => {
              if (!active || !payload?.length) return null
              const d = payload[0].payload
              return (
                <div className="tip">
                  <div className="tip-title">{label}</div>
                  {payload.filter((p) => p.value > 0).map((p) => (
                    <div className="tip-row" key={p.dataKey}>
                      <span className="dot" style={{ background: p.fill }} />
                      {p.name}
                      <span className="v">{fmtInt(p.value)}</span>
                    </div>
                  ))}
                  <div className="tip-foot"><span>Total</span><span>{fmtInt(d.total)}</span></div>
                  {gran === 'weekly' && d.change != null && (
                    <div className="tip-row" style={{ color: d.change >= 0 ? 'var(--good)' : 'var(--bad)', fontWeight: 700 }}>
                      {d.change >= 0 ? '▲' : '▼'} {Math.abs(d.change).toFixed(0)}% vs previous week
                    </div>
                  )}
                </div>
              )
            }} />
            {persons.map((p, i) => (
              <Bar isAnimationActive={false} key={p} dataKey={p} name={p} stackId="a" fill={colorOf(p)} maxBarSize={48}
                radius={i === persons.length - 1 ? [4, 4, 0, 0] : 0}>
                {i === persons.length - 1 && (
                  <LabelList dataKey="total" position="top"
                    style={{ fill: '#47536b', fontSize: 10.5, fontWeight: 700 }} />
                )}
              </Bar>
            ))}
          </BarChart>
        </ResponsiveContainer>
        <Legend items={persons.map((p) => ({ name: p, color: colorOf(p) }))} />
      </Card>

      <div className="grid two-col section-gap">
        <Card title={gran === 'weekly' ? 'Week-over-Week Trend per Person' : 'Day-over-Day Trend per Person'}
          sub="How each person's output changed over time">
          <ResponsiveContainer width="100%" height={330}>
            <LineChart data={series} margin={{ top: 8, right: 12 }}>
              <CartesianGrid vertical={false} stroke={GRID} />
              <XAxis dataKey="label" tick={{ fill: AXIS, fontSize: 11 }} axisLine={{ stroke: GRID }}
                tickLine={false} angle={-35} textAnchor="end" height={62} interval="preserveStartEnd" minTickGap={14} />
              <YAxis tick={{ fill: AXIS, fontSize: 12 }} axisLine={false} tickLine={false} allowDecimals={false} />
              <Tooltip content={<ChartTip />} />
              {persons.map((p) => (
                <Line isAnimationActive={false} key={p} type="monotone" dataKey={p} name={p} stroke={colorOf(p)} strokeWidth={2}
                  dot={{ r: 3, fill: colorOf(p), strokeWidth: 0 }} activeDot={{ r: 5 }} connectNulls />
              ))}
            </LineChart>
          </ResponsiveContainer>
          <Legend items={persons.map((p) => ({ name: p, color: colorOf(p) }))} />
        </Card>

        <Card title="Share of Total Contribution" sub={`Overall split of ${unit} completed by each person`}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 18, flexWrap: 'wrap' }}>
            <div style={{ position: 'relative', width: 230, height: 230 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie isAnimationActive={false} data={activeTotals} dataKey="count" nameKey="person" innerRadius={66} outerRadius={100}
                    paddingAngle={2} strokeWidth={2} stroke="#ffffff">
                    {activeTotals.map((t) => <Cell key={t.person} fill={colorOf(t.person)} />)}
                  </Pie>
                  <Tooltip content={<ChartTip />} />
                </PieChart>
              </ResponsiveContainer>
              <div style={{
                position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
                alignItems: 'center', justifyContent: 'center', pointerEvents: 'none',
              }}>
                <div style={{ fontSize: 25, fontWeight: 750 }}>{fmtInt(grandTotal)}</div>
                <div style={{ fontSize: 12, color: 'var(--muted)' }}>{unitCap}</div>
              </div>
            </div>
            <div style={{ flex: 1, minWidth: 170 }}>
              {totals.map((t) => (
                <div key={t.person} className="tip-row" style={{ padding: '5px 0', fontSize: 13 }}>
                  <span className="dot" style={{ background: colorOf(t.person) }} />
                  {t.person}
                  <span className="v">{fmtInt(t.count)} ({grandTotal ? Math.round((t.count / grandTotal) * 100) : 0}%)</span>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>

      {showCumulative && (
        <Card className="section-gap" title="Cumulative Output Over Time" sub={`Running total of ${unit} completed so far`}>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={series} margin={{ top: 8, right: 12 }}>
              <defs>
                <linearGradient id="prodCumFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#059669" stopOpacity={0.2} />
                  <stop offset="100%" stopColor="#059669" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid vertical={false} stroke={GRID} />
              <XAxis dataKey="label" tick={{ fill: AXIS, fontSize: 11 }} axisLine={{ stroke: GRID }}
                tickLine={false} angle={-35} textAnchor="end" height={62} interval="preserveStartEnd" minTickGap={12} />
              <YAxis tick={{ fill: AXIS, fontSize: 12 }} axisLine={false} tickLine={false} allowDecimals={false} />
              <Tooltip content={<ChartTip />} />
              <Area isAnimationActive={false} type="monotone" dataKey="cumulative" name={`Cumulative ${unit}`} stroke="#059669"
                strokeWidth={2} fill="url(#prodCumFill)" dot={false} activeDot={{ r: 5 }} />
            </AreaChart>
          </ResponsiveContainer>
        </Card>
      )}

      <Card className="section-gap" title="Person Comparison" sub={`Total ${unit} for the selected period`}>
        <ResponsiveContainer width="100%" height={Math.max(140, totals.length * 52)}>
          <BarChart data={[...totals].sort((a, b) => a.count - b.count)} layout="vertical"
            margin={{ left: 8, right: 60, top: 4 }} barSize={22}>
            <CartesianGrid horizontal={false} stroke={GRID} />
            <XAxis type="number" tick={{ fill: AXIS, fontSize: 12 }} axisLine={{ stroke: GRID }} tickLine={false} allowDecimals={false} />
            <YAxis type="category" dataKey="person" width={130} tick={{ fill: '#47536b', fontSize: 13 }}
              axisLine={false} tickLine={false} />
            <Tooltip cursor={{ fill: '#f4f6fa' }} content={<ChartTip />} />
            <Bar isAnimationActive={false} dataKey="count" name={`Total ${unit}`} radius={[0, 4, 4, 0]}>
              {[...totals].sort((a, b) => a.count - b.count).map((t) => (
                <Cell key={t.person} fill={colorOf(t.person)} />
              ))}
              <LabelList dataKey="count" position="right" style={{ fill: '#0f172a', fontSize: 12, fontWeight: 700 }} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Card>

      <Card className="section-gap" title="Full Daily Log" sub={`${unitCap} per person per day for the selected period`}>
        <div className="table-wrap scroll-y">
          <table className="data">
            <thead>
              <tr>
                <th>Date</th>
                {persons.map((p) => <th className="num" key={p}>{p}</th>)}
                <th className="num">Team Total</th>
              </tr>
            </thead>
            <tbody>
              {tableRows.map((r) => (
                <tr key={r.date}>
                  <td>{shortDate(r.date)}</td>
                  {persons.map((p) => <td className="num" key={p}>{r[p] || 0}</td>)}
                  <td className="num"><b>{r.total}</b></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  )
}
