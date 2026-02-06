import streamlit as st
import pandas as pd
from datetime import date
import itertools

# ------------------------
# 1. Page Configuration
# ------------------------
st.set_page_config(page_title="Badger | Asset Matrix Creator", page_icon="🦡", layout="wide")

st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #FF4B4B; margin-bottom: 0.5rem; }
    div[data-baseweb="tag"] { background-color: #FF4B4B !important; color: white !important; }
    .stButton > button { width: auto !important; padding-left: 30px !important; padding-right: 30px !important; }
</style>
""", unsafe_allow_html=True)

# ------------------------
# 2. Reference Data
# ------------------------
LOB_DATA = {
    "Connected Home": {"client": "RHE", "product": "IGN"},
    "Consumer Wireless": {"client": "RCS", "product": "WLS"},
    "Rogers Business": {"client": "RNS", "product": "BRA"},
    "Rogers Bank": {"client": "RBG", "product": "RBK"},
    "Corporate Brand": {"client": "RCP", "product": "RCB"},
    "Shaw Direct": {"client": "RSH", "product": "CBL"},
}

PRODUCT_LIST = ["IGN", "WLS", "BRA", "RBK", "RCB", "CBL", "TSP", "FIN", "SHM", "CWI", "FWI", "IDV", "RWI", "SOH", "FIB", "IOT"]

PLATFORM_SIZES = {
    "Meta": ["1x1 Meta", "9x16 Story", "9x16 Reel"],
    "Pinterest": ["2x3 Pinterest", "1x1 Pinterest", "9x16 Pinterest"],
    "Reddit": ["1x1 Reddit", "4x5 Reddit", "16x9 Reddit"],
    "Display": ["300x250", "728x90", "160x600", "300x600", "970x250"]
}

def fmt_date(d: date) -> str:
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    return f"{months[d.month-1]}.{d.day:02d}.{d.year}"

def clean_val(s: str) -> str:
    return str(s).replace("_", " ").strip()

# ------------------------
# 3. Input Panel
# ------------------------
st.markdown('<div class="main-header">🦡 Badger | Asset Matrix Creator</div>', unsafe_allow_html=True)

left, right = st.columns([1.3, 2.7], gap="large")

with left:
    # 1. Configuration
    with st.container(border=True):
        st.markdown("### 🛠️ 1. Configuration")
        matrix_type = st.radio("Type", ["Social", "Display"], horizontal=True)
        
        # SIZES: Presets + Custom
        suggested = []
        if matrix_type == "Social":
            platforms = st.multiselect("Platforms", ["Meta", "Pinterest", "Reddit"], default=["Meta"])
            for p in platforms: suggested.extend(PLATFORM_SIZES[p])
        else:
            suggested = PLATFORM_SIZES["Display"]
        
        selected_sizes = st.multiselect("Sizes", options=list(set(suggested)), default=suggested)
        custom_size = st.text_input("Add Custom Size (e.g. 320x50)")
        if custom_size: selected_sizes.append(custom_size)

    # 2. Identity
    with st.container(border=True):
        st.markdown("### 📋 2. Identity")
        lob_choice = st.selectbox("LOB", options=list(LOB_DATA.keys()))
        c1, c2 = st.columns(2)
        client_code = c1.text_input("Client", value=LOB_DATA[lob_choice]["client"])
        product_code = c2.selectbox("Product", options=PRODUCT_LIST, index=PRODUCT_LIST.index(LOB_DATA[lob_choice]["product"]))
        start_date = st.date_input("Start Date", value=date.today())

    # 3. Campaign & Offers
    with st.container(border=True):
        st.markdown("### 🏗️ 3. Campaign & Offers")
        camp_title = st.text_input("Campaign Title", value="Q3 Offer")
        
        # Simplified Funnels
        funnels = st.multiselect("Funnel", ["AWR", "COV", "COS"], default=["COS"])
        regions = st.multiselect("Region", ["ATL", "ROC", "QC", "Halifax"], default=["ROC", "QC"])
        
        st.write("**Messaging & Pricing**")
        if 'offer_rows' not in st.session_state:
            st.session_state.offer_rows = [{"msg": "Internet Offer", "price": ""}]
        
        def add_offer(): st.session_state.offer_rows.append({"msg": "", "price": ""})
        
        for i, row in enumerate(st.session_state.offer_rows):
            r1, r2 = st.columns([2, 1])
            st.session_state.offer_rows[i]["msg"] = r1.text_input(f"Msg {i+1}", value=row["msg"], key=f"m{i}")
            st.session_state.offer_rows[i]["price"] = r2.text_input(f"Price {i+1}", value=row["price"], key=f"p{i}", placeholder="$65")
        
        st.button("➕ Add Offer", on_click=add_offer)

    # 4. Durations
    with st.container(border=True):
        st.markdown("### 🎨 4. Asset Specs")
        preset_durs = ["6s", "15s", "30s", "Static"]
        selected_durs = st.multiselect("Durations", options=preset_durs, default=["15s"])
        custom_dur = st.text_input("Add Custom Duration (e.g. 5s)")
        if custom_dur: selected_durs.append(custom_dur)
        custom_suffix = st.text_input("Custom Suffix")

# ------------------------
# 4. Conditional Logic Engine
# ------------------------
if st.button("🚀 Generate Asset Matrix", type="primary"):
    flat_data = []
    
    # Nested loops to handle FR/QC logic
    for f, r, dur, siz in itertools.product(funnels, regions, selected_durs, selected_sizes):
        
        # Logic: FR only for QC. Everyone else only gets EN.
        langs = ["FR", "EN"] if r == "QC" else ["EN"]
        
        for l in langs:
            for offer in st.session_state.offer_rows:
                msg = clean_val(offer["msg"])
                price = clean_val(offer["price"])
                size_code = siz.split()[0]
                
                # Build Taxonomy
                full_campaign = f"{camp_title}-{f}-{r}-{l}"
                
                name_parts = [
                    "2026", client_code, product_code, l,
                    clean_val(full_campaign), msg, size_code,
                    fmt_date(start_date), clean_val(dur)
                ]
                
                creative_name = "_".join(name_parts)
                if price: creative_name += f"_{price}"
                if custom_suffix: creative_name += f"_{clean_val(custom_suffix)}"
                
                flat_data.append({
                    "FUNNEL": f, "REGION": r, "LANGUAGE": l, "MESSAGING": msg, "PRICE": price,
                    "DURATION": dur, "SIZE": siz, "Creative Name": creative_name
                })

    if flat_data:
        st.session_state.matrix_df = pd.DataFrame(flat_data)

# ------------------------
# 5. Output Section
# ------------------------
with right:
    if "matrix_df" in st.session_state:
        st.markdown("### 📊 Generated Matrix")
        
        edited_df = st.data_editor(st.session_state.matrix_df, use_container_width=True, hide_index=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            csv = edited_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download CSV", data=csv, file_name="Badger_Matrix.csv", use_container_width=True)
            
        with col2:
            # Copy to Clipboard (Using st.dataframe workaround for web clipboard)
            # In modern browsers, users can select all and copy from data_editor.
            # To make it easier, we provide a markdown snippet.
            if st.button("📋 Copy to Clipboard", use_container_width=True):
                st.write("Selected data ready! Use `Ctrl+C` on the table above.")
                st.toast("Table ready for copying!")

        with col3:
            if st.button("🗑️ Reset Matrix", use_container_width=True):
                del st.session_state.matrix_df
                st.rerun()
    else:
        st.info("Adjust settings on the left and click Generate.")
