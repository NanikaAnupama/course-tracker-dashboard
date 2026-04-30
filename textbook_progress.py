import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import io
import requests

def render_textbook_progress():
        # ─────────────────────────── PAGE CONFIG ──────────────────────
        # Page config is handled by the outer app when imported.

        # ══════════════════════════════════════════════════════════════
        #  DARK THEME PALETTE
        #  ─────────────────
        #  Page bg        : #0B1120  (deep navy)
        #  Card surface   : #131D2F  (dark indigo-slate)
        #  Card border    : #1E2D45  (muted blue-grey)
        #  Card hover     : #182640  (slightly lighter)
        #  Primary accent : #6C63FF  (vivid indigo)
        #  Success        : #34D399  (emerald)
        #  Warning        : #FBBF24  (amber)
        #  Danger/orange  : #FB923C  (orange)
        #  Heading text   : #F1F5F9  (near-white)
        #  Body text      : #CBD5E1  (cool grey)
        #  Muted text     : #8896AB  (grey-blue)
        #  Input surface  : #0F1A2E  (darker than card)
        #  Input border   : #253552  (subtle blue)
        # ══════════════════════════════════════════════════════════════

        st.markdown("""
        <style>
            /* ===== FORCE DARK BACKGROUND EVERYWHERE ===== */
            .stApp, [data-testid="stAppViewContainer"],
            [data-testid="stHeader"], [data-testid="stToolbar"],
            section[data-testid="stSidebar"],
            [data-testid="stBottomBlockContainer"] {
                background-color: #0B1120 !important;
            }
            .main .block-container {
                padding: 1.2rem 2rem 2rem 2rem;
                max-width: 1300px;
            }

            /* ===== GLOBAL TYPOGRAPHY ===== */
            html, body, [class*="css"] {
                font-family: 'Source Sans Pro', 'Segoe UI', sans-serif;
                color: #CBD5E1 !important;
            }
            h1, h2, h3, h4, h5, h6 { color: #F1F5F9 !important; }
            p, span, div, label, li  { color: #CBD5E1 !important; }

            /* ===== HEADER BANNER ===== */
            .dash-header {
                background: linear-gradient(135deg, #1E1B4B 0%, #312E81 50%, #4338CA 100%);
                border: 1px solid #3730A3;
                border-radius: 16px; padding: 30px 38px;
                margin-bottom: 28px; position: relative; overflow: hidden;
            }
            .dash-header::before {
                content: ''; position: absolute; top: -50px; right: -30px;
                width: 220px; height: 220px; border-radius: 50%;
                background: rgba(99,102,241,0.15);
            }
            .dash-header::after {
                content: ''; position: absolute; bottom: -70px; right: 100px;
                width: 160px; height: 160px; border-radius: 50%;
                background: rgba(99,102,241,0.08);
            }
            .dash-header h1 {
                color: #FFFFFF !important; font-size: 1.7rem; font-weight: 700;
                margin: 0 0 6px; letter-spacing: -0.3px; position: relative;
            }
            .dash-header p {
                color: #A5B4FC !important; font-size: 0.92rem;
                margin: 0; position: relative;
            }

            /* ===== TABS ===== */
            .stTabs [data-baseweb="tab-list"] {
                gap: 0; background: #131D2F; border-radius: 12px;
                padding: 5px; border: 1px solid #1E2D45;
            }
            .stTabs [data-baseweb="tab"] {
                border-radius: 8px; padding: 10px 28px;
                font-weight: 600; font-size: 0.88rem;
                color: #8896AB !important;
                background: transparent; border: none !important;
            }
            .stTabs [aria-selected="true"] {
                background: #6C63FF !important;
                color: #FFFFFF !important;
                box-shadow: 0 2px 12px rgba(108,99,255,0.35);
            }
            .stTabs [data-baseweb="tab-panel"] { padding-top: 24px; }
            button[data-baseweb="tab"] > div > p { color: inherit !important; }
            [aria-selected="true"] > div > p { color: #FFFFFF !important; }

            /* ===== KPI METRIC CARDS (colored surface) ===== */
            [data-testid="stMetric"] {
                background: #131D2F !important;
                border: 1px solid #1E2D45;
                border-radius: 14px; padding: 20px 24px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.25);
                transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
            }
            [data-testid="stMetric"]:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(0,0,0,0.35);
                border-color: #6C63FF;
            }
            [data-testid="stMetricLabel"] p {
                font-size: 0.78rem !important; color: #8896AB !important;
                font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;
            }
            [data-testid="stMetricValue"] div {
                font-size: 1.85rem !important; font-weight: 800 !important;
                color: #F1F5F9 !important;
            }
            [data-testid="stMetricDelta"] div {
                color: #8896AB !important; font-size: 0.8rem !important;
            }

            /* ===== SECTION HEADERS ===== */
            .section-hdr {
                font-size: 1rem; font-weight: 700; color: #F1F5F9 !important;
                padding: 10px 0 8px; margin-top: 8px;
                border-bottom: 2px solid #1E2D45; margin-bottom: 16px;
                display: flex; align-items: center; gap: 8px;
            }
            .section-hdr .icon {
                width: 30px; height: 30px; border-radius: 8px;
                display: inline-flex; align-items: center; justify-content: center;
                font-size: 0.85rem;
            }

            /* ===== STATUS PILLS (bright on dark) ===== */
            .pill {
                display: inline-block; padding: 5px 16px; border-radius: 20px;
                font-size: 0.78rem; font-weight: 700; letter-spacing: 0.3px;
            }
            .pill-ready    { background: rgba(52,211,153,0.15); color: #34D399 !important; border: 1px solid rgba(52,211,153,0.3); }
            .pill-none     { background: rgba(251,191,36,0.15); color: #FBBF24 !important; border: 1px solid rgba(251,191,36,0.3); }
            .pill-progress { background: rgba(108,99,255,0.15); color: #A5B4FC !important; border: 1px solid rgba(108,99,255,0.3); }

            /* ===== DETAIL CARD ===== */
            .detail-card {
                background: #131D2F; border: 1px solid #1E2D45;
                border-radius: 16px; padding: 28px 32px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.25); margin-bottom: 20px;
            }
            .detail-title {
                font-size: 1.3rem; font-weight: 800; color: #F1F5F9 !important;
                margin: 0 0 10px; line-height: 1.3;
            }
            .detail-tags {
                display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
                margin-bottom: 22px;
            }
            .tag {
                display: inline-block; padding: 5px 14px; border-radius: 8px;
                font-size: 0.78rem; font-weight: 600;
                background: #1A2744; color: #A5B4FC !important;
                border: 1px solid #253552;
            }

            /* ===== STAT GRID ===== */
            .stat-grid {
                display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
                gap: 14px; margin-bottom: 20px;
            }
            .stat-box {
                background: #0F1A2E; border: 1px solid #1E2D45;
                border-radius: 12px; padding: 18px 20px; text-align: center;
                transition: transform 0.15s ease, border-color 0.15s ease;
            }
            .stat-box:hover { transform: translateY(-2px); border-color: #6C63FF; }
            .stat-label {
                font-size: 0.7rem; color: #8896AB !important; text-transform: uppercase;
                letter-spacing: 0.6px; font-weight: 700; margin-bottom: 6px;
            }
            .stat-value {
                font-size: 1.45rem; font-weight: 800; color: #F1F5F9 !important;
            }

            /* ===== MARGIN BAR ===== */
            .margin-card {
                background: #0F1A2E; border: 1px solid #1E2D45;
                border-radius: 12px; padding: 18px 24px; margin-bottom: 20px;
            }
            .margin-header {
                display: flex; justify-content: space-between; align-items: center;
                margin-bottom: 12px;
            }
            .margin-label { font-size: 0.88rem; font-weight: 700; color: #CBD5E1 !important; }
            .margin-value { font-size: 1.1rem; font-weight: 800; }
            .margin-track {
                background: #1E2D45; border-radius: 8px; height: 12px; overflow: hidden;
            }
            .margin-fill { height: 100%; border-radius: 8px; transition: width 0.4s ease; }

            /* ===== PEER GRID ===== */
            .peer-grid {
                display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px;
            }
            .peer-box {
                background: #131D2F; border: 1px solid #1E2D45;
                border-radius: 12px; padding: 18px 20px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.2);
            }
            .peer-label {
                font-size: 0.72rem; color: #8896AB !important; text-transform: uppercase;
                letter-spacing: 0.5px; font-weight: 700; margin-bottom: 6px;
            }
            .peer-value { font-size: 1.3rem; font-weight: 800; color: #F1F5F9 !important; }
            .peer-delta { font-size: 0.78rem; color: #8896AB !important; margin-top: 4px; }

            /* ===== DATAFRAME / TABLE ===== */
            [data-testid="stDataFrame"] {
                border-radius: 12px; overflow: hidden;
                border: 1px solid #1E2D45;
                box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            }
            [data-testid="stDataFrame"] * {
                color: #CBD5E1 !important;
            }

            /* ===== CHART CONTAINERS ===== */
            [data-testid="stPlotlyChart"] {
                background: #131D2F; border: 1px solid #1E2D45;
                border-radius: 14px; padding: 14px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            }

            /* ===== INPUT WIDGETS ===== */
            [data-testid="stTextInput"] input {
                background: #0F1A2E !important; color: #F1F5F9 !important;
                border: 1px solid #253552 !important; border-radius: 10px !important;
                padding: 10px 14px !important;
            }
            [data-testid="stTextInput"] input::placeholder { color: #5A6B83 !important; }
            [data-testid="stTextInput"] input:focus {
                border-color: #6C63FF !important;
                box-shadow: 0 0 0 2px rgba(108,99,255,0.2) !important;
            }

            /* Multiselect */
            [data-testid="stMultiSelect"] > div,
            [data-testid="stMultiSelect"] > div > div {
                background: #0F1A2E !important;
                border-color: #253552 !important;
                border-radius: 10px !important;
            }
            div[data-baseweb="select"] > div {
                background: #0F1A2E !important; color: #F1F5F9 !important;
                border-color: #253552 !important; border-radius: 10px !important;
            }
            div[data-baseweb="select"] span { color: #F1F5F9 !important; }
            div[data-baseweb="popover"] > div {
                background: #131D2F !important; border: 1px solid #1E2D45 !important;
            }
            div[data-baseweb="popover"] li {
                color: #CBD5E1 !important;
            }
            div[data-baseweb="popover"] li:hover {
                background: #1A2744 !important;
            }

            /* Tag chips inside multiselect */
            [data-baseweb="tag"] {
                background-color: rgba(108,99,255,0.2) !important;
                color: #A5B4FC !important;
                border: 1px solid rgba(108,99,255,0.35) !important;
                border-radius: 6px !important;
            }
            [data-baseweb="tag"] span { color: #A5B4FC !important; }

            /* ===== RADIO BUTTONS ===== */
            [data-testid="stRadio"] label span,
            [data-testid="stRadio"] label p {
                color: #CBD5E1 !important; font-weight: 500;
            }

            /* ===== SELECTBOX ===== */
            [data-testid="stSelectbox"] > div > div {
                background: #0F1A2E !important; color: #F1F5F9 !important;
                border-color: #253552 !important; border-radius: 10px !important;
            }
            [data-testid="stSelectbox"] svg { fill: #8896AB !important; }

            /* ===== WIDGET LABELS ===== */
            .stSelectbox label, .stMultiSelect label, .stTextInput label,
            .stRadio > label {
                color: #8896AB !important; font-weight: 600 !important;
                font-size: 0.85rem !important;
            }

            /* ===== DIVIDER ===== */
            hr { border-color: #1E2D45 !important; opacity: 0.8; }

            /* ===== LINKS ===== */
            a { color: #818CF8 !important; text-decoration: none !important; }
            a:hover { color: #A5B4FC !important; text-decoration: underline !important; }

            /* ===== INFO ALERT ===== */
            [data-testid="stAlert"] {
                background: #1A2744 !important; color: #A5B4FC !important;
                border: 1px solid #253552 !important; border-radius: 10px !important;
            }
            [data-testid="stAlert"] p { color: #A5B4FC !important; }

            /* ===== EMPTY STATE ===== */
            .empty-state {
                text-align: center; padding: 60px 20px;
                background: #131D2F; border-radius: 16px;
                border: 2px dashed #1E2D45;
            }
            .empty-state h3 { color: #8896AB !important; font-weight: 700; }
            .empty-state p { color: #5A6B83 !important; }

            /* ===== TIP BOX ===== */
            .tip-box {
                background: rgba(108,99,255,0.08); border: 1px solid rgba(108,99,255,0.25);
                border-radius: 10px; padding: 12px 18px;
                font-size: 0.84rem; color: #A5B4FC !important;
                margin-bottom: 16px;
            }
            .tip-box span, .tip-box strong { color: #A5B4FC !important; }

            /* ===== FOOTER ===== */
            .footer-text {
                text-align: center; font-size: 0.78rem; color: #5A6B83 !important;
                padding: 16px 0 8px;
            }

            /* ===== SCROLLBAR ===== */
            ::-webkit-scrollbar { width: 8px; height: 8px; }
            ::-webkit-scrollbar-track { background: #0B1120; }
            ::-webkit-scrollbar-thumb { background: #253552; border-radius: 4px; }
            ::-webkit-scrollbar-thumb:hover { background: #344868; }
        </style>
        """, unsafe_allow_html=True)


        # ─────────────────────────── LOAD DATA ────────────────────────
        SHAREPOINT_URL = "https://globaledulinkuk-my.sharepoint.com/:x:/g/personal/sadeev_imperiallearning_co_uk/IQC_Trx-ci8SSozWqvstwuKwATXY7Xl96n-kik3FIVmhdRo?download=1"
        LOCAL_FILE_PATH = "TextBook.xlsx"
        AUTO_REFRESH_INTERVAL = 300


        @st.cache_data(ttl=AUTO_REFRESH_INTERVAL)
        def load_from_sharepoint(url):
            try:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                return pd.read_excel(io.BytesIO(response.content), sheet_name="DashboardSheet"), "SharePoint"
            except Exception:
                return None, None


        @st.cache_data(ttl=AUTO_REFRESH_INTERVAL)
        def load_from_local(path):
            try:
                return pd.read_excel(path), "Local File"
            except Exception:
                return None, None


        def load_data():
            df, source = load_from_sharepoint(SHAREPOINT_URL)
            if df is None:
                df, source = load_from_local(LOCAL_FILE_PATH)
            if df is None:
                st.error("Failed to load data from both SharePoint and local file.")
                st.stop()

            df.columns = ["Course Name", "Course Link", "Units", "Pages",
                           "Estimation", "Cost to Print", "Price", "Status"]
            df.drop(columns=["Estimation"], inplace=True)

            df["Cost to Print"] = (
                df["Cost to Print"].astype(str)
                .str.replace("£", "", regex=False)
                .str.replace(",", "", regex=False)
                .str.strip()
            )
            df["Cost to Print"] = pd.to_numeric(df["Cost to Print"], errors="coerce")

            def map_status(s):
                if pd.isna(s) or str(s).strip() in ("", "None"):
                    return "No Textbook"
                s = str(s).strip()
                if s in ("Completed", "Done"):
                    return "Textbook Ready"
                return "In Progress"

            df["Textbook Status"] = df["Status"].apply(map_status)
            df["Level"] = df["Course Name"].apply(
                lambda x: int(m.group(1)) if (m := re.search(r"Level (\d+)", str(x))) else None
            )

            def get_type(name):
                name = str(name)
                for t in ["Extended Diploma", "Diploma", "Certificate", "Award"]:
                    if t in name:
                        return t
                return "Other"

            df["Qualification"] = df["Course Name"].apply(get_type)
            return df, source


        df, data_source = load_data()


        # ─────────────────────────── HELPERS ──────────────────────────
        def status_pill(status):
            cls = {"Textbook Ready": "pill-ready", "No Textbook": "pill-none",
                   "In Progress": "pill-progress"}.get(status, "pill-none")
            return f'<span class="pill {cls}">{status}</span>'

        def fmt_currency(v):
            return "—" if pd.isna(v) else f"£{v:,.2f}"

        def fmt_int(v):
            return "—" if pd.isna(v) else f"{int(v):,}"


        # ── Chart colour palette ──
        COLOR_MAP = {
            "Textbook Ready": "#34D399",   # emerald
            "No Textbook":    "#FB923C",   # orange
            "In Progress":    "#818CF8",   # soft indigo
        }
        CHART_LAYOUT = dict(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Source Sans Pro, sans-serif", color="#CBD5E1", size=13),
            margin=dict(l=30, r=30, t=20, b=50),
        )


        # ─────────────────────────── HEADER ───────────────────────────
        st.markdown("""
        <div class="dash-header">
            <h1>📚 Textbook Production Tracker</h1>
            <p>South London College — Course Textbook Status Dashboard</p>
        </div>
        """, unsafe_allow_html=True)


        # ─────────────────────────── TABS ─────────────────────────────
        tab_overview, tab_explorer, tab_details = st.tabs([
            "📊  Executive Overview",
            "🔍  Course Explorer",
            "📋  Course Details",
        ])


        # ═══════════════════ TAB 1 : EXECUTIVE OVERVIEW ═══════════════
        with tab_overview:

            total   = len(df)
            ready   = len(df[df["Textbook Status"] == "Textbook Ready"])
            pending = len(df[df["Textbook Status"] == "No Textbook"])
            in_prog = len(df[df["Textbook Status"] == "In Progress"])
            pct     = (ready / total * 100) if total else 0

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Total Courses", total)
            c2.metric("Textbook Ready ✅", ready)
            c3.metric("No Textbook ⚠️", pending)
            c4.metric("In Progress 🔄", in_prog)
            c5.metric("Completion Rate", f"{pct:.1f}%")

            st.markdown("")

            # ── Charts row ──
            col_l, col_r = st.columns([1.15, 1])

            with col_l:
                st.markdown(
                    '<div class="section-hdr">'
                    '<span class="icon" style="background:rgba(108,99,255,0.15);">📊</span>'
                    '<span style="color:#F1F5F9 !important;">Textbook Status by Course Level</span></div>',
                    unsafe_allow_html=True,
                )
                level_df = (
                    df.dropna(subset=["Level"])
                    .groupby(["Level", "Textbook Status"]).size()
                    .reset_index(name="Count")
                )
                level_df["Level"] = level_df["Level"].astype(int)
                level_df = level_df.sort_values("Level")
                level_df["Level Label"] = "Level " + level_df["Level"].astype(str)

                level_order = [f"Level {i}" for i in sorted(level_df["Level"].unique())]

                fig1 = px.bar(
                    level_df, x="Level Label", y="Count", color="Textbook Status",
                    color_discrete_map=COLOR_MAP, barmode="stack",
                    labels={"Level Label": "Course Level", "Count": "Courses"},
                    category_orders={"Level Label": level_order, "Textbook Status": ["Textbook Ready", "In Progress", "No Textbook"]},
                )
                fig1.update_layout(
                    **CHART_LAYOUT, height=390,
                    legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center",
                                font=dict(size=12, color="#CBD5E1")),
                    xaxis=dict(showgrid=False, color="#8896AB", tickfont=dict(color="#8896AB")),
                    yaxis=dict(gridcolor="#1E2D45", gridwidth=1, color="#8896AB",
                               tickfont=dict(color="#8896AB")),
                )
                fig1.update_traces(
                    marker_line_width=0, marker_cornerradius=6,
                    hovertemplate="<b>%{x}</b><br>%{data.name}: %{y} courses<extra></extra>",
                )
                st.plotly_chart(fig1, use_container_width=True)

            with col_r:
                st.markdown(
                    '<div class="section-hdr">'
                    '<span class="icon" style="background:rgba(52,211,153,0.15);">🎯</span>'
                    '<span style="color:#F1F5F9 !important;">Overall Textbook Coverage</span></div>',
                    unsafe_allow_html=True,
                )
                pie_df = df["Textbook Status"].value_counts().reset_index()
                pie_df.columns = ["Status", "Count"]

                fig2 = go.Figure(go.Pie(
                    labels=pie_df["Status"], values=pie_df["Count"],
                    hole=0.6,
                    marker=dict(
                        colors=[COLOR_MAP.get(s, "#5A6B83") for s in pie_df["Status"]],
                        line=dict(color="#0B1120", width=3),
                    ),
                    textinfo="label+value",
                    textfont=dict(size=13, color="#F1F5F9"),
                    hovertemplate="<b>%{label}</b><br>%{value} courses (%{percent})<extra></extra>",
                ))
                fig2.update_layout(
                    **CHART_LAYOUT, height=390, showlegend=False,
                    annotations=[dict(
                        text=f"<b style='font-size:34px;color:#F1F5F9'>{pct:.0f}%</b>"
                             f"<br><span style='font-size:12px;color:#8896AB'>Complete</span>",
                        x=0.5, y=0.5, font_size=16, showarrow=False,
                    )],
                )
                st.plotly_chart(fig2, use_container_width=True)

            # ── Qualification breakdown ──
            st.markdown(
                '<div class="section-hdr">'
                '<span class="icon" style="background:rgba(251,191,36,0.15);">🎓</span>'
                '<span style="color:#F1F5F9 !important;">Textbook Status by Qualification Type</span></div>',
                unsafe_allow_html=True,
            )
            qual_df = (
                df.groupby(["Qualification", "Textbook Status"])
                .size().reset_index(name="Count")
            )
            fig3 = px.bar(
                qual_df, x="Qualification", y="Count", color="Textbook Status",
                color_discrete_map=COLOR_MAP, barmode="group",
                labels={"Count": "Courses"},
                category_orders={"Textbook Status": ["Textbook Ready", "In Progress", "No Textbook"]},
            )
            fig3.update_layout(
                **CHART_LAYOUT, height=350,
                legend=dict(orientation="h", y=-0.22, x=0.5, xanchor="center",
                            font=dict(size=12, color="#CBD5E1")),
                xaxis=dict(showgrid=False, color="#8896AB", tickfont=dict(color="#8896AB")),
                yaxis=dict(gridcolor="#1E2D45", gridwidth=1, color="#8896AB",
                           tickfont=dict(color="#8896AB")),
            )
            fig3.update_traces(
                marker_line_width=0, marker_cornerradius=6,
                hovertemplate="<b>%{x}</b><br>%{data.name}: %{y} courses<extra></extra>",
            )
            st.plotly_chart(fig3, use_container_width=True)


        # ═══════════════════ TAB 2 : COURSE EXPLORER ══════════════════
        with tab_explorer:

            st.markdown(
                '<div class="section-hdr">'
                '<span class="icon" style="background:rgba(108,99,255,0.15);">🔎</span>'
                '<span style="color:#F1F5F9 !important;">Filter Courses</span></div>',
                unsafe_allow_html=True,
            )

            fc1, fc2, fc3, fc4 = st.columns([1.5, 1, 1, 1])
            with fc1:
                search = st.text_input("Search course name", "", placeholder="Type to search…")
            with fc2:
                status_opts = ["All", "Textbook Ready", "No Textbook", "In Progress"]
                status_filter = st.selectbox("Textbook Status", options=status_opts, index=0)
            with fc3:
                lvl_vals = sorted(df["Level"].dropna().unique().astype(int).tolist())
                lvl_opts = ["All"] + [f"Level {l}" for l in lvl_vals]
                level_filter = st.selectbox("Course Level", options=lvl_opts, index=0)
            with fc4:
                qual_vals = sorted(df["Qualification"].unique().tolist())
                qual_opts = ["All"] + qual_vals
                qual_filter = st.selectbox("Qualification Type", options=qual_opts, index=0)

            # Apply filters
            filtered = df.copy()
            if search:
                filtered = filtered[filtered["Course Name"].str.contains(search, case=False, na=False)]
            if status_filter != "All":
                filtered = filtered[filtered["Textbook Status"] == status_filter]
            if level_filter != "All":
                sel_level = int(level_filter.replace("Level ", ""))
                filtered = filtered[filtered["Level"] == sel_level]
            if qual_filter != "All":
                filtered = filtered[filtered["Qualification"] == qual_filter]

            st.markdown("")
            sc1, sc2, sc3, sc4 = st.columns(4)
            sc1.metric("Showing", f"{len(filtered)} courses")
            sc2.metric("Ready ✅", f"{len(filtered[filtered['Textbook Status']=='Textbook Ready'])}")
            sc3.metric("No Textbook ⚠️", f"{len(filtered[filtered['Textbook Status']=='No Textbook'])}")
            sc4.metric("In Progress 🔄", f"{len(filtered[filtered['Textbook Status']=='In Progress'])}")

            st.markdown("")

            if filtered.empty:
                st.markdown(
        '<div class="empty-state">'
        '<h3>No courses match your filters</h3>'
        '<p>Try adjusting the filters above to see results.</p>'
        '</div>', unsafe_allow_html=True)
            else:
                st.markdown(
                    '<div class="tip-box">'
                    '<span>💡 <strong>Tip:</strong> Use the <strong>Course Details</strong> '
                    'tab to click into any course for full information.</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )

                display = filtered[[
                    "Course Name", "Qualification", "Level",
                    "Units", "Pages", "Cost to Print", "Price", "Textbook Status"
                ]].copy()
                display["Level"] = display["Level"].apply(lambda x: f"Level {int(x)}" if pd.notna(x) else "—")
                display["Units"] = display["Units"].apply(fmt_int)
                display["Pages"] = display["Pages"].apply(fmt_int)
                display["Cost to Print"] = display["Cost to Print"].apply(fmt_currency)
                display["Price"] = display["Price"].apply(fmt_currency)

                def color_status(val):
                    return {
                        "Textbook Ready": "background-color: rgba(52,211,153,0.15); color: #34D399; font-weight: 700;",
                        "No Textbook":    "background-color: rgba(251,191,36,0.15); color: #FBBF24; font-weight: 700;",
                        "In Progress":    "background-color: rgba(129,140,248,0.15); color: #A5B4FC; font-weight: 700;",
                    }.get(val, "")

                styled = (
                    display.reset_index(drop=True).style
                    .map(color_status, subset=["Textbook Status"])
                    .set_properties(**{"font-size": "0.85rem", "color": "#CBD5E1"})
                )
                st.dataframe(styled, use_container_width=True, height=520, hide_index=True)


        # ═══════════════════ TAB 3 : COURSE DETAILS ═══════════════════
        with tab_details:

            st.markdown(
                '<div class="section-hdr">'
                '<span class="icon" style="background:rgba(108,99,255,0.15);">📋</span>'
                '<span style="color:#F1F5F9 !important;">Select a Course for Detailed View</span></div>',
                unsafe_allow_html=True,
            )

            d1, d2 = st.columns([1, 2])
            with d1:
                detail_status = st.radio(
                    "Quick filter",
                    ["All", "Textbook Ready", "No Textbook", "In Progress"],
                    horizontal=True,
                )
            detail_df = df if detail_status == "All" else df[df["Textbook Status"] == detail_status]

            with d2:
                names = detail_df["Course Name"].tolist()
                selected = st.selectbox("Choose a course", options=names, index=0,
                                        placeholder="Start typing to search…") if names else None

            st.markdown("")

            if selected:
                row = df[df["Course Name"] == selected].iloc[0]

                # ── Course detail card ──
                level_display = int(row["Level"]) if pd.notna(row["Level"]) else "—"
                detail_html = f"""<div class="detail-card">
        <div class="detail-title">{row["Course Name"]}</div>
        <div class="detail-tags">
        {status_pill(row["Textbook Status"])}
        <span class="tag">🎓 {row["Qualification"]}</span>
        <span class="tag">📘 Level {level_display}</span>
        </div>
        <div class="stat-grid">
        <div class="stat-box">
        <div class="stat-label">Number of Units</div>
        <div class="stat-value">{fmt_int(row["Units"])}</div>
        </div>
        <div class="stat-box">
        <div class="stat-label">Page Count</div>
        <div class="stat-value">{fmt_int(row["Pages"])}</div>
        </div>
        <div class="stat-box">
        <div class="stat-label">Cost to Print</div>
        <div class="stat-value">{fmt_currency(row["Cost to Print"])}</div>
        </div>
        <div class="stat-box">
        <div class="stat-label">Selling Price</div>
        <div class="stat-value">{fmt_currency(row["Price"])}</div>
        </div>
        <div class="stat-box">
        <div class="stat-label">Textbook Status</div>
        <div style="margin-top:6px;">{status_pill(row["Textbook Status"])}</div>
        </div>
        </div>"""
                st.markdown(detail_html, unsafe_allow_html=True)

                # close detail card div
                st.markdown("</div>", unsafe_allow_html=True)

                # ── Course link ──
                if pd.notna(row["Course Link"]):
                    st.markdown(f'🔗 **Course page:** [{row["Course Link"][:80]}…]({row["Course Link"]})')
            else:
                st.markdown(
        '<div class="empty-state">'
        '<h3>No courses available</h3>'
        '<p>Adjust the quick filter above to see courses.</p>'
        '</div>', unsafe_allow_html=True)


        # ─────────────────────────── FOOTER ───────────────────────────
        st.markdown("---")
        st.markdown(
            '<p class="footer-text">'
            '📚 Textbook Tracker Dashboard · South London College · Data Source: ' + data_source + ' · Auto-refreshes every 5 minutes'
            '</p>',
            unsafe_allow_html=True,
        )

# Page config is handled by the outer app when imported.

if __name__ == "__main__":
    st.set_page_config(
        page_title="Textbook Tracker – South London College",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    render_textbook_progress()
