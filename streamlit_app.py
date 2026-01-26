import streamlit as st
import pandas as pd
from datetime import date, datetime
import itertools
from urllib.parse import urlparse

st.set_page_config(page_title="Badger – Asset Matrix Generator", page_icon="🦡", layout="wide")

# ------------------------
# Helpers
# ------------------------
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def fmt_date(d: date) -> str:
    return f"{MONTHS[d.month-1]}.{d.day:02d}.{d.year}"

def sanitize_freeform(s: str) -> str:
    # underscores are reserved as delimiters; replace with spaces
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
    """Returns (name, warnings). Naming order can be edited here."""

    warnings = []

    # Free-form fields
    messaging_raw = messaging
    additional_raw = additional_info

    if "_" in (messaging_raw or ""):
        warnings.append("Messaging contained '_' (replaced with spaces)")
    if "_" in (additional_raw or ""):
        warnings.append("Additional info contained '_' (replaced with spaces)")

    messaging_clean = sanitize_freeform(messaging_raw)
    additional_clean = sanitize_freeform(additional_raw)

    date_part = fmt_date(start_date)

    # Example order (adjust if your official order differs):
    # Year_Client_Product_Lang_Funnel_Region_Messaging_Size_Date_Duration_[DeliveryTag]_[Additional]
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

    # Basic missing checks
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
        return True  # allow blank
    try:
        p = urlparse(str(u).strip())
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False


def cartesian_generate(config: dict) -> pd.DataFrame:
    """Generate one row per creative (flat format)."""

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
    """Pivot to match your screenshot style: size columns with name inside cells."""
    idx = ["Funnel", "Messaging", "Region", "Language", "Duration"]
    pivot = df_flat.pivot_table(
        index=idx,
        columns="Size",
        values="Creative Name",
        aggfunc="first",
    ).reset_index()

    # Optional: put sizes in a consistent order if present
    size_cols = [c for c in pivot.columns if c not in idx]
    # Keep as-is; you can sort sizes here if you want.

    return pivot


# ------------------------
# UI
# ------------------------
st.title("🦡 Badger")
st.caption("Fast bulk naming convention generator for AEs — few clicks, many outputs.")
st.caption("Generate a full naming matrix in a few clicks (multi-select + paste list + Generate).")

left, right = st.columns([1, 1.35], gap="large")

# --- Shared fields (set once)
with left:
    st.subheader("Shared fields (set once)")

    # LOB presets (edit these to match your internal taxonomy)
    LOB_PRESETS = {
        "Business": {"client_code": "RNS", "product_code": "BRA"},
        "Wireless": {"client_code": "RCS", "product_code": "WLS"},
        "Connected Home": {"client_code": "RHE", "product_code": "IGN"},
        "Rogers Bank": {"client_code": "RBG", "product_code": "RBK"},
        "Corporate Brand": {"client_code": "RCP", "product_code": "RCB"},
        "Shaw Direct": {"client_code": "RSH", "product_code": "CBL"},
        "Custom": {"client_code": "", "product_code": ""},
    }

    # Session-state defaults (so presets can update inputs)
    if "client_code" not in st.session_state:
        st.session_state.client_code = "RNS"
    if "product_code" not in st.session_state:
        st.session_state.product_code = "BRA"
    if "lob" not in st.session_state:
        st.session_state.lob = "Business"

    def apply_lob_preset():
        preset = LOB_PRESETS.get(st.session_state.lob, None)
        if not preset:
            return
        # Only overwrite when preset has values (Custom keeps user's typed values)
        if preset.get("client_code") is not None:
            if preset["client_code"] != "":
                st.session_state.client_code = preset["client_code"]
        if preset.get("product_code") is not None:
            if preset["product_code"] != "":
                st.session_state.product_code = preset["product_code"]

    year = st.number_input("Year", min_value=2000, max_value=2100, value=2026, step=1)

    st.selectbox(
        "LOB (prefills codes)",
        options=list(LOB_PRESETS.keys()),
        key="lob",
        on_change=apply_lob_preset,
    )

    client_code = st.text_input("Client Code", key="client_code")
    product_code = st.text_input("Product Code", key="product_code")

    start_date = st.date_input("Start date", value=date.today())
    end_date = st.date_input("End date", value=date.today())

    url = st.text_input("URL (optional)", value="", placeholder="https://...")
    if url and not is_valid_url(url):
        st.warning("URL looks invalid. Please use a full http(s) URL, e.g. https://example.com")

    delivery_tag = st.text_input("Delivery tag (optional)", value="")  # e.g., Rel / Pros
    additional_info = st.text_input("Additional info (optional)", value="")

    delimiter = st.text_input("Delimiter", value="_")

    st.divider()

    st.subheader("Asset matrix type")

    # Asset matrix presets (edit these once, and AEs will be fast)
    ASSET_MATRIX_PRESETS = {
        "Social": {
            "sizes": ["1x1", "4x3", "9x16", "16x9"],
            "durations": ["6s", "15s"],
        },
        "Display": {
            "sizes": ["300x250", "300x600", "728x90", "160x600", "970x250"],
            "durations": ["10s"],
        },
        "Video": {
            "sizes": ["16x9", "9x16"],
            "durations": ["6s", "15s", "30s"],
        },
    }

    if "asset_type" not in st.session_state:
        st.session_state.asset_type = "Social"

    if "sizes" not in st.session_state:
        st.session_state.sizes = ASSET_MATRIX_PRESETS[st.session_state.asset_type]["sizes"].copy()
    if "durations" not in st.session_state:
        st.session_state.durations = ASSET_MATRIX_PRESETS[st.session_state.asset_type]["durations"].copy()

    def apply_asset_preset():
        preset = ASSET_MATRIX_PRESETS.get(st.session_state.asset_type)
        if not preset:
            return
        st.session_state.sizes = preset["sizes"].copy()
        st.session_state.durations = preset["durations"].copy()

    st.selectbox(
        "What kind of asset matrix?",
        options=list(ASSET_MATRIX_PRESETS.keys()),
        key="asset_type",
        on_change=apply_asset_preset,
    )

    st.divider()
    st.subheader("Variants")

    funnels = st.multiselect("Funnel", options=["AWR", "COS", "COV"], default=["AWR", "COS", "COV"])
    regions = st.multiselect("Region", options=["ROC", "QC", "ATL"], default=["ROC"])
    languages = st.multiselect("Language", options=["EN", "FR"], default=["EN", "FR"])
    # Disable duration selection for Display assets
disable_duration = st.session_state.get("asset_type") == "Display"

durations = st.multiselect(
    "Duration",
    options=["6s", "10s", "15s", "30s"],
    key="durations",
    default=st.session_state.durations,
    disabled=disable_duration,
)
        "Duration",
        options=["6s", "10s", "15s", "30s"],
        key="durations",
        default=st.session_state.durations,
    )

    sizes = st.multiselect(
        "Sizes",
        options=["1x1", "4x3", "9x16", "16x9", "300x250", "300x600", "728x90", "160x600", "970x250"],
        key="sizes",
        default=st.session_state.sizes,
    )

    st.markdown("**Messaging (paste one per line):**")
    messages_text = st.text_area(
        "",
        height=160,
        value="Lower Costs\nTransparent Pricing\nPricing\nLatest Equipment\nManagement\nSupport\nSavings",
        placeholder="Paste messages here, one per line",
        label_visibility="collapsed",
    )

    # Presets
    st.divider()
    st.subheader("Presets")

    p1, p2, p3 = st.columns(3)
    if p1.button("Standard Social Pack", use_container_width=True):
        sizes = ["1x1", "4x3", "9x16"]
        durations = ["6s", "15s"]
        regions = ["ROC", "QC"]
        languages = ["EN", "FR"]
    if p2.button("Video Pack", use_container_width=True):
        sizes = ["16x9", "9x16"]
        durations = ["6s", "15s", "30s"]
    if p3.button("Display Pack", use_container_width=True):
        sizes = ["300x250", "300x600", "728x90"]
        durations = ["10s"]

# Turn pasted lines into list
messages = [line.strip() for line in messages_text.splitlines() if line.strip()]

# Validate config
config = {
    "year": year,
    "client_code": client_code,
    "product_code": product_code,
    "start_date": start_date,
    "end_date": end_date,
    "url": url.strip(),
    "delivery_tag": delivery_tag.strip(),
    "additional_info": additional_info.strip(),
    "delimiter": delimiter,
    "funnels": funnels,
    "regions": regions,
    "languages": languages,
    "durations": durations,
    "sizes": sizes,
    "messages": messages,
}

with right:
    st.subheader("Generate")

    # quick stats
    total = len(funnels) * len(regions) * len(languages) * len(durations) * len(sizes) * len(messages)
    st.info(f"This will generate **{total:,}** creative names.")

    mode = st.radio(
        "Output format",
        options=["Sheet mode (pivot by Size)", "Trafficking mode (one row per creative)"],
        index=0,
        horizontal=True,
    )

    generate = st.button("Generate naming conventions", type="primary", use_container_width=True)

    if generate:
        if total == 0:
            st.error("Nothing to generate — select at least one option in each variant.")
            st.stop()

        if config.get("url") and not is_valid_url(config.get("url")):
            st.error("URL is invalid. Please use a full http(s) URL, e.g. https://example.com")
            st.stop()

        df_flat = cartesian_generate(config)

        # Duplicate detection (same name appearing multiple times)
        dupes = df_flat[df_flat.duplicated(subset=["Creative Name"], keep=False)].copy()

        if mode.startswith("Sheet"):
            df_out = pivot_like_sheet(df_flat)
            st.markdown("### Output (sheet-style)")
            st.dataframe(df_out, use_container_width=True)
            csv_bytes = df_out.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download CSV (sheet mode)",
                data=csv_bytes,
                file_name="naming_matrix_sheet_mode.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            df_out = df_flat
            st.markdown("### Output (trafficking-style)")
            st.dataframe(df_out, use_container_width=True)
            csv_bytes = df_out.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download CSV (trafficking mode)",
                data=csv_bytes,
                file_name="naming_matrix_trafficking_mode.csv",
                mime="text/csv",
                use_container_width=True,
            )

        # Warnings + duplicate names
        warn_count = (df_flat["Warnings"].astype(str).str.len() > 0).sum()
        if warn_count:
            st.warning(f"Warnings found in {warn_count} row(s). Check the 'Warnings' column in trafficking mode.")

        if not dupes.empty:
            st.error(f"Duplicate creative names detected: {len(dupes)} rows share identical 'Creative Name'.")
            st.dataframe(dupes[["Funnel","Messaging","Region","Language","Duration","Size","Creative Name"]], use_container_width=True)

        # Copy-ready list
        st.markdown("### Copy-ready list (one per line)")
        st.code("\n".join(df_flat["Creative Name"].astype(str).tolist()), language=None)

st.caption(
    "Tip: If your official naming order differs, edit the `parts = [...]` list inside `build_name()` to match Rogers rules."
)
