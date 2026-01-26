import streamlit as st
import pandas as pd
from datetime import date, datetime
import itertools
from urllib.parse import urlparse

# ------------------------
# Configuration & Helpers
# ------------------------
st.set_page_config(page_title="Badger – Asset Matrix Generator", page_icon="🦡", layout="wide")

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def fmt_date(d: date) -> str:
    return f"{MONTHS[d.month-1]}.{d.day:02d}.{d.year}"

def sanitize_freeform(s: str) -> str:
    return (s or "").replace("_", " ").strip()

def is_valid_url(u: str) -> bool:
    if not u or not str(u).strip():
        return True
    try:
        p = urlparse(str(u).strip())
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False

def build_name(year, client_code, product_code, language, funnel, region, messaging, size, start_date, duration, delivery_tag="", additional_info="", delimiter="_"):
    messaging_clean = sanitize_freeform(messaging)
    additional_clean = sanitize_freeform(additional_info)
    date_part = fmt_date(start_date)

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
    
    warnings = []
    if "_" in messaging: warnings.append("Messaging '_' cleaned")
    if not all([year, client_code, product_code, language, funnel, region, messaging, size]):
        warnings.append("Missing required fields")
        
    return name, " | ".join(warnings)

def cartesian_generate(config: dict) -> pd.DataFrame:
    combos = itertools.product(
        config["funnels"], config["messages"], config["regions"],
        config["languages"], config["durations"], config["sizes"]
    )
    rows = []
    for funnel, msg, region, lang, dur, size in combos:
        name, warn = build_name(
            config["year"], config["client_code"], config["product_code"],
            lang, funnel, region, msg, size, config["start_date"], dur,
            config.get("delivery_tag", ""), config.get("additional_info", ""), config.get("delimiter", "_")
        )
        rows.append({
            "Funnel": funnel, "Messaging": sanitize_freeform(msg), "Region": region,
            "Language": lang, "Duration": dur, "Size": size, "Creative Name": name,
            "Warnings": warn, "URL": config.get("url", "")
        })
    return pd.DataFrame(rows)

# ------------------------
# UI - Left Column (Inputs)
# ------------------------
st.title("🦡 Badger")
st.caption("Fast bulk naming convention generator.")

left, right = st.columns([1, 1.35], gap="large")

with left:
    st.subheader("Shared fields")
    
    LOB_PRESETS = {
        "Business": {"client_code": "RNS", "product_code": "BRA"},
        "Wireless": {"client_code": "RCS", "product_code": "WLS"},
        "Connected Home": {"client_code": "RHE", "product_code": "IGN"},
        "Rogers Bank": {"client_code": "RBG", "product_code": "RBK"},
        "Custom": {"client_code": "", "product_code": ""},
    }

    if "client_code" not in st.session_state: st.session_state.client_code = "RNS"
    if "product_code" not in st.session_state: st.session_state.product_code = "BRA"

    def apply_lob():
        preset = LOB_PRESETS.get(st.session_state.lob)
        if preset and preset["client_code"]:
            st.session_state.client_code = preset["client_code"]
            st.session_state.product_code = preset["product_code"]

    year = st.number_input("Year", value=2026)
    st.selectbox("LOB Preset", options=list(LOB_PRESETS.keys()), key="lob", on_change=apply_lob)
    client_code = st.text_input("Client Code", key="client_code")
    product_code = st.text_input("Product Code", key="product_code")
    
    start_date = st.date_input("Start date", value=date.today())
    url_input = st.text_input("Global URL (Optional)", placeholder="https://...")
    delimiter = st.text_input("Delimiter", value="_")

    st.divider()
    st.subheader("Variants")
    funnels = st.multiselect("Funnel", ["AWR", "COS", "COV"], default=["AWR", "COS"])
    regions = st.multiselect("Region", ["ROC", "QC", "ATL"], default=["ROC"])
    languages = st.multiselect("Language", ["EN", "FR"], default=["EN"])
    durations = st.multiselect("Duration", ["6s", "15s", "30s"], default=["15s"])
    sizes = st.multiselect("Sizes", ["1x1", "9x16", "16x9", "300x250", "728x90"], default=["1x1", "9x16"])
    
    messages_text = st.text_area("Messaging (one per line)", value="Promo_A\nPromo_B")
    messages = [line.strip() for line in messages_text.splitlines() if line.strip()]

# ------------------------
# UI - Right Column (Output)
# ------------------------
with right:
    st.subheader("Generate")
    
    config = {
        "year": year, "client_code": client_code, "product_code": product_code,
        "start_date": start_date, "url": url_input, "delimiter": delimiter,
        "funnels": funnels, "regions": regions, "languages": languages,
        "durations": durations, "sizes": sizes, "messages": messages
    }

    total = len(funnels) * len(regions) * len(languages) * len(durations) * len(sizes) * len(messages)
    st.info(f"Generating **{total:,}** variations.")

    mode = st.radio("Display Mode", ["Sheet Mode", "Trafficking Mode"], horizontal=True)
    
    # Initialize session state for data
    if "master_df" not in st.session_state:
        st.session_state.master_df = None

    if st.button("Generate Matrix", type="primary", use_container_width=True):
        if total > 0:
            st.session_state.master_df = cartesian_generate(config)
        else:
            st.error("Please select variants.")

    if st.session_state.master_df is not None:
        # PIVOT FOR SHEET MODE
        if mode == "Sheet Mode":
            idx = ["Funnel", "Messaging", "Region", "Language", "Duration", "URL"]
            df_display = st.session_state.master_df.pivot_table(
                index=idx, columns="Size", values="Creative Name", aggfunc="first"
            ).reset_index()
            
            st.write("### 📝 Edit URLs in Table")
            edited_df = st.data_editor(
                df_display,
                use_container_width=True,
                column_config={
                    "URL": st.column_config.TextColumn("URL (Editable)", width="large", placeholder="Paste row-specific URL here")
                },
                disabled=["Funnel", "Messaging", "Region", "Language", "Duration"] # Lock these
            )
            final_output = edited_df
        
        # FLAT LIST FOR TRAFFICKING
        else:
            st.write("### 📋 Flat List")
            edited_df = st.data_editor(
                st.session_state.master_df,
                use_container_width=True,
                column_config={"URL": st.column_config.TextColumn("URL", width="large")},
                disabled=["Funnel", "Messaging", "Region", "Language", "Duration", "Size", "Creative Name", "Warnings"]
            )
            final_output = edited_df

        # DOWNLOAD
        st.download_button(
            "Download Edited CSV",
            data=final_output.to_csv(index=False).encode('utf-8'),
            file_name="naming_matrix.csv",
            mime="text/csv"
        )

        st.divider()
        st.write("### Copy-Ready Names")
        st.code("\n".join(st.session_state.master_df["Creative Name"].tolist()))
