import streamlit as st
import pandas as pd
from datetime import date
import itertools

# ------------------------
# 1. Page Configuration & Forced Large-Tag Styling
# ------------------------
st.set_page_config(page_title="Badger | Asset Matrix", page_icon="🦡", layout="wide")

st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #FF4B4B; margin-bottom: 0.5rem; }
    
    /* FIX: Force tags to be large, readable, and non-truncated */
    div[data-baseweb="tag"] {
        background-color: #FF4B4B !important;
        color: white !important;
        border-radius: 6px !important;
        padding: 8px 16px !important; 
        height: auto !important;
    }
    
    div[data-baseweb="tag"] span {
        font-size: 1.1rem !important; 
        font-weight: 600 !important;
        white-space: nowrap !important;
    }

    .stMultiSelect div[data-baseweb="select"] > div {
        min-height: 50px !important;
    }

    .stTextInput label, .stSelectbox label, .stMultiSelect label, .stDateInput label { 
        font-weight: 700; 
        font-size: 1rem; 
    }
    
    .info-box { background-color: #f0f2f6; padding: 1rem; border-radius: 8px; border-left: 5px solid #FF4B4B; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

# ------------------------
# 2. Reference Data & Mappings
# ------------------------
LOB_CODES = {
    "Connected Home": {"client": "RHE", "product": "IGN"},
    "Consumer Wireless": {"client": "RCS", "product": "WLS"},
    "Rogers Business": {"client": "RNS", "product": "BRA"},
    "Rogers Bank": {"client": "RBG", "product": "RBK"},
    "Corporate Brand": {"client": "RCP", "product": "RCB"},
    "Shaw Direct": {"client": "RSH", "product": "CBL"},
}

# Platform to Size Mapping
PLATFORM_SIZES = {
    "Meta": ["1x1 Meta", "9x16 Story", "9x16 Reel"],
    "Pinterest": ["2x3 Pinterest", "1x1 Pinterest", "9x16 Pinterest"],
    "Reddit": ["1x1 Reddit", "4x5 Reddit", "16x9 Reddit"],
    "Display (Standard)": ["300x250", "728x90", "160x600", "300x600", "970x250"],
}

def fmt_date(d: date) -> str:
    """Format: MMM.dd.yyyy (e.g., Jun.27.2025)"""
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    return f"{months[d.month-1]}.{d.day:02d}.{d.year}"

def clean_val(s: str) -> str:
    return (s or "").replace("_", " ").strip()

# ------------------------
# 3. Sidebar / Input Panel
# ------------------------
st.markdown('<div class="main-header">🦡 Badger | 2026 Asset Matrix</div>', unsafe_allow_html=True)

left, right = st.columns([1.2, 2.8], gap="large")

with left:
    # --- 1. Matrix Type & Intelligence ---
    with st.container(border=True):
        st.markdown("### 🛠️ 1. Matrix Configuration")
        matrix_type = st.radio("Asset Matrix Type", ["Social", "Display"], horizontal=True)
        
        selected_platforms = []
        default_sizes = []
        
        if matrix_type == "Social":
            selected_platforms = st.multiselect("Platforms", list(PLATFORM_SIZES.keys())[:-1], default=["Meta", "Pinterest"])
            for p in selected_platforms:
                default_sizes.extend(PLATFORM_SIZES[p])
        else:
            default_sizes = PLATFORM_SIZES["Display (Standard)"]

    # --- 2. Identity ---
    with st.container(border=True):
        st.markdown("### 📋 2. Identity")
        lob = st.selectbox("Line of Business", options=list(LOB_CODES.keys()), index=0)
        
        c1, c2 = st.columns(2)
        client_code = c1.text_input("Client Code", value=LOB_CODES[lob]["client"])
        product_code = c2.text_input("Product Code", value=LOB_CODES[lob]["product"])
        
        d1, d2 = st.columns(2)
        start_date = d1.date_input("Start Date", value=date.today())
        end_date = d2.date_input("End Date", value=date(2026, 3, 31))

    # --- 3. Campaign Builder ---
    with st.container(border=True):
        st.markdown("### 🏗️ 3. Campaign Builder")
        camp_title = st.text_input("Campaign Title (No Underscores)", value="Q3 Comwave QC")
        
        funnels = st.multiselect("Funnel", ["COS", "AWR", "COV", "D3B", "D3Y", "PNX"], default=["COS"])
        regions = st.multiselect("Region", ["ATL", "ROC", "QC", "Halifax"], default=["ATL"])
        langs = st.multiselect("Language", ["EN", "FR"], default=["EN"])
        
        msg_input = st.text_area("Messaging (one per line)", value="Internet Offer V1")

    # --- 4. Asset Specs (Pre-filled based on Section 1) ---
    with st.container(border=True):
        st.markdown("### 🎨 4. Asset Specs")
        durations = st.multiselect("Durations", ["6s", "10s", "15s", "30s", "Static"], default=["15s"])
        
        # This list updates dynamically based on the "Matrix Configuration" above
        final_sizes = st.multiselect("Sizes", options=sorted(list(set(default_sizes + ["16x9", "300x250"]))), default=default_sizes)
        
        extension = st.selectbox("Extension", [".zip", ".mp4", ".jpg", ".html"], index=0 if matrix_type == "Social" else 3)

# ------------------------
# 4. Processing Logic
# ------------------------
if st.button("🚀 Generate Asset Matrix", type="primary", use_container_width=True):
    messages = [m.strip() for m in msg_input.splitlines() if m.strip()]
    combos = itertools.product(funnels, messages, regions, langs, durations, final_sizes)
    raw_rows = []

    for f, m, r, l, dur, siz in combos:
        full_camp = f"{camp_title}-{f}-{r}-{l}"
        add_info = f"{dur}{extension}"
        dim = siz.split()[0] 

        # 9-Part Taxonomy: Year_Client_Prod_Lang_Camp_Msg_Size_Date_AddInfo
        parts = [
            "2026",
            client_code.strip(),
            product_code.strip(),
            l,
            clean_val(full_camp),
            clean_val(m),
            dim,
            fmt_date(start_date),
            clean_val(add_info)
        ]
        
        raw_rows.append({
            "FUNNEL": f, "MESSAGING": m, "REGION": r, "LANGUAGE": l, "DURATION": dur,
            "SizeHeader": siz, "Convention": "_".join(parts)
        })

    if raw_rows:
        df_flat = pd.DataFrame(raw_rows)
        pivot_df = df_flat.pivot_table(
            index=["FUNNEL", "MESSAGING", "REGION", "LANGUAGE", "DURATION"],
            columns="SizeHeader", values="Convention", aggfunc="first"
        ).reset_index()

        pivot_df["START DATE"] = fmt_date(start_date)
        pivot_df["END DATE"] = fmt_date(end_date)
        pivot_df["URL"] = "https://www.rogers.com"

        st.session_state.final_matrix = pivot_df

# ------------------------
# 5. Output
# ------------------------
with right:
    if "final_matrix" in st.session_state:
        st.markdown(f'<div class="info-box">Matrix built for **{matrix_type}**. Export ready.</div>', unsafe_allow_html=True)
        st.dataframe(st.session_state.final_matrix, use_container_width=True, hide_index=True)
        
        csv_data = st.session_state.final_matrix.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Final Sheet", data=csv_data, file_name="Badger_Matrix.csv", use_container_width=True)
    else:
        st.info("Configure your matrix type on the left to begin.")
