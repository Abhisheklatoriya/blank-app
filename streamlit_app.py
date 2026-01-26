import streamlit as st
import pandas as pd
from datetime import date
import itertools
from urllib.parse import urlparse

# ------------------------
# Helpers
# ------------------------
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def fmt_date(d: date) -> str:
    return f"{MONTHS[d.month-1]}.{d.day:02d}.{d.year}"

def sanitize_freeform(s: str) -> str:
    return (s or "").replace("_", " ").strip()

def build_name(year, client_code, product_code, language, funnel, region, messaging, size, start_date, duration, delivery_tag="", additional_info="", delimiter="_"):
    messaging_clean = sanitize_freeform(messaging)
    additional_clean = sanitize_freeform(additional_info)
    date_part = fmt_date(start_date)

    # Order: Year_Client_Product_Lang_Funnel_Region_Messaging_Size_Date_Duration
    parts = [
        str(year).strip(),
        client_code.strip(),
        product_code.strip(),
        language.strip(),
        funnel.strip(),
        region.strip(),
        messaging_clean,
        size.strip(),
        date_part,
        str(duration).strip(),
    ]

    if delivery_tag: parts.append(str(delivery_tag).strip())
    if additional_clean: parts.append(additional_clean)

    name = delimiter.join([p for p in parts if p])
    return name

def cartesian_generate(config: dict) -> pd.DataFrame:
    combos = itertools.product(
        config["funnels"], 
        config["messages"], 
        config["regions"], 
        config["languages"], 
        config["durations"], 
        config["sizes"]
    )
    rows = []
    current_year = date.today().year 
    for funnel, msg, region, lang, dur, size in combos:
        name = build_name(
            current_year, config["client_code"], config["product_code"], 
            lang, funnel, region, msg, size, config["start_date"], dur, 
            config.get("delivery_tag", ""), config.get("additional_info", ""), config.get("delimiter", "_")
        )
        rows.append({
            "Funnel": funnel, 
            "Messaging": sanitize_freeform(msg), 
            "Region": region, 
            "Language": lang, 
            "Duration": dur, 
            "Size": size, 
            "Creative Name": name,
            "Start Date": fmt_date(config["start_date"]), 
            "End Date": fmt_date(config["end_date"]), 
            "URL": "" 
        })
    return pd.DataFrame(rows)

def pivot_like_sheet(df_flat: pd.DataFrame) -> pd.DataFrame:
    idx = ["Funnel", "Messaging", "Region", "Language", "Duration", "Start Date", "End Date"]
    pivot = df_flat.pivot_table(
        index=idx, 
        columns="Size", 
        values="Creative Name", 
        aggfunc="first"
    ).reset_index()
    pivot["URL"] = ""
    return pivot

# ------------------------
# UI Setup
# ------------------------
st.set_page_config(page_title="Badger – Asset Matrix Generator", page_icon="🦡", layout="wide")
st.title("🦡 Badger")

# LOB Presets Logic
LOB_PRESETS = {
    "Business": {"client_code": "RNS", "product_code": "BRA"},
    "Wireless": {"client_code": "RCS", "product_code": "WLS"},
    "Connected Home": {"client_code": "RHE", "product_code": "IGN"},
    "Rogers Bank": {"client_code": "RBG", "product_code": "RBK"},
    "Corporate Brand": {"client_code": "RCP", "product_code": "RCB"},
    "Shaw Direct": {"client_code": "RSH", "product_code": "CBL"},
    "Custom": {"client_code": "", "product_code": ""},
}

def apply_lob_preset():
    preset = LOB_PRESETS.get(st.session_state.lob_select)
    if preset and st.session_state.lob_select != "Custom":
        st.session_state.client_code_input = preset["client_code"]
        st.session_state.product_code_input = preset["product_code"]

left, right = st.columns([1, 1.35], gap="large")

with left:
    st.subheader("Shared fields")
    
    st.selectbox(
        "LOB (Prefills codes)", 
        options=list(LOB_PRESETS.keys()), 
        key="lob_select", 
        on_change=apply_lob_preset
    )

    # Use session state for pre-filling logic
    if "client_code_input" not in st.session_state:
        st.session_state.client_code_input = "RNS"
    if "product_code_input" not in st.session_state:
        st.session_state.product_code_input = "BRA"

    client_code = st.text_input("Client Code", key="client_code_input")
    product_code = st.text_input("Product Code", key="product_code_input")
    
    start_date = st.date_input("Start date", value=date.today())
    end_date = st.date_input("End date", value=date.today())
    delivery_tag = st.text_input("Delivery tag (optional)")
    additional_info = st.text_input("Additional info (optional)")
    delimiter = st.text_input("Delimiter", value="_")

    st.divider()
    st.subheader("Variants")
    funnels = st.multiselect("Funnel", ["AWR", "COS", "COV"], default=["AWR", "COS", "COV"])
    regions = st.multiselect("Region", ["ROC", "QC", "ATL"], default=["ROC"])
    languages = st.multiselect("Language", ["EN", "FR"], default=["EN", "FR"])
    durations = st.multiselect("Duration", ["6s", "15s", "30s"], default=["6s", "15s"])
    sizes = st.multiselect("Sizes", ["1x1", "9x16Story", "9x16Reel", "16x9"], default=["1x1", "9x16Story"])
    
    messages_text = st.text_area("Messaging (one per line)", value="Lower Costs\nSupport\nTransparent Pricing")
    messages = [line.strip() for line in messages_text.splitlines() if line.strip()]

config = {
    "client_code": client_code, 
    "product_code": product_code, 
    "start_date": start_date, "end_date": end_date,
    "delivery_tag": delivery_tag, "additional_info": additional_info, "delimiter": delimiter,
    "funnels": funnels, "regions": regions, "languages": languages, 
    "durations": durations, "sizes": sizes, "messages": messages
}

with right:
    st.subheader("Generate")
    
    total_names = len(funnels) * len(regions) * len(languages) * len(durations) * len(sizes) * len(messages)
    st.info(f"This will generate **{total_names:,}** creative names.")
    
    mode = st.radio("Output format", ["Sheet mode (pivot by Size)", "Trafficking mode"], horizontal=True)

    if "df_flat" not in st.session_state:
        st.session_state.df_flat = None

    if st.button("Generate naming conventions", type="primary", use_container_width=True):
        st.session_state.df_flat = cartesian_generate(config)

    if st.session_state.df_flat is not None:
        if mode.startswith("Sheet"):
            df_out = pivot_like_sheet(st.session_state.df_flat)
            st.markdown("### Output (sheet-style)")
            
            edited_sheet = st.data_editor(
                df_out,
                use_container_width=True,
                column_config={"URL": st.column_config.TextColumn("URL", width="large")},
                key="sheet_editor"
            )
            
            st.download_button(
                label="Download CSV",
                data=edited_sheet.to_csv(index=False).encode('utf-8'),
                file_name=f"asset_matrix_{date.today()}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.dataframe(st.session_state.df_flat, use_container_width=True)

        st.markdown("### Copy-ready list")
        st.code("\n".join(st.session_state.df_flat["Creative Name"].tolist()), language=None)
