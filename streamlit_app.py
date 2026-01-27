import streamlit as st
import pandas as pd
from datetime import date
import itertools

# ------------------------
# 1. Page Configuration & Custom Styling
# ------------------------
st.set_page_config(page_title="Badger | Asset Matrix", page_icon="🦡", layout="wide")

st.markdown("""
<style>
    .stTextInput label, .stSelectbox label, .stMultiSelect label, .stDateInput label { font-weight: 600; color: #31333F; }
    .main-header { font-size: 2.5rem; font-weight: 700; color: #FF4B4B; margin-bottom: 0.5rem; }
    .info-box { background-color: #f0f2f6; padding: 1rem; border-radius: 8px; border-left: 5px solid #FF4B4B; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

# ------------------------
# 2. Logic & Helper Functions
# ------------------------
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def fmt_date(d: date) -> str:
    """Format: MMM.DD.YYYY (e.g., Jun.27.2025)"""
    return f"{MONTHS[d.month-1]}.{d.day:02d}.{d.year}"

def clean_val(s: str) -> str:
    """Enforces 'No Underscore' rule per updated taxonomy."""
    return (s or "").replace("_", " ").strip()

def build_name(year, client, product, lang, campaign, messaging, size, start_date, add_info, delimiter="_"):
    """
    Constructs the name based on the 2026 Hierarchy:
    Year_Client_Product_Language_CampaignName_Messaging_Size_Date_AdditionalInfo
    """
    parts = [
        str(year).strip(),
        client.strip(),
        product.strip(),
        lang.strip(),
        clean_val(campaign),
        clean_val(messaging),
        size.strip(),
        fmt_date(start_date),
        clean_val(add_info)
    ]
    return delimiter.join([p for p in parts if p])

def cartesian_generate(config: dict) -> pd.DataFrame:
    combos = itertools.product(
        config["campaign_names"],
        config["messages"], 
        config["languages"], 
        config["durations"], 
        config["sizes"]
    )
    rows = []
    current_year = date.today().year 
    for camp, msg, lang, dur, size in combos:
        # Per taxonomy: Additional Info contains Duration and File Extension (e.g., 10s.zip)
        info = f"{dur}{config['extension']}"
        
        name = build_name(
            current_year, config["client_code"], config["product_code"], 
            lang, camp, msg, size, config["start_date"], info
        )
        rows.append({
            "Campaign": camp,
            "Messaging": msg, 
            "Language": lang, 
            "Duration": dur, 
            "Size": size, 
            "Creative Name": name,
            "Start Date": fmt_date(config["start_date"])
        })
    return pd.DataFrame(rows)

# ------------------------
# 3. Data Libraries & Corrected Options
# ------------------------
CLIENT_CODES = {
    "RCP": "ROGERS CORPORATE BRAND", "RHE": "CONNECTED HOME",
    "RCS": "CONSUMER WIRELESS", "RNS": "ROGERS BUSINESS",
    "RBG": "ROGERS BANK", "RSH": "ROGERS SHAW DIRECT"
}

PRODUCT_CODES = {
    "RCB": "CORPORATE BRAND", "TSP": "TITLING SPONSORSHIP", "FIN": "FIDO INTERNET",
    "IGN": "IGNITE", "SHM": "SMART HOME MONITORING", "CWI": "CHATR",
    "FWI": "FIDO WIRELESS", "IDV": "INDIVIDUALLY LIABLE", "RWI": "ROGERS WIRELESS",
    "SOH": "SOHO", "BRA": "BRAND", "INT": "INTERNET", "WLS": "WIRELESS",
    "FIB": "FIBRE", "IOT": "IOT", "CBL": "CABLE", "RBK": "ROGERS BANK"
}

# Master list of all possible sizes to avoid Streamlit error
ALL_SIZES = [
    "1x1", "9x16", "16x9", "9x16Story", "9x16Reel", "2x3", "4x5",
    "300x250", "300x600", "728x90", "160x600", "970x250"
]

ASSET_MATRIX_PRESETS = {
    "Social": {"durations": ["6s", "15s"], "sizes": ["1x1", "9x16Story", "9x16Reel"]},
    "Display": {"durations": ["Static"], "sizes": ["300x250", "300x600", "728x90", "160x600", "970x250"]},
    "Video": {"durations": ["6s", "15s", "30s"], "sizes": ["16x9", "9x16"]},
    "Custom": {"durations": [], "sizes": []}
}

# ------------------------
# 4. UI Layout
# ------------------------
st.markdown('<div class="main-header">🦡 Badger</div>', unsafe_allow_html=True)

left, right = st.columns([1, 1.4], gap="medium")

with left:
    with st.container(border=True):
        st.markdown("### 📋 Campaign Identifiers")
        client_code = st.selectbox("Client Code", options=list(CLIENT_CODES.keys()), format_func=lambda x: f"{x} - {CLIENT_CODES[x]}")
        product_code = st.selectbox("Product Code", options=list(PRODUCT_CODES.keys()), format_func=lambda x: f"{x} - {PRODUCT_CODES[x]}")
        start_date = st.date_input("Start Date", value=date.today())

    with st.container(border=True):
        st.markdown("### 🎨 Asset Strategy")
        matrix_type = st.selectbox("Matrix Type", options=list(ASSET_MATRIX_PRESETS.keys()))
        
        # Get defaults based on selection
        default_dur = ASSET_MATRIX_PRESETS[matrix_type]["durations"]
        default_siz = ASSET_MATRIX_PRESETS[matrix_type]["sizes"]
        
        durations = st.multiselect("Durations", ["Static", "6s", "10s", "15s", "30s", "60s"], default=default_dur)
        # Use master list ALL_SIZES to prevent "default value not in options" error
        sizes = st.multiselect("Sizes", ALL_SIZES, default=default_siz)
        extension = st.selectbox("File Extension (Optional)", ["", ".zip", ".mp4", ".jpg"], index=1)

    with st.container(border=True):
        st.markdown("### 🔀 Bulk Variations")
        languages = st.multiselect("Languages", ["EN", "FR"], default=["EN"])
        
        campaign_input = st.text_area("Campaign Names (one per line)", value="Q3 Comwave QC")
        messaging_input = st.text_area("Messaging (one per line)", value="Internet Offer V1")
        
        c_names = [line.strip() for line in campaign_input.splitlines() if line.strip()]
        m_names = [line.strip() for line in messaging_input.splitlines() if line.strip()]

config = {
    "client_code": client_code, "product_code": product_code, "start_date": start_date,
    "campaign_names": c_names, "messages": m_names, "languages": languages, 
    "durations": durations, "sizes": sizes, "extension": extension
}

with right:
    # --- OUTPUT SECTION ---
    total = len(c_names) * len(m_names) * len(languages) * len(durations) * len(sizes)
    st.markdown(f'<div class="info-box">Generating <strong>{total:,}</strong> creative names.</div>', unsafe_allow_html=True)
    
    if st.button("Generate Matrix", type="primary", use_container_width=True):
        df = cartesian_generate(config)
        st.divider()
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.download_button("📥 Download CSV", data=df.to_csv(index=False).encode('utf-8'), file_name=f"badger_matrix_{date.today()}.csv", use_container_width=True)
        
        st.markdown("### 📝 Copy-Ready List")
        st.code("\n".join(df["Creative Name"].tolist()), language=None)
