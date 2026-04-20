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



# ── Person colours for chapter-wise AI video log tab ──
LOG_NB_COLORS = {
    'Yenushka': '#10b981',
    'Piyumi': '#a78bfa',
    'Amana': '#0ea5e9',
    'Fathima': '#f59e0b',
    'Rukaiya': '#f43f5e',
}
LOG_WT_COLORS = {
    'Anjani': '#f59e0b',
    'Anjani De silva': '#f59e0b',
    'Menuka': '#ec4899',
    'Other': '#64748b',
}
# Fallback palette for any new names
LOG_FALLBACK_COLORS = ['#06b6d4', '#f43f5e', '#84cc16', '#e879f9', '#fb923c', '#22d3ee']


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





# ── Load chapter-wise AI video LOG sheet (NEW) ──
def load_video_log_data(file_bytes):
    """Parse the 'Chapter-wise AI video log' sheet and return two DataFrames:
       one for NotebookLM creators and one for WebTool processors."""
    try:
        if isinstance(file_bytes, bytes):
            file_content = BytesIO(file_bytes)
        else:
            file_content = file_bytes

        xls = pd.ExcelFile(file_content, engine='openpyxl')
        sheet_name = None
        for s in xls.sheet_names:
            if 'chapter' in s.lower() and 'video' in s.lower() and 'log' in s.lower():
                sheet_name = s
                break
        if sheet_name is None:
            return None, None

        raw = pd.read_excel(xls, sheet_name=sheet_name, header=None)
        data = raw.iloc[2:].copy()

        # Assign column names based on known structure
        col_names = ['Date', 'AwardingBody', 'CourseName', 'UnitNo', 'ChapterNo',
                      'NB_Person', 'URL', 'WT_Person', 'AddedToFolder', 'VimeoLink', 'AddedToCoursePage']
        # Handle sheets with fewer/more columns gracefully
        if len(data.columns) >= len(col_names):
            data = data.iloc[:, :len(col_names)]
            data.columns = col_names
        else:
            for i in range(len(data.columns), len(col_names)):
                data[col_names[i]] = np.nan
            data.columns = col_names[:len(data.columns)] + col_names[len(data.columns):]

        data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
        data = data[data['Date'].notna()].copy()
        if data.empty:
            return pd.DataFrame(), pd.DataFrame()

        # Fix wrong year
        mask_2025 = data['Date'].dt.year == 2025
        if mask_2025.any():
            data.loc[mask_2025, 'Date'] = data.loc[mask_2025, 'Date'].apply(lambda d: d.replace(year=2026))

        data['Day'] = data['Date'].dt.day_name().str[:3]
        data['Date Label'] = data['Date'].dt.strftime('%d %b %Y')
        data['Short Date'] = data['Date'].dt.strftime('%d %b') + ' (' + data['Day'] + ')'

        # Clean person names
        data['NB_Person'] = data['NB_Person'].astype(str).str.strip().replace('nan', np.nan)
        data['WT_Person'] = data['WT_Person'].astype(str).str.strip().replace('nan', np.nan)

        # ── NotebookLM aggregated by person & date ──
        # A video only counts as complete when the URL column is present
        nb_data = data[(data['NB_Person'].notna()) & (data['URL'].notna()) & (data['URL'].astype(str).str.strip() != '') & (data['URL'].astype(str).str.strip().str.lower() != 'nan')].copy()
        nb_daily = nb_data.groupby(['Date', 'Date Label', 'Day', 'Short Date', 'NB_Person']).size().reset_index(name='Videos')
        nb_daily.rename(columns={'NB_Person': 'Person'}, inplace=True)

        # ── WebTool aggregated by person & date ──
        # A video only counts as complete when AddedToFolder says 'yes'
        wt_data = data[(data['WT_Person'].notna()) & (data['AddedToFolder'].astype(str).str.strip().str.lower() == 'yes')].copy()
        wt_daily = wt_data.groupby(['Date', 'Date Label', 'Day', 'Short Date', 'WT_Person']).size().reset_index(name='Videos')
        wt_daily.rename(columns={'WT_Person': 'Person'}, inplace=True)

        return nb_daily, wt_daily
    except Exception as e:
        st.error(f"Error loading video log data: {str(e)}")
        return None, None


# ── Load WebtoolStatus sheet (daily upload counts per person) ──
def load_webtool_status_data(file_bytes):
    """Parse the 'WebtoolStatus' sheet — daily WebTool upload counts per person."""
    try:
        if isinstance(file_bytes, bytes):
            file_content = BytesIO(file_bytes)
        else:
            file_content = file_bytes

        xls = pd.ExcelFile(file_content, engine='openpyxl')
        sheet_name = None
        for s in xls.sheet_names:
            if 'webtool' in s.lower() and 'status' in s.lower():
                sheet_name = s
                break
        if sheet_name is None:
            return None

        df = pd.read_excel(xls, sheet_name=sheet_name, header=1)
        df.columns = df.columns.astype(str).str.strip()

        if 'Date' not in df.columns:
            return None

        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df[df['Date'].notna()].copy()

        # Identify person columns (all non-Date columns)
        person_cols = [c for c in df.columns if c != 'Date']
        for col in person_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

        # Melt to long format for easier processing
        long_df = df.melt(id_vars=['Date'], value_vars=person_cols,
                          var_name='Person', value_name='Videos')
        long_df['Day'] = long_df['Date'].dt.day_name().str[:3]
        long_df['Date Label'] = long_df['Date'].dt.strftime('%d %b %Y')
        long_df['Short Date'] = long_df['Date'].dt.strftime('%d %b') + ' (' + long_df['Day'] + ')'

        # Keep only days with any upload activity across any person
        active_dates = long_df.groupby('Date')['Videos'].sum()
        active_dates = active_dates[active_dates > 0].index
        long_df = long_df[long_df['Date'].isin(active_dates)].copy()

        # Drop persons who have zero total across all days (e.g. empty "Other" column)
        person_totals = long_df.groupby('Person')['Videos'].sum()
        active_persons = person_totals[person_totals > 0].index
        long_df = long_df[long_df['Person'].isin(active_persons)].copy()

        return long_df
    except Exception as e:
        st.error(f"Error loading WebtoolStatus data: {str(e)}")
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


# ── Helper: get colour for a person from a colour map with fallback ──
def _get_color(person, color_map, idx=0):
    if person in color_map:
        return color_map[person]
    return LOG_FALLBACK_COLORS[idx % len(LOG_FALLBACK_COLORS)]


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

# ── Download the file ONCE — all parsers share the same bytes ──
file_bytes = download_excel_bytes(sharepoint_url)
df = None
nb_log = None
wt_log = None
wt_status_df = None

if file_bytes is not None:
    df = load_data(file_bytes)
    nb_log, wt_log = load_video_log_data(file_bytes)
    wt_status_df = load_webtool_status_data(file_bytes)

if df is None:
    st.warning("⚠️ Automatic Update Failed. Company security may be blocking the direct link.")
    st.info("👇 Download the tracker file and upload it here.")
    uploaded_file = st.file_uploader("Upload 'Additional Material Tracker Sheet.xlsx'", type=['xlsx'])
    if uploaded_file is not None:
        upload_bytes = uploaded_file.read()
        df = load_data(upload_bytes)
        nb_log, wt_log = load_video_log_data(upload_bytes)
        wt_status_df = load_webtool_status_data(upload_bytes)
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

tab_overview, tab_content, tab_subjects, tab_quickwins, tab_priority, tab_videolog, tab_allcourses = st.tabs([
    "📈 Overview", "🎯 Content Analysis", "📚 Subject & Level",
    "✅ Quick Wins", "⚠️ Priority Watch",
    "📹 Chapter-wise AI Video Progress", "📋 All Courses"
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
                
                nzf = go.Figure()
                nzf.add_trace(go.Bar(
                    y=nbz['Course Size'], x=nbz['Needed'], orientation='h',
                    marker_color='#f59e0b',
                    text=nbz['Needed'].apply(lambda v: f"{int(v)} items"),
                    textposition='inside', textfont=dict(color='white', size=14, family='Arial Black'),
                    insidetextanchor='middle',
                    hovertemplate='<b>%{y}</b><br>Content Needed: %{x}<extra></extra>'
                ))
                
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
#  TAB 6 — CHAPTER-WISE AI VIDEO PROGRESS  (from log sheet)
# ═══════════════════════════════════════════════════════════════════

with tab_videolog:
    st.markdown("## 📹 Chapter-wise AI Video Progress")
    st.markdown("*Detailed video-level production log — track who produced each video using NotebookLM and who produced it using WebTool*")
    st.markdown("<br>", unsafe_allow_html=True)

    # ── If SharePoint load didn't get the log, allow upload ──
    _nb = nb_log
    _wt = wt_status_df
    if (_nb is None or (isinstance(_nb, pd.DataFrame) and _nb.empty)) and (_wt is None or (isinstance(_wt, pd.DataFrame) and _wt.empty)):
        st.info("👇 Upload the tracker file to view the Chapter-wise AI Video Log data.")
        log_upload = st.file_uploader("Upload 'Additional Material Tracker Sheet.xlsx' (for Video Log tab)", type=['xlsx'], key='log_upload')
        if log_upload is not None:
            upload_log_bytes = log_upload.read()
            _nb, _ = load_video_log_data(upload_log_bytes)
            _wt = load_webtool_status_data(upload_log_bytes)

    has_nb = _nb is not None and isinstance(_nb, pd.DataFrame) and not _nb.empty
    has_wt = _wt is not None and isinstance(_wt, pd.DataFrame) and not _wt.empty

    if not has_nb and not has_wt:
        st.markdown('<div class="warning-card"><strong>⚠️ No Chapter-wise AI Video Log Data Available</strong><br><br>'
                    'The "Chapter-wise AI video log" sheet could not be found or is empty. Please upload the tracker file above.</div>', unsafe_allow_html=True)
    else:
        # ── Sub-tabs ──
        sub_nb, sub_wt = st.tabs(["🔬 Using NotebookLM", "🌐 Using WebTool"])

        # ─────────────────────────────────────────────────────
        #  SUB-TAB A: NotebookLM
        # ─────────────────────────────────────────────────────
        with sub_nb:
            st.markdown("<br>", unsafe_allow_html=True)
            if not has_nb:
                st.info("No NotebookLM data available yet.")
            else:
                nb_persons = sorted(_nb['Person'].unique())
                nb_dates = sorted(_nb['Date'].unique())
                nb_num_days = len(nb_dates)
                nb_date_order = _nb.drop_duplicates('Date').sort_values('Date')['Short Date'].tolist()

                # ── Key Metrics ──
                st.markdown("### Key Metrics")
                st.markdown("<br>", unsafe_allow_html=True)
                nb_total = int(_nb['Videos'].sum())
                m1, m2 = st.columns(2)
                with m1: st.metric("Total Videos Created", f"{nb_total}")
                with m2: st.metric("Active Days", f"{nb_num_days}")
                st.markdown("<br>", unsafe_allow_html=True)

                # Person cards
                pcols = st.columns(4)
                nb_all_persons = ['Amana', 'Piyumi', 'Yenushka', 'Rukaiya']
                for i, person in enumerate(nb_all_persons):
                    with pcols[i]:
                        color = _get_color(person, LOG_NB_COLORS, i)
                        pv = int(_nb[_nb['Person'] == person]['Videos'].sum()) if person in nb_persons else 0
                        st.markdown(
                            f'<div style="background:rgba(30,41,59,0.7);border-radius:10px;padding:18px 20px;'
                            f'border:1px solid rgba(255,255,255,0.1);border-left:4px solid {color};'
                            f'box-shadow:0 4px 15px rgba(0,0,0,0.2);">'
                            f'<div style="color:#94a3b8;font-size:12px;font-weight:500;text-transform:uppercase;letter-spacing:0.5px;">{person} Total Videos</div>'
                            f'<div style="color:{color};font-size:28px;font-weight:700;margin-top:4px;">{pv}</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("---")
                st.markdown("<br>", unsafe_allow_html=True)

                # ── Chart 1: Daily production stacked bar ──
                st.markdown("### 📊 Daily Video Production by Person")
                st.markdown("*Each bar shows total videos produced per day, broken down by contributor*")
                st.markdown("<br>", unsafe_allow_html=True)

                nb_stacked = go.Figure()
                for i, person in enumerate(nb_persons):
                    pdata = _nb[_nb['Person'] == person].sort_values('Date')
                    color = _get_color(person, LOG_NB_COLORS, i)
                    nb_stacked.add_trace(go.Bar(
                        x=pdata['Short Date'], y=pdata['Videos'], name=person, marker_color=color,
                        text=pdata['Videos'].apply(lambda v: str(int(v)) if v > 0 else ''),
                        textposition='inside', textfont=dict(color='white', size=13, family='Arial Black'),
                        hovertemplate=(
                            f"<b>{person}</b><br>"
                            "Date: %{x}<br>"
                            "Videos produced: %{y}"
                            "<extra></extra>"
                        )
                    ))
                # Team total annotations above bars
                nb_team_daily = _nb.groupby(['Date', 'Short Date'])['Videos'].sum().reset_index().sort_values('Date')
                for _, row in nb_team_daily.iterrows():
                    nb_stacked.add_annotation(x=row['Short Date'], y=row['Videos'], text=str(int(row['Videos'])),
                        showarrow=False, yanchor='bottom', yshift=5, font=dict(color='white', size=14, family='Arial Black'))
                nb_stacked.update_traces(cliponaxis=False)
                nb_stacked.update_layout(
                    barmode='stack',
                    xaxis=dict(title="", tickfont=dict(color='#e2e8f0', size=12), categoryorder='array', categoryarray=nb_date_order, tickangle=-30),
                    yaxis=dict(title=dict(text="Videos Produced", font=AXIS_TITLE_FONT), tickfont=AXIS_TICK_FONT,
                               gridcolor=GRID_COLOR, rangemode='tozero',
                               range=[0, nb_team_daily['Videos'].max() * 1.25]),
                    height=420, margin=dict(t=20, b=80, l=60, r=30),
                    paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, font=LEGEND_FONT, bgcolor=CHART_BG)
                )
                st.plotly_chart(nb_stacked, use_container_width=True, config=PLOTLY_CONFIG)

                st.markdown("<br>", unsafe_allow_html=True)

                # ── Chart 2: Day-over-day trend line ──
                lc, rc = st.columns(2)
                with lc:
                    st.markdown("#### Day-over-Day Trend per Person")
                    st.markdown("*How each person's output changed from one day to the next*")
                    st.markdown("<br>", unsafe_allow_html=True)

                    nb_trend = go.Figure()
                    for i, person in enumerate(nb_persons):
                        pdata = _nb[_nb['Person'] == person].sort_values('Date')
                        color = _get_color(person, LOG_NB_COLORS, i)
                        nb_trend.add_trace(go.Scatter(
                            x=pdata['Short Date'], y=pdata['Videos'], mode='lines+markers',
                            line=dict(color=color, width=3), marker=dict(size=10, color=color, line=dict(width=2, color='white')),
                            name=person,
                            hovertemplate=(
                                f"<b>{person}</b><br>"
                                "Date: %{x}<br>"
                                "Videos: %{y}"
                                "<extra></extra>"
                            )
                        ))
                    nb_trend.update_layout(
                        xaxis=dict(title="", tickfont=dict(color='#e2e8f0', size=11), categoryorder='array', categoryarray=nb_date_order, tickangle=-30),
                        yaxis=dict(title=dict(text="Videos", font=AXIS_TITLE_FONT), tickfont=AXIS_TICK_FONT, gridcolor=GRID_COLOR, rangemode='tozero'),
                        height=380, margin=dict(t=20, b=70, l=50, r=20),
                        paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, font=LEGEND_FONT, bgcolor=CHART_BG)
                    )
                    st.plotly_chart(nb_trend, use_container_width=True, config=PLOTLY_CONFIG)

                with rc:
                    st.markdown("#### Share of Total Contribution")
                    st.markdown("*Overall split of videos produced by each person*")
                    st.markdown("<br>", unsafe_allow_html=True)

                    nb_person_totals = _nb.groupby('Person')['Videos'].sum().reset_index().sort_values('Videos', ascending=False)
                    pie_colors = [_get_color(p, LOG_NB_COLORS, i) for i, p in enumerate(nb_person_totals['Person'])]
                    nb_pie = px.pie(nb_person_totals, values='Videos', names='Person',
                                   color_discrete_sequence=pie_colors, hole=0.45)
                    nb_pie.update_traces(
                        textposition='inside', textinfo='value+percent',
                        textfont=dict(size=15, color='white'),
                        hovertemplate="<b>%{label}</b><br>Videos: %{value}<br>Share: %{percent}<extra></extra>"
                    )
                    nb_pie.update_layout(
                        height=380, margin=dict(t=20, b=20, l=20, r=20),
                        legend=dict(font=LEGEND_FONT, bgcolor=CHART_BG),
                        paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG
                    )
                    st.plotly_chart(nb_pie, use_container_width=True, config=PLOTLY_CONFIG)

                st.markdown("<br>", unsafe_allow_html=True)

                # ── Chart 3: Person comparison bar ──
                st.markdown("#### Person Comparison — Total Videos via NotebookLM")
                st.markdown("<br>", unsafe_allow_html=True)
                nb_comp = nb_person_totals.sort_values('Videos', ascending=True)
                nb_comp_fig = go.Figure()
                for _, row in nb_comp.iterrows():
                    color = _get_color(row['Person'], LOG_NB_COLORS)
                    nb_comp_fig.add_trace(go.Bar(
                        y=[row['Person']], x=[row['Videos']], orientation='h',
                        marker_color=color, showlegend=False,
                        text=[f"{int(row['Videos'])} videos"],
                        textposition='inside', textfont=LABEL_FONT,
                        hovertemplate=(
                            f"<b>{row['Person']}</b><br>"
                            f"Total videos: {int(row['Videos'])}"
                            "<extra></extra>"
                        )
                    ))
                nb_comp_fig.update_traces(cliponaxis=False)
                nb_comp_fig.update_layout(
                    xaxis=dict(title=dict(text="Total Videos", font=AXIS_TITLE_FONT), tickfont=AXIS_TICK_FONT, gridcolor=GRID_COLOR,
                               range=[0, nb_comp['Videos'].max() * 1.25]),
                    yaxis=dict(tickfont=dict(color='#e2e8f0', size=14), automargin=True),
                    height=250, margin=dict(t=10, b=20, l=10, r=20),
                    paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG
                )
                st.plotly_chart(nb_comp_fig, use_container_width=True, config=PLOTLY_CONFIG)

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("---")
                st.markdown("<br>", unsafe_allow_html=True)

                # ── Summary ──
                st.markdown("### 📋 Summary")
                st.markdown("<br>", unsafe_allow_html=True)
                top_nb = nb_person_totals.iloc[0]
                bottom_nb = nb_person_totals.iloc[-1]
                best_day_nb = nb_team_daily.loc[nb_team_daily['Videos'].idxmax()]
                worst_day_nb = nb_team_daily.loc[nb_team_daily['Videos'].idxmin()]

                # Day-over-day change
                if len(nb_team_daily) >= 2:
                    last_day_val = nb_team_daily.iloc[-1]['Videos']
                    prev_day_val = nb_team_daily.iloc[-2]['Videos']
                    dod_change = last_day_val - prev_day_val
                    dod_pct = (dod_change / prev_day_val * 100) if prev_day_val > 0 else 0
                    if dod_change > 0:
                        dod_text = f"The most recent day saw <strong>{int(last_day_val)} videos</strong>, an increase of <strong>{int(dod_change)} ({dod_pct:+.0f}%)</strong> compared to the previous day."
                    elif dod_change < 0:
                        dod_text = f"The most recent day saw <strong>{int(last_day_val)} videos</strong>, a decrease of <strong>{int(abs(dod_change))} ({dod_pct:+.0f}%)</strong> compared to the previous day."
                    else:
                        dod_text = f"The most recent day produced <strong>{int(last_day_val)} videos</strong>, unchanged from the previous day."
                else:
                    dod_text = f"Only one day of data so far with <strong>{int(nb_team_daily.iloc[0]['Videos'])} videos</strong>."

                st.markdown(
                    f'<div class="insight-card"><strong>🔬 NotebookLM Video Production Summary</strong><br><br>'
                    f'Over <strong>{nb_num_days} active days</strong>, the team created a total of <strong>{nb_total} videos</strong> using NotebookLM.<br><br>'
                    f'<strong>{top_nb["Person"]}</strong> leads with <strong>{int(top_nb["Videos"])} videos</strong>, '
                    f'while <strong>{bottom_nb["Person"]}</strong> contributed <strong>{int(bottom_nb["Videos"])} videos</strong>.<br><br>'
                    f'The most productive day was <strong>{best_day_nb["Short Date"]}</strong> with <strong>{int(best_day_nb["Videos"])} videos</strong>. '
                    f'{dod_text}</div>',
                    unsafe_allow_html=True
                )

                # ── Full data table ──
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("### 📋 Full Daily Log — NotebookLM")
                st.markdown("<br>", unsafe_allow_html=True)
                nb_pivot = _nb.pivot_table(index=['Date', 'Date Label', 'Day'], columns='Person', values='Videos', aggfunc='sum', fill_value=0).reset_index()
                nb_pivot = nb_pivot.sort_values('Date')
                nb_pivot['Team Total'] = nb_pivot[nb_persons].sum(axis=1)
                display_nb_cols = ['Date Label', 'Day'] + nb_persons + ['Team Total']
                st.dataframe(nb_pivot[display_nb_cols].rename(columns={'Date Label': 'Date', 'Day': 'Weekday'}),
                    hide_index=True, use_container_width=True)


        # ─────────────────────────────────────────────────────
        #  SUB-TAB B: WebTool
        # ─────────────────────────────────────────────────────
        with sub_wt:
            st.markdown("<br>", unsafe_allow_html=True)
            if not has_wt:
                st.info("No WebTool data available yet. Videos produced via WebTool will appear here once data is entered.")
            else:
                wt_persons = sorted(_wt['Person'].unique())
                wt_dates = sorted(_wt['Date'].unique())
                wt_num_days = len(wt_dates)
                wt_date_order = _wt.drop_duplicates('Date').sort_values('Date')['Short Date'].tolist()

                # ── Key Metrics ──
                st.markdown("### Key Metrics")
                st.markdown("<br>", unsafe_allow_html=True)
                wt_total = int(_wt['Videos'].sum())
                m1, m2 = st.columns(2)
                with m1: st.metric("Total Videos Produced", f"{wt_total}")
                with m2: st.metric("Active Days", f"{wt_num_days}")
                st.markdown("<br>", unsafe_allow_html=True)

                # Person cards
                pcols = st.columns(len(wt_persons))
                for i, person in enumerate(wt_persons):
                    with pcols[i]:
                        color = _get_color(person, LOG_WT_COLORS, i)
                        pv = int(_wt[_wt['Person'] == person]['Videos'].sum())
                        st.markdown(
                            f'<div style="background:rgba(30,41,59,0.7);border-radius:10px;padding:18px 20px;'
                            f'border:1px solid rgba(255,255,255,0.1);border-left:4px solid {color};'
                            f'box-shadow:0 4px 15px rgba(0,0,0,0.2);">'
                            f'<div style="color:#94a3b8;font-size:12px;font-weight:500;text-transform:uppercase;letter-spacing:0.5px;">{person} Total Videos</div>'
                            f'<div style="color:{color};font-size:28px;font-weight:700;margin-top:4px;">{pv}</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("---")
                st.markdown("<br>", unsafe_allow_html=True)

                # ── Chart 1: Daily production stacked bar ──
                st.markdown("### 📊 Daily Video Production by Person")
                st.markdown("*Each bar shows total videos produced via WebTool per day*")
                st.markdown("<br>", unsafe_allow_html=True)

                wt_stacked = go.Figure()
                for i, person in enumerate(wt_persons):
                    pdata = _wt[_wt['Person'] == person].sort_values('Date')
                    color = _get_color(person, LOG_WT_COLORS, i)
                    wt_stacked.add_trace(go.Bar(
                        x=pdata['Short Date'], y=pdata['Videos'], name=person, marker_color=color,
                        text=pdata['Videos'].apply(lambda v: str(int(v)) if v > 0 else ''),
                        textposition='inside', textfont=dict(color='white', size=13, family='Arial Black'),
                        hovertemplate=(
                            f"<b>{person}</b><br>"
                            "Date: %{x}<br>"
                            "Videos produced: %{y}"
                            "<extra></extra>"
                        )
                    ))
                wt_team_daily = _wt.groupby(['Date', 'Short Date'])['Videos'].sum().reset_index().sort_values('Date')
                for _, row in wt_team_daily.iterrows():
                    wt_stacked.add_annotation(x=row['Short Date'], y=row['Videos'], text=str(int(row['Videos'])),
                        showarrow=False, yanchor='bottom', yshift=5, font=dict(color='white', size=14, family='Arial Black'))
                wt_stacked.update_traces(cliponaxis=False)
                wt_stacked.update_layout(
                    barmode='stack',
                    xaxis=dict(title="", tickfont=dict(color='#e2e8f0', size=12), categoryorder='array', categoryarray=wt_date_order, tickangle=-30),
                    yaxis=dict(title=dict(text="Videos Produced", font=AXIS_TITLE_FONT), tickfont=AXIS_TICK_FONT,
                               gridcolor=GRID_COLOR, rangemode='tozero',
                               range=[0, wt_team_daily['Videos'].max() * 1.3]),
                    height=420, margin=dict(t=20, b=80, l=60, r=30),
                    paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, font=LEGEND_FONT, bgcolor=CHART_BG)
                )
                st.plotly_chart(wt_stacked, use_container_width=True, config=PLOTLY_CONFIG)

                st.markdown("<br>", unsafe_allow_html=True)

                # ── Charts: Trend + Pie side by side ──
                lc, rc = st.columns(2)
                with lc:
                    st.markdown("#### Day-over-Day Trend per Person")
                    st.markdown("*How each person's production changed between days*")
                    st.markdown("<br>", unsafe_allow_html=True)

                    wt_trend = go.Figure()
                    for i, person in enumerate(wt_persons):
                        pdata = _wt[_wt['Person'] == person].sort_values('Date')
                        color = _get_color(person, LOG_WT_COLORS, i)
                        wt_trend.add_trace(go.Scatter(
                            x=pdata['Short Date'], y=pdata['Videos'], mode='lines+markers',
                            line=dict(color=color, width=3),
                            marker=dict(size=10, color=color, line=dict(width=2, color='white')),
                            name=person,
                            hovertemplate=(
                                f"<b>{person}</b><br>"
                                "Date: %{x}<br>"
                                "Videos: %{y}"
                                "<extra></extra>"
                            )
                        ))
                    wt_trend.update_layout(
                        xaxis=dict(title="", tickfont=dict(color='#e2e8f0', size=11), categoryorder='array', categoryarray=wt_date_order, tickangle=-30),
                        yaxis=dict(title=dict(text="Videos", font=AXIS_TITLE_FONT), tickfont=AXIS_TICK_FONT, gridcolor=GRID_COLOR, rangemode='tozero'),
                        height=380, margin=dict(t=20, b=70, l=50, r=20),
                        paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, font=LEGEND_FONT, bgcolor=CHART_BG)
                    )
                    st.plotly_chart(wt_trend, use_container_width=True, config=PLOTLY_CONFIG)

                with rc:
                    st.markdown("#### Share of Total Contribution")
                    st.markdown("*Overall split of videos produced by each person*")
                    st.markdown("<br>", unsafe_allow_html=True)

                    wt_person_totals = _wt.groupby('Person')['Videos'].sum().reset_index().sort_values('Videos', ascending=False)
                    wt_pie_colors = [_get_color(p, LOG_WT_COLORS, i) for i, p in enumerate(wt_person_totals['Person'])]
                    wt_pie = px.pie(wt_person_totals, values='Videos', names='Person',
                                   color_discrete_sequence=wt_pie_colors, hole=0.45)
                    wt_pie.update_traces(
                        textposition='inside', textinfo='value+percent',
                        textfont=dict(size=15, color='white'),
                        hovertemplate="<b>%{label}</b><br>Videos: %{value}<br>Share: %{percent}<extra></extra>"
                    )
                    wt_pie.update_layout(
                        height=380, margin=dict(t=20, b=20, l=20, r=20),
                        legend=dict(font=LEGEND_FONT, bgcolor=CHART_BG),
                        paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG
                    )
                    st.plotly_chart(wt_pie, use_container_width=True, config=PLOTLY_CONFIG)

                st.markdown("<br>", unsafe_allow_html=True)

                # ── Chart: Person comparison bar ──
                st.markdown("#### Person Comparison — Total Videos via WebTool")
                st.markdown("<br>", unsafe_allow_html=True)
                wt_comp = wt_person_totals.sort_values('Videos', ascending=True)
                wt_comp_fig = go.Figure()
                for _, row in wt_comp.iterrows():
                    color = _get_color(row['Person'], LOG_WT_COLORS)
                    wt_comp_fig.add_trace(go.Bar(
                        y=[row['Person']], x=[row['Videos']], orientation='h',
                        marker_color=color, showlegend=False,
                        text=[f"{int(row['Videos'])} videos"],
                        textposition='inside', textfont=LABEL_FONT,
                        hovertemplate=(
                            f"<b>{row['Person']}</b><br>"
                            f"Total videos: {int(row['Videos'])}"
                            "<extra></extra>"
                        )
                    ))
                wt_comp_fig.update_traces(cliponaxis=False)
                wt_comp_fig.update_layout(
                    xaxis=dict(title=dict(text="Total Videos", font=AXIS_TITLE_FONT), tickfont=AXIS_TICK_FONT, gridcolor=GRID_COLOR,
                               range=[0, wt_comp['Videos'].max() * 1.25]),
                    yaxis=dict(tickfont=dict(color='#e2e8f0', size=14), automargin=True),
                    height=220, margin=dict(t=10, b=20, l=10, r=20),
                    paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG
                )
                st.plotly_chart(wt_comp_fig, use_container_width=True, config=PLOTLY_CONFIG)

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("---")
                st.markdown("<br>", unsafe_allow_html=True)

                # ── Summary ──
                st.markdown("### 📋 Summary")
                st.markdown("<br>", unsafe_allow_html=True)
                top_wt = wt_person_totals.iloc[0]
                bottom_wt = wt_person_totals.iloc[-1]

                st.markdown(
                    f'<div class="insight-card"><strong>🌐 WebTool Video Production Summary</strong><br><br>'
                    f'Over <strong>{wt_num_days} active day{"s" if wt_num_days > 1 else ""}</strong>, the team produced <strong>{wt_total} videos</strong> via WebTool.<br><br>'
                    f'<strong>{top_wt["Person"]}</strong> produced the most with <strong>{int(top_wt["Videos"])} videos</strong>'
                    + (f', while <strong>{bottom_wt["Person"]}</strong> produced <strong>{int(bottom_wt["Videos"])} videos</strong>.' if len(wt_persons) > 1 else '.')
                    + '</div>',
                    unsafe_allow_html=True
                )

                # ── Full data table ──
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("### 📋 Full Daily Log — WebTool")
                st.markdown("<br>", unsafe_allow_html=True)
                wt_pivot = _wt.pivot_table(index=['Date', 'Date Label', 'Day'], columns='Person', values='Videos', aggfunc='sum', fill_value=0).reset_index()
                wt_pivot = wt_pivot.sort_values('Date')
                wt_pivot['Team Total'] = wt_pivot[wt_persons].sum(axis=1)
                display_wt_cols = ['Date Label', 'Day'] + wt_persons + ['Team Total']
                st.dataframe(wt_pivot[display_wt_cols].rename(columns={'Date Label': 'Date', 'Day': 'Weekday'}),
                    hide_index=True, use_container_width=True)


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
