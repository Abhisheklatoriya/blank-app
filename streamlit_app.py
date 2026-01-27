import streamlit as st
import pandas as pd
from datetime import date
import itertools

# ------------------------
# 1. Page Config & Professional Styling
# ------------------------
st.set_page_config(page_title="Badger | Asset Matrix", page_icon="🦡", layout="wide")

st.markdown("""
<style>
    .stTextInput label, .stSelectbox label, .stMultiSelect label, .stDateInput label { font-weight: 600; color: #31333F; }
    .main-header { font-size: 2.2rem; font-weight: 700; color: #FF4B4B; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1rem; color: #666; margin-bottom: 1.5rem; }
    .info-box { background-color: #f0f2f6; padding: 1rem; border-radius: 8px; border-left: 5px solid #FF4B4B; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

# ------------------------
# 2. Taxonomy Data & Mappings
# ------------------------
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

# Full LOB mapping from your screenshot tables
LOB_MAP = {
    "Rogers Corporate Brand": {"client": "RCP", "product": "RCB"},
    "Connected Home": {"client": "RHE", "product": "IGN"},
    "Consumer Wireless": {"client": "RCS", "product": "WLS"},
    "Rogers Business": {"client": "RNS", "product": "BRA"},
    "Rogers Bank": {"client": "RBG", "product": "RBK"},
    "Rogers Shaw Direct": {"client": "RSH", "product": "CBL"},
}

# Master list of all sizes mentioned in your screenshots/presets to prevent API errors
ALL_SIZES = [
    "1x1", "9x16", "16x9", "9x16Story", "9x16Reel", "2x3", "4x5", 
    "300x250", "300x600", "728x90", "160x600", "970x250"
]

ASSET_PRESETS = {
    "Social": {"dur": ["6s", "15s"], "siz": ["1x1", "9x16Story", "9x16Reel"]},
    "Display": {"dur": ["Static"], "siz": ["300x250", "300x600", "728x90", "160x600", "970x250"]},
    "Video": {"dur": ["6s", "15s", "30s"], "siz": ["16x9", "9x16"]},
}

def fmt_date(d: date) -> str:
    """Format: MMM.DD.YYYY (e.g., Jun.27.2025)"""
    return f"{MONTHS[d.month-1]}.{d.day:02d}.{d.year}"

def clean_val(s: str) -> str:
    """Strict 'No Underscore' rule enforcement"""
    return (s or "").replace("_", " ").strip()

# ------------------------
# 3. State Management for Pre-fills
# ------------------------
if "lob_choice" not in st.session_state:
    st.session_state.lob_choice = "Connected Home"

# This updates the codes immediately when LOB changes
current_lob = LOB_MAP[st.session_state.lob_choice]

# ------------------------
# 4. UI Layout
# ------------------------
st.markdown('<div class="main-header">🦡 Badger</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">2026 Asset Matrix & Naming Convention Generator</div>', unsafe_allow_html=True)

left, right = st.columns([1, 1.4], gap="medium")

with left:
    # --- SECTION 1: Identity ---
    with st.container(border=True):
        st.markdown("### 📋 1. Identity & Pre-fills")
        st.selectbox("Line of Business (LOB)", options=list(LOB_MAP.keys()), key="lob_choice")
        
        c1, c2 = st.columns(2)
        # We use the state to pre-fill but allow manual overrides
        client_code = c1.text_input("Client Code", value=current_lob["client"])
        product_code = c2.text_input("Product Code", value=current_lob["product"])
        
        start_date = st.date_input("Start Date", value=date.today())

    # --- SECTION 2: Campaign Builder ---
    with st.container(border=True):
        st.markdown("### 🏗️ 2. Campaign & Messaging")
        # Following the "Messaging Guide" logic from your screenshot
        camp_base = st.text_input("Creative Campaign Name", value="Q3 Comwave QC")
        
        col_f, col_r, col_l = st.columns(3)
        funnels = col_f.multiselect("Funnel", ["COS", "AWR", "COV"], default=["COS"])
        regions = col_r.multiselect("Region", ["ATL", "ROC", "QC"], default=["ATL"])
        languages = col_l.multiselect("Language", ["EN", "FR"], default=["EN"])
        
        msg_input = st.text_area("Messaging (one per line)", value="Internet Offer V1")

    # --- SECTION 3: Asset Specs ---
    with st.container(border=True):
        st.markdown("### 🎨 3. Asset Specs")
        m_type = st.selectbox("Matrix Type", options=list(ASSET_PRESETS.keys()))
        
        # FIXED: Ensure default values are ALWAYS inside the options list
        selected_durations = st.multiselect(
            "Durations", 
            options=["Static", "6s", "10s", "15s", "30s", "60s"], 
            default=ASSET_PRESETS[m_type]["dur"]
        )
        
        selected_sizes = st.multiselect(
            "Sizes", 
            options=ALL_SIZES, 
            default=ASSET_PRESETS[m_type]["siz"]
        )
        
        extension = st.selectbox("Extension", ["", ".zip", ".mp4", ".jpg"], index=1)

# ------------------------
# 5. Generation & Results
# ------------------------
with right:
    # Calculate Total
    messages = [m.strip() for m in msg_input.splitlines() if m.strip()]
    total_count = len(funnels) * len(regions) * len(languages) * len(messages) * len(selected_durations) * len(selected_sizes)
    
    st.markdown(f'<div class="info-box">Generating <strong>{total_count:,}</strong> names.</div>', unsafe_allow_html=True)
    
    if st.button("Generate Matrix", type="primary", use_container_width=True):
        # Create all combinations
        combos = itertools.product(funnels, regions, languages, messages, selected_durations, selected_sizes)
        rows = []
        
        for f, r, l, m, dur, siz in combos:
            # Build Campaign Name like the example: "Q3 Comwave QC-COS-ATL-EN"
            full_camp = f"{camp_base}-{f}-{r}-{l}"
            
            # Additional Info: Duration + Extension (e.g., 10s.zip)
            add_info = f"{dur}{extension}"
            
            # TAXONOMY: Year_Client_Prod_Lang_Camp_Msg_Size_Date_AddInfo
            name_parts = [
                str(start_date.year),
                client_code.strip(),
                product_code.strip(),
                l,
                clean_val(full_camp),
                clean_val(m),
                siz,
                fmt_date(start_date),
                clean_val(add_info)
            ]
            
            final_name = "_".join([p for p in name_parts if p])
            
            rows.append({
                "Creative Name": final_name,
                "Campaign": full_camp,
                "Messaging": m,
                "Size": siz,
                "Duration": dur,
                "Language": l
            })
        
        df = pd.DataFrame(rows)
        st.divider()
        
        # Display Results
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Actions
        c_dl, c_copy = st.columns(2)
        c_dl.download_button("📥 Download CSV", data=df.to_csv(index=False).encode('utf-8'), file_name="asset_matrix.csv", use_container_width=True)
        
        st.markdown("### 📝 Quick Copy List")
        st.code("\n".join(df["Creative Name"].tolist()), language=None)
