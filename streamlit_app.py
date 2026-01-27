import streamlit as st
import pandas as pd
from datetime import date
import itertools

# ------------------------
# 1. Page Configuration & Style
# ------------------------
st.set_page_config(page_title="Badger | Asset Matrix", page_icon="🦡", layout="wide")

st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #FF4B4B; margin-bottom: 0.5rem; }
    .stTextInput label, .stSelectbox label, .stMultiSelect label, .stDateInput label { font-weight: 600; }
    .info-box { background-color: #f0f2f6; padding: 1rem; border-radius: 8px; border-left: 5px solid #FF4B4B; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

# ------------------------
# 2. Taxonomy Data (Sourced from Screenshots)
# ------------------------
LOB_MAP = {
    "Rogers Corporate Brand": {"client": "RCP", "product": "RCB"},
    "Connected Home": {"client": "RHE", "product": "IGN"},
    "Consumer Wireless": {"client": "RCS", "product": "WLS"},
    "Rogers Business": {"client": "RNS", "product": "BRA"},
    "Rogers Bank": {"client": "RBG", "product": "RBK"},
    "Rogers Shaw Direct": {"client": "RSH", "product": "CBL"},
}

# Sizes as seen in the spreadsheet header
DEFAULT_SIZES = ["1x1 Meta", "2x3 Pinterest", "9x16 Story", "9x16 Reel"]

def fmt_date(d: date) -> str:
    """Format: MMM.dd.yyyy (e.g., Jun.27.2025)"""
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    return f"{months[d.month-1]}.{d.day:02d}.{d.year}"

def clean_val(s: str) -> str:
    """Replaces underscores with spaces per taxonomy rules."""
    return (s or "").replace("_", " ").strip()

# ------------------------
# 3. Sidebar & State
# ------------------------
if "lob_choice" not in st.session_state:
    st.session_state.lob_choice = "Connected Home"

curr_lob = LOB_MAP[st.session_state.lob_choice]

# ------------------------
# 4. UI Layout
# ------------------------
st.markdown('<div class="main-header">🦡 Badger | Asset Matrix Generator</div>', unsafe_allow_html=True)

left, right = st.columns([1, 1.8], gap="medium")

with left:
    with st.container(border=True):
        st.markdown("### 📋 1. Identity")
        st.selectbox("Line of Business (LOB)", options=list(LOB_MAP.keys()), key="lob_choice")
        
        c1, c2 = st.columns(2)
        client_code = c1.text_input("Client Code", value=curr_lob["client"])
        product_code = c2.text_input("Product Code", value=curr_lob["product"])
        
        d1, d2 = st.columns(2)
        start_date = d1.date_input("Start Date", value=date.today())
        end_date = d2.date_input("End Date", value=date.today())
        delivery_date = st.date_input("Delivery Date", value=date.today())

    with st.container(border=True):
        st.markdown("### 🏗️ 2. Campaign Builder")
        camp_title = st.text_input("Campaign Title (Free Form)", value="Q3 Comwave QC")
        
        f_col, r_col, l_col = st.columns(3)
        funnels = f_col.multiselect("Funnel", ["COS", "AWR", "COV"], default=["COS"])
        regions = r_col.multiselect("Region", ["ATL", "ROC", "QC"], default=["ATL"])
        languages = l_col.multiselect("Language", ["EN", "FR"], default=["EN"])
        
        msg_input = st.text_area("Messaging (one per line)", value="Internet Offer V1")

    with st.container(border=True):
        st.markdown("### 🎨 3. Asset Specs")
        durations = st.multiselect("Durations", ["6s", "15s", "30s", "Static"], default=["15s"])
        sizes = st.multiselect("Sizes", DEFAULT_SIZES + ["16x9", "300x250"], default=DEFAULT_SIZES)
        extension = st.selectbox("Extension", [".zip", ".mp4", ".jpg", ".html"], index=0)

# ------------------------
# 5. Generation Logic
# ------------------------
if st.button("Generate Matrix", type="primary", use_container_width=True):
    messages = [m.strip() for m in msg_input.splitlines() if m.strip()]
    
    # 9-part taxonomy logic
    combos = itertools.product(funnels, messages, regions, languages, durations, sizes)
    flat_data = []

    for f, m, r, l, dur, siz in combos:
        # Auto-build Campaign Name: Title-Funnel-Region-Lang
        full_camp = f"{camp_title}-{f}-{r}-{l}"
        
        # Additional Info slot: Duration + Extension
        add_info = f"{dur}{extension}"
        
        # Build the final creative name
        name_parts = [
            str(start_date.year),
            client_code.strip(),
            product_code.strip(),
            l,
            clean_val(full_camp),
            clean_val(m),
            siz.split()[0], # Use only the dimensions for the naming convention
            fmt_date(start_date),
            clean_val(add_info)
        ]
        creative_name = "_".join(name_parts)

        flat_data.append({
            "Funnel": f,
            "Messaging": m,
            "Region": r,
            "Language": l,
            "Duration": dur,
            "SizeLabel": siz,
            "Creative Name": creative_name
        })

    if flat_data:
        df_flat = pd.DataFrame(flat_data)
        
        # Pivot to create the spreadsheet view
        pivot_df = df_flat.pivot_table(
            index=["Funnel", "Messaging", "Region", "Language", "Duration"],
            columns="SizeLabel",
            values="Creative Name",
            aggfunc="first"
        ).reset_index()

        # Add Metadata columns on the right
        pivot_df["Delivery Date"] = fmt_date(delivery_date)
        pivot_df["Start Date"] = fmt_date(start_date)
        pivot_df["End Date"] = fmt_date(end_date)
        pivot_df["URL"] = "https://www.rogers.com"

        st.session_state.final_matrix = pivot_df

# ------------------------
# 6. Final Output Display
# ------------------------
with right:
    if "final_matrix" in st.session_state:
        st.markdown(f'<div class="info-box">Matrix generated successfully. Columns correspond to specific creative sizes.</div>', unsafe_allow_html=True)
        
        # Display the pivoted dataframe
        st.dataframe(st.session_state.final_matrix, use_container_width=True, hide_index=True)
        
        # Download button
        csv = st.session_state.final_matrix.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Final Spreadsheet", data=csv, file_name="asset_matrix_2026.csv", use_container_width=True)
        
        # Quick Copy Area
        st.markdown("### 📝 Quick Copy: All Names")
        all_names = []
        for col in st.session_state.final_matrix.columns:
            if col not in ["Funnel", "Messaging", "Region", "Language", "Duration", "Delivery Date", "Start Date", "End Date", "URL"]:
                all_names.extend(st.session_state.final_matrix[col].dropna().tolist())
        st.code("\n".join(all_names), language=None)
    else:
        st.info("Adjust settings on the left and click 'Generate Matrix' to see the final sheet output.")
