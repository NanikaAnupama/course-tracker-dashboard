import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import re
from io import BytesIO
import numpy as np
import textwrap

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Course Content Tracker", layout="wide", page_icon="📊")

# --- CUSTOM CSS FOR DARK THEME UI ---
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }
    [data-testid="stMetricDelta"] {
        display: none !important;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #f1f5f9 !important;
        font-weight: 600 !important;
    }
    p, span, li, label {
        color: #cbd5e1 !important;
    }
    .stMarkdown, .stMarkdown p, .stMarkdown span {
        color: #cbd5e1 !important;
    }
    .stTabs {
        background: transparent;
    }
    .stTabs [data-baseweb="tab-list"] {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d4a6f 100%);
        padding: 14px 18px;
        border-radius: 12px;
        gap: 10px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
        flex-wrap: wrap;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 8px;
        padding: 12px 24px;
        font-size: 14px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.8) !important;
        transition: all 0.3s ease;
        white-space: nowrap;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.15);
        border-color: rgba(255, 255, 255, 0.3);
        color: #ffffff !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%) !important;
        color: #ffffff !important;
        border: none;
        box-shadow: 0 4px 15px rgba(14, 165, 233, 0.4);
    }
    .stTabs [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"] {
        display: none !important;
    }
    .insight-card, .warning-card, .success-card, .danger-card {
        background: rgba(30, 41, 59, 0.8);
        border-radius: 10px;
        padding: 20px 24px;
        margin: 20px 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        font-size: 15px;
        line-height: 1.7;
        color: #e2e8f0 !important;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .insight-card {
        border-left: 4px solid #3b82f6;
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(30, 41, 59, 0.9) 100%);
    }
    .warning-card {
        border-left: 4px solid #f59e0b;
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(30, 41, 59, 0.9) 100%);
    }
    .success-card {
        border-left: 4px solid #10b981;
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(30, 41, 59, 0.9) 100%);
    }
    .danger-card {
        border-left: 4px solid #ef4444;
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(30, 41, 59, 0.9) 100%);
    }
    .insight-card strong, .warning-card strong, .success-card strong, .danger-card strong {
        color: #ffffff !important;
    }
    [data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.7);
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.2s ease;
    }
    [data-testid="stMetric"]:hover {
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
        border-color: rgba(255, 255, 255, 0.2);
        transform: translateY(-2px);
    }
    [data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 28px !important;
        font-weight: 700 !important;
    }
    .stButton > button {
        background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%);
        color: white !important;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 14px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(14, 165, 233, 0.3);
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #06b6d4 0%, #0ea5e9 100%);
        box-shadow: 0 6px 20px rgba(14, 165, 233, 0.4);
        transform: translateY(-2px);
    }
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }
    .stDataFrame [data-testid="stDataFrameResizable"] {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    .streamlit-expanderHeader {
        background: rgba(30, 41, 59, 0.7) !important;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #e2e8f0 !important;
    }
    .streamlit-expanderContent {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-top: none;
        border-radius: 0 0 10px 10px;
        color: #cbd5e1 !important;
    }
    details summary span {
        color: #e2e8f0 !important;
    }
    .stProgress > div > div {
        background: linear-gradient(90deg, #10b981, #06b6d4);
        border-radius: 10px;
    }
    .stProgress {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    .stMultiSelect [data-baseweb="tag"] {
        background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%) !important;
        color: white !important;
        border-radius: 6px;
    }
    .stMultiSelect [data-baseweb="select"] > div {
        background: rgba(30, 41, 59, 0.7) !important;
        border-radius: 8px;
        border-color: rgba(255, 255, 255, 0.2) !important;
        color: #e2e8f0 !important;
    }
    .stMultiSelect [data-baseweb="select"] > div:hover {
        border-color: rgba(255, 255, 255, 0.4) !important;
    }
    [data-baseweb="popover"] {
        background: #1e293b !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    [data-baseweb="menu"] {
        background: #1e293b !important;
    }
    [role="option"] {
        color: #e2e8f0 !important;
    }
    [role="option"]:hover {
        background: rgba(14, 165, 233, 0.2) !important;
    }
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(to right, transparent, rgba(255, 255, 255, 0.2), transparent);
        margin: 32px 0;
    }
    .block-container {
        padding: 2rem 3rem 3rem 3rem;
        max-width: 100%;
    }
    [data-testid="stPlotlyChart"] {
        background: rgba(30, 41, 59, 0.5);
        border-radius: 10px;
        padding: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .stAlert {
        background: rgba(30, 41, 59, 0.7) !important;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #e2e8f0 !important;
    }
    [data-testid="stNotification"] {
        background: rgba(30, 41, 59, 0.9) !important;
        color: #e2e8f0 !important;
    }
    .stTabs .stTabs [data-baseweb="tab-list"] {
        background: rgba(15, 23, 42, 0.6);
        padding: 8px 12px;
        border-radius: 8px;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .stTabs .stTabs [data-baseweb="tab"] {
        background: transparent;
        border: 1px solid transparent;
        color: #94a3b8 !important;
        padding: 10px 20px;
        font-size: 13px;
    }
    .stTabs .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.05);
        color: #e2e8f0 !important;
    }
    .stTabs .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: rgba(14, 165, 233, 0.2) !important;
        color: #0ea5e9 !important;
        border: 1px solid rgba(14, 165, 233, 0.3);
    }
    .footer-text {
        text-align: center;
        color: #94a3b8 !important;
        padding: 24px;
        font-size: 14px;
        background: rgba(30, 41, 59, 0.5);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-top: 32px;
    }
    .footer-text b {
        color: #0ea5e9 !important;
    }
    [data-testid="stFileUploader"] {
        background: rgba(30, 41, 59, 0.5);
        border-radius: 10px;
        padding: 20px;
        border: 2px dashed rgba(255, 255, 255, 0.2);
    }
    [data-testid="stFileUploader"]:hover {
        border-color: rgba(14, 165, 233, 0.5);
    }
    .row-widget {
        color: #e2e8f0 !important;
    }
    .stMarkdown strong {
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Shared text style constants for all Plotly charts ──
LABEL_FONT = dict(color='white', size=15, family='Arial Black')
AXIS_TITLE_FONT = dict(color='#94a3b8', size=13)
AXIS_TICK_FONT = dict(color='#e2e8f0', size=12)
GRID_COLOR = 'rgba(255,255,255,0.08)'
LEGEND_FONT = dict(size=13, color='#e2e8f0')
CHART_BG = 'rgba(0,0,0,0)'

# ── Shared Plotly config to disable scrollZoom and unwanted interactions ──
PLOTLY_CONFIG = dict(scrollZoom=False, displayModeBar=False)

# ── Person colours used across the new AI video tab ──
PERSON_COLORS = {
    'Fathima Rukaiya': '#f59e0b',
    'Amana Nasik': '#0ea5e9',
    'Yenushka Bandara': '#10b981',
    'Piyumi Shanika': '#a78bfa',
}
DAILY_TARGET = 50          # per person per day
TEAM_DAILY_TARGET = 200    # all 4 persons combined per day


# --- ROBUST DATA CLEANING FUNCTION ---
def clean_and_preprocess(df):
    df.columns = df.columns.str.strip()
    df = df[df['Course Name'].notna()].copy()
    df = df[~df['Course Name'].str.contains('Status of the Project', case=False, na=False)]
    df['Course Name'] = df['Course Name'].astype(str).str.strip()
    df['Course Name'] = df['Course Name'].str.replace(r'^\n+', '', regex=True)
    df['Course Name'] = df['Course Name'].str.replace(r'\n+', ' ', regex=True)
    df['Course Name'] = df['Course Name'].str.replace(r'\s+', ' ', regex=True)
    numeric_cols = ['Number of Units', 'Number of AI Videos', 'Number of Podcasts', 'Number of Study Guides']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df[df['Number of Units'].notna() & (df['Number of Units'] > 0)].copy()
    for col in ['Number of AI Videos', 'Number of Podcasts', 'Number of Study Guides']:
        df[col] = df[col].fillna(0).astype(int)
    df['Number of Units'] = df['Number of Units'].astype(int)
    return df

@st.cache_data(ttl=300)
def download_excel_bytes(url):
    """Download the Excel file ONCE and return raw bytes (shared by both parsers)."""
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.content
        return None
    except Exception:
        return None

def load_data(file_bytes):
    """Parse the main tracker sheet (first sheet) from raw file bytes or file-like object."""
    try:
        if isinstance(file_bytes, bytes):
            file_content = BytesIO(file_bytes)
        else:
            file_content = file_bytes
        df = pd.read_excel(file_content, engine='openpyxl')
        df = clean_and_preprocess(df)
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None


# ── Load chapter-wise AI video sheet ──
def load_chapter_video_data(file_bytes):
    """Parse the 'Chapter-wise AI video Project' sheet from raw file bytes or file-like object."""
    try:
        if isinstance(file_bytes, bytes):
            file_content = BytesIO(file_bytes)
        else:
            file_content = file_bytes

        # Try to find the sheet — handle trailing space / slight name variations
        xls = pd.ExcelFile(file_content, engine='openpyxl')
        sheet_name = None
        for s in xls.sheet_names:
            if 'chapter' in s.lower() and 'video' in s.lower():
                sheet_name = s
                break
        if sheet_name is None:
            return None

        raw = pd.read_excel(xls, sheet_name=sheet_name, header=None)

        # Extract person names from row 1 (cols 2-5)
        persons = []
        for c in [2, 3, 4, 5]:
            if c < len(raw.columns):
                name = str(raw.iloc[1, c]).strip() if pd.notna(raw.iloc[1, c]) else f'Person {c-1}'
            else:
                name = f'Person {c-1}'
            persons.append(name)

        # Build the week label column (forward-fill the week markers)
        raw['Week'] = raw[0].where(raw[0].notna()).ffill()
        raw['Week'] = raw['Week'].astype(str).str.replace(r'\n+', '', regex=True).str.strip()

        # Keep only rows that have a valid date in column 1
        data_rows = raw.copy()
        data_rows = data_rows.iloc[2:]  # skip header rows

        records = []
        for _, row in data_rows.iterrows():
            date_val = row[1]
            if pd.isna(date_val):
                continue
            date_val = pd.to_datetime(date_val, errors='coerce')
            if pd.isna(date_val):
                continue
            # Fix dates with wrong year (2025 instead of 2026)
            if date_val.year == 2025:
                date_val = date_val.replace(year=2026)
            week_label = row['Week'] if pd.notna(row.get('Week')) else ''
            for i, person in enumerate(persons):
                col_idx = i + 2
                raw_val = row[col_idx] if col_idx < len(row) - 1 else np.nan  # -1 because of added 'Week' col
                # Check if value is a note/text (non-numeric)
                note = ''
                videos = 0
                if pd.notna(raw_val):
                    # Handle values that might be numeric strings, ints, floats, or text
                    try:
                        v = float(raw_val)
                        if not np.isnan(v):
                            videos = int(v)
                    except (ValueError, TypeError):
                        note = str(raw_val).strip()
                        videos = 0
                records.append({
                    'Date': date_val,
                    'Week': week_label,
                    'Person': person,
                    'Videos': videos,
                    'Note': note,
                    'Day': date_val.day_name()[:3],
                    'Date Label': date_val.strftime('%d %b %Y'),
                })

        if not records:
            return pd.DataFrame()

        vdf = pd.DataFrame(records)
        vdf['Day'] = vdf['Date'].dt.day_name().str[:3]
        vdf['Met Target'] = vdf['Videos'] >= DAILY_TARGET
        vdf['Shortfall'] = np.where(vdf['Videos'] < DAILY_TARGET, DAILY_TARGET - vdf['Videos'], 0)
        vdf['Surplus'] = np.where(vdf['Videos'] >= DAILY_TARGET, vdf['Videos'] - DAILY_TARGET, 0)
        return vdf
    except Exception as e:
        st.error(f"Error loading chapter-wise video data: {str(e)}")
        return None


def engineer_features(df):
    df['Videos Completed'] = df['Number of AI Videos']
    df['Podcasts Completed'] = df['Number of Podcasts']
    df['Guides Completed'] = df['Number of Study Guides']
    df['Total Required'] = df['Number of Units'] * 3
    df['Total Completed'] = df['Videos Completed'] + df['Podcasts Completed'] + df['Guides Completed']
    df['Still Pending'] = df['Total Required'] - df['Total Completed']
    df['Completion %'] = np.where(df['Total Required'] > 0, (df['Total Completed'] / df['Total Required']) * 100, 0)
    df['Video %'] = np.where(df['Number of Units'] > 0, (df['Videos Completed'] / df['Number of Units']) * 100, 0)
    df['Podcast %'] = np.where(df['Number of Units'] > 0, (df['Podcasts Completed'] / df['Number of Units']) * 100, 0)
    df['Guide %'] = np.where(df['Number of Units'] > 0, (df['Guides Completed'] / df['Number of Units']) * 100, 0)
    def get_status(row):
        pct = row['Completion %']
        if pct == 0: return 'Not Started'
        elif pct < 50: return 'Early Stage'
        elif pct < 75: return 'In Progress'
        elif pct < 100: return 'Almost Done'
        else: return 'Complete'
    df['Status'] = df.apply(get_status, axis=1)
    df['Priority Score'] = df['Number of Units'] * (100 - df['Completion %'])
    df['Course Level'] = df['Course Name'].str.extract(r'(Level \d+)', expand=False)
    df['Course Level'] = df['Course Level'].fillna('Other')
    def categorise_subject(title):
        title = str(title).lower()
        if any(word in title for word in ['business', 'management', 'accounting', 'finance', 'administration', 'customer service']): return 'Business & Management'
        elif any(word in title for word in ['computing', 'cyber', 'web', 'software', 'data', 'ai', 'artificial', 'digital', 'networking']): return 'Computing & IT'
        elif any(word in title for word in ['health', 'care', 'nutrition', 'dementia', 'safeguarding', 'diabetes', 'autism', 'mental health', 'counselling', 'adult care']): return 'Health & Social Care'
        elif any(word in title for word in ['teaching', 'education', 'child', 'assessing', 'learning', 'early years', 'playwork', 'residential childcare']): return 'Education & Childcare'
        elif 'law' in title: return 'Law'
        elif any(word in title for word in ['sports', 'fitness', 'gym', 'personal training', 'leisure']): return 'Sports & Fitness'
        elif any(word in title for word in ['hospitality', 'tourism']): return 'Hospitality & Tourism'
        else: return 'Other Specialisations'
    df['Subject Area'] = df['Course Name'].apply(categorise_subject)
    def size_category(units):
        if units <= 3: return 'Small (1-3 units)'
        elif units <= 7: return 'Medium (4-7 units)'
        elif units <= 12: return 'Large (8-12 units)'
        else: return 'Very Large (13+ units)'
    df['Course Size'] = df['Number of Units'].apply(size_category)
    df['Videos Pending'] = df['Number of Units'] - df['Videos Completed']
    df['Podcasts Pending'] = df['Number of Units'] - df['Podcasts Completed']
    df['Guides Pending'] = df['Number of Units'] - df['Guides Completed']
    df['Content Imbalance'] = df[['Video %', 'Podcast %', 'Guide %']].max(axis=1) - df[['Video %', 'Podcast %', 'Guide %']].min(axis=1)
    def weakest_type(row):
        types = {'AI Videos': row['Video %'], 'Podcasts': row['Podcast %'], 'Study Guides': row['Guide %']}
        return min(types, key=types.get)
    df['Weakest Content Type'] = df.apply(weakest_type, axis=1)
    return df


# --- MAIN APP ---
st.title("📊 Course Content Production Dashboard")
with st.expander("📖 How to Read This Dashboard"):
    st.markdown("""
    **Key Terms:**
    - **Units:** Individual teaching modules within a course
    - **Content per Unit:** Each unit requires 3 items — 1 AI Video, 1 Podcast, and 1 Study Guide
    - **Completion %:** Percentage of all required AI Videos, Podcasts, and Study Guides produced
    - **Still Pending:** Number of AI Videos, Podcasts, and Study Guides yet to be created
    - **Priority Score:** Larger courses with less progress have higher priority
    
    **Status Categories:**
    - **Not Started:** 0% — no AI Videos, Podcasts, or Study Guides produced
    - **Early Stage:** 1-49%  |  **In Progress:** 50-74%  |  **Almost Done:** 75-99%  |  **Complete:** 100%
    """)

sharepoint_url = "https://globaledulinkuk-my.sharepoint.com/:x:/g/personal/sadeev_imperiallearning_co_uk/IQCgqczvPccERK5x-3fcBFPdAUsHzB0rMIahy7kRMz39xtU?download=1"

# ── Download the file ONCE — both parsers share the same bytes ──
file_bytes = download_excel_bytes(sharepoint_url)
df = None
vdf = None

if file_bytes is not None:
    df = load_data(file_bytes)
    vdf = load_chapter_video_data(file_bytes)

if df is None:
    st.warning("⚠️ Automatic Update Failed. Company security may be blocking the direct link.")
    st.info("👇 Download the tracker file and upload it here.")
    uploaded_file = st.file_uploader("Upload 'Additional Material Tracker Sheet.xlsx'", type=['xlsx'])
    if uploaded_file is not None:
        upload_bytes = uploaded_file.read()
        df = load_data(upload_bytes)
        vdf = load_chapter_video_data(upload_bytes)
    else:
        st.stop()

df = engineer_features(df)
total_courses = len(df)
total_units = df['Number of Units'].sum()
total_required = df['Total Required'].sum()
total_completed = df['Total Completed'].sum()
total_pending = total_required - total_completed
overall_completion = (total_completed / total_required * 100) if total_required > 0 else 0
complete_courses = len(df[df['Completion %'] == 100])
not_started_courses = len(df[df['Completion %'] == 0])
in_progress_courses = total_courses - complete_courses - not_started_courses
total_videos_done = df['Videos Completed'].sum()
total_podcasts_done = df['Podcasts Completed'].sum()
total_guides_done = df['Guides Completed'].sum()
videos_pending = total_units - total_videos_done
podcasts_pending = total_units - total_podcasts_done
guides_pending = total_units - total_guides_done
video_pct = (total_videos_done / total_units * 100) if total_units > 0 else 0
podcast_pct = (total_podcasts_done / total_units * 100) if total_units > 0 else 0
guide_pct = (total_guides_done / total_units * 100) if total_units > 0 else 0

if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()
st.markdown("---")

tab_overview, tab_content, tab_subjects, tab_quickwins, tab_priority, tab_aivideos, tab_allcourses = st.tabs([
    "📈 Overview", "🎯 Content Analysis", "📚 Subject & Level",
    "✅ Quick Wins", "⚠️ Priority Watch", "🎬 Daily Chapter-wise AI Video Progress", "📋 All Courses"
])

# ═══════════════════════════════════════════════════════════════════
#  TAB 1 — OVERVIEW
# ═══════════════════════════════════════════════════════════════════
with tab_overview:
    st.markdown("## Executive Summary")
    st.markdown("*High-level view of content production across AI Videos, Podcasts, and Study Guides*")
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Key Metrics")
    st.markdown("<br>", unsafe_allow_html=True)
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1: st.metric("Overall Completion", f"{overall_completion:.1f}%")
    with k2: st.metric("AI Videos Completed", f"{int(total_videos_done)}/{int(total_units)}")
    with k3: st.metric("Podcasts Completed", f"{int(total_podcasts_done)}/{int(total_units)}")
    with k4: st.metric("Study Guides Completed", f"{int(total_guides_done)}/{int(total_units)}")
    with k5: st.metric("Courses Fully Done", f"{complete_courses}")
    with k6: st.metric("Courses Not Started", f"{not_started_courses}")
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Overall Progress")
    st.markdown("<br>", unsafe_allow_html=True)
    progress_fig = go.Figure(go.Bar(x=[overall_completion], y=['Progress'], orientation='h',
        marker=dict(color='#0ea5e9'), text=[f'{overall_completion:.1f}%'], textposition='inside',
        textfont=dict(color='white', size=20, family='Arial Black')))
    progress_fig.add_shape(type="line", x0=100, x1=100, y0=-0.5, y1=0.5, line=dict(color="#10b981", width=3, dash="dash"))
    progress_fig.add_annotation(x=100, y=0.6, text="Target: 100%", showarrow=False, font=dict(size=13, color="#94a3b8"))
    progress_fig.update_traces(cliponaxis=False)
    progress_fig.update_layout(xaxis=dict(range=[0, 110], title=dict(text="Completion %", font=AXIS_TITLE_FONT), tickfont=AXIS_TICK_FONT, gridcolor=GRID_COLOR),
        yaxis=dict(visible=False), height=100, margin=dict(l=0, r=0, t=10, b=40), showlegend=False, paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG)
    st.plotly_chart(progress_fig, use_container_width=True, config=PLOTLY_CONFIG)
    st.markdown("<br>", unsafe_allow_html=True)

    if overall_completion < 30:
        st.markdown(f'<div class="danger-card" style="max-width: 100%;"><strong>⚠️ Critical Status:</strong> At <strong>{overall_completion:.1f}%</strong> completion.<br><br>Still pending: <strong>{int(videos_pending)} AI Videos</strong>, <strong>{int(podcasts_pending)} Podcasts</strong>, and <strong>{int(guides_pending)} Study Guides</strong> across <strong>{total_courses} courses</strong>. <strong>{not_started_courses} courses</strong> have not begun.</div>', unsafe_allow_html=True)
    elif overall_completion < 50:
        st.markdown(f'<div class="warning-card" style="max-width: 100%;"><strong>⚡ Behind Schedule:</strong> At <strong>{overall_completion:.1f}%</strong>.<br><br>Still needed: <strong>{int(videos_pending)} AI Videos</strong>, <strong>{int(podcasts_pending)} Podcasts</strong>, <strong>{int(guides_pending)} Study Guides</strong>. Focus on {in_progress_courses} in-progress courses.</div>', unsafe_allow_html=True)
    elif overall_completion < 75:
        st.markdown(f'<div class="insight-card" style="max-width: 100%;"><strong>📊 Making Progress:</strong> At <strong>{overall_completion:.1f}%</strong>.<br><br>Remaining: <strong>{int(videos_pending)} AI Videos</strong>, <strong>{int(podcasts_pending)} Podcasts</strong>, <strong>{int(guides_pending)} Study Guides</strong>. <strong>{complete_courses} courses</strong> fully complete.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="success-card" style="max-width: 100%;"><strong>✅ Strong Position:</strong> At <strong>{overall_completion:.1f}%</strong>.<br><br>Only <strong>{int(videos_pending)} AI Videos</strong>, <strong>{int(podcasts_pending)} Podcasts</strong>, <strong>{int(guides_pending)} Study Guides</strong> left.</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### Progress by Content Type & Course Status")
    st.markdown("<br>", unsafe_allow_html=True)
    left_col, right_col = st.columns(2)
    with left_col:
        st.markdown("#### AI Videos vs Podcasts vs Study Guides")
        st.markdown("*How far each content type has progressed*")
        tp_fig = go.Figure()
        for name, done, pend, color in [("AI Videos", total_videos_done, videos_pending, "#f59e0b"),
            ("Podcasts", total_podcasts_done, podcasts_pending, "#0ea5e9"), ("Study Guides", total_guides_done, guides_pending, "#10b981")]:
            pct = done / total_units * 100 if total_units > 0 else 0
            tp_fig.add_trace(go.Bar(y=[name], x=[pct], orientation='h', marker=dict(color=color),
                text=[f'{pct:.1f}%  ({int(done)} done, {int(pend)} pending)'], textposition='inside',
                textfont=LABEL_FONT, name=name, showlegend=False))
        tp_fig.add_shape(type="line", x0=100, x1=100, y0=-0.5, y1=2.5, line=dict(color="#ffffff", width=2, dash="dash"))
        tp_fig.update_traces(cliponaxis=False)
        tp_fig.update_layout(xaxis=dict(range=[0, 115], title=dict(text="Completion %", font=AXIS_TITLE_FONT), tickfont=AXIS_TICK_FONT, gridcolor=GRID_COLOR),
            yaxis=dict(tickfont=dict(color='#e2e8f0', size=14), automargin=True), height=260, margin=dict(l=0, r=0, t=10, b=40), paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG)
        st.plotly_chart(tp_fig, use_container_width=True, config=PLOTLY_CONFIG)
        
        st.markdown(f'<div class="insight-card" style="max-width: 100%;"><strong>🎯 Content Progress:</strong> The highest completion rate is in <strong>{max([("AI Videos", video_pct), ("Podcasts", podcast_pct), ("Study Guides", guide_pct)], key=lambda item:item[1])[0]}</strong>, while the lowest is in <strong>{min([("AI Videos", video_pct), ("Podcasts", podcast_pct), ("Study Guides", guide_pct)], key=lambda item:item[1])[0]}</strong>.</div>', unsafe_allow_html=True)
        
    with right_col:
        st.markdown("#### Course Status Breakdown")
        st.markdown("*How many courses are in each stage*")
        sc = df['Status'].value_counts().reset_index(); sc.columns = ['Status', 'Count']
        sc_map = {'Not Started': '#ef4444', 'Early Stage': '#f59e0b', 'In Progress': '#0ea5e9', 'Almost Done': '#10b981', 'Complete': '#059669'}
        fs = px.pie(sc, values='Count', names='Status', color='Status', color_discrete_map=sc_map, hole=0.45)
        fs.update_traces(
            textposition='inside', 
            textinfo='value+percent', 
            textfont=dict(size=15, color='white'),
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>"
        )
        fs.update_layout(height=260, margin=dict(t=10, b=10, l=10, r=10), legend=dict(font=LEGEND_FONT, bgcolor=CHART_BG), paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG)
        st.plotly_chart(fs, use_container_width=True, config=PLOTLY_CONFIG)
        
        st.markdown(f'<div class="insight-card" style="max-width: 100%;"><strong>📊 Status Overview:</strong> <strong>{complete_courses}</strong> courses are fully complete, while <strong>{not_started_courses}</strong> remain untouched.</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
#  TAB 2 — CONTENT ANALYSIS
# ═══════════════════════════════════════════════════════════════════
with tab_content:
    st.markdown("## Content Type Analysis")
    st.markdown("*Identifying which content type — AI Videos, Podcasts, or Study Guides — is slowing us down*")
    st.markdown("<br>", unsafe_allow_html=True)
    lc, rc = st.columns(2)
    with lc:
        st.markdown("#### Completed vs Pending — AI Videos, Podcasts, Study Guides")
        st.markdown("*Green = done, Red = still needed*")
        cd = pd.DataFrame({'Content Type': ['AI Videos', 'Podcasts', 'Study Guides'],
            'Completed': [total_videos_done, total_podcasts_done, total_guides_done],
            'Pending': [videos_pending, podcasts_pending, guides_pending],
            'Required': [total_units, total_units, total_units]})
        cd['Completion %'] = (cd['Completed'] / cd['Required'] * 100).round(1)
        fc = go.Figure()
        fc.add_trace(go.Bar(name='Completed', x=cd['Content Type'], y=cd['Completed'], marker_color='#10b981',
            text=cd['Completed'].astype(int), textposition='inside', textfont=LABEL_FONT))
        fc.add_trace(go.Bar(name='Still Pending', x=cd['Content Type'], y=cd['Pending'], marker_color='#ef4444',
            text=cd['Pending'].astype(int), textposition='inside', textfont=LABEL_FONT))
        fc.update_traces(cliponaxis=False)
        fc.update_layout(barmode='stack', legend=dict(orientation="h", yanchor="bottom", y=1.02, font=LEGEND_FONT), height=420, margin=dict(t=60, b=20, l=20, r=20),
            paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG, xaxis=dict(tickfont=dict(color='#e2e8f0', size=14)),
            yaxis=dict(title=dict(text="Number of Items", font=AXIS_TITLE_FONT), tickfont=AXIS_TICK_FONT, gridcolor=GRID_COLOR))
        st.plotly_chart(fc, use_container_width=True, config=PLOTLY_CONFIG)
        
        st.markdown(f'<div class="insight-card" style="max-width: 100%;"><strong>📦 Volume Insight:</strong> A total of <strong>{int(total_completed)}</strong> contents (videos, podcast, guides) have been created so far, with <strong>{int(total_pending)}</strong> remaining across all active courses.</div>', unsafe_allow_html=True)
        
    with rc:
        st.markdown("#### Completion Rate per Content Type")
        st.markdown("*Which content type is closest to — or farthest from — 100%?*")
        rf = go.Figure()
        clrs = ['#f59e0b', '#0ea5e9', '#10b981']
        for i, row in cd.iterrows():
            rf.add_trace(go.Bar(y=[row['Content Type']], x=[row['Completion %']], orientation='h', marker=dict(color=clrs[i]),
                text=[f"{row['Completion %']:.1f}%"], textposition='inside', textfont=LABEL_FONT, showlegend=False))
        rf.add_shape(type="line", x0=100, x1=100, y0=-0.5, y1=2.5, line=dict(color="#ffffff", width=2, dash="dash"))
        rf.add_annotation(x=100, y=2.7, text="100% Target", showarrow=False, font=dict(size=12, color="#94a3b8"))
        rf.update_traces(cliponaxis=False)
        rf.update_layout(xaxis=dict(range=[0, 115], title=dict(text="Completion %", font=AXIS_TITLE_FONT), tickfont=AXIS_TICK_FONT, gridcolor=GRID_COLOR),
            yaxis=dict(tickfont=dict(color='#e2e8f0', size=14), automargin=True), height=420, margin=dict(t=60, b=20, l=0, r=20), paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG)
        st.plotly_chart(rf, use_container_width=True, config=PLOTLY_CONFIG)
        
        bm = {'AI Videos': video_pct, 'Podcasts': podcast_pct, 'Study Guides': guide_pct}
        bn = min(bm, key=bm.get); bp = bm[bn]; best = max(bm, key=bm.get); bestp = bm[best]; gap = bestp - bp
        st.markdown(f'<div class="warning-card" style="max-width: 100%;"><strong>🔍 Bottleneck:</strong> <strong>{bn}</strong> is the slowest at only <strong>{bp:.1f}%</strong> — <strong>{gap:.1f} points</strong> behind {best}. Prioritising {bn} will clear the backlog fastest.</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### Top 15 Courses — Most Content Still Missing")
    st.markdown("*Sorted by total AI Videos, Podcasts, and Study Guides still needed*")
    gdf = df[['Course Name', 'Number of Units', 'Videos Completed', 'Podcasts Completed', 'Guides Completed']].copy()
    gdf['Videos Gap'] = gdf['Number of Units'] - gdf['Videos Completed']
    gdf['Podcasts Gap'] = gdf['Number of Units'] - gdf['Podcasts Completed']
    gdf['Guides Gap'] = gdf['Number of Units'] - gdf['Guides Completed']
    gdf['Total Gap'] = gdf['Videos Gap'] + gdf['Podcasts Gap'] + gdf['Guides Gap']
    gdf = gdf[gdf['Total Gap'] > 0].sort_values('Total Gap', ascending=False)
    st.dataframe(gdf[['Course Name', 'Number of Units', 'Videos Gap', 'Podcasts Gap', 'Guides Gap', 'Total Gap']].head(15).rename(columns={
        'Number of Units': 'Units', 'Videos Gap': 'AI Videos Needed', 'Podcasts Gap': 'Podcasts Needed',
        'Guides Gap': 'Study Guides Needed', 'Total Gap': 'Total Needed'}), hide_index=True, use_container_width=True, height=480)
    tg = gdf.iloc[0]
    st.markdown(f'<div class="insight-card"><strong>📋 Biggest Gap:</strong> "<strong>{tg["Course Name"]}</strong>" needs <strong>{int(tg["Videos Gap"])} AI Videos</strong>, <strong>{int(tg["Podcasts Gap"])} Podcasts</strong>, <strong>{int(tg["Guides Gap"])} Study Guides</strong>.</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
#  TAB 3 — SUBJECT & LEVEL
# ═══════════════════════════════════════════════════════════════════
with tab_subjects:
    st.markdown("## Performance by Subject Area & Level")
    st.markdown("*Which Subject Area and levels need attention for AI Videos, Podcasts, and Study Guides*")
    st.markdown("<br>", unsafe_allow_html=True)
    st1, st2 = st.tabs(["📚 By Subject Area", "📊 By Course Level"])
    with st1:
        st.markdown("<br>", unsafe_allow_html=True)
        sdf = df.groupby('Subject Area').agg({'Course Name': 'count', 'Number of Units': 'sum', 'Total Completed': 'sum', 'Total Required': 'sum', 'Completion %': 'mean'}).reset_index()
        sdf.columns = ['Subject Area', 'Number of Courses', 'Total Units', 'Content Completed', 'Content Required', 'Avg Completion %']
        sdf['Content Pending'] = sdf['Content Required'] - sdf['Content Completed']
        sdf = sdf.sort_values('Avg Completion %', ascending=True)
        sdf = sdf[sdf['Number of Courses'] >= 2]
        lc, rc = st.columns(2)
        with lc:
            st.markdown("#### Average Completion by Subject Area")
            st.markdown("*How close each subject area is to finishing all content*")
            fsg = go.Figure(go.Bar(y=sdf['Subject Area'], x=sdf['Avg Completion %'].round(1), orientation='h',
                marker=dict(color=sdf['Avg Completion %'], colorscale=[[0,'#ef4444'],[0.5,'#f59e0b'],[1,'#10b981']], cmin=0, cmax=100, showscale=False),
                text=sdf['Avg Completion %'].round(1).astype(str)+'%', textposition='outside', textfont=dict(color='white', size=14)))
            fsg.add_vline(x=50, line_dash="dash", line_color="#f59e0b", annotation_text="50%", annotation_font=dict(color='white', size=13))
            fsg.update_traces(cliponaxis=False)
            fsg.update_layout(xaxis=dict(range=[0, 115], title=dict(text="Avg Completion %", font=AXIS_TITLE_FONT), tickfont=AXIS_TICK_FONT, gridcolor=GRID_COLOR),
                yaxis=dict(title="", tickfont=dict(color='#e2e8f0', size=12), automargin=True), height=450, margin=dict(t=10, b=20, l=10, r=70), paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG)
            st.plotly_chart(fsg, use_container_width=True, config=PLOTLY_CONFIG)
            
            bs = sdf.iloc[-1]; ws = sdf.iloc[0]
            st.markdown(f'<div class="insight-card" style="max-width: 100%;"><strong>🏆 Top & Bottom Subjects:</strong> <strong>{bs["Subject Area"]}</strong> leads with {bs["Avg Completion %"]:.1f}%, while <strong>{ws["Subject Area"]}</strong> lags at {ws["Avg Completion %"]:.1f}%.</div>', unsafe_allow_html=True)
            
        with rc:
            st.markdown("#### Pending AI Videos, Podcasts & Study Guides by Subject")
            st.markdown("*Hover over segments for exact values*")
            sp = df.groupby('Subject Area').agg({'Videos Pending': 'sum', 'Podcasts Pending': 'sum', 'Guides Pending': 'sum'}).reset_index()
            sp['Total'] = sp['Videos Pending'] + sp['Podcasts Pending'] + sp['Guides Pending']
            sp = sp[sp['Subject Area'].isin(sdf['Subject Area'])].sort_values('Total', ascending=True)
            
            # Smart text: only show numbers inside segments that are wide enough to read
            sp_max = sp['Total'].max() if len(sp) > 0 else 1
            sp_thresh = sp_max * 0.07
            
            pf = go.Figure()
            pf.add_trace(go.Bar(y=sp['Subject Area'], x=sp['Videos Pending'], name='AI Videos', marker_color='#f59e0b', orientation='h',
                text=[str(int(v)) if v >= sp_thresh else '' for v in sp['Videos Pending']],
                textposition='inside', textfont=dict(color='white', size=13, family='Arial Black'), insidetextanchor='middle',
                hovertemplate='<b>%{y}</b><br>AI Videos Pending: %{x}<extra></extra>'))
            pf.add_trace(go.Bar(y=sp['Subject Area'], x=sp['Podcasts Pending'], name='Podcasts', marker_color='#0ea5e9', orientation='h',
                text=[str(int(v)) if v >= sp_thresh else '' for v in sp['Podcasts Pending']],
                textposition='inside', textfont=dict(color='white', size=13, family='Arial Black'), insidetextanchor='middle',
                hovertemplate='<b>%{y}</b><br>Podcasts Pending: %{x}<extra></extra>'))
            pf.add_trace(go.Bar(y=sp['Subject Area'], x=sp['Guides Pending'], name='Study Guides', marker_color='#10b981', orientation='h',
                text=[str(int(v)) if v >= sp_thresh else '' for v in sp['Guides Pending']],
                textposition='inside', textfont=dict(color='white', size=13, family='Arial Black'), insidetextanchor='middle',
                hovertemplate='<b>%{y}</b><br>Study Guides Pending: %{x}<extra></extra>'))
            
            # Total annotations at end of each bar
            for _, row in sp.iterrows():
                pf.add_annotation(x=row['Total'], y=row['Subject Area'],
                    text=f"  {int(row['Total'])}", showarrow=False, xanchor='left',
                    font=dict(color='#94a3b8', size=12, family='Arial'))
            
            pf.update_traces(cliponaxis=False)
            pf.update_layout(barmode='stack', xaxis=dict(title=dict(text="Pending Items", font=AXIS_TITLE_FONT), tickfont=AXIS_TICK_FONT, gridcolor=GRID_COLOR, range=[0, sp['Total'].max() * 1.2]),
                yaxis=dict(title="", tickfont=dict(color='#e2e8f0', size=12), automargin=True), height=450, margin=dict(t=10, b=20, l=10, r=60),
                paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG, legend=dict(orientation="h", yanchor="bottom", y=1.02, font=LEGEND_FONT, bgcolor=CHART_BG))
            st.plotly_chart(pf, use_container_width=True, config=PLOTLY_CONFIG)
            
            max_pending = sp.iloc[-1]
            st.markdown(f'<div class="warning-card" style="max-width: 100%;"><strong>🏋️ Heaviest Workload:</strong> <strong>{max_pending["Subject Area"]}</strong> requires the most effort, needing <strong>{int(max_pending["Total"])}</strong> combined items.</div>', unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Subject Area Details")
        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(sdf[['Subject Area', 'Number of Courses', 'Total Units', 'Content Completed', 'Content Pending', 'Avg Completion %']].sort_values('Avg Completion %', ascending=False),
            column_config={"Avg Completion %": st.column_config.ProgressColumn("Avg Progress", format="%.1f%%", min_value=0, max_value=100)}, hide_index=True, use_container_width=True)
            
    with st2:
        st.markdown("<br>", unsafe_allow_html=True)
        ldf = df.groupby('Course Level').agg({'Course Name': 'count', 'Number of Units': 'sum', 'Total Completed': 'sum', 'Total Required': 'sum', 'Completion %': 'mean'}).reset_index()
        ldf.columns = ['Course Level', 'Number of Courses', 'Total Units', 'Content Completed', 'Content Required', 'Avg Completion %']
        lo = ['Level 1', 'Level 2', 'Level 3', 'Level 4', 'Level 5', 'Level 6', 'Level 7', 'Other']
        ldf['Level Order'] = ldf['Course Level'].apply(lambda x: lo.index(x) if x in lo else 99)
        ldf = ldf.sort_values('Level Order')
        ldf = ldf[ldf['Number of Courses'] >= 1]
        lc, rc = st.columns(2)
        with lc:
            st.markdown("#### Average Completion by Course Level")
            st.markdown("*Which qualification levels are furthest ahead or behind?*")
            fl = go.Figure(go.Bar(x=ldf['Course Level'], y=ldf['Avg Completion %'].round(1),
                marker=dict(color=ldf['Avg Completion %'], colorscale=[[0,'#ef4444'],[0.5,'#f59e0b'],[1,'#10b981']], cmin=0, cmax=100, showscale=False),
                text=ldf['Avg Completion %'].round(1).astype(str)+'%', textposition='outside', textfont=dict(color='white', size=14)))
            fl.update_traces(cliponaxis=False)
            fl.update_layout(yaxis=dict(range=[0, 115], title=dict(text="Avg Completion %", font=AXIS_TITLE_FONT), tickfont=AXIS_TICK_FONT, gridcolor=GRID_COLOR),
                xaxis=dict(title=dict(text="Course Level", font=AXIS_TITLE_FONT), tickfont=dict(color='#e2e8f0', size=13), automargin=True),
                height=420, margin=dict(t=10, b=20, l=20, r=20), paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG)
            st.plotly_chart(fl, use_container_width=True, config=PLOTLY_CONFIG)
            
            lds = ldf.sort_values('Avg Completion %'); wl = lds.iloc[0]; bl = lds.iloc[-1]
            st.markdown(f'<div class="insight-card" style="max-width: 100%;"><strong>📊 Level Highlights:</strong> <strong>{bl["Course Level"]}</strong> is the most complete at {bl["Avg Completion %"]:.1f}%, while <strong>{wl["Course Level"]}</strong> is trailing at {wl["Avg Completion %"]:.1f}%.</div>', unsafe_allow_html=True)
            
        with rc:
            st.markdown("#### Pending Items by Course Level")
            st.markdown("*Hover over segments for exact values*")
            lp = df.groupby('Course Level').agg({'Videos Pending': 'sum', 'Podcasts Pending': 'sum', 'Guides Pending': 'sum'}).reset_index()
            lp['Order'] = lp['Course Level'].apply(lambda x: lo.index(x) if x in lo else 99)
            lp = lp.sort_values('Order')
            lp['Total'] = lp['Videos Pending'] + lp['Podcasts Pending'] + lp['Guides Pending']
            
            # Smart text: only show numbers in segments tall enough to read
            lp_max = lp['Total'].max() if len(lp) > 0 else 1
            lp_thresh = lp_max * 0.07
            
            lpf = go.Figure()
            lpf.add_trace(go.Bar(x=lp['Course Level'], y=lp['Videos Pending'], name='AI Videos', marker_color='#f59e0b',
                text=[str(int(v)) if v >= lp_thresh else '' for v in lp['Videos Pending']],
                textposition='inside', textfont=dict(color='white', size=13, family='Arial Black'), insidetextanchor='middle',
                hovertemplate='<b>%{x}</b><br>AI Videos Pending: %{y}<extra></extra>'))
            lpf.add_trace(go.Bar(x=lp['Course Level'], y=lp['Podcasts Pending'], name='Podcasts', marker_color='#0ea5e9',
                text=[str(int(v)) if v >= lp_thresh else '' for v in lp['Podcasts Pending']],
                textposition='inside', textfont=dict(color='white', size=13, family='Arial Black'), insidetextanchor='middle',
                hovertemplate='<b>%{x}</b><br>Podcasts Pending: %{y}<extra></extra>'))
            lpf.add_trace(go.Bar(x=lp['Course Level'], y=lp['Guides Pending'], name='Study Guides', marker_color='#10b981',
                text=[str(int(v)) if v >= lp_thresh else '' for v in lp['Guides Pending']],
                textposition='inside', textfont=dict(color='white', size=13, family='Arial Black'), insidetextanchor='middle',
                hovertemplate='<b>%{x}</b><br>Study Guides Pending: %{y}<extra></extra>'))
            
            # Total annotations above each stacked bar
            for _, row in lp.iterrows():
                lpf.add_annotation(x=row['Course Level'], y=row['Total'],
                    text=str(int(row['Total'])), showarrow=False, yanchor='bottom', yshift=5,
                    font=dict(color='white', size=13, family='Arial Black'))
            
            lpf.update_traces(cliponaxis=False)
            lpf.update_layout(barmode='stack',
                yaxis=dict(title=dict(text="Pending Items", font=AXIS_TITLE_FONT), tickfont=AXIS_TICK_FONT, gridcolor=GRID_COLOR,
                    range=[0, lp['Total'].max() * 1.15]),
                xaxis=dict(tickfont=dict(color='#e2e8f0', size=12), automargin=True), height=420, margin=dict(t=30, b=20, l=20, r=20),
                paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG, legend=dict(orientation="h", yanchor="bottom", y=1.02, font=LEGEND_FONT, bgcolor=CHART_BG))
            st.plotly_chart(lpf, use_container_width=True, config=PLOTLY_CONFIG)
            
            heaviest_lvl = lp.sort_values('Total', ascending=False).iloc[0]
            st.markdown(f'<div class="warning-card" style="max-width: 100%;"><strong>📦 Largest Backlog:</strong> <strong>{heaviest_lvl["Course Level"]}</strong> holds the largest volume of incomplete work ({int(heaviest_lvl["Total"])} items).</div>', unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Course Level Details")
        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(ldf[['Course Level', 'Number of Courses', 'Total Units', 'Content Completed', 'Avg Completion %']],
            column_config={"Avg Completion %": st.column_config.ProgressColumn("Avg Progress", format="%.1f%%", min_value=0, max_value=100)}, hide_index=True, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════
#  TAB 4 — QUICK WINS
# ═══════════════════════════════════════════════════════════════════
with tab_quickwins:
    st.markdown("## Quick Wins: Courses Close to Completion")
    st.markdown("*Low effort, high impact — finish these AI Videos, Podcasts, and Study Guides first!*")
    st.markdown("<br>", unsafe_allow_html=True)
    qw = df[(df['Completion %'] >= 75) & (df['Completion %'] < 100)].sort_values('Completion %', ascending=False)
    if not qw.empty:
        total_quick_win_pending = qw['Still Pending'].sum(); qvp = qw['Videos Pending'].sum(); qpp = qw['Podcasts Pending'].sum(); qgp = qw['Guides Pending'].sum()
        q1, q2, q3 = st.columns(3)
        with q1: st.metric("Quick Win Courses", len(qw))
        with q2: st.metric("Total Content Needed", int(total_quick_win_pending))
        with q3: st.metric("Average Completion", f"{qw['Completion %'].mean():.1f}%")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("<br>", unsafe_allow_html=True)
        
        lc, rc = st.columns(2)
        with lc:
            st.markdown("#### What Each Quick Win Course Still Needs")
            st.markdown("*Short bars = easiest to finish first. Hover for details.*")
            qd = qw.head(12).sort_values('Still Pending', ascending=True).copy()
            qd['Wrapped Name'] = qd['Course Name'].apply(lambda x: '<br>'.join(textwrap.wrap(str(x), width=40)))
            
            # Smart text threshold
            qd_max = qd['Still Pending'].max() if len(qd) > 0 else 1
            qd_thresh = max(qd_max * 0.10, 1.5)
            
            qb = go.Figure()
            qb.add_trace(go.Bar(y=qd['Wrapped Name'], x=qd['Videos Pending'], name='AI Videos Needed', marker_color='#f59e0b', orientation='h',
                text=[str(int(v)) if v >= qd_thresh else '' for v in qd['Videos Pending']],
                textposition='inside', textfont=dict(color='white', size=12, family='Arial Black'), insidetextanchor='middle',
                hovertemplate='AI Videos Needed: %{x}<extra></extra>'))
            qb.add_trace(go.Bar(y=qd['Wrapped Name'], x=qd['Podcasts Pending'], name='Podcasts Needed', marker_color='#0ea5e9', orientation='h',
                text=[str(int(v)) if v >= qd_thresh else '' for v in qd['Podcasts Pending']],
                textposition='inside', textfont=dict(color='white', size=12, family='Arial Black'), insidetextanchor='middle',
                hovertemplate='Podcasts Needed: %{x}<extra></extra>'))
            qb.add_trace(go.Bar(y=qd['Wrapped Name'], x=qd['Guides Pending'], name='Study Guides Needed', marker_color='#10b981', orientation='h',
                text=[str(int(v)) if v >= qd_thresh else '' for v in qd['Guides Pending']],
                textposition='inside', textfont=dict(color='white', size=12, family='Arial Black'), insidetextanchor='middle',
                hovertemplate='Study Guides Needed: %{x}<extra></extra>'))
            
            # Total annotations
            for _, row in qd.iterrows():
                qb.add_annotation(x=row['Still Pending'], y=row['Wrapped Name'],
                    text=f"  {int(row['Still Pending'])}", showarrow=False, xanchor='left',
                    font=dict(color='#94a3b8', size=11))
            
            qb.update_traces(cliponaxis=False)
            qb.update_layout(barmode='stack', bargap=0.25,
                xaxis=dict(title=dict(text="Items Still Needed", font=AXIS_TITLE_FONT), tickfont=AXIS_TICK_FONT, gridcolor=GRID_COLOR, range=[0, qd['Still Pending'].max() * 1.35]),
                yaxis=dict(title="", tickfont=dict(color='#e2e8f0', size=11), automargin=True),
                height=500, margin=dict(t=10, b=20, l=10, r=50),
                paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG, legend=dict(orientation="h", yanchor="bottom", y=1.02, font=LEGEND_FONT, bgcolor=CHART_BG))
            st.plotly_chart(qb, use_container_width=True, config=PLOTLY_CONFIG)
            
            easiest_win = qw[qw['Still Pending'] == qw['Still Pending'].min()].iloc[0]
            st.markdown(f'<div class="insight-card" style="max-width: 100%;"><strong>💡 Easiest Win:</strong> "<strong>{easiest_win["Course Name"]}</strong>" needs only <strong>{int(easiest_win["Still Pending"])} items</strong> to hit 100%.</div>', unsafe_allow_html=True)
            
        with rc:
            st.markdown("#### Current Completion of Quick Win Courses")
            st.markdown("*All 75%+ done — just a final push needed*")
            qc = qw.head(12).sort_values('Completion %', ascending=True).copy()
            qc['Wrapped Name'] = qc['Course Name'].apply(lambda x: '<br>'.join(textwrap.wrap(str(x), width=40)))
            qcf = go.Figure(go.Bar(y=qc['Wrapped Name'], x=qc['Completion %'].round(1), orientation='h', marker=dict(color='#10b981'),
                text=qc['Completion %'].round(1).astype(str)+'%', textposition='outside', textfont=dict(color='white', size=13)))
            qcf.add_vline(x=100, line_dash="dash", line_color="#ffffff", annotation_text="100%", annotation_font=dict(color='white', size=13))
            qcf.update_traces(cliponaxis=False)
            qcf.update_layout(bargap=0.25, xaxis=dict(range=[0, 125], title=dict(text="Completion %", font=AXIS_TITLE_FONT), tickfont=AXIS_TICK_FONT, gridcolor=GRID_COLOR),
                yaxis=dict(title="", tickfont=dict(color='#e2e8f0', size=11), automargin=True),
                height=500, margin=dict(t=10, b=20, l=10, r=60),
                paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG)
            st.plotly_chart(qcf, use_container_width=True, config=PLOTLY_CONFIG)
            
            st.markdown(f'<div class="success-card" style="max-width: 100%;"><strong>🎯 Volume Check:</strong> Completing just <strong>{int(total_quick_win_pending)} remaining items</strong> will add {len(qw)} fully finished courses to the portfolio.</div>', unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Quick Win Courses — Full Details")
        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(qw[['Course Name', 'Subject Area', 'Number of Units', 'Completion %', 'Videos Completed', 'Podcasts Completed', 'Guides Completed', 'Still Pending']].rename(columns={
            'Number of Units': 'Units', 'Videos Completed': 'AI Videos ✓', 'Podcasts Completed': 'Podcasts ✓', 'Guides Completed': 'Study Guides ✓', 'Still Pending': 'To Complete'}),
            column_config={"Completion %": st.column_config.ProgressColumn("Progress", format="%.1f%%", min_value=0, max_value=100)}, hide_index=True, use_container_width=True)
    else:
        st.info("No courses are currently in the 75-99% range.")


# ═══════════════════════════════════════════════════════════════════
#  TAB 5 — PRIORITY WATCH
# ═══════════════════════════════════════════════════════════════════
with tab_priority:
    st.markdown("## Priority Watchlist")
    st.markdown("*Large courses falling behind — need immediate attention for AI Videos, Podcasts, and Study Guides*")
    st.markdown("<br>", unsafe_allow_html=True)
    pc = df[(df['Number of Units'] >= 5) & (df['Completion %'] < 50)].sort_values('Priority Score', ascending=False)
    ns = df[df['Completion %'] == 0].sort_values('Number of Units', ascending=False)
    pt1, pt2 = st.tabs(["⚠️ High Risk Courses", "🔴 Not Started"])
    with pt1:
        st.markdown("<br>", unsafe_allow_html=True)
        if not pc.empty:
            tpp = pc['Still Pending'].sum(); prv = pc['Videos Pending'].sum(); prp = pc['Podcasts Pending'].sum(); prg = pc['Guides Pending'].sum()
            p1, p2, p3 = st.columns(3)
            with p1: st.metric("High Risk Courses", len(pc))
            with p2: st.metric("Content Pending", int(tpp))
            with p3: st.metric("Avg Completion", f"{pc['Completion %'].mean():.1f}%")
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("---")
            st.markdown("<br>", unsafe_allow_html=True)
            
            top_10_pc = pc.head(10)
            
            lc, rc = st.columns(2)
            with lc:
                st.markdown("#### What Each At-Risk Course Still Needs")
                st.markdown("*Longer bars = more remaining. Hover for details.*")
                pd2 = top_10_pc.sort_values('Still Pending', ascending=True).copy()
                pd2['Wrapped Name'] = pd2['Course Name'].apply(lambda x: '<br>'.join(textwrap.wrap(str(x), width=40)))
                
                # Smart text threshold
                pd2_max = pd2['Still Pending'].max() if len(pd2) > 0 else 1
                pd2_thresh = max(pd2_max * 0.08, 1.5)
                
                pb = go.Figure()
                pb.add_trace(go.Bar(y=pd2['Wrapped Name'], x=pd2['Videos Pending'], name='AI Videos', marker_color='#f59e0b', orientation='h',
                    text=[str(int(v)) if v >= pd2_thresh else '' for v in pd2['Videos Pending']],
                    textposition='inside', textfont=dict(color='white', size=12, family='Arial Black'), insidetextanchor='middle',
                    hovertemplate='AI Videos Pending: %{x}<extra></extra>'))
                pb.add_trace(go.Bar(y=pd2['Wrapped Name'], x=pd2['Podcasts Pending'], name='Podcasts', marker_color='#0ea5e9', orientation='h',
                    text=[str(int(v)) if v >= pd2_thresh else '' for v in pd2['Podcasts Pending']],
                    textposition='inside', textfont=dict(color='white', size=12, family='Arial Black'), insidetextanchor='middle',
                    hovertemplate='Podcasts Pending: %{x}<extra></extra>'))
                pb.add_trace(go.Bar(y=pd2['Wrapped Name'], x=pd2['Guides Pending'], name='Study Guides', marker_color='#10b981', orientation='h',
                    text=[str(int(v)) if v >= pd2_thresh else '' for v in pd2['Guides Pending']],
                    textposition='inside', textfont=dict(color='white', size=12, family='Arial Black'), insidetextanchor='middle',
                    hovertemplate='Study Guides Pending: %{x}<extra></extra>'))
                
                # Total annotations
                for _, row in pd2.iterrows():
                    pb.add_annotation(x=row['Still Pending'], y=row['Wrapped Name'],
                        text=f"  {int(row['Still Pending'])}", showarrow=False, xanchor='left',
                        font=dict(color='#94a3b8', size=11))
                
                pb.update_traces(cliponaxis=False)
                pb.update_layout(barmode='stack', bargap=0.25,
                    xaxis=dict(title=dict(text="Items Needed", font=AXIS_TITLE_FONT), tickfont=AXIS_TICK_FONT, gridcolor=GRID_COLOR, range=[0, pd2['Still Pending'].max() * 1.3]),
                    yaxis=dict(title="", tickfont=dict(color='#e2e8f0', size=11), automargin=True),
                    height=500, margin=dict(t=10, b=20, l=10, r=50),
                    paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG, legend=dict(orientation="h", yanchor="bottom", y=1.02, font=LEGEND_FONT, bgcolor=CHART_BG))
                st.plotly_chart(pb, use_container_width=True, config=PLOTLY_CONFIG)
                
                highest_risk = pc.iloc[0]
                st.markdown(f'<div class="danger-card" style="max-width: 100%;"><strong>⚡ Highest Risk:</strong> "<strong>{highest_risk["Course Name"]}</strong>" needs <strong>{int(highest_risk["Still Pending"])} items</strong>.</div>', unsafe_allow_html=True)
                
            with rc:
                st.markdown("#### How Far Behind Are These Top 10 Courses?")
                st.markdown("*All below 50% — far from the finish line*")
                pc2 = top_10_pc.sort_values('Completion %', ascending=True).copy()
                pc2['Wrapped Name'] = pc2['Course Name'].apply(lambda x: '<br>'.join(textwrap.wrap(str(x), width=40)))
                pcf = go.Figure(go.Bar(y=pc2['Wrapped Name'], x=pc2['Completion %'].round(1), orientation='h', marker=dict(color='#ef4444'),
                    text=pc2.apply(lambda r: f"{r['Completion %']:.0f}% ({int(r['Number of Units'])} units)", axis=1), textposition='outside', textfont=dict(color='white', size=12)))
                pcf.add_vline(x=50, line_dash="dash", line_color="#f59e0b", annotation_text="50%", annotation_font=dict(color='white', size=13))
                pcf.update_traces(cliponaxis=False)
                pcf.update_layout(bargap=0.25, xaxis=dict(range=[0, 125], title=dict(text="Completion %", font=AXIS_TITLE_FONT), tickfont=AXIS_TICK_FONT, gridcolor=GRID_COLOR),
                    yaxis=dict(title="", tickfont=dict(color='#e2e8f0', size=11), automargin=True),
                    height=500, margin=dict(t=10, b=20, l=10, r=120),
                    paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG)
                st.plotly_chart(pcf, use_container_width=True, config=PLOTLY_CONFIG)
                
                st.markdown(f'<div class="warning-card" style="max-width: 100%;"><strong>🚨 Overdue Burden:</strong> These {len(pc)} courses represent <strong>{int(tpp)} pending content pieces</strong> and pose a high risk to delivery timelines.</div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### High Risk Courses — Full Details")
            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(pc[['Course Name', 'Course Level', 'Subject Area', 'Number of Units', 'Completion %', 'Still Pending']].rename(columns={
                'Number of Units': 'Units', 'Still Pending': 'AI Videos + Podcasts + Guides Pending'}),
                column_config={"Completion %": st.column_config.ProgressColumn("Progress", format="%.1f%%", min_value=0, max_value=100)}, hide_index=True, use_container_width=True)
        else:
            st.success("✅ No large courses are critically behind!")

    with pt2:
        st.markdown("<br>", unsafe_allow_html=True)
        if not ns.empty:
            tnw = ns['Total Required'].sum(); nsu = ns['Number of Units'].sum()
            n1, n2, n3 = st.columns(3)
            with n1: st.metric("Courses Not Started", len(ns))
            with n2: st.metric("Total Content Needed", int(tnw))
            with n3: st.metric("Avg Course Size", f"{ns['Number of Units'].mean():.1f} units")
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("---")
            st.markdown("<br>", unsafe_allow_html=True)
            
            lc, rc = st.columns(2)
            with lc:
                st.markdown("#### Unstarted Courses by Subject Area")
                st.markdown("*Which departments have the most courses waiting?*")
                nbs = ns.groupby('Subject Area').agg(Courses=('Course Name', 'count'), Needed=('Total Required', 'sum')).sort_values('Needed', ascending=True).reset_index()
                nsf = go.Figure(go.Bar(y=nbs['Subject Area'], x=nbs['Needed'], orientation='h', marker=dict(color='#ef4444'),
                    text=nbs.apply(lambda r: f"{int(r['Needed'])} items ({int(r['Courses'])} courses)", axis=1), textposition='outside', textfont=dict(color='white', size=13)))
                nsf.update_traces(cliponaxis=False)
                nsf.update_layout(xaxis=dict(title=dict(text="Items Needed", font=AXIS_TITLE_FONT), tickfont=AXIS_TICK_FONT, gridcolor=GRID_COLOR, range=[0, nbs['Needed'].max()*1.5]),
                    yaxis=dict(title="", tickfont=dict(color='#e2e8f0', size=12), automargin=True), height=450, margin=dict(t=10, b=20, l=10, r=160), paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG)
                st.plotly_chart(nsf, use_container_width=True, config=PLOTLY_CONFIG)
                
                top_unstarted_sub = nbs.iloc[-1]
                st.markdown(f'<div class="warning-card" style="max-width: 100%;"><strong>📋 Focus Area:</strong> <strong>{top_unstarted_sub["Subject Area"]}</strong> has {int(top_unstarted_sub["Courses"])} unstarted courses requiring {int(top_unstarted_sub["Needed"])} items.</div>', unsafe_allow_html=True)
                
            with rc:
                st.markdown("#### Unstarted Courses by Size")
                st.markdown("*Start with smallest for quick momentum*")
                sol = ['Small (1-3 units)', 'Medium (4-7 units)', 'Large (8-12 units)', 'Very Large (13+ units)']
                nbz = ns.groupby('Course Size').agg(Courses=('Course Name', 'count'), Needed=('Total Required', 'sum')).reset_index()
                nbz['Order'] = nbz['Course Size'].apply(lambda x: sol.index(x) if x in sol else 99)
                nbz = nbz.sort_values('Order')
                
                # Redesigned: clean horizontal bar chart — content needed per size,
                # with course count shown as annotation (no confusing dual axis)
                nzf = go.Figure()
                nzf.add_trace(go.Bar(
                    y=nbz['Course Size'], x=nbz['Needed'], orientation='h',
                    marker_color='#f59e0b',
                    text=nbz['Needed'].apply(lambda v: f"{int(v)} items"),
                    textposition='inside', textfont=dict(color='white', size=14, family='Arial Black'),
                    insidetextanchor='middle',
                    hovertemplate='<b>%{y}</b><br>Content Needed: %{x}<extra></extra>'
                ))
                
                # Course count annotations at end of each bar
                for _, row in nbz.iterrows():
                    nzf.add_annotation(
                        x=row['Needed'], y=row['Course Size'],
                        text=f"  {int(row['Courses'])} courses",
                        showarrow=False, xanchor='left',
                        font=dict(color='#94a3b8', size=12)
                    )
                
                nzf.update_traces(cliponaxis=False)
                nzf.update_layout(
                    xaxis=dict(title=dict(text="Content Items Needed", font=AXIS_TITLE_FONT), tickfont=AXIS_TICK_FONT, gridcolor=GRID_COLOR,
                        range=[0, nbz['Needed'].max() * 1.35]),
                    yaxis=dict(title="", tickfont=dict(color='#e2e8f0', size=12), automargin=True, categoryorder='array', categoryarray=list(nbz['Course Size'])),
                    height=350, margin=dict(t=10, b=20, l=10, r=100),
                    paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG, showlegend=False
                )
                st.plotly_chart(nzf, use_container_width=True, config=PLOTLY_CONFIG)
                
                smallest_not_started = ns.nsmallest(3, 'Number of Units')
                st.markdown(f'<div class="insight-card" style="max-width: 100%;"><strong>🚀 Quick Start:</strong> The 3 smallest unstarted courses need only <strong>{int(smallest_not_started["Total Required"].sum())} items</strong> total. Start there.</div>', unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(ns[['Course Name', 'Subject Area', 'Number of Units', 'Total Required']].rename(columns={
                'Number of Units': 'Units', 'Total Required': 'AI Videos + Podcasts + Guides Needed'}), hide_index=True, use_container_width=True)
        else:
            st.success("✅ All courses have started!")


# ═══════════════════════════════════════════════════════════════════
#  TAB 6 — DAILY CHAPTER-WISE AI VIDEO PROGRESS  (NEW)
# ═══════════════════════════════════════════════════════════════════
with tab_aivideos:
    st.markdown("## 🎬 Daily Chapter-wise AI Video Progress")
    st.markdown(f"*Each person must deliver **{DAILY_TARGET} AI videos per day**. Combined team target: **{TEAM_DAILY_TARGET} videos per day** (4 members × {DAILY_TARGET}).*")
    st.markdown("<br>", unsafe_allow_html=True)

    # Attempt to load from uploaded file if SharePoint load failed
    _vdf = vdf
    if _vdf is None or (isinstance(_vdf, pd.DataFrame) and _vdf.empty):
        st.info("👇 Upload the tracker file to view the Chapter-wise AI Video Progress data.")
        vid_upload = st.file_uploader("Upload 'Additional Material Tracker Sheet.xlsx' (for AI Video tab)", type=['xlsx'], key='vid_upload')
        if vid_upload is not None:
            _vdf = load_chapter_video_data(vid_upload.read())

    if _vdf is not None and isinstance(_vdf, pd.DataFrame) and not _vdf.empty:
        persons = list(_vdf['Person'].unique())
        all_dates = sorted(_vdf['Date'].unique())
        total_days = len(all_dates)

        # Check if there is any actual numeric data
        has_data = _vdf['Videos'].sum() > 0

        # If no data, offer a quick upload to override with a fresh file
        if not has_data:
            st.markdown('<div class="warning-card"><strong>📋 Tracker Ready — No Data Entered Yet</strong><br><br>'
                        f'The schedule is set up for <strong>{len(persons)} team members</strong> across '
                        f'<strong>{total_days} working days</strong>. Once daily video counts are entered in the Excel sheet, '
                        'all charts and analytics will populate automatically.<br><br>'
                        '<strong>Already added values?</strong> Click the <strong>🔄 Refresh Data</strong> button at the top to pull the latest version from SharePoint. '
                        'Data is cached for 5 minutes to keep the dashboard fast.</div>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            with st.expander("🔍 Data Diagnostic — What the dashboard received"):
                st.write(f"**Rows parsed:** {len(_vdf)}")
                st.write(f"**Unique dates found:** {total_days}")
                st.write(f"**Team members detected:** {', '.join(persons)}")
                st.write(f"**Sum of all video values:** {_vdf['Videos'].sum()}")
                st.write(f"**Non-zero video entries:** {(_vdf['Videos'] > 0).sum()} of {len(_vdf)}")
                st.write(f"**Notes/text entries found:** {(_vdf['Note'] != '').sum()}")
                st.write(f"**Data source:** {'SharePoint (live)' if file_bytes is not None else 'Uploaded file'}")
                st.markdown("If the sum is 0 but you've entered values in the SharePoint sheet, click **🔄 Refresh Data** above. "
                            "If that doesn't work, download the file from SharePoint and upload it below.")

            st.markdown("<br>", unsafe_allow_html=True)
            quick_upload = st.file_uploader("📂 Upload updated tracker here to see the latest data", type=['xlsx'], key='vid_quick_upload')
            if quick_upload is not None:
                _vdf_override = load_chapter_video_data(quick_upload.read())
                if _vdf_override is not None and not _vdf_override.empty:
                    _vdf = _vdf_override
                    persons = list(_vdf['Person'].unique())
                    all_dates = sorted(_vdf['Date'].unique())
                    total_days = len(all_dates)
                    has_data = _vdf['Videos'].sum() > 0

        if not has_data:
            st.markdown("### 📅 Scheduled Working Days")
            st.markdown("<br>", unsafe_allow_html=True)
            m1, m2, m3, m4, m5 = st.columns(5)
            with m1: st.metric("Team Members", len(persons))
            with m2: st.metric("Scheduled Days So Far", total_days)
            with m3: st.metric("Target per Person/Day", f"{DAILY_TARGET} videos")
            with m4: st.metric("Combined Team Target/Day", f"{TEAM_DAILY_TARGET} videos")
            with m5: st.metric("Expected So Far", f"{TEAM_DAILY_TARGET * total_days:,} videos")
            st.markdown("<br>", unsafe_allow_html=True)
            sched = _vdf[['Date', 'Date Label', 'Day', 'Week', 'Person']].drop_duplicates(subset=['Date']).sort_values('Date')
            sched_display = sched[['Date Label', 'Day', 'Week']].rename(columns={'Date Label': 'Date', 'Day': 'Weekday'})
            st.dataframe(sched_display, hide_index=True, use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 👥 Team Members")
            st.markdown("<br>", unsafe_allow_html=True)
            pcols = st.columns(len(persons))
            for i, person in enumerate(persons):
                with pcols[i]:
                    color = list(PERSON_COLORS.values())[i % len(PERSON_COLORS)]
                    st.markdown(f'<div style="background:rgba(30,41,59,0.7);border-radius:10px;padding:20px;'
                                f'border-left:4px solid {color};border:1px solid rgba(255,255,255,0.1);">'
                                f'<span style="color:{color};font-weight:700;font-size:16px;">{person}</span><br>'
                                f'<span style="color:#94a3b8;font-size:13px;">Daily target: {DAILY_TARGET} videos</span></div>',
                                unsafe_allow_html=True)
            notes_df = _vdf[_vdf['Note'] != ''][['Date Label', 'Person', 'Note']].drop_duplicates()
            if not notes_df.empty:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("### 📝 Notes & Remarks")
                st.dataframe(notes_df.rename(columns={'Date Label': 'Date'}), hide_index=True, use_container_width=True)

        else:
            # ═══════════════════════════════════════════════════════
            #  DATA EXISTS — REDESIGNED ANALYTICS
            # ═══════════════════════════════════════════════════════

            # ── Filter to only days/rows with actual activity ──
            active_vdf = _vdf[_vdf.groupby('Date')['Videos'].transform('sum') > 0].copy()
            active_dates = sorted(active_vdf['Date'].unique())
            num_active_days = len(active_dates)

            # ── Build short readable date labels (e.g. "25 Mar (Tue)") ──
            active_vdf['Short Date'] = active_vdf['Date'].dt.strftime('%d %b') + ' (' + active_vdf['Day'] + ')'
            date_label_order = active_vdf.drop_duplicates('Date').sort_values('Date')['Short Date'].tolist()

            # ── Precompute daily team totals (ONLY active days) ──
            daily_team = active_vdf.groupby(['Date', 'Short Date', 'Date Label', 'Day', 'Week']).agg(
                Total=('Videos', 'sum')
            ).reset_index().sort_values('Date')
            daily_team['Team Met'] = daily_team['Total'] >= TEAM_DAILY_TARGET
            daily_team['Team Shortfall'] = np.where(daily_team['Total'] < TEAM_DAILY_TARGET, TEAM_DAILY_TARGET - daily_team['Total'], 0)
            daily_team['Team Surplus'] = np.where(daily_team['Total'] >= TEAM_DAILY_TARGET, daily_team['Total'] - TEAM_DAILY_TARGET, 0)

            # ── Grand totals ──
            grand_total = _vdf['Videos'].sum()
            team_met_days = daily_team['Team Met'].sum()
            team_hit_pct = (team_met_days / num_active_days * 100) if num_active_days > 0 else 0

            # Per-person totals for metrics row
            person_video_totals = active_vdf.groupby('Person')['Videos'].sum().to_dict()

            # ═══════════════════════════════════════════════════
            #  KEY METRICS
            # ═══════════════════════════════════════════════════
            st.markdown("### Key Metrics")
            st.markdown("<br>", unsafe_allow_html=True)
            total_expected_so_far = TEAM_DAILY_TARGET * num_active_days
            m1, m2, m3 = st.columns(3)
            with m1: st.metric("Total Videos Produced", f"{int(grand_total):,}")
            with m2: st.metric("Total Videos Expected So Far", f"{int(total_expected_so_far):,}")
            with m3: st.metric("Active Working Days", f"{num_active_days}")
            st.markdown("<br>", unsafe_allow_html=True)
            pcols = st.columns(len(persons))
            for i, person in enumerate(persons):
                with pcols[i]:
                    color = PERSON_COLORS.get(person, '#0ea5e9')
                    pv = int(person_video_totals.get(person, 0))
                    st.markdown(
                        f'<div style="background:rgba(30,41,59,0.7);border-radius:10px;padding:18px 20px;'
                        f'border:1px solid rgba(255,255,255,0.1);border-left:4px solid {color};'
                        f'box-shadow:0 4px 15px rgba(0,0,0,0.2);">'
                        f'<div style="color:#94a3b8;font-size:12px;font-weight:500;text-transform:uppercase;letter-spacing:0.5px;">{person}</div>'
                        f'<div style="color:{color};font-size:28px;font-weight:700;margin-top:4px;">{pv} videos</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("---")
            st.markdown("<br>", unsafe_allow_html=True)

            # ═══════════════════════════════════════════════════
            #  SECTION A — COMBINED TEAM (200/day)
            # ═══════════════════════════════════════════════════
            st.markdown(f"### 📊 Combined Team Daily Target — {TEAM_DAILY_TARGET} Videos per Day")
            st.markdown(f"*All 4 members combined must produce **{TEAM_DAILY_TARGET} videos every working day**. Green bars hit the target, red bars fall short.*")
            st.markdown("<br>", unsafe_allow_html=True)

            t1, t2, t3, t4 = st.columns(4)
            with t1: st.metric("Daily Team Target", f"{TEAM_DAILY_TARGET} videos")
            with t2: st.metric("Days Target Achieved", f"{int(team_met_days)} of {num_active_days}")
            with t3: st.metric("Average Daily Output", f"{daily_team['Total'].mean():.0f}" if num_active_days > 0 else "—")
            with t4: st.metric("Cumulative Shortfall", f"{int(daily_team['Team Shortfall'].sum())}")
            st.markdown("<br>", unsafe_allow_html=True)

            # ── Team daily bar chart — categorical x-axis ──
            bar_colors = ['#10b981' if v >= TEAM_DAILY_TARGET else '#ef4444' for v in daily_team['Total']]
            team_bar = go.Figure()
            team_bar.add_hline(y=TEAM_DAILY_TARGET, line_dash="dash", line_color="rgba(255,255,255,0.5)",
                annotation_text=f"Target: {TEAM_DAILY_TARGET}", annotation_position="top right",
                annotation_font=dict(color='#94a3b8', size=12))
            team_bar.add_trace(go.Bar(
                x=daily_team['Short Date'], y=daily_team['Total'],
                marker_color=bar_colors,
                text=daily_team['Total'].apply(lambda v: str(int(v))),
                textposition='outside', textfont=dict(color='white', size=14, family='Arial Black'),
                hovertemplate=daily_team.apply(
                    lambda r: (
                        f"<b>{r['Date Label']} ({r['Day']})</b><br>"
                        f"Team total: {int(r['Total'])} videos<br>"
                        f"Target: {TEAM_DAILY_TARGET}<br>"
                        + (f"Above target by: {int(r['Team Surplus'])}" if r['Team Surplus'] > 0 else
                           f"Below target by: {int(r['Team Shortfall'])}" if r['Team Shortfall'] > 0 else
                           "Exactly on target")
                        + "<extra></extra>"
                    ), axis=1
                ),
                showlegend=False
            ))
            team_bar.update_traces(cliponaxis=False)
            team_bar.update_layout(
                xaxis=dict(title="", tickfont=dict(color='#e2e8f0', size=12), categoryorder='array', categoryarray=date_label_order, tickangle=-30),
                yaxis=dict(title=dict(text="Team Total Videos", font=AXIS_TITLE_FONT), tickfont=AXIS_TICK_FONT,
                           gridcolor=GRID_COLOR, rangemode='tozero',
                           range=[0, max(daily_team['Total'].max(), TEAM_DAILY_TARGET) * 1.3]),
                height=420, margin=dict(t=20, b=80, l=60, r=30),
                paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG
            )
            st.plotly_chart(team_bar, use_container_width=True, config=PLOTLY_CONFIG)

            if team_hit_pct >= 80:
                st.markdown(f'<div class="success-card"><strong>✅ Excellent Team Output:</strong> The team hit the <strong>{TEAM_DAILY_TARGET}-video daily target</strong> on <strong>{int(team_met_days)} of {num_active_days}</strong> active days ({team_hit_pct:.0f}% hit rate). Total produced: <strong>{int(grand_total):,}</strong>.</div>', unsafe_allow_html=True)
            elif team_hit_pct >= 50:
                st.markdown(f'<div class="warning-card"><strong>⚡ Team Needs Improvement:</strong> The {TEAM_DAILY_TARGET}-video target was met on only <strong>{int(team_met_days)} of {num_active_days}</strong> days ({team_hit_pct:.0f}%). Cumulative shortfall: <strong>{int(daily_team["Team Shortfall"].sum())} videos</strong>.</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="danger-card"><strong>⚠️ Critical Team Shortfall:</strong> The {TEAM_DAILY_TARGET}-video target was met on only <strong>{int(team_met_days)} of {num_active_days}</strong> days ({team_hit_pct:.0f}%). Total shortfall: <strong>{int(daily_team["Team Shortfall"].sum())} videos</strong> behind schedule.</div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Who contributed what each day — grouped bar ──
            st.markdown("#### Daily Contribution Breakdown by Person")
            st.markdown(f"*How each team member contributed to the daily {TEAM_DAILY_TARGET}-video target*")
            st.markdown("<br>", unsafe_allow_html=True)

            stacked_fig = go.Figure()
            for person in persons:
                pdata = active_vdf[active_vdf['Person'] == person].sort_values('Date')
                color = PERSON_COLORS.get(person, '#0ea5e9')
                stacked_fig.add_trace(go.Bar(
                    x=pdata['Short Date'], y=pdata['Videos'], name=person, marker_color=color,
                    text=pdata['Videos'].apply(lambda v: str(int(v)) if v > 0 else ''),
                    textposition='inside', textfont=dict(color='white', size=12, family='Arial Black'),
                    hovertemplate=(
                        f"<b>{person}</b><br>"
                        "Date: %{x}<br>"
                        f"Videos: %{{y}}<br>"
                        f"Individual target: {DAILY_TARGET}"
                        "<extra></extra>"
                    )
                ))
            stacked_fig.add_hline(y=TEAM_DAILY_TARGET, line_dash="dash", line_color="rgba(255,255,255,0.5)",
                annotation_text=f"Team Target: {TEAM_DAILY_TARGET}", annotation_position="top right",
                annotation_font=dict(color='#94a3b8', size=12))
            stacked_fig.update_traces(cliponaxis=False)
            stacked_fig.update_layout(
                barmode='stack',
                xaxis=dict(title="", tickfont=dict(color='#e2e8f0', size=12), categoryorder='array', categoryarray=date_label_order, tickangle=-30),
                yaxis=dict(title=dict(text="Videos", font=AXIS_TITLE_FONT), tickfont=AXIS_TICK_FONT,
                           gridcolor=GRID_COLOR, rangemode='tozero',
                           range=[0, max(daily_team['Total'].max(), TEAM_DAILY_TARGET) * 1.25]),
                height=450, margin=dict(t=20, b=80, l=60, r=30),
                paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, font=LEGEND_FONT, bgcolor=CHART_BG)
            )
            st.plotly_chart(stacked_fig, use_container_width=True, config=PLOTLY_CONFIG)

            # ── Cumulative progress — categorical x-axis ──
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### Cumulative Team Progress vs Expected")
            st.markdown(f"*Running total of videos produced compared to the expected pace ({TEAM_DAILY_TARGET} per day)*")
            st.markdown("<br>", unsafe_allow_html=True)

            cum = daily_team.sort_values('Date').copy()
            cum['Cumulative Actual'] = cum['Total'].cumsum()
            cum['Day Number'] = range(1, len(cum) + 1)
            cum['Cumulative Expected'] = cum['Day Number'] * TEAM_DAILY_TARGET

            cum_fig = go.Figure()
            cum_fig.add_trace(go.Scatter(
                x=cum['Short Date'], y=cum['Cumulative Expected'], mode='lines+markers',
                line=dict(color='rgba(255,255,255,0.5)', width=2, dash='dash'),
                marker=dict(size=6, color='rgba(255,255,255,0.5)'),
                name=f'Expected Pace ({TEAM_DAILY_TARGET}/day)',
                hovertemplate=cum.apply(lambda r: f"<b>Expected</b><br>{r['Date Label']}<br>Cumulative: {int(r['Cumulative Expected'])}<extra></extra>", axis=1)
            ))
            cum_fig.add_trace(go.Scatter(
                x=cum['Short Date'], y=cum['Cumulative Actual'], mode='lines+markers',
                line=dict(color='#0ea5e9', width=3),
                marker=dict(size=9, color='#0ea5e9', line=dict(width=2, color='white')),
                name='Actual Production',
                fill='tonexty', fillcolor='rgba(14,165,233,0.1)',
                hovertemplate=cum.apply(
                    lambda r: (
                        f"<b>{r['Date Label']} ({r['Day']})</b><br>"
                        f"Actual cumulative: {int(r['Cumulative Actual'])}<br>"
                        f"Expected cumulative: {int(r['Cumulative Expected'])}<br>"
                        + (f"Ahead by: {int(r['Cumulative Actual'] - r['Cumulative Expected'])}" if r['Cumulative Actual'] >= r['Cumulative Expected'] else
                           f"Behind by: {int(r['Cumulative Expected'] - r['Cumulative Actual'])}")
                        + "<extra></extra>"
                    ), axis=1
                )
            ))
            cum_fig.update_layout(
                xaxis=dict(title="", tickfont=dict(color='#e2e8f0', size=11), categoryorder='array', categoryarray=date_label_order, tickangle=-30),
                yaxis=dict(title=dict(text="Cumulative Videos", font=AXIS_TITLE_FONT), tickfont=AXIS_TICK_FONT,
                           gridcolor=GRID_COLOR, rangemode='tozero'),
                height=400, margin=dict(t=20, b=80, l=60, r=30),
                paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, font=LEGEND_FONT, bgcolor=CHART_BG)
            )
            st.plotly_chart(cum_fig, use_container_width=True, config=PLOTLY_CONFIG)

            cum_gap = int(cum.iloc[-1]['Cumulative Expected'] - cum.iloc[-1]['Cumulative Actual'])
            if cum_gap > 0:
                st.markdown(f'<div class="danger-card"><strong>📉 Behind Schedule:</strong> The team is <strong>{cum_gap} videos behind</strong> the expected cumulative pace across {len(cum)} active days so far.</div>', unsafe_allow_html=True)
            elif cum_gap < 0:
                st.markdown(f'<div class="success-card"><strong>📈 Ahead of Schedule:</strong> The team is <strong>{abs(cum_gap)} videos ahead</strong> of the expected pace across {len(cum)} active days so far.</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="insight-card"><strong>📊 Exactly On Track:</strong> The team is perfectly aligned with the expected cumulative pace.</div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("---")
            st.markdown("<br>", unsafe_allow_html=True)

            # ═══════════════════════════════════════════════════
            #  SECTION B — INDIVIDUAL PERFORMANCE (50/day each)
            # ═══════════════════════════════════════════════════
            st.markdown(f"### 👤 Individual Daily Performance — {DAILY_TARGET} Videos per Person per Day")
            st.markdown(f"*Each of the 4 team members is responsible for **{DAILY_TARGET} AI videos every working day**. The dashed line marks this individual target.*")
            st.markdown("<br>", unsafe_allow_html=True)

            # ── Two persons per row for better side-by-side comparison ──
            for row_start in range(0, len(persons), 2):
                row_persons = persons[row_start:row_start+2]
                cols = st.columns(len(row_persons))
                for col_idx, person in enumerate(row_persons):
                    with cols[col_idx]:
                        pdf = active_vdf[active_vdf['Person'] == person].sort_values('Date').copy()
                        color = PERSON_COLORS.get(person, '#0ea5e9')

                        person_total = pdf['Videos'].sum()
                        person_avg = pdf['Videos'].mean() if len(pdf) > 0 else 0
                        person_max = pdf['Videos'].max() if len(pdf) > 0 else 0
                        person_data_days = (pdf['Videos'] > 0).sum()
                        person_target_days = (pdf['Videos'] >= DAILY_TARGET).sum()
                        person_expected = DAILY_TARGET * num_active_days
                        person_hit_rate = (person_target_days / person_data_days * 100) if person_data_days > 0 else 0
                        person_shortfall = max(0, person_expected - person_total)

                        # ── Bar chart per person — clear, readable ──
                        bar_clrs = [color if v >= DAILY_TARGET else '#ef4444' for v in pdf['Videos']]
                        fig = go.Figure()
                        fig.add_hline(y=DAILY_TARGET, line_dash="dash", line_color="rgba(255,255,255,0.35)",
                            annotation_text=f"Target: {DAILY_TARGET}", annotation_position="top right",
                            annotation_font=dict(color='#94a3b8', size=11))
                        fig.add_trace(go.Bar(
                            x=pdf['Short Date'], y=pdf['Videos'],
                            marker_color=bar_clrs,
                            text=pdf['Videos'].apply(lambda v: str(int(v)) if v > 0 else ''),
                            textposition='outside', textfont=dict(color='white', size=13, family='Arial Black'),
                            hovertemplate=pdf.apply(
                                lambda r: (
                                    f"<b>{r['Person']}</b><br>"
                                    f"Date: {r['Date Label']} ({r['Day']})<br>"
                                    f"Videos: {int(r['Videos'])}<br>"
                                    f"Target: {DAILY_TARGET}<br>"
                                    + (f"Above target by: {int(r['Surplus'])}" if r['Surplus'] > 0 else
                                       f"Below target by: {int(r['Shortfall'])}" if r['Shortfall'] > 0 else
                                       "Exactly on target")
                                    + (f"<br>Note: {r['Note']}" if r['Note'] else "")
                                    + "<extra></extra>"
                                ), axis=1
                            ),
                            showlegend=False
                        ))
                        fig.update_traces(cliponaxis=False)
                        fig.update_layout(
                            title=dict(text=f"  {person}", font=dict(color=color, size=16), x=0, xanchor='left'),
                            xaxis=dict(title="", tickfont=dict(color='#e2e8f0', size=10),
                                       categoryorder='array', categoryarray=date_label_order, tickangle=-40),
                            yaxis=dict(title="", tickfont=AXIS_TICK_FONT, gridcolor=GRID_COLOR, rangemode='tozero',
                                       range=[0, max(person_max, DAILY_TARGET) * 1.35] if person_max > 0 else [0, DAILY_TARGET * 1.5]),
                            height=340, margin=dict(t=40, b=70, l=40, r=10),
                            paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG
                        )
                        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

                        # Mini stats
                        s1, s2, s3 = st.columns(3)
                        with s1: st.metric("Total", f"{int(person_total)}")
                        with s2: st.metric("Avg/Day", f"{person_avg:.1f}")
                        with s3: st.metric("Target Achived", f"{person_hit_rate:.0f}%")

                        # Status card
                        if person_hit_rate >= 80:
                            st.markdown(f'<div class="success-card"><strong>✅ On Track</strong> — met {DAILY_TARGET}/day target on <strong>{person_target_days} of {person_data_days}</strong> days. Total: <strong>{int(person_total)}</strong> of {person_expected} expected.</div>', unsafe_allow_html=True)
                        elif person_hit_rate >= 50:
                            st.markdown(f'<div class="warning-card"><strong>⚡ Needs Push</strong> — met target on <strong>{person_target_days} of {person_data_days}</strong> days. <strong>{int(person_shortfall)}</strong> videos behind pace.</div>', unsafe_allow_html=True)
                        elif person_data_days > 0:
                            st.markdown(f'<div class="danger-card"><strong>⚠️ Below Target</strong> — hit rate only <strong>{person_hit_rate:.0f}%</strong>. Behind by <strong>{int(person_shortfall)}</strong> videos.</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="danger-card"><strong>⚠️ No Activity</strong> — no videos recorded yet. Expected: <strong>{person_expected}</strong>.</div>', unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("<br>", unsafe_allow_html=True)

            # ═══════════════════════════════════════════════════
            #  SECTION C — WEEKLY & COMPARISON
            # ═══════════════════════════════════════════════════
            st.markdown("### 📅 Weekly Performance Summary")
            st.markdown("*Aggregated weekly view — compare performance across weeks*")
            st.markdown("<br>", unsafe_allow_html=True)

            weekly = active_vdf.groupby(['Week', 'Person']).agg(
                Total=('Videos', 'sum'),
                Days=('Date', 'nunique'),
                Target_Met=('Met Target', 'sum')
            ).reset_index()
            weekly['Avg/Day'] = (weekly['Total'] / weekly['Days']).round(1)

            wlc, wrc = st.columns(2)
            with wlc:
                st.markdown("#### Weekly Total by Person")
                st.markdown(f"*Dashed line shows team target ({TEAM_DAILY_TARGET} × days in week)*")
                wk_order = sorted(weekly['Week'].unique())
                wkf = go.Figure()
                for person in persons:
                    pw = weekly[weekly['Person'] == person].copy()
                    pw = pw.set_index('Week').reindex(wk_order).fillna(0).reset_index()
                    color = PERSON_COLORS.get(person, '#0ea5e9')
                    wkf.add_trace(go.Bar(
                        x=pw['Week'], y=pw['Total'], name=person, marker_color=color,
                        text=pw['Total'].apply(lambda v: str(int(v)) if v > 0 else ''),
                        textposition='inside', textfont=dict(color='white', size=12, family='Arial Black'),
                        hovertemplate=f"<b>{person}</b><br>Week: %{{x}}<br>Videos: %{{y}}<extra></extra>"
                    ))
                wk_expected = active_vdf.groupby('Week').agg(Days=('Date', 'nunique')).reset_index()
                wk_expected['Expected'] = wk_expected['Days'] * TEAM_DAILY_TARGET
                wk_expected = wk_expected.set_index('Week').reindex(wk_order).fillna(0).reset_index()
                wkf.add_trace(go.Scatter(
                    x=wk_expected['Week'], y=wk_expected['Expected'], mode='lines+markers',
                    line=dict(color='white', width=2, dash='dash'), marker=dict(size=8, color='white'),
                    name=f'Team Target ({TEAM_DAILY_TARGET}/day)',
                    hovertemplate=f"<b>Team Target</b><br>Week: %{{x}}<br>Expected: %{{y}}<extra></extra>"
                ))
                wkf.update_traces(cliponaxis=False)
                wkf.update_layout(
                    barmode='stack',
                    xaxis=dict(tickfont=dict(color='#e2e8f0', size=12)),
                    yaxis=dict(title=dict(text="Videos", font=AXIS_TITLE_FONT), tickfont=AXIS_TICK_FONT, gridcolor=GRID_COLOR),
                    height=400, margin=dict(t=20, b=20, l=20, r=20),
                    paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, font=LEGEND_FONT, bgcolor=CHART_BG)
                )
                st.plotly_chart(wkf, use_container_width=True, config=PLOTLY_CONFIG)

            with wrc:
                st.markdown("#### Person Comparison — Total Videos")
                st.markdown(f"*Expected per person so far: {DAILY_TARGET} × {num_active_days} active days*")
                person_totals = active_vdf.groupby('Person').agg(
                    Total=('Videos', 'sum'),
                    Avg=('Videos', 'mean'),
                    Best=('Videos', 'max'),
                    Target_Met=('Met Target', 'sum'),
                    Active_Days=('Videos', lambda x: (x > 0).sum())
                ).reset_index().sort_values('Total', ascending=True)
                person_expected_total = DAILY_TARGET * num_active_days

                ptf = go.Figure()
                for _, row in person_totals.iterrows():
                    color = PERSON_COLORS.get(row['Person'], '#0ea5e9')
                    ptf.add_trace(go.Bar(
                        y=[row['Person']], x=[row['Total']], orientation='h',
                        marker_color=color, showlegend=False,
                        text=[f"{int(row['Total'])} videos"],
                        textposition='inside', textfont=LABEL_FONT,
                        hovertemplate=(
                            f"<b>{row['Person']}</b><br>"
                            f"Total videos: {int(row['Total'])}<br>"
                            f"Expected: {person_expected_total}<br>"
                            f"Daily average: {row['Avg']:.1f}<br>"
                            f"Best day: {int(row['Best'])}<br>"
                            f"Target met ({DAILY_TARGET}): {int(row['Target_Met'])} of {int(row['Active_Days'])} days"
                            "<extra></extra>"
                        )
                    ))
                ptf.add_vline(x=person_expected_total, line_dash="dash", line_color="rgba(255,255,255,0.4)",
                    annotation_text=f"Expected: {person_expected_total}", annotation_position="top",
                    annotation_font=dict(color='#94a3b8', size=11))
                ptf.update_traces(cliponaxis=False)
                ptf.update_layout(
                    xaxis=dict(title=dict(text="Total Videos", font=AXIS_TITLE_FONT), tickfont=AXIS_TICK_FONT, gridcolor=GRID_COLOR,
                               range=[0, max(person_totals['Total'].max(), person_expected_total) * 1.2]),
                    yaxis=dict(tickfont=dict(color='#e2e8f0', size=14), automargin=True),
                    height=400, margin=dict(t=20, b=20, l=10, r=20),
                    paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG
                )
                st.plotly_chart(ptf, use_container_width=True, config=PLOTLY_CONFIG)

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Leaderboard ──
            st.markdown("### 🏆 Team Leaderboard")
            st.markdown("<br>", unsafe_allow_html=True)
            lb = person_totals.sort_values('Total', ascending=False).copy()
            lb['Rank'] = range(1, len(lb)+1)
            lb['Avg/Day'] = lb['Avg'].round(1)
            lb['Expected'] = DAILY_TARGET * num_active_days
            lb['Shortfall'] = (lb['Expected'] - lb['Total']).clip(lower=0).astype(int)
            _hr = np.where(lb['Active_Days'] > 0, (lb['Target_Met'] / lb['Active_Days']) * 100, np.nan)
            lb['Hit Rate'] = pd.Series(_hr, index=lb.index).apply(lambda v: f'{int(round(v))}%' if pd.notna(v) else '—')
            st.dataframe(
                lb[['Rank', 'Person', 'Total', 'Expected', 'Shortfall', 'Avg/Day', 'Best', 'Active_Days', 'Target_Met', 'Hit Rate']].rename(columns={
                    'Total': 'Total Videos', 'Expected': f'Expected ({DAILY_TARGET}×{num_active_days}d)',
                    'Best': 'Best Day', 'Active_Days': 'Active Days',
                    'Target_Met': f'Days ≥{DAILY_TARGET}'
                }),
                hide_index=True, use_container_width=True
            )

            # Notes
            notes_df = _vdf[_vdf['Note'] != ''][['Date Label', 'Person', 'Note']].drop_duplicates()
            if not notes_df.empty:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("### 📝 Notes & Remarks")
                st.markdown("*Non-numeric entries or special notes recorded in the tracker*")
                st.markdown("<br>", unsafe_allow_html=True)
                st.dataframe(notes_df.rename(columns={'Date Label': 'Date'}), hide_index=True, use_container_width=True)

            # ── Full daily log ──
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 📋 Full Daily Log")
            st.markdown(f"*Individual target: {DAILY_TARGET}/person — Team target: {TEAM_DAILY_TARGET}/day combined*")
            st.markdown("<br>", unsafe_allow_html=True)
            log = _vdf.pivot_table(index=['Date', 'Date Label', 'Day', 'Week'], columns='Person', values='Videos', aggfunc='sum').reset_index()
            log = log.sort_values('Date')
            log['Team Total'] = log[persons].sum(axis=1)
            log[f'Team ≥{TEAM_DAILY_TARGET}?'] = log['Team Total'].apply(lambda v: '✅ Yes' if v >= TEAM_DAILY_TARGET else ('❌ No' if v > 0 else '—'))
            for person in persons:
                first_name = person.split()[0]
                log[f'{first_name} ≥{DAILY_TARGET}?'] = log[person].apply(lambda v: '✅' if v >= DAILY_TARGET else ('❌' if v > 0 else '—'))
            display_cols = ['Date Label', 'Day', 'Week'] + persons + ['Team Total', f'Team ≥{TEAM_DAILY_TARGET}?']
            st.dataframe(log[display_cols].rename(columns={'Date Label': 'Date', 'Day': 'Weekday'}),
                hide_index=True, use_container_width=True, height=400)

    else:
        st.markdown('<div class="warning-card"><strong>⚠️ No Chapter-wise AI Video Data Available</strong><br><br>'
                    'The "Chapter-wise AI video Project" sheet could not be loaded. Please upload the tracker file using the uploader above.</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
#  TAB 7 — ALL COURSES
# ═══════════════════════════════════════════════════════════════════
with tab_allcourses:
    st.markdown("## Complete Course List")
    st.markdown("*Filter and explore all courses — see every AI Video, Podcast, and Study Guide status*")
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: selected_status = st.multiselect("Filter by Status", options=sorted(df['Status'].unique()), default=sorted(df['Status'].unique()))
    with c2: selected_subject = st.multiselect("Filter by Subject Area", options=sorted(df['Subject Area'].unique()), default=sorted(df['Subject Area'].unique()))
    with c3: selected_level = st.multiselect("Filter by Course Level", options=sorted(df['Course Level'].unique()), default=sorted(df['Course Level'].unique()))
    st.markdown("<br>", unsafe_allow_html=True)
    fdf = df[(df['Status'].isin(selected_status)) & (df['Subject Area'].isin(selected_subject)) & (df['Course Level'].isin(selected_level))]
    st.markdown(f"**Showing {len(fdf)} of {len(df)} courses**")
    st.markdown("<br>", unsafe_allow_html=True)
    st.dataframe(fdf[['Course Name', 'Course Level', 'Subject Area', 'Number of Units', 'Status', 'Completion %',
        'Videos Completed', 'Podcasts Completed', 'Guides Completed', 'Still Pending']].sort_values('Completion %', ascending=False).rename(columns={
        'Number of Units': 'Units', 'Videos Completed': 'AI Videos ✓', 'Podcasts Completed': 'Podcasts ✓', 'Guides Completed': 'Study Guides ✓', 'Still Pending': 'Pending'}),
        column_config={"Completion %": st.column_config.ProgressColumn("Progress", format="%.1f%%", min_value=0, max_value=100)},
        hide_index=True, use_container_width=True, height=500)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📊 Summary Statistics")
    st.markdown("<br>", unsafe_allow_html=True)
    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        st.markdown("**Content Production**")
        st.write(f"• Total required: {int(total_required):,}")
        st.write(f"• Completed: {int(total_completed):,}")
        st.write(f"• Pending: {int(total_pending):,}")
    with sc2:
        st.markdown("**By Content Type**")
        st.write(f"• AI Videos: {int(total_videos_done)}/{int(total_units)}")
        st.write(f"• Podcasts: {int(total_podcasts_done)}/{int(total_units)}")
        st.write(f"• Study Guides: {int(total_guides_done)}/{int(total_units)}")
    with sc3:
        st.markdown("**Course Status**")
        st.write(f"• Complete: {complete_courses}")
        st.write(f"• In progress: {in_progress_courses}")
        st.write(f"• Not started: {not_started_courses}")
    with sc4:
        st.markdown("**Workload Estimate**")
        apc = total_pending / (total_courses - complete_courses) if (total_courses - complete_courses) > 0 else 0
        st.write(f"• Avg pending/course: {apc:.1f}")
        st.write(f"• Largest pending: {int(df['Still Pending'].max())}")
        mpv = df[df['Still Pending'] > 0]['Still Pending'].min() if len(df[df['Still Pending'] > 0]) > 0 else 0
        st.write(f"• Smallest pending: {int(mpv)}")

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

st.markdown("""
<div class="footer-text">
    <b>Course Development Progress Tracker</b><br>
    Dashboard refreshes data on page load. Click 'Refresh Data' button to get the latest information.
</div>
""", unsafe_allow_html=True)