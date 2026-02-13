# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import requests
# from io import BytesIO

# # --- PAGE CONFIGURATION ---
# st.set_page_config(page_title="Course Content Tracker", layout="wide")

# # --- DATA LOADING FUNCTION ---
# @st.cache_data(ttl=600)
# def load_data(url):
#     try:
#         # 1. We use requests to get the file content first
#         # This allows us to "pretend" to be a browser if needed
#         response = requests.get(url)
        
#         # Check if the request was successful
#         if response.status_code != 200:
#             st.error(f"⚠️ Connection Failed. Status Code: {response.status_code}")
#             return None
            
#         # 2. Convert the content into a format pandas can read
#         file_content = BytesIO(response.content)
        
#         # 3. Load Excel
#         df = pd.read_excel(file_content, engine='openpyxl')
        
#         # Clean Column Names
#         df.columns = df.columns.str.strip()
        
#         # Ensure numeric columns are actually numbers
#         cols_to_clean = ['Number of Units', 'Number of AI Videos', 'Number of Podcasts', 'Number of Study Guides']
        
#         # Check if columns exist
#         missing_cols = [c for c in cols_to_clean if c not in df.columns]
#         if missing_cols:
#             st.error(f"⚠️ Error: The file is missing these columns: {missing_cols}")
#             return None

#         for col in cols_to_clean:
#             df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

#         # Filter out inactive courses
#         active_df = df[df['Number of Units'] > 0].copy()
#         return active_df
        
#     except Exception as e:
#         st.error(f"Debug Error: {e}")
#         return None

# # --- MAIN APP LOGIC ---

# st.title("📊 Course Content Production Dashboard")

# # THE KEY CHANGE: Using the direct share link with '?download=1' appended
# sharepoint_url = "https://globaledulinkuk-my.sharepoint.com/:x:/g/personal/malinda_imperiallearning_co_uk/IQBJWtESoY7aS4mrdvmQQ6SUAdELVAXa5QmZs2O_W7U1qmo?download=1"

# # Load the data
# df = load_data(sharepoint_url)

# # IF AUTOMATIC FAILS, SHOW UPLOADER
# if df is None:
#     st.warning("⚠️ **Automatic Update Failed.** Your company security is blocking the direct link.")
#     st.info("👇 **Solution:** Please download the file and drag it here.")
    
#     uploaded_file = st.file_uploader("Upload 'Additional Material Tracker Sheet.xlsx'", type=['xlsx'])
    
#     if uploaded_file is not None:
#         # Load the uploaded file directly
#         df = pd.read_excel(uploaded_file, engine='openpyxl')
#         # ... (Same cleaning logic as above) ...
#         df.columns = df.columns.str.strip()
#         cols = ['Number of Units', 'Number of AI Videos', 'Number of Podcasts', 'Number of Study Guides']
#         for col in cols:
#             df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
#         df = df[df['Number of Units'] > 0].copy()
#     else:
#         st.stop() 

# # --- DASHBOARD METRICS ---

# st.markdown("### Managerial Overview")

# if st.button("🔄 Refresh Data"):
#     st.cache_data.clear()
#     st.rerun()

# # Metrics Calculations
# total_units = df['Number of Units'].sum()
# total_assets_target = total_units * 3 
# total_completed = df['Number of AI Videos'].sum() + df['Number of Podcasts'].sum() + df['Number of Study Guides'].sum()

# completion_rate = (total_completed / total_assets_target) * 100 if total_assets_target > 0 else 0

# # KPI ROW
# k1, k2, k3, k4 = st.columns(4)
# k1.metric("Overall Completion", f"{completion_rate:.1f}%", delta=f"{100-completion_rate:.1f}% Remaining")
# k2.metric("Total Assets Done", int(total_completed))
# k3.metric("Target Assets", int(total_assets_target))
# k4.metric("Not Started", len(df[(df['Number of AI Videos']==0) & (df['Number of Podcasts']==0) & (df['Number of Study Guides']==0)]), delta_color="inverse")

# st.markdown("---")

# # Bottleneck Analysis
# c1, c2 = st.columns([2, 1])

# with c1:
#     st.subheader("⚠️ Production Bottlenecks")
    
#     v_comp = (df['Number of AI Videos'].sum() / total_units * 100) if total_units else 0
#     p_comp = (df['Number of Podcasts'].sum() / total_units * 100) if total_units else 0
#     g_comp = (df['Number of Study Guides'].sum() / total_units * 100) if total_units else 0
    
#     bn_data = pd.DataFrame({
#         'Type': ['AI Videos', 'Podcasts', 'Study Guides'],
#         'Completion': [v_comp, p_comp, g_comp]
#     })
    
#     fig = px.bar(bn_data, x='Type', y='Completion', text='Completion', 
#                  color='Type', color_discrete_sequence=['#FF4B4B', '#FFA15A', '#00CC96'])
#     fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
#     fig.add_hline(y=100, line_dash="dot", annotation_text="Target")
#     st.plotly_chart(fig, use_container_width=True)

# with c2:
#     st.subheader("🔍 Insights")
#     gap = total_assets_target - total_completed
#     st.warning(f"**The Gap:** You need to produce **{int(gap)}** more assets to finish.")
    
#     metrics = {'AI Videos': v_comp, 'Podcasts': p_comp, 'Study Guides': g_comp}
#     slowest = min(metrics, key=metrics.get)
#     st.error(f"**Primary Bottleneck:** {slowest} ({metrics[slowest]:.1f}% complete).")

# # Risk Table
# st.subheader("📋 Priority Watchlist (High Effort / Low Progress)")
# df['Progress'] = ((df['Number of AI Videos'] + df['Number of Podcasts'] + df['Number of Study Guides']) / (df['Number of Units'] * 3)) * 100
# df['Risk_Score'] = df['Number of Units'] * (100 - df['Progress'])

# risk_df = df.sort_values('Risk_Score', ascending=False)[['Course Name', 'Number of Units', 'Progress', 'Number of AI Videos', 'Number of Podcasts', 'Number of Study Guides']]

# st.dataframe(
#     risk_df,
#     column_config={"Progress": st.column_config.ProgressColumn("Completion %", format="%.1f%%", min_value=0, max_value=100)},
#     hide_index=True,
#     use_container_width=True
# )










# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import requests
# import re
# from io import BytesIO

# # --- PAGE CONFIGURATION ---
# st.set_page_config(page_title="Course Content Tracker", layout="wide")

# # --- DATA LOADING FUNCTION ---
# @st.cache_data(ttl=600)
# def load_data(url):
#     try:
#         if isinstance(url, str) and url.startswith("http"):
#             response = requests.get(url)
#             if response.status_code != 200:
#                 return None
#             file_content = BytesIO(response.content)
#         else:
#             file_content = url

#         df = pd.read_excel(file_content, engine='openpyxl')
#         df.columns = df.columns.str.strip()
        
#         cols_to_clean = ['Number of Units', 'Number of AI Videos', 'Number of Podcasts', 'Number of Study Guides']
        
#         if any(c not in df.columns for c in cols_to_clean):
#             return None

#         for col in cols_to_clean:
#             df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

#         active_df = df[df['Number of Units'] > 0].copy()
#         return active_df
        
#     except Exception as e:
#         return None

# # --- MAIN APP LOGIC ---

# st.title("📊 Course Content Production Dashboard")

# # THE KEY: Glossary of Terms
# with st.expander("📖 Dashboard Dictionary (Click to view definitions)"):
#     st.markdown("""
#     * **Asset:** A single piece of content. We assume 1 Unit requires 3 Assets (1 Video, 1 Podcast, 1 Study Guide).
#     * **Production Bottleneck:** The specific type of content (Videos, Podcasts, or Guides) that has the lowest completion rate and is holding up overall delivery.
#     * **The Gap:** The exact number of individual assets still missing to reach 100% completion across all active courses.
#     * **Risk Score (Priority Watchlist):** A calculation of `Course Size (Units) × Amount Incomplete`. A high risk score means a massive course has very little progress, making it a critical threat to deadlines.
#     * **Quick Wins:** Courses that are over 75% complete but not yet 100%. These require minimal effort to finish completely.
#     """)

# sharepoint_url = "https://globaledulinkuk-my.sharepoint.com/:x:/g/personal/malinda_imperiallearning_co_uk/IQBJWtESoY7aS4mrdvmQQ6SUAdELVAXa5QmZs2O_W7U1qmo?download=1"

# df = load_data(sharepoint_url)

# if df is None:
#     st.warning("⚠️ **Automatic Update Failed.** Company security is blocking the direct link.")
#     st.info("👇 **Solution:** Download the file and drag it here.")
#     uploaded_file = st.file_uploader("Upload 'Additional Material Tracker Sheet.xlsx'", type=['xlsx'])
#     if uploaded_file is not None:
#         df = load_data(uploaded_file)
#     else:
#         st.stop() 

# # --- DATA ENGINEERING (NEW HIDDEN METRICS) ---

# # Calculate Base Progress
# df['Total_Target'] = df['Number of Units'] * 3
# df['Total_Actual'] = df['Number of AI Videos'] + df['Number of Podcasts'] + df['Number of Study Guides']
# df['Progress'] = (df['Total_Actual'] / df['Total_Target']) * 100
# df['Risk_Score'] = df['Number of Units'] * (100 - df['Progress'])

# # Extract Course Level (e.g., Level 3, Level 4)
# df['Course Level'] = df['Course Name'].str.extract(r'(Level \d+)', expand=False).fillna('Unspecified')

# # Categorise by Subject Area based on keywords in title
# def categorise_subject(title):
#     title = str(title).lower()
#     if any(word in title for word in ['business', 'management', 'accounting', 'finance']):
#         return 'Business & Management'
#     elif any(word in title for word in ['computing', 'cyber', 'web', 'software', 'data', 'ai', 'artificial']):
#         return 'Computing & IT'
#     elif any(word in title for word in ['health', 'care', 'nutrition', 'dementia', 'safeguarding']):
#         return 'Health & Social Care'
#     elif any(word in title for word in ['teaching', 'education', 'child', 'assessing']):
#         return 'Education & Teaching'
#     elif 'law' in title:
#         return 'Law'
#     else:
#         return 'Other/General'

# df['Subject Area'] = df['Course Name'].apply(categorise_subject)

# # --- DASHBOARD METRICS ---

# st.markdown("### Managerial Overview")

# if st.button("🔄 Refresh Data"):
#     st.cache_data.clear()
#     st.rerun()

# total_units = df['Number of Units'].sum()
# total_assets_target = df['Total_Target'].sum()
# total_completed = df['Total_Actual'].sum()
# completion_rate = (total_completed / total_assets_target) * 100 if total_assets_target > 0 else 0

# # KPI ROW
# k1, k2, k3, k4 = st.columns(4)
# k1.metric("Overall Completion", f"{completion_rate:.1f}%", delta=f"{100-completion_rate:.1f}% Remaining")
# k2.metric("Total Assets Done", int(total_completed))
# k3.metric("Target Assets", int(total_assets_target))
# k4.metric("Not Started", len(df[df['Total_Actual'] == 0]), delta_color="inverse")

# st.markdown("---")

# # --- NEW SECTION: ADVANCED INSIGHTS ---
# st.markdown("### 📈 Advanced Portfolio Insights")

# tab1, tab2, tab3 = st.tabs(["Performance by Subject", "Performance by Level", "🎯 Quick Wins"])

# with tab1:
#     # Aggregating progress by subject
#     subject_df = df.groupby('Subject Area').agg(
#         Total_Units=('Number of Units', 'sum'),
#         Progress=('Progress', 'mean')
#     ).reset_index().sort_values(by='Progress', ascending=False)
    
#     fig_sub = px.bar(subject_df, x='Progress', y='Subject Area', orientation='h', 
#                      text='Progress', color='Progress', color_continuous_scale='Viridis',
#                      title="Average Completion % by Department")
#     fig_sub.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
#     fig_sub.update_layout(coloraxis_showscale=False)
#     st.plotly_chart(fig_sub, use_container_width=True)

# with tab2:
#     level_df = df.groupby('Course Level').agg(
#         Courses=('Course Name', 'count'),
#         Progress=('Progress', 'mean')
#     ).reset_index().sort_values(by='Course Level')
    
#     fig_lvl = px.bar(level_df, x='Course Level', y='Progress', 
#                      text='Progress', color='Course Level',
#                      title="Average Completion % by Academic Level")
#     fig_lvl.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
#     st.plotly_chart(fig_lvl, use_container_width=True)

# with tab3:
#     st.write("Courses between 75% and 99% complete. Focus resources here to close these out quickly.")
#     quick_wins = df[(df['Progress'] >= 75) & (df['Progress'] < 100)].sort_values(by='Progress', ascending=False)
    
#     if not quick_wins.empty:
#         st.dataframe(
#             quick_wins[['Course Name', 'Subject Area', 'Progress', 'Number of AI Videos', 'Number of Podcasts', 'Number of Study Guides']],
#             column_config={"Progress": st.column_config.ProgressColumn("Completion %", format="%.1f%%", min_value=0, max_value=100)},
#             hide_index=True, use_container_width=True
#         )
#     else:
#         st.info("No courses currently sit in the 75%-99% Quick Win bracket.")

# st.markdown("---")

# # --- ORIGINAL BOTTLENECK ANALYSIS ---
# c1, c2 = st.columns([2, 1])

# with c1:
#     st.subheader("⚠️ Production Bottlenecks")
    
#     v_comp = (df['Number of AI Videos'].sum() / total_units * 100) if total_units else 0
#     p_comp = (df['Number of Podcasts'].sum() / total_units * 100) if total_units else 0
#     g_comp = (df['Number of Study Guides'].sum() / total_units * 100) if total_units else 0
    
#     bn_data = pd.DataFrame({
#         'Type': ['AI Videos', 'Podcasts', 'Study Guides'],
#         'Completion': [v_comp, p_comp, g_comp]
#     })
    
#     fig = px.bar(bn_data, x='Type', y='Completion', text='Completion', 
#                  color='Type', color_discrete_sequence=['#FF4B4B', '#FFA15A', '#00CC96'])
#     fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
#     fig.add_hline(y=100, line_dash="dot", annotation_text="Target")
#     st.plotly_chart(fig, use_container_width=True)

# with c2:
#     st.subheader("🔍 Insights")
#     gap = total_assets_target - total_completed
#     st.warning(f"**The Gap:** You need to produce **{int(gap)}** more assets to finish.")
    
#     metrics = {'AI Videos': v_comp, 'Podcasts': p_comp, 'Study Guides': g_comp}
#     slowest = min(metrics, key=metrics.get)
#     st.error(f"**Primary Bottleneck:** {slowest} ({metrics[slowest]:.1f}% complete).")

# st.markdown("---")

# # --- RISK TABLE ---
# st.subheader("📋 Priority Watchlist (High Effort / Low Progress)")

# risk_df = df.sort_values('Risk_Score', ascending=False)[['Course Name', 'Course Level', 'Subject Area', 'Number of Units', 'Progress', 'Risk_Score']]

# st.dataframe(
#     risk_df.drop(columns=['Risk_Score']),
#     column_config={"Progress": st.column_config.ProgressColumn("Completion %", format="%.1f%%", min_value=0, max_value=100)},
#     hide_index=True,
#     use_container_width=True
# )


import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import re
from io import BytesIO

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Course Content Tracker", layout="wide")

# --- DATA LOADING FUNCTION ---
@st.cache_data(ttl=600)
def load_data(url):
    try:
        if isinstance(url, str) and url.startswith("http"):
            response = requests.get(url)
            if response.status_code != 200:
                return None
            file_content = BytesIO(response.content)
        else:
            file_content = url

        df = pd.read_excel(file_content, engine='openpyxl')
        df.columns = df.columns.str.strip()
        
        cols_to_clean = ['Number of Units', 'Number of AI Videos', 'Number of Podcasts', 'Number of Study Guides']
        
        if any(c not in df.columns for c in cols_to_clean):
            return None

        for col in cols_to_clean:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        active_df = df[df['Number of Units'] > 0].copy()
        return active_df
        
    except Exception as e:
        return None

# --- MAIN APP LOGIC ---

st.title("📊 Course Content Production Dashboard")

# THE KEY: Glossary of Terms
with st.expander("📖 Dashboard Dictionary (Click to view definitions)"):
    st.markdown("""
    * **Asset:** A single piece of content. We assume 1 Unit requires 3 Assets (1 Video, 1 Podcast, 1 Study Guide).
    * **Production Bottleneck:** The specific type of content (Videos, Podcasts, or Guides) that has the lowest completion rate and is holding up overall delivery.
    * **The Gap:** The exact number of individual assets still missing to reach 100% completion across all active courses.
    * **Risk Score (Priority Watchlist):** A calculation of `Course Size (Units) × Amount Incomplete`. A high risk score means a massive course has very little progress, making it a critical threat to deadlines.
    * **Quick Wins:** Courses that are over 75% complete but not yet 100%. These require minimal effort to finish completely.
    """)

sharepoint_url = "https://globaledulinkuk-my.sharepoint.com/:x:/g/personal/malinda_imperiallearning_co_uk/IQBJWtESoY7aS4mrdvmQQ6SUAdELVAXa5QmZs2O_W7U1qmo?download=1"

df = load_data(sharepoint_url)

if df is None:
    st.warning("⚠️ **Automatic Update Failed.** Company security is blocking the direct link.")
    st.info("👇 **Solution:** Download the file and drag it here.")
    uploaded_file = st.file_uploader("Upload 'Additional Material Tracker Sheet.xlsx'", type=['xlsx'])
    if uploaded_file is not None:
        df = load_data(uploaded_file)
    else:
        st.stop() 

# --- DATA ENGINEERING (NEW HIDDEN METRICS) ---

# Calculate Base Progress
df['Total_Target'] = df['Number of Units'] * 3
df['Total_Actual'] = df['Number of AI Videos'] + df['Number of Podcasts'] + df['Number of Study Guides']
df['Progress'] = (df['Total_Actual'] / df['Total_Target']) * 100
df['Risk_Score'] = df['Number of Units'] * (100 - df['Progress'])

# Extract Course Level (e.g., Level 3, Level 4)
df['Course Level'] = df['Course Name'].str.extract(r'(Level \d+)', expand=False).fillna('Unspecified')

# Categorise by Subject Area based on keywords in title
def categorise_subject(title):
    title = str(title).lower()
    if any(word in title for word in ['business', 'management', 'accounting', 'finance']):
        return 'Business & Management'
    elif any(word in title for word in ['computing', 'cyber', 'web', 'software', 'data', 'ai', 'artificial']):
        return 'Computing & IT'
    elif any(word in title for word in ['health', 'care', 'nutrition', 'dementia', 'safeguarding']):
        return 'Health & Social Care'
    elif any(word in title for word in ['teaching', 'education', 'child', 'assessing']):
        return 'Education & Teaching'
    elif 'law' in title:
        return 'Law'
    else:
        return 'Other/General'

df['Subject Area'] = df['Course Name'].apply(categorise_subject)

# --- DASHBOARD METRICS ---

st.markdown("### Managerial Overview")

if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

total_units = df['Number of Units'].sum()
total_assets_target = df['Total_Target'].sum()
total_completed = df['Total_Actual'].sum()
completion_rate = (total_completed / total_assets_target) * 100 if total_assets_target > 0 else 0

# KPI ROW
k1, k2, k3, k4 = st.columns(4)
k1.metric("Overall Completion", f"{completion_rate:.1f}%", delta=f"{100-completion_rate:.1f}% Remaining")
k2.metric("Total Assets Done", int(total_completed))
k3.metric("Target Assets", int(total_assets_target))
k4.metric("Units Not Started", len(df[df['Total_Actual'] == 0]), delta_color="inverse")

st.markdown("---")

# --- NEW SECTION: ADVANCED INSIGHTS ---
st.markdown("### 📈 Advanced Portfolio Insights")

tab1, tab2, tab3 = st.tabs(["Performance by Subject", "Performance by Level", "🎯 Quick Wins"])

with tab1:
    # Aggregating progress by subject
    subject_df = df.groupby('Subject Area').agg(
        Total_Units=('Number of Units', 'sum'),
        Progress=('Progress', 'mean')
    ).reset_index().sort_values(by='Progress', ascending=False)
    
    # Filter out 'Other/General'
    subject_df = subject_df[subject_df['Subject Area'] != 'Other/General']
    
    fig_sub = px.bar(subject_df, x='Progress', y='Subject Area', orientation='h', 
                     text='Progress', color='Progress', color_continuous_scale='Viridis',
                     title="Average Completion % by Subject")
    fig_sub.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig_sub.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig_sub, use_container_width=True)

with tab2:
    level_df = df.groupby('Course Level').agg(
        Courses=('Course Name', 'count'),
        Progress=('Progress', 'mean')
    ).reset_index().sort_values(by='Course Level')
    
    # Filter out 'Unspecified'
    level_df = level_df[level_df['Course Level'] != 'Unspecified']
    
    fig_lvl = px.bar(level_df, x='Course Level', y='Progress', 
                     text='Progress', color='Course Level',
                     title="Average Completion % by Academic Level")
    fig_lvl.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    st.plotly_chart(fig_lvl, use_container_width=True)

with tab3:
    st.write("Courses between 75% and 99% complete. Focus resources here to close these out quickly.")
    quick_wins = df[(df['Progress'] >= 75) & (df['Progress'] < 100)].sort_values(by='Progress', ascending=False)
    
    if not quick_wins.empty:
        st.dataframe(
            quick_wins[['Course Name', 'Subject Area', 'Progress', 'Number of AI Videos', 'Number of Podcasts', 'Number of Study Guides']],
            column_config={"Progress": st.column_config.ProgressColumn("Completion %", format="%.1f%%", min_value=0, max_value=100)},
            hide_index=True, use_container_width=True
        )
    else:
        st.info("No courses currently sit in the 75%-99% Quick Win bracket.")

st.markdown("---")

# --- ORIGINAL BOTTLENECK ANALYSIS ---
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("⚠️ Production Bottlenecks")
    
    v_comp = (df['Number of AI Videos'].sum() / total_units * 100) if total_units else 0
    p_comp = (df['Number of Podcasts'].sum() / total_units * 100) if total_units else 0
    g_comp = (df['Number of Study Guides'].sum() / total_units * 100) if total_units else 0
    
    bn_data = pd.DataFrame({
        'Type': ['AI Videos', 'Podcasts', 'Study Guides'],
        'Completion': [v_comp, p_comp, g_comp]
    })
    
    fig = px.bar(bn_data, x='Type', y='Completion', text='Completion', 
                 color='Type', color_discrete_sequence=['#FF4B4B', '#FFA15A', '#00CC96'])
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.add_hline(y=100, line_dash="dot", annotation_text="Target")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("🔍 Insights")
    gap = total_assets_target - total_completed
    st.warning(f"**The Gap:** You need to produce **{int(gap)}** more assets to finish.")
    
    metrics = {'AI Videos': v_comp, 'Podcasts': p_comp, 'Study Guides': g_comp}
    slowest = min(metrics, key=metrics.get)
    st.error(f"**Primary Bottleneck:** {slowest} ({metrics[slowest]:.1f}% complete).")

st.markdown("---")

# --- RISK TABLE ---
st.subheader("📋 Priority Watchlist (High Effort / Low Progress)")

risk_df = df.sort_values('Risk_Score', ascending=False)[['Course Name', 'Course Level', 'Subject Area', 'Number of Units', 'Progress', 'Risk_Score']]

st.dataframe(
    risk_df.drop(columns=['Risk_Score']),
    column_config={"Progress": st.column_config.ProgressColumn("Completion %", format="%.1f%%", min_value=0, max_value=100)},
    hide_index=True,
    use_container_width=True
)
