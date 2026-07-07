const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

export function parseDate(iso) {
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, m - 1, d)
}

export function shortDate(iso) {
  const d = parseDate(iso)
  return `${String(d.getDate()).padStart(2, '0')} ${MONTH_NAMES[d.getMonth()]} (${DAY_NAMES[d.getDay()]})`
}

export function longDate(iso) {
  const d = parseDate(iso)
  return `${String(d.getDate()).padStart(2, '0')} ${MONTH_NAMES[d.getMonth()]} ${d.getFullYear()}`
}

export function monthKey(iso) {
  return iso.slice(0, 7)
}

export function monthLabel(key) {
  const [y, m] = key.split('-').map(Number)
  return `${MONTH_NAMES[m - 1]} ${y}`
}

// Monday-based week start for week-on-week grouping.
export function weekStartISO(iso) {
  const d = parseDate(iso)
  const day = (d.getDay() + 6) % 7 // Mon=0 … Sun=6
  d.setDate(d.getDate() - day)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${dd}`
}

export function weekLabel(startIso) {
  const d = parseDate(startIso)
  return `Wk of ${String(d.getDate()).padStart(2, '0')} ${MONTH_NAMES[d.getMonth()]}`
}

export function fmtInt(v) {
  return v == null ? '—' : Number(v).toLocaleString()
}

export function fmtPct(v, nd = 1) {
  return v == null ? '—' : `${Number(v).toFixed(nd)}%`
}

export function fmtGBP(v) {
  return v == null ? '—' : `£${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

// Wrap long course names for chart axis labels.
export function truncate(s, n = 42) {
  return s.length > n ? s.slice(0, n - 1) + '…' : s
}
