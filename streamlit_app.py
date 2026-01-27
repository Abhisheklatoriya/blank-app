import streamlit as st
import pandas as pd
from datetime import date
import itertools

# ------------------------
# 1. Page Configuration & Professional Styling
# ------------------------
st.set_page_config(page_title="Badger | Asset Matrix", page_icon="🦡", layout="wide")

st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #FF4B4B; margin-bottom: 0.5rem; }
    .stTextInput label, .stSelectbox label, .stMultiSelect label, .stDateInput label { font-weight: 600; font-size: 0.95rem; }
    .info-box { background-color: #f0f2f6; padding: 1rem; border-radius: 8px; border-left: 5px solid #FF4B4B; margin-bottom: 1rem; }
    /* Improve multiselect tag visibility */
    .stMultiSelect div div div div { background-color: #FF4B4B !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# ------------------------
# 2. Taxonomy Data & Helper Functions
# ------------------------
# Sourced from Client/Product Code Tables
CLIENT_CODES = {
    "RCP": "ROGERS CORPORATE BRAND",
    "RHE": "CONNECTED HOME",
    "RCS": "CONSUMER WIRELESS",
    "RNS": "ROGERS BUSINESS",
    "RBG": "ROGERS BANK",
    "RSH": "ROGERS SHAW DIRECT"
}

PRODUCT_CODES = {
    "RCB": "CORPORATE BRAND", "TSP": "TITLING SPONSORSHIP", "FIN": "FIDO INTERNET",
    "IGN": "IGNITE", "SHM": "SMART HOME MONITORING", "CWI": "CHATR",
    "FWI": "FIDO WIRELESS", "IDV": "INDIVIDUALLY LIABLE", "RWI": "ROGERS WIRELESS",
    "SOH": "SOHO", "BRA": "BRAND", "INT": "INTERNET", "WLS": "WIRELESS",
    "FIB": "FIBRE", "IOT": "IOT", "CBL": "CABLE", "RBK": "ROGERS BANK"
}

def fmt_date(d: date) -> str:
    """Format: MMM.DD.YYYY (e.g., Jun.27.2025)"""
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    return f"{months[d.month-1]}.{d.day:02d}.{d.year}"

def clean_val(s: str) -> str:
    """Strict Rule: No underscores allowed in free-form fields."""
    return (s or "").replace("_", " ").strip()

# ------------------------
# 3. Main UI Layout
# ------------------------
st.markdown('<div class="main-header">🦡 Badger | 2026 Asset Matrix</div>', unsafe_allow_html=True)

left, right = st.columns([1.1, 1.9], gap="large")

with left:
    # --- SECTION 1: Identity ---
    with st.container(border=True):
        st.markdown("### 📋 1. Identity & Codes")
        client_choice = st.selectbox("Client Code", options=list(CLIENT_CODES.keys()), 
                                     format_func=lambda x: f"{x} - {CLIENT_CODES[x]}")
        product_choice = st.selectbox("Product Code", options=list(PRODUCT_CODES.keys()),
                                      format_func=lambda x: f"{x} - {PRODUCT_CODES[x]}")
        
        d1, d2 = st.columns(2)
        start_date = d1.date_input("Start Date", value=date.today())
        end_date = d2.date_input("End Date", value=date(2026, 3, 31))
        delivery_date = st.date_input("Delivery Date", value=date.today())

    # --- SECTION 2: Campaign Builder ---
    with st.container(border=True):
        st.markdown("### 🏗️ 2. Campaign Builder")
        camp_title = st.text_input("Campaign Title (Free Form)", value="Q3 Comwave QC")
        
        # Expanded columns to fix visibility issues
        f_col, r_col = st.columns(2)
        funnels = f_col.multiselect("Funnel", ["COS", "AWR", "COV", "D3B", "D3Y", "PNX"], default=["COS"])
        regions = r_col.multiselect("Region", ["ATL", "ROC", "QC", "Halifax"], default=["ATL"])
        
        languages = st.multiselect("Language", ["EN", "FR"], default=["EN"])
        
        msg_input = st.text_area("Messaging (one per line)", value="Internet Offer V1")

    # --- SECTION 3: Asset Specs ---
    with st.container(border=True):
        st.markdown("### 🎨 3. Asset Specs")
        durations = st.multiselect("Durations", ["6s", "10s", "15s", "30s", "Static"], default=["15s"])
        # Sizes formatted as headers in the final spreadsheet
        available_sizes = ["1x1 Meta", "2x3 Pinterest", "9x16 Story", "9x16 Reel", "16x9", "300x250"]
        selected_sizes = st.multiselect("Sizes", available_sizes, default=available_sizes[:4])
        extension = st.selectbox("File Extension", [".zip", ".mp4", ".jpg", ".html"], index=0)

# ------------------------
# 4. Generation Logic
# ------------------------
if st.button("🚀 Generate Full Asset Matrix", type="primary", use_container_width=True):
    messages = [m.strip() for m in msg_input.splitlines() if m.strip()]
    
    # Cartesian product for all variations
    combos = itertools.product(funnels, messages, regions, languages, durations, selected_sizes)
    flat_data = []

    for f, m, r, l, dur, siz in combos:
        # Hierarchy Build: Year_Client_Product_Lang_Campaign_Messaging_Size_Date_AddInfo
        
        # 1. Campaign Name includes Funnel, Region, Language
        full_camp = f"{camp_title}-{f}-{r}-{l}"
        
        # 2. Additional Info includes Duration and Extension
        add_info = f"{dur}{extension}"
        
        # 3. Size Part (First word of label, e.g., '1x1')
        size_code = siz.split()[0]

        name_parts = [
            "2026",
            client_choice,
            product_choice,
            l,
            clean_val(full_camp),
            clean_val(m),
            size_code,
            fmt_date(start_date),
            clean_val(add_info)
        ]
        
        creative_name = "_".join(name_parts)

        flat_data.append({
            "FUNNEL": f,
            "MESSAGING": m,
            "REGION": r,
            "LANGUAGE": l,
            "DURATION": dur,
            "SizeLabel": siz,
            "Creative Name": creative_name
        })

    if flat_data:
        df_flat = pd.DataFrame(flat_data)
        
        # Pivot to mirror the spreadsheet layout
        pivot_df = df_flat.pivot_table(
            index=["FUNNEL", "MESSAGING", "REGION", "LANGUAGE", "DURATION"],
            columns="SizeLabel",
            values="Creative Name",
            aggfunc="first"
        ).reset_index()

        # Add Metadata columns per screenshot
        pivot_df["DELIVERY DATE"] = fmt_date(delivery_date)
        pivot_df["START DATE"] = fmt_date(start_date)
        pivot_df["END DATE"] = fmt_date(end_date)
        pivot_df["URL"] = "https://www.rogers.com"

        st.session_state.matrix_ready = pivot_df

# ------------------------
# 5. Results Display
# ------------------------
with right:
    if "matrix_ready" in st.session_state:
        st.markdown("### 📊 Generated Spreadsheet View")
        # Display the pivoted matrix exactly like the spreadsheet screenshot
        st.dataframe(st.session_state.matrix_ready, use_container_width=True, hide_index=True)
        
        # Actions
        col_dl, col_copy = st.columns(2)
        csv = st.session_state.matrix_ready.to_csv(index=False).encode('utf-8')
        col_dl.download_button("📥 Download Excel/CSV", data=csv, file_name=f"Asset_Matrix_{date.today()}.csv", use_container_width=True)
        
        st.markdown("### 📝 All Generated Conventions")
        all_names = []
        for col in st.session_state.matrix_ready.columns:
            if col not in ["FUNNEL", "MESSAGING", "REGION", "LANGUAGE", "DURATION", "DELIVERY DATE", "START DATE", "END DATE", "URL"]:
                all_names.extend(st.session_state.matrix_ready[col].dropna().tolist())
        st.code("\n".join(all_names), language=None)
    else:
        st.info("Fill out the parameters and click Generate to build the matrix.")
