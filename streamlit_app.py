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
        padding: 6px 14px !important; /* Increased padding */
        height: auto !important;
        min-width: 50px !important; /* Ensure a minimum width */
    }
    
    div[data-baseweb="tag"] span {
        font-size: 1rem !important; /* Increased font size */
        font-weight: 600 !important;
        white-space: nowrap !important;
        overflow: visible !important;
        text-overflow: clip !important;
    }

    /* Increase the height of the input box itself to accommodate larger tags */
    .stMultiSelect div[data-baseweb="select"] > div {
        min-height: 45px !important;
    }

    .stTextInput label, .stSelectbox label, .stMultiSelect label, .stDateInput label { 
        font-weight: 700; 
        font-size: 1rem; 
        color: #31333F;
    }
    
    .info-box { background-color: #f0f2f6; padding: 1rem; border-radius: 8px; border-left: 5px solid #FF4B4B; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

# ------------------------
# 2. Reference Data (from Taxonomy Screenshots)
# ------------------------
LOB_CODES = {
    "Connected Home": {"client": "RHE", "product": "IGN"},
    "Consumer Wireless": {"client": "RCS", "product": "WLS"},
    "Rogers Business": {"client": "RNS", "product": "BRA"},
    "Rogers Bank": {"client": "RBG", "product": "RBK"},
    "Corporate Brand": {"client": "RCP", "product": "RCB"},
    "Shaw Direct": {"client": "RSH", "product": "CBL"},
}

PRODUCT_CODES = ["IGN", "WLS", "BRA", "RBK", "RCB", "CBL", "TSP", "FIN", "SHM", "CWI", "FWI", "IDV", "RWI", "SOH", "FIB", "IOT"]

def fmt_date(d: date) -> str:
    """Format: MMM.dd.yyyy (e.g., Jun.27.2025)"""
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    return f"{months[d.month-1]}.{d.day:02d}.{d.year}"

def clean_val(s: str) -> str:
    """Strictly remove underscores for taxonomy compliance"""
    return (s or "").replace("_", " ").strip()

# ------------------------
# 3. Input Panel
# ------------------------
st.markdown('<div class="main-header">🦡 Badger | 2026 Asset Matrix</div>', unsafe_allow_html=True)

left, right = st.columns([1.2, 2.8], gap="large")

with left:
    with st.container(border=True):
        st.markdown("### 📋 1. Identity")
        lob = st.selectbox("Line of Business", options=list(LOB_CODES.keys()), index=0)
        
        c1, c2 = st.columns(2)
        client_code = c1.text_input("Client Code", value=LOB_CODES[lob]["client"])
        product_code = c2.selectbox("Product Code", options=PRODUCT_CODES, index=PRODUCT_CODES.index(LOB_CODES[lob]["product"]))
        
        d1, d2 = st.columns(2)
        start_date = d1.date_input("Start Date", value=date.today())
        end_date = d2.date_input("End Date", value=date(2026, 3, 31))
        
        delivery_date = st.date_input("Delivery Date", value=date.today())

    with st.container(border=True):
        st.markdown("### 🏗️ 2. Campaign Builder")
        camp_title = st.text_input("Campaign Title (Free Form)", value="Q3 Comwave QC")
        
        # Tags here will be large and visible
        funnels = st.multiselect("Funnel", ["COS", "AWR", "COV", "D3B", "D3Y", "PNX"], default=["COS"])
        regions = st.multiselect("Region", ["ATL", "ROC", "QC", "Halifax"], default=["ATL"])
        langs = st.multiselect("Language", ["EN", "FR"], default=["EN"])
        
        msg_input = st.text_area("Messaging (one per line)", value="Internet Offer V1")

    with st.container(border=True):
        st.markdown("### 🎨 3. Asset Specs")
        durations = st.multiselect("Durations", ["6s", "10s", "15s", "30s", "Static"], default=["15s"])
        
        sheet_sizes = ["1x1 Meta", "2x3 Pinterest", "9x16 Story", "9x16 Reel"]
        selected_sizes = st.multiselect("Sizes", sheet_sizes + ["16x9", "300x250"], default=sheet_sizes)
        extension = st.selectbox("Extension", [".zip", ".mp4", ".jpg", ".html"], index=0)

# ------------------------
# 4. Pivot Generation
# ------------------------
if st.button("🚀 Generate Final Matrix", type="primary", use_container_width=True):
    messages = [m.strip() for m in msg_input.splitlines() if m.strip()]
    combos = itertools.product(funnels, messages, regions, langs, durations, selected_sizes)
    raw_rows = []

    for f, m, r, l, dur, siz in combos:
        full_camp = f"{camp_title}-{f}-{r}-{l}"
        add_info = f"{dur}{extension}"
        dim = siz.split()[0] # e.g., '1x1'

        # Year_Client_Prod_Lang_Camp_Msg_Size_Date_AddInfo
        parts = [
            str(start_date.year),
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

        pivot_df["DELIVERY DATE"] = fmt_date(delivery_date)
        pivot_df["START DATE"] = fmt_date(start_date)
        pivot_df["END DATE"] = fmt_date(end_date)
        pivot_df["URL"] = "https://www.rogers.com"

        st.session_state.final_matrix = pivot_df

# ------------------------
# 5. Result Display
# ------------------------
with right:
    if "final_matrix" in st.session_state:
        st.markdown(f'<div class="info-box">Generated **{len(st.session_state.final_matrix)}** row variations.</div>', unsafe_allow_html=True)
        st.dataframe(st.session_state.final_matrix, use_container_width=True, hide_index=True)
        
        csv_data = st.session_state.final_matrix.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Asset Matrix (CSV)", data=csv_data, file_name=f"Asset_Matrix_{date.today()}.csv", use_container_width=True)
    else:
        st.info("Fill out the parameters and click Generate.")
