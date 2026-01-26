import streamlit as st
import pandas as pd
from datetime import date, datetime
import itertools
from urllib.parse import urlparse
import json
import uuid
import streamlit.components.v1 as components

st.set_page_config(page_title="Badger – Asset Matrix Generator", page_icon="🦡", layout="wide")

# ------------------------
# Helpers
# ------------------------
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def fmt_date(d: date) -> str:
    return f"{MONTHS[d.month-1]}.{d.day:02d}.{d.year}"

def sanitize_freeform(s: str) -> str:
    return (s or "").replace("_", " ").strip()

def build_name(
    year: int,
    client_code: str,
    product_code: str,
    language: str,
    funnel: str,
    region: str,
    messaging: str,
    size: str,
    start_date: date,
    duration: str,
    delivery_tag: str = "",
    additional_info: str = "",
    delimiter: str = "_",
) -> tuple[str, str]:
    warnings = []
    messaging_raw = messaging
    additional_raw = additional_info

    if "_" in (messaging_raw or ""):
        warnings.append("Messaging contained '_' (replaced with spaces)")
    if "_" in (additional_raw or ""):
        warnings.append("Additional info contained '_' (replaced with spaces)")

    messaging_clean = sanitize_freeform(messaging_raw)
    additional_clean = sanitize_freeform(additional_raw)
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

    if delivery_tag:
        parts.append(str(delivery_tag).strip())
    if additional_clean:
        parts.append(additional_clean)

    parts = [p for p in parts if p]
    name = delimiter.join(parts)

    required_missing = []
    if not year: required_missing.append("Year")
    if not client_code: required_missing.append("ClientCode")
    if not product_code: required_missing.append("ProductCode")
    if not language: required_missing.append("Language")
    if not funnel: required_missing.append("Funnel")
    if not region: required_missing.append("Region")
    if not messaging_clean: required_missing.append("Messaging")
    if not size: required_missing.append("Size")
    if not start_date: required_missing.append("StartDate")
    if not duration: required_missing.append("Duration")

    if required_missing:
        warnings.append("Missing: " + ", ".join(required_missing))

    return name, " | ".join(warnings)

def is_valid_url(u: str) -> bool:
    if not u or not str(u).strip():
        return True
    try:
        p = urlparse(str(u).strip())
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False

def cartesian_generate(config: dict) -> pd.DataFrame:
    combos = itertools.product(
        config["funnels"],
        config["messages"],
        config["regions"],
        config["languages"],
        config["durations"],
        config["sizes"],
    )

    rows = []
    for funnel, msg, region, lang, dur, size in combos:
        name, warn = build_name(
            year=config["year"],
            client_code=config["client_code"],
            product_code=config["product_code"],
            language=lang,
            funnel=funnel,
            region=region,
            messaging=msg,
            size=size,
            start_date=config["start_date"],
            duration=dur,
            delivery_tag=config.get("delivery_tag", ""),
            additional_info=config.get("additional_info", ""),
            delimiter=config.get("delimiter", "_"),
        )
        rows.append({
            "Funnel": funnel,
            "Messaging": sanitize_freeform(msg),
            "Region": region,
            "Language": lang,
            "Duration": dur,
            "Size": size,
            "Creative Name": name,
            "Warnings": warn,
            "Delivery Tag": config.get("delivery_tag", ""),
            "Asset Type": config.get("asset_type", ""),
            "Start Date": fmt_date(config["start_date"]),
            "End Date": fmt_date(config["end_date"]) if config.get("end_date") else "",
            "URL": config.get("url", ""),
        })
    return pd.DataFrame(rows)

def pivot_like_sheet(df_flat: pd.DataFrame) -> pd.DataFrame:
    idx = ["Funnel", "Messaging", "Region", "Language", "Duration", "URL"]
    pivot = df_flat.pivot_table(
        index=idx,
        columns="Size",
        values="Creative Name",
        aggfunc="first",
    ).reset_index()
    return pivot

# ------------------------
# UI
# ------------------------
st.title("🦡 Badger")
st.caption("Fast bulk naming convention generator for AEs — few clicks, many outputs.")

left, right = st.columns([1, 1.35], gap="large")

with left:
    st.subheader("Shared fields (set once)")
    LOB_PRESETS = {
        "Business": {"client_code": "RNS", "product_code": "BRA"},
        "Wireless": {"client_code": "RCS", "product_code": "WLS"},
        "Connected Home": {"client_code": "RHE", "product_code": "IGN"},
        "Rogers Bank": {"client_code": "RBG", "product_code": "RBK"},
        "Corporate Brand": {"client_code": "RCP", "product_code": "RCB"},
        "Shaw Direct": {"client_code": "RSH", "product_code": "CBL"},
        "Custom": {"client_code": "", "product_code": ""},
    }

    if "client_code" not in st.session_state: st.session_state.client_code = "RNS"
    if "product_code" not in st.session_state: st.session_state.product_code = "BRA"
    if "lob" not in st.session_state: st.session_state.lob = "Business"

    def apply_lob_preset():
        preset = LOB_PRESETS.get(st.session_state.lob, None)
        if preset:
            if preset["client_code"] != "": st.session_state.client_code = preset["client_code"]
            if preset["product_code"] != "": st.session_state.product_code = preset["product_code"]

    year = st.number_input("Year", min_value=2000, max_value=2100, value=2026, step=1)
    st.selectbox("LOB (prefills codes)", options=list(LOB_PRESETS.keys()), key="lob", on_change=apply_lob_preset)
    client_code = st.text_input("Client Code", key="client_code")
    product_code = st.text_input("Product Code", key="product_code")
    start_date = st.date_input("Start date", value=date.today())
    end_date = st.date_input("End date", value=date.today())
    url = st.text_input("URL (optional)", value="", placeholder="https://...")
    delivery_tag = st.text_input("Delivery tag (optional)", value="")
    additional_info = st.text_input("Additional info (optional)", value="")
    delimiter = st.text_input("Delimiter", value="_")

    st.divider()
    st.subheader("Asset matrix type")
    SOCIAL_PLATFORM_SIZES = {"Meta": ["1x1", "9x16Story", "9x16Reel"], "Pinterest": ["2x3"], "Reddit": ["1x1"]}
    def union_sizes(platforms: list[str]) -> list[str]:
        out = []
        for p in platforms:
            for s in SOCIAL_PLATFORM_SIZES.get(p, []):
                if s not in out: out.append(s)
        return out

    ASSET_MATRIX_PRESETS = {
        "Social": {"durations": ["6s", "15s"]},
        "Display": {"sizes": ["300x250", "300x600", "728x90", "160x600", "970x250"], "durations": ["10s"]},
        "Video": {"sizes": ["16x9", "9x16"], "durations": ["6s", "15s", "30s"]},
    }

    if "asset_type" not in st.session_state: st.session_state.asset_type = "Social"
    if "social_platforms" not in st.session_state: st.session_state.social_platforms = list(SOCIAL_PLATFORM_SIZES.keys())
    if "sizes" not in st.session_state:
        if st.session_state.asset_type == "Social": st.session_state.sizes = union_sizes(st.session_state.social_platforms)
        else: st.session_state.sizes = ASSET_MATRIX_PRESETS[st.session_state.asset_type]["sizes"].copy()
    if "durations" not in st.session_state: st.session_state.durations = ASSET_MATRIX_PRESETS[st.session_state.asset_type]["durations"].copy()

    def apply_asset_preset():
        preset = ASSET_MATRIX_PRESETS.get(st.session_state.asset_type)
        if not preset: return
        if st.session_state.asset_type == "Social":
            st.session_state.sizes = union_sizes(st.session_state.social_platforms)
        else:
            st.session_state.sizes = preset["sizes"].copy()
        st.session_state.durations = preset["durations"].copy()

    def apply_social_platforms():
        st.session_state.sizes = union_sizes(st.session_state.get("social_platforms", []))

    st.selectbox("What kind of asset matrix?", options=list(ASSET_MATRIX_PRESETS.keys()), key="asset_type", on_change=apply_asset_preset)
    st.multiselect("Social platforms", options=list(SOCIAL_PLATFORM_SIZES.keys()), key="social_platforms", default=list(SOCIAL_PLATFORM_SIZES.keys()), on_change=apply_social_platforms)

    st.divider()
    st.subheader("Variants")
    funnels = st.multiselect("Funnel", options=["AWR", "COS", "COV"], default=["AWR", "COS", "COV"])
    regions = st.multiselect("Region", options=["ROC", "QC", "ATL"], default=["ROC"])
    languages = st.multiselect("Language", options=["EN", "FR"], default=["EN", "FR"])
    durations = st.multiselect("Duration", options=["6s", "10s", "15s", "30s"], key="durations", default=st.session_state.durations, disabled=(st.session_state.get("asset_type") == "Display"))
    sizes = st.multiselect("Sizes", options=["1x1", "2x3", "4x3", "9x16", "9x16Story", "9x16Reel", "16x9", "300x250", "300x600", "728x90", "160x600", "970x250"], key="sizes", default=st.session_state.sizes)
    messages_text = st.text_area("Messaging", height=160, value="Lower Costs\nTransparent Pricing\nSupport")
    messages = [line.strip() for line in messages_text.splitlines() if line.strip()]

config = {
    "year": year, "client_code": client_code, "product_code": product_code, "start_date": start_date, "end_date": end_date,
    "url": url.strip(), "delivery_tag": delivery_tag.strip(), "additional_info": additional_info.strip(), "delimiter": delimiter,
    "asset_type": st.session_state.get("asset_type", ""), "funnels": funnels, "regions": regions, "languages": languages,
    "durations": durations, "sizes": sizes, "messages": messages,
}

with right:
    st.subheader("Generate")
    total = len(funnels) * len(regions) * len(languages) * len(durations) * len(sizes) * len(messages)
    st.info(f"This will generate **{total:,}** creative names.")
    mode = st.radio("Output format", options=["Sheet mode (pivot by Size)", "Trafficking mode (one row per creative)"], index=0, horizontal=True)

    if st.button("Generate naming conventions", type="primary", use_container_width=True):
        if total == 0: st.stop()
        df_flat = cartesian_generate(config)
        dupes = df_flat[df_flat.duplicated(subset=["Creative Name"], keep=False)].copy()

        if mode.startswith("Sheet"):
            df_out = pivot_like_sheet(df_flat)
            st.markdown("### Output (sheet-style)")
            
            # This is the interactive table where the URL column is editable
            edited_sheet = st.data_editor(
                df_out,
                use_container_width=True,
                column_config={
                    "URL": st.column_config.TextColumn("URL", help="Users can paste/edit URLs here", width="large")
                },
                key="sheet_editor"
            )
            
            csv_bytes = edited_sheet.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", data=csv_bytes, file_name="naming_matrix.csv", mime="text/csv", use_container_width=True)

        else:
            st.dataframe(df_flat, use_container_width=True)

        if not dupes.empty:
            st.error(f"Duplicate creative names detected!")
            st.dataframe(dupes[["Creative Name"]], use_container_width=True)

        st.markdown("### Copy-ready list")
        st.code("\n".join(df_flat["Creative Name"].tolist()), language=None)
