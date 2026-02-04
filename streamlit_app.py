import streamlit as st
import pandas as pd
from datetime import date
import itertools

# ------------------------
# 1. Page Configuration & Professional Styling
# ------------------------
st.set_page_config(page_title="Badger | Asset Matrix Creator", page_icon="🦡", layout="wide")

st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #FF4B4B; margin-bottom: 0.5rem; }
    
    /* Selection tags remain large and adapt to text width */
    div[data-baseweb="tag"] {
        background-color: #FF4B4B !important;
        color: white !important;
        border-radius: 4px !important;
        padding: 6px 12px !important;
        height: auto !important;
        max-width: fit-content !important;
    }
    div[data-baseweb="tag"] span {
        font-size: 0.95rem !important;
        font-weight: 600 !important;
    }
    .stMultiSelect div[data-baseweb="select"] > div {
        min-height: 48px !important;
    }
    
    /* Standard button sizing (not full width) */
    div.stButton > button {
        width: auto !important;
        padding-left: 30px !important;
        padding-right: 30px !important;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------
# 2. Reference Data (LOB, Client, Product)
# ------------------------
# Mappings sourced from your taxonomy reference
LOB_DATA = {
    "Connected Home": {"client": "RHE", "product": "IGN"},
    "Consumer Wireless": {"client": "RCS", "product": "WLS"},
    "Rogers Business": {"client": "RNS", "product": "BRA"},
    "Rogers Bank": {"client": "RBG", "product": "RBK"},
    "Corporate Brand": {"client": "RCP", "product": "RCB"},
    "Shaw Direct": {"client": "RSH", "product": "CBL"},
}

# Full product list from your documentation
PRODUCT_LIST = ["IGN", "WLS", "BRA", "RBK", "RCB", "CBL", "TSP", "FIN", "SHM", "CWI", "FWI", "IDV", "RWI", "SOH", "FIB", "IOT"]

PLATFORM_SIZES = {
    "Meta": ["1x1 Meta", "9x16 Story", "9x16 Reel"],
    "Pinterest": ["2x3 Pinterest", "1x1 Pinterest", "9x16 Pinterest"],
    "Reddit": ["1x1 Reddit", "4x5 Reddit", "16x9 Reddit"],
    "Display": ["300x250", "728x90", "160x600", "300x600", "970x250"]
}

def fmt_date(d: date) -> str:
    """Format: XXXdd.yyyy (e.g., Jun.27.2025)"""
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    return f"{months[d.month-1]}.{d.day:02d}.{d.year}"

def clean_val(s: str) -> str:
    """Taxonomy Rule: No Underscores Allowed in free-form segments"""
    return (s or "").replace("_", " ").strip()

# ------------------------
# 3. Sidebar / Input Panel
# ------------------------
st.markdown('<div class="main-header">🦡 Badger | 2026 Asset Matrix</div>', unsafe_allow_html=True)

left, right = st.columns([1.2, 2.8], gap="large")

with left:
    # --- SECTION 1: Matrix Type ---
    with st.container(border=True):
        st.markdown("### 🛠️ 1. Matrix Configuration")
        matrix_type = st.radio("Asset Matrix Type", ["Social", "Display"], horizontal=True)
        
        suggested_sizes = []
        if matrix_type == "Social":
            platforms = st.multiselect("Platforms", ["Meta", "Pinterest", "Reddit"], default=["Meta", "Pinterest"])
            for p in platforms:
                suggested_sizes.extend(PLATFORM_SIZES[p])
        else:
            suggested_sizes = PLATFORM_SIZES["Display"]

    # --- SECTION 2: Identity ---
    with st.container(border=True):
        st.markdown("### 📋 2. Identity")
        # Restored LOB Selector
        lob_choice = st.selectbox("Line of Business", options=list(LOB_DATA.keys()), index=0)
        
        # Pre-filled based on LOB choice
        c1, c2 = st.columns(2)
        client_code = c1.text_input("Client Code", value=LOB_DATA[lob_choice]["client"])
        product_code = c2.selectbox("Product Code", options=PRODUCT_LIST, index=PRODUCT_LIST.index(LOB_DATA[lob_choice]["product"]))
        
        d1, d2 = st.columns(2)
        start_date = d1.date_input("Start Date", value=date.today())
        end_date = d2.date_input("End Date", value=date(2026, 3, 31))
        delivery_date = st.date_input("Delivery Date", value=date.today())

    # --- SECTION 3: Campaign Builder ---
    with st.container(border=True):
        st.markdown("### 🏗️ 3. Campaign Builder")
        camp_title = st.text_input("Campaign Title (Free Form)", value="Q3 Comwave QC")
        
        funnels = st.multiselect("Funnel", ["COS", "AWR", "COV", "D3B", "D3Y", "PNX"], default=["COS"])
        regions = st.multiselect("Region", ["ATL", "ROC", "QC", "Halifax"], default=["ATL"])
        langs = st.multiselect("Language", ["EN", "FR"], default=["EN"])
        
        msg_input = st.text_area("Messaging (one per line)", value="Internet Offer V1")

    # --- SECTION 4: Asset Specs ---
    with st.container(border=True):
        st.markdown("### 🎨 4. Asset Specs")
        durations = st.multiselect("Durations", ["6s", "10s", "15s", "30s", "Static"], default=["15s"])
        selected_sizes = st.multiselect("Sizes", options=sorted(list(set(suggested_sizes + ["16x9"]))), default=suggested_sizes)
        custom_suffix = st.text_input("Custom Suffix (Free Form)", placeholder="e.g. V1, Final")

# ------------------------
# 4. Processing & Pivot Logic
# ------------------------
if st.button("🚀 Generate Asset Matrix", type="primary"):
    messages = [m.strip() for m in msg_input.splitlines() if m.strip()]
    combos = itertools.product(funnels, messages, regions, langs, durations, selected_sizes)
    flat_data = []

    for f, m, r, l, dur, siz in combos:
        full_campaign = f"{camp_title}-{f}-{r}-{l}"
        size_code = siz.split()[0]
        
        # Taxonomy Construction based on 2026 Rules
        name_parts = [
            "2026",
            client_code,
            product_code,
            l,
            clean_val(full_campaign),
            clean_val(m),
            size_code,
            fmt_date(start_date),
            clean_val(dur)
        ]
        
        creative_name = "_".join(name_parts)
        if custom_suffix:
            creative_name += f"_{clean_val(custom_suffix)}"
        
        flat_data.append({
            "FUNNEL": f, "MESSAGING": m, "REGION": r, "LANGUAGE": l, "DURATION": dur,
            "SizeLabel": siz, "Creative Name": creative_name
        })

    if flat_data:
        df = pd.DataFrame(flat_data)
        pivot_df = df.pivot_table(
            index=["FUNNEL", "MESSAGING", "REGION", "LANGUAGE", "DURATION"],
            columns="SizeLabel", values="Creative Name", aggfunc="first"
        ).reset_index()

        # Metadata Columns
        pivot_df["DELIVERY DATE"] = fmt_date(delivery_date)
        pivot_df["START DATE"] = fmt_date(start_date)
        pivot_df["END DATE"] = fmt_date(end_date)
        pivot_df["URL"] = "" 
        
        st.session_state.matrix_df = pivot_df

# ------------------------
# 5. Output with Editable Data Editor
# ------------------------
with right:
    if "matrix_df" in st.session_state:
        st.markdown(f"### 📊 Generated {matrix_type} Matrix")
        st.caption("Editable: Click cells to adjust names or paste URLs before downloading.")
        
        edited_df = st.data_editor(
            st.session_state.matrix_df, 
            use_container_width=True, 
            hide_index=True,
            num_rows="dynamic"
        )
        
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download Final Sheet", 
            data=csv, 
            file_name=f"Asset_Matrix_{lob_choice}_{matrix_type}.csv",
            mime='text/csv'
        )
    else:
        st.info("Configure the sections on the left and click Generate.")
