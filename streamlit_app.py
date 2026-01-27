import streamlit as st
import pandas as pd
from datetime import date
import itertools

# ------------------------
# 1. Page Configuration & Custom Compact Styling
# ------------------------
st.set_page_config(page_title="Badger | Asset Matrix", page_icon="🦡", layout="wide")

st.markdown("""
<style>
    .main-header { font-size: 2rem; font-weight: 700; color: #FF4B4B; margin-bottom: 0.5rem; }
    .stTextInput label, .stSelectbox label, .stMultiSelect label, .stDateInput label { font-weight: 600; font-size: 0.85rem; }
    
    /* FIX: Shrink Multiselect Tags to hug text */
    div[data-baseweb="tag"] {
        height: 22px !important;
        padding: 0px 6px !important;
        font-size: 0.75rem !important;
        margin: 2px !important;
    }
    .stMultiSelect div div div div {
        min-height: 32px !important; /* Reduces vertical bulk of the input box */
    }
    
    .info-box { background-color: #f0f2f6; padding: 1rem; border-radius: 8px; border-left: 5px solid #FF4B4B; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

# ------------------------
# 2. Reference Data & Logic
# ------------------------
LOB_MAP = {
    "Consumer Wireless": {"client": "RCS", "product": "WLS"},
    "Connected Home": {"client": "RHE", "product": "IGN"},
    "Rogers Business": {"client": "RNS", "product": "BRA"},
    "Rogers Bank": {"client": "RBG", "product": "RBK"},
    "Corporate Brand": {"client": "RCP", "product": "RCB"},
    "Shaw Direct": {"client": "RSH", "product": "CBL"},
}

def fmt_date(d: date) -> str:
    """Format: MMM.dd.yyyy (e.g., Jun.27.2025)"""
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    return f"{months[d.month-1]}.{d.day:02d}.{d.year}"

def clean_val(s: str) -> str:
    """Enforces No Underscore Allowed rule"""
    return (s or "").replace("_", " ").strip()

# ------------------------
# 3. Sidebar / Input Panel
# ------------------------
if "lob_choice" not in st.session_state:
    st.session_state.lob_choice = "Connected Home"

curr_lob = LOB_MAP[st.session_state.lob_choice]

st.markdown('<div class="main-header">🦡 Badger | 2026 Asset Matrix</div>', unsafe_allow_html=True)

left, right = st.columns([1, 2], gap="medium")

with left:
    with st.container(border=True):
        st.markdown("### 📋 1. Identity")
        st.selectbox("Line of Business", options=list(LOB_MAP.keys()), key="lob_choice")
        
        c1, c2 = st.columns(2)
        client_code = c1.text_input("Client", value=curr_lob["client"])
        product_code = c2.text_input("Product", value=curr_lob["product"])
        
        d1, d2 = st.columns(2)
        start_date = d1.date_input("Start Date", value=date.today())
        end_date = d2.date_input("End Date", value=date(2026, 3, 31))
        delivery_date = st.date_input("Delivery Date", value=date.today())

    with st.container(border=True):
        st.markdown("### 🏗️ 2. Campaign Builder")
        camp_title = st.text_input("Campaign Title (Free Form)", value="Q3 Comwave QC")
        
        # Tags are now styled to be compact
        f_col, r_col, l_col = st.columns(3)
        funnels = f_col.multiselect("Funnel", ["COS", "AWR", "COV", "D3B", "D3Y", "PNX"], default=["COS"])
        regions = r_col.multiselect("Region", ["ATL", "ROC", "QC", "Halifax"], default=["ATL"])
        languages = l_col.multiselect("Language", ["EN", "FR"], default=["EN"])
        
        msg_input = st.text_area("Messaging (one per line)", value="Internet Offer V1")

    with st.container(border=True):
        st.markdown("### 🎨 3. Asset Specs")
        durations = st.multiselect("Durations", ["6s", "10s", "15s", "30s", "Static"], default=["15s"])
        # Columns used for the spreadsheet layout
        sheet_sizes = ["1x1 Meta", "2x3 Pinterest", "9x16 Story", "9x16 Reel"]
        selected_sizes = st.multiselect("Sizes", sheet_sizes + ["16x9", "300x250"], default=sheet_sizes)
        extension = st.selectbox("Extension", [".zip", ".mp4", ".jpg", ".html"], index=0)

# ------------------------
# 4. Generation Logic
# ------------------------
if st.button("🚀 Generate Final Matrix", type="primary", use_container_width=True):
    messages = [m.strip() for m in msg_input.splitlines() if m.strip()]
    
    # Cartesian product of all variations
    combos = itertools.product(funnels, messages, regions, languages, durations, selected_sizes)
    rows = []

    for f, m, r, l, dur, siz in combos:
        # Build Campaign Name: Title-Funnel-Region-Lang
        full_camp = f"{camp_title}-{f}-{r}-{l}"
        
        # Build Additional Info: Duration + Extension
        add_info = f"{dur}{extension}"
        
        # Dimensions for naming convention (e.g., '1x1')
        dim = siz.split()[0]

        # Year_Client_Prod_Lang_Camp_Msg_Size_Date_AddInfo
        name_parts = [
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
        
        rows.append({
            "FUNNEL": f,
            "MESSAGING": m,
            "REGION": r,
            "LANGUAGE": l,
            "DURATION": dur,
            "SizeHeader": siz,
            "Convention": "_".join(name_parts)
        })

    if rows:
        df = pd.DataFrame(rows)
        
        # Pivot to create spreadsheet view
        pivot_df = df.pivot_table(
            index=["FUNNEL", "MESSAGING", "REGION", "LANGUAGE", "DURATION"],
            columns="SizeHeader",
            values="Convention",
            aggfunc="first"
        ).reset_index()

        # Add Metadata columns
        pivot_df["DELIVERY DATE"] = fmt_date(delivery_date)
        pivot_df["START DATE"] = fmt_date(start_date)
        pivot_df["END DATE"] = fmt_date(end_date)
        pivot_df["URL"] = "https://www.rogers.com"

        st.session_state.matrix_final = pivot_df

# ------------------------
# 5. Output Display
# ------------------------
with right:
    if "matrix_final" in st.session_state:
        st.markdown(f'<div class="info-box">Generated **{len(st.session_state.matrix_final)}** row variations.</div>', unsafe_allow_html=True)
        
        # Show spreadsheet-style preview
        st.dataframe(st.session_state.matrix_final, use_container_width=True, hide_index=True)
        
        # Download
        csv = st.session_state.matrix_final.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Asset Matrix CSV", data=csv, file_name=f"Asset_Matrix_{date.today()}.csv", use_container_width=True)
        
        with st.expander("📋 View All Conventions (Flat List)"):
            all_names = []
            for col in st.session_state.matrix_final.columns:
                if col not in ["FUNNEL", "MESSAGING", "REGION", "LANGUAGE", "DURATION", "DELIVERY DATE", "START DATE", "END DATE", "URL"]:
                    all_names.extend(st.session_state.matrix_final[col].dropna().tolist())
            st.code("\n".join(all_names), language=None)
    else:
        st.info("Fill out the Campaign Builder and click Generate to see the matrix.")
