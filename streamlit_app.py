import streamlit as st
import pandas as pd
from datetime import date
import itertools

# ------------------------
# 1. Page Configuration
# ------------------------
st.set_page_config(page_title="Badger | Asset Matrix", page_icon="🦡", layout="wide")

st.markdown("""
<style>
    .stTextInput label, .stSelectbox label, .stMultiSelect label, .stDateInput label { font-weight: 600; }
    .main-header { font-size: 2.2rem; font-weight: 700; color: #FF4B4B; margin-bottom: 1rem; }
    .info-box { background-color: #f0f2f6; padding: 1rem; border-radius: 8px; border-left: 5px solid #FF4B4B; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

# ------------------------
# 2. Logic & Taxonomy Data
# ------------------------
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

# Mappings from screenshot tables
LOB_DATA = {
    "Consumer Wireless": {"client": "RCS", "product": "WLS"},
    "Connected Home": {"client": "RHE", "product": "IGN"},
    "Rogers Business": {"client": "RNS", "product": "BRA"},
    "Rogers Bank": {"client": "RBG", "product": "RBK"},
    "Corporate Brand": {"client": "RCP", "product": "RCB"},
    "Shaw Direct": {"client": "RSH", "product": "CBL"},
}

ASSET_PRESETS = {
    "Social": {"dur": ["6s", "15s"], "siz": ["1x1", "9x16Story", "9x16Reel"]},
    "Display": {"dur": ["Static"], "siz": ["300x250", "300x600", "728x90", "160x600", "970x250"]},
    "Video": {"dur": ["6s", "15s", "30s"], "siz": ["16x9", "9x16"]},
}

def fmt_date(d: date) -> str:
    return f"{MONTHS[d.month-1]}.{d.day:02d}.{d.year}"

def clean_val(s: str) -> str:
    """Enforces 'No Underscore' rule."""
    return (s or "").replace("_", " ").strip()

# ------------------------
# 3. State Management
# ------------------------
if "client_code" not in st.session_state: st.session_state.client_code = "RCS"
if "product_code" not in st.session_state: st.session_state.product_code = "WLS"
if "camp_title" not in st.session_state: st.session_state.camp_title = "Q1 Always On"

def sync_lob():
    data = LOB_DATA.get(st.session_state.lob_select)
    st.session_state.client_code = data["client"]
    st.session_state.product_code = data["product"]

# ------------------------
# 4. UI Layout
# ------------------------
st.markdown('<div class="main-header">🦡 Badger | 2026 Taxonomy</div>', unsafe_allow_html=True)

left, right = st.columns([1, 1.4], gap="medium")

with left:
    with st.container(border=True):
        st.markdown("### 📋 1. Identity")
        st.selectbox("Line of Business", options=list(LOB_DATA.keys()), key="lob_select", on_change=sync_lob)
        
        c1, c2 = st.columns(2)
        with c1: st.text_input("Client Code", key="client_code")
        with c2: st.text_input("Product Code", key="product_code")
        
        st.date_input("Start Date", value=date.today(), key="start_date")

    with st.container(border=True):
        st.markdown("### 🏗️ 2. Campaign Builder")
        # Automating the "Campaign Name" logic from the Messaging Guide
        st.text_input("Campaign Title (e.g. Q1 Promo)", key="camp_title")
        
        v1, v2, v3 = st.columns(3)
        with v1: funnels = st.multiselect("Funnel", ["COS", "AWR", "COV"], default=["COS"])
        with v2: regions = st.multiselect("Region", ["ATL", "ROC", "QC"], default=["ATL"])
        with v3: languages = st.multiselect("Language", ["EN", "FR"], default=["EN"])

    with st.container(border=True):
        st.markdown("### 🎨 3. Asset Specs")
        m_type = st.selectbox("Matrix Type", options=list(ASSET_PRESETS.keys()))
        
        durations = st.multiselect("Durations", ["Static", "6s", "15s", "30s"], default=ASSET_PRESETS[m_type]["dur"])
        sizes = st.multiselect("Sizes", ["1x1", "9x16", "16x9", "9x16Story", "9x16Reel", "300x250", "300x600"], default=ASSET_PRESETS[m_type]["siz"])
        
        st.text_area("Messaging (one per line)", value="Bundle Offer V1", key="msg_input")

# ------------------------
# 5. Generation Logic
# ------------------------
if st.button("Generate Matrix", type="primary", use_container_width=True):
    messages = [m.strip() for m in st.session_state.msg_input.splitlines() if m.strip()]
    
    # Cartesian product of all selections
    combos = itertools.product(funnels, regions, languages, messages, durations, sizes)
    rows = []
    
    for f, r, l, m, d, s in combos:
        # Build the structured Campaign Name: Title-Funnel-Region-Lang
        full_camp_name = f"{st.session_state.camp_title}-{f}-{r}-{l}"
        
        # Taxonomy: Year_Client_Prod_Lang_Camp_Msg_Size_Date_AddInfo
        name_parts = [
            "2026",
            st.session_state.client_code,
            st.session_state.product_code,
            l,
            clean_val(full_camp_name),
            clean_val(m),
            s,
            fmt_date(st.session_state.start_date),
            f"{d}.zip" # Additional Info slot
        ]
        
        rows.append({
            "Creative Name": "_".join(name_parts),
            "Campaign": full_camp_name,
            "Messaging": m,
            "Size": s,
            "Duration": d
        })
    
    st.session_state.results = pd.DataFrame(rows)

# ------------------------
# 6. Results Display
# ------------------------
with right:
    if "results" in st.session_state:
        st.markdown(f'<div class="info-box">Generated **{len(st.session_state.results)}** conventions.</div>', unsafe_allow_html=True)
        st.dataframe(st.session_state.results, use_container_width=True, hide_index=True)
        
        csv = st.session_state.results.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Asset Matrix", data=csv, file_name="asset_matrix.csv", use_container_width=True)
        
        st.markdown("### 📝 Quick Copy")
        st.code("\n".join(st.session_state.results["Creative Name"].tolist()), language=None)
