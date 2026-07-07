import { useState } from 'react'
import { refreshData } from './api'
import { useApi } from './components/ui'
import Overview from './pages/Overview'
import VideoLog from './pages/VideoLog'
import ContentAnalysis from './pages/ContentAnalysis'
import SubjectLevel from './pages/SubjectLevel'
import QuickWins from './pages/QuickWins'
import PriorityWatch from './pages/PriorityWatch'
import AllCourses from './pages/AllCourses'
import Textbook from './pages/Textbook'
import Workstreams from './pages/Workstreams'

const PAGES = {
  overview: {
    title: 'Overview',
    sub: 'High-level view of content production across AI Videos, Podcasts, and Study Guides',
    el: Overview,
  },
  videolog: {
    title: 'Chapter-wise AI Video Progress',
    sub: 'Video-level production log — who produced each video via NotebookLM and WebTool',
    el: VideoLog,
  },
  content: {
    title: 'Content Analysis',
    sub: 'Which content type — AI Videos, Podcasts, or Study Guides — is slowing us down',
    el: ContentAnalysis,
  },
  subjects: {
    title: 'Subject & Level',
    sub: 'Which subject areas and qualification levels need attention',
    el: SubjectLevel,
  },
  quickwins: {
    title: 'Quick Wins',
    sub: 'Courses at 75–99% — low effort, high impact, finish these first',
    el: QuickWins,
  },
  priority: {
    title: 'Priority Watch',
    sub: 'Large courses falling behind — need immediate attention',
    el: PriorityWatch,
  },
  textbook: {
    title: 'TextBook Progress',
    sub: 'South London College — course textbook status',
    el: Textbook,
  },
  allcourses: {
    title: 'All Courses',
    sub: 'Filter and explore every course and its content status',
    el: AllCourses,
  },
  workstreams: {
    title: 'Production Workstreams',
    sub: 'Day-by-day and week-on-week output per workstream',
    el: Workstreams,
  },
}

const STATISTICS = [
  ['content', 'Content Analysis'],
  ['subjects', 'Subject & Level'],
  ['quickwins', 'Quick Wins'],
  ['priority', 'Priority Watch'],
  ['textbook', 'TextBook Progress'],
  ['allcourses', 'All Courses'],
]

export default function App() {
  const initial = window.location.hash.replace('#', '')
  const [page, setPage] = useState(PAGES[initial] ? initial : 'overview')
  const [wsSelected, setWsSelected] = useState('all')
  const wsMeta = useApi('/api/workstreams')
  const wsNames = wsMeta.data?.workstreams || []
  const [statsOpen, setStatsOpen] = useState(false)
  const [wsOpen, setWsOpen] = useState(false)
  const [navOpen, setNavOpen] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [reloadKey, setReloadKey] = useState(0)

  const go = (p) => { setPage(p); setNavOpen(false); window.location.hash = p }

  async function onRefresh() {
    setRefreshing(true)
    try {
      await refreshData()
      setReloadKey((k) => k + 1)
    } catch { /* backend unreachable; nothing to do */ }
    setRefreshing(false)
  }

  const { title, sub, el: PageEl } = PAGES[page]
  const statsActive = STATISTICS.some(([k]) => k === page)

  return (
    <div className="shell">
      <aside className={`sidebar ${navOpen ? 'open' : ''}`}>
        <div className="brand">
          <div className="brand-mark">▶</div>
          <div>
            <div className="brand-name">CourseFlow</div>
            <div className="brand-sub">Production</div>
          </div>
        </div>

        <button className={`nav-item ${page === 'overview' ? 'active' : ''}`} onClick={() => go('overview')}>
          <span>📊</span> Overview
        </button>
        <button className={`nav-item ${page === 'videolog' ? 'active' : ''}`} onClick={() => go('videolog')}>
          <span>🎬</span> Chapter-wise AI Video Progress
        </button>

        <div className="nav-group-label">Analytics</div>
        <button
          className={`nav-item ${statsActive && !statsOpen ? 'active' : ''}`}
          onClick={() => setStatsOpen((o) => !o)}
        >
          <span>📈</span> Statistics
          <span className={`chev ${statsOpen ? 'open' : ''}`}>▶</span>
        </button>
        {statsOpen && (
          <div className="nav-children">
            {STATISTICS.map(([key, label]) => (
              <button key={key} className={`nav-item ${page === key ? 'active' : ''}`} onClick={() => go(key)}>
                {label}
              </button>
            ))}
          </div>
        )}

        <button
          className={`nav-item ${page === 'workstreams' && !wsOpen ? 'active' : ''}`}
          onClick={() => setWsOpen((o) => !o)}
        >
          <span>🏭</span> Production Workstreams
          <span className={`chev ${wsOpen ? 'open' : ''}`}>▶</span>
        </button>
        {wsOpen && (
          <div className="nav-children">
            {wsNames.map((w) => (
              <button
                key={w}
                className={`nav-item ${page === 'workstreams' && wsSelected === w ? 'active' : ''}`}
                onClick={() => { setWsSelected(w); go('workstreams') }}
              >
                {w}
              </button>
            ))}
          </div>
        )}

        <div className="sidebar-foot">
          Data refreshes from the tracker sheet every 5 minutes. Use Refresh to force an update.
        </div>
      </aside>

      <main className="main">
        <div className="page-head">
          <div>
            <button className="btn menu-btn" onClick={() => setNavOpen((o) => !o)}>☰ Menu</button>
            <h1 className="page-title">{title}</h1>
            <p className="page-sub">{sub}</p>
          </div>
          <button className="btn" onClick={onRefresh} disabled={refreshing}>
            {refreshing ? 'Refreshing…' : '⟳ Refresh Data'}
          </button>
        </div>
        <PageEl key={`${page}-${wsSelected}-${reloadKey}`} selected={wsSelected} onSelect={setWsSelected} />
      </main>
    </div>
  )
}
