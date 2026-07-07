// Chart palette — validated for the light surface (CVD-safe, >=3:1 contrast).

export const CONTENT_COLORS = {
  'AI Videos': '#d97706',
  'Podcasts': '#0284c7',
  'Study Guides': '#059669',
}

export const STATUS_COLORS = {
  'Not Started': '#dc2626',
  'Early Stage': '#d97706',
  'In Progress': '#0284c7',
  'Almost Done': '#10b981',
  'Complete': '#047857',
}

export const PERSON_COLORS = {
  Yenushka: '#059669',
  Piyumi: '#7c3aed',
  Amana: '#0284c7',
  Fathima: '#d97706',
  Rukaiya: '#e11d48',
  Anjani: '#d97706',
  'Anjani De silva': '#d97706',
  'Anjani De Silva': '#d97706',
  Menuka: '#db2777',
  'Aaisha Shahani': '#0891b2',
  'Dulmini Hasinika': '#65a30d',
  'Nandika Anupama': '#c026d3',
  'Ridma Keshan': '#ea580c',
  'Yoga Milona': '#4f46e5',
  Other: '#64748b',
}

export const FALLBACK_COLORS = ['#0891b2', '#e11d48', '#65a30d', '#c026d3', '#ea580c', '#0e7490']

export function personColor(person, idx = 0) {
  return PERSON_COLORS[person] || FALLBACK_COLORS[idx % FALLBACK_COLORS.length]
}

export const TEXTBOOK_COLORS = {
  'Textbook Ready': '#059669',
  'In Progress': '#7c3aed',
  'No Textbook': '#d97706',
}

export const GRID = '#e8ebf1'
export const AXIS = '#8b96a8'
export const ACCENT = '#2563eb'
