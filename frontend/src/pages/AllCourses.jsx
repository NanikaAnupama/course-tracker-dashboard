import { useMemo, useState } from 'react'
import { useApi, Loading, ErrorState, Card, PctBar, StatusChip } from '../components/ui'
import { STATUS_COLORS } from '../theme'
import { fmtInt, truncate } from '../utils'

export default function AllCourses() {
  const { data, error, loading } = useApi('/api/courses')
  const [status, setStatus] = useState('All')
  const [subject, setSubject] = useState('All')
  const [level, setLevel] = useState('All')
  const [search, setSearch] = useState('')

  const options = useMemo(() => {
    if (!data) return { statuses: [], subjects: [], levels: [] }
    return {
      statuses: [...new Set(data.map((c) => c.status))].sort(),
      subjects: [...new Set(data.map((c) => c.subject))].sort(),
      levels: [...new Set(data.map((c) => c.level))].sort(),
    }
  }, [data])

  if (loading) return <Loading />
  if (error) return <ErrorState error={error} />

  const filtered = data
    .filter((c) => (status === 'All' || c.status === status)
      && (subject === 'All' || c.subject === subject)
      && (level === 'All' || c.level === level)
      && (!search || c.name.toLowerCase().includes(search.toLowerCase())))
    .sort((a, b) => b.pct - a.pct)

  const totals = {
    required: data.reduce((a, c) => a + c.required, 0),
    completed: data.reduce((a, c) => a + c.videosDone + c.podcastsDone + c.guidesDone, 0),
  }
  const active = data.filter((c) => c.pct < 100)
  const pendingActive = active.reduce((a, c) => a + c.pending, 0)
  const withPending = data.filter((c) => c.pending > 0)
  const largestPending = data.length ? Math.max(...data.map((c) => c.pending)) : null
  const smallestPending = withPending.length ? Math.min(...withPending.map((c) => c.pending)) : null

  return (
    <>
      <div className="filters">
        <input className="control" style={{ minWidth: 220 }} placeholder="Search course name…"
          value={search} onChange={(e) => setSearch(e.target.value)} />
        <span className="filter-label">Status</span>
        <select className="control" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option>All</option>
          {options.statuses.map((s) => <option key={s}>{s}</option>)}
        </select>
        <span className="filter-label">Subject Area</span>
        <select className="control" value={subject} onChange={(e) => setSubject(e.target.value)}>
          <option>All</option>
          {options.subjects.map((s) => <option key={s}>{s}</option>)}
        </select>
        <span className="filter-label">Level</span>
        <select className="control" value={level} onChange={(e) => setLevel(e.target.value)}>
          <option>All</option>
          {options.levels.map((s) => <option key={s}>{s}</option>)}
        </select>
        <span className="filter-label" style={{ marginLeft: 'auto' }}>
          Showing {filtered.length} of {data.length} courses
        </span>
      </div>

      <Card>
        <div className="table-wrap" style={{ maxHeight: 560, overflowY: 'auto' }}>
          <table className="data">
            <thead>
              <tr>
                <th>Course Name</th>
                <th>Level</th>
                <th>Subject Area</th>
                <th className="num">Units</th>
                <th>Status</th>
                <th>Progress</th>
                <th className="num">AI Videos ✓</th>
                <th className="num">Podcasts ✓</th>
                <th className="num">Study Guides ✓</th>
                <th className="num">Pending</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((c) => (
                <tr key={c.name}>
                  <td title={c.name}>{truncate(c.name, 58)}</td>
                  <td>{c.level}</td>
                  <td>{c.subject}</td>
                  <td className="num">{c.units}</td>
                  <td><StatusChip status={c.status} /></td>
                  <td><PctBar pct={c.pct} color={STATUS_COLORS[c.status]} /></td>
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

      <div className="grid two-col section-gap">
        <Card title="Summary Statistics">
          <div className="grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
            <div>
              <p className="card-sub" style={{ marginBottom: 6 }}><b style={{ color: 'var(--ink)' }}>Content Production</b></p>
              <p style={{ margin: '4px 0', color: 'var(--ink-2)' }}>Total required: {fmtInt(totals.required)}</p>
              <p style={{ margin: '4px 0', color: 'var(--ink-2)' }}>Completed: {fmtInt(totals.completed)}</p>
              <p style={{ margin: '4px 0', color: 'var(--ink-2)' }}>Pending: {fmtInt(totals.required - totals.completed)}</p>
            </div>
            <div>
              <p className="card-sub" style={{ marginBottom: 6 }}><b style={{ color: 'var(--ink)' }}>Workload Estimate</b></p>
              <p style={{ margin: '4px 0', color: 'var(--ink-2)' }}>
                Avg pending / active course: {active.length ? (pendingActive / active.length).toFixed(1) : '—'}
              </p>
              <p style={{ margin: '4px 0', color: 'var(--ink-2)' }}>Largest pending: {fmtInt(largestPending)}</p>
              <p style={{ margin: '4px 0', color: 'var(--ink-2)' }}>Smallest pending: {fmtInt(smallestPending)}</p>
            </div>
          </div>
        </Card>
        <Card title="Course Status">
          {Object.keys(STATUS_COLORS).map((s) => {
            const n = data.filter((c) => c.status === s).length
            if (!n) return null
            return (
              <div key={s} className="tip-row" style={{ padding: '5px 0', fontSize: 13 }}>
                <span className="dot" style={{ background: STATUS_COLORS[s] }} />
                {s}
                <span className="v">{n}</span>
              </div>
            )
          })}
        </Card>
      </div>
    </>
  )
}
