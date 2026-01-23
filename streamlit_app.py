import streamlit as st
import pandas as pd
from datetime import date, datetime
import itertools

st.set_page_config(page_title="Bulk Naming Convention Generator", layout="wide")

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
            "Start Date": fmt_date(config["start_date"]),
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
st.title("Bulk Naming Convention Generator")
st.caption("Generate a full naming matrix in a few clicks (multi-select + paste list + Generate).")

left, right = st.columns([1, 1.35], gap="large")

# --- Shared fields (set once)
with left:
    st.subheader("Shared fields (set once)")

    year = st.number_input("Year", min_value=2000, max_value=2100, value=2026, step=1)

    client_code = st.text_input("Client Code (LOB)", value="RNS")
    product_code = st.text_input("Product Code", value="BRA")

    start_date = st.date_input("Start date", value=date.today())

    delivery_tag = st.text_input("Delivery tag (optional)", value="")  # e.g., Rel / Pros
    additional_info = st.text_input("Additional info (optional)", value="")

    delimiter = st.text_input("Delimiter", value="_")

    st.divider()

    st.subheader("Variants")

    funnels = st.multiselect("Funnel", options=["AWR", "COS", "COV"], default=["AWR", "COS", "COV"])
    regions = st.multiselect("Region", options=["ROC", "QC", "ATL"], default=["ROC"])
    languages = st.multiselect("Language", options=["EN", "FR"], default=["EN", "FR"])
    durations = st.multiselect("Duration", options=["6s", "10s", "15s", "30s"], default=["15s"])

    sizes = st.multiselect(
        "Sizes",
        options=["1x1", "4x3", "9x16", "16x9", "300x250", "300x600", "728x90"],
        default=["1x1", "4x3", "9x16", "16x9"],
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
