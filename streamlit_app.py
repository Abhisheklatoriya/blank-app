import streamlit as st
import pandas as pd
from datetime import date, datetime

st.set_page_config(page_title="Naming Convention Creator", layout="wide")
st.title("Naming Convention Creator")

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def format_date_any(x) -> str:
    """
    Accepts: datetime/date, 'YYYY-MM-DD', 'Jun.27.2025', 'Jun 27 2025', etc.
    Returns: Mon.DD.YYYY
    """
    if x is None or (isinstance(x, float) and pd.isna(x)) or (isinstance(x, str) and not x.strip()):
        return ""

    if isinstance(x, (datetime, date)):
        d = x
        return f"{MONTHS[d.month-1]}.{d.day:02d}.{d.year}"

    s = str(x).strip()

    # Already in Mon.DD.YYYY?
    try:
        parts = s.split(".")
        if len(parts) == 3 and parts[0] in MONTHS:
            dd = int(parts[1])
            yyyy = int(parts[2])
            return f"{parts[0]}.{dd:02d}.{yyyy}"
    except Exception:
        pass

    # Try common parse
    for fmt in ("%Y-%m-%d", "%b %d %Y", "%B %d %Y", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            d = datetime.strptime(s, fmt).date()
            return f"{MONTHS[d.month-1]}.{d.day:02d}.{d.year}"
        except Exception:
            continue

    # Last resort: pandas parser
    try:
        d = pd.to_datetime(s, errors="coerce").date()
        if d:
            return f"{MONTHS[d.month-1]}.{d.day:02d}.{d.year}"
    except Exception:
        pass

    return ""  # invalid/unparsable

def sanitize_freeform(s: str) -> str:
    return (s or "").replace("_", " ").strip()

def build_name_row(row: dict):
    year = str(row.get("Year","")).strip()
    client = str(row.get("ClientCode","")).strip()
    product = str(row.get("ProductCode","")).strip()
    lang = str(row.get("Language","")).strip()

    campaign_raw = str(row.get("CampaignName","") or "")
    messaging_raw = str(row.get("Messaging","") or "")
    size = str(row.get("Size","")).strip()
    date_raw = row.get("StartDate","")
    additional_raw = str(row.get("AdditionalInfo","") or "")

    warnings = []

    # underscore validation
    underscore_fields = []
    if "_" in campaign_raw: underscore_fields.append("CampaignName")
    if "_" in messaging_raw: underscore_fields.append("Messaging")
    if "_" in additional_raw: underscore_fields.append("AdditionalInfo")
    if underscore_fields:
        warnings.append(f"Underscore(s) found in: {', '.join(underscore_fields)} (replaced with spaces).")

    campaign = sanitize_freeform(campaign_raw)
    messaging = sanitize_freeform(messaging_raw)
    additional = sanitize_freeform(additional_raw)
    date_fmt = format_date_any(date_raw)

    # missing required fields
    required = {
        "Year": year,
        "ClientCode": client,
        "ProductCode": product,
        "Language": lang,
        "CampaignName": campaign,
        "Messaging": messaging,
        "Size": size,
        "StartDate": date_fmt,
    }
    missing = [k for k,v in required.items() if not v]
    if missing:
        warnings.append("Missing: " + ", ".join(missing))

    parts = [year, client, product, lang, campaign, messaging, size, date_fmt]
    if additional:
        parts.append(additional)

    parts = [p for p in parts if p]
    output = "_".join(parts)

    return output, " | ".join(warnings)

# --- Tabs ---
tab1, tab2 = st.tabs(["Single Builder", "Bulk Builder"])

with tab1:
    st.subheader("Single Builder (quick one-off)")
    c1, c2, c3 = st.columns(3)

    with c1:
        year = st.number_input("Year", min_value=2000, max_value=2100, value=2025, step=1)
        client = st.text_input("ClientCode (LOB)", value="RHE")
        lang = st.selectbox("Language", ["EN","FR"], index=1)

    with c2:
        product = st.text_input("ProductCode", value="IGN")
        size = st.text_input("Size", value="9x16")
        start_date = st.date_input("StartDate", value=date.today())

    with c3:
        campaign = st.text_input("CampaignName (no underscore)", value="Q3 Comwave QC")
        messaging = st.text_input("Messaging (no underscore)", value="Internet Offer V1")
        additional = st.text_input("AdditionalInfo (no underscore)", value="10s.zip")

    out, warn = build_name_row({
        "Year": year,
        "ClientCode": client,
        "ProductCode": product,
        "Language": lang,
        "CampaignName": campaign,
        "Messaging": messaging,
        "Size": size,
        "StartDate": start_date,
        "AdditionalInfo": additional,
    })

    st.markdown("### Output")
    st.code(out, language=None)
    if warn:
        st.warning(warn)
    else:
        st.success("Looks good.")

with tab2:
    st.subheader("Bulk Builder (paste rows or upload CSV)")

    st.markdown(
        """
**Input columns required (header row):**  
`Year,ClientCode,ProductCode,Language,CampaignName,Messaging,Size,StartDate,AdditionalInfo`

- `StartDate` can be `YYYY-MM-DD` or `Jun.27.2025`
- Free-form fields must not contain `_` (we auto-fix but warn)
        """
    )

    sample = """Year,ClientCode,ProductCode,Language,CampaignName,Messaging,Size,StartDate,AdditionalInfo
2025,RHE,IGN,FR,Q3 Comwave QC,Internet Offer V1,9x16,2025-06-27,10s.zip
2025,RCS,WLS,EN,Q1 Always On,Bring your own phone,1x1,2025-01-10,Static
"""

    colA, colB = st.columns([1,1])

    with colA:
        uploaded = st.file_uploader("Upload CSV", type=["csv"])
        st.caption("If you upload a CSV, we’ll use it. Otherwise paste below.")

    with colB:
        pasted = st.text_area("Or paste CSV text here", value=sample, height=170)

    df = None
    if uploaded is not None:
        df = pd.read_csv(uploaded)
    else:
        try:
            df = pd.read_csv(pd.io.common.StringIO(pasted))
        except Exception as e:
            st.error("Could not parse pasted CSV. Make sure it includes a header row and commas.")
            st.stop()

    # Ensure required columns exist
    required_cols = ["Year","ClientCode","ProductCode","Language","CampaignName","Messaging","Size","StartDate","AdditionalInfo"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        st.error(f"Missing columns: {', '.join(missing_cols)}")
        st.stop()

    st.markdown("### Preview (edit before generating if you want)")
    edited = st.data_editor(df, use_container_width=True, num_rows="dynamic")

    if st.button("Generate naming conventions", type="primary", use_container_width=True):
        out_rows = []
        for _, r in edited.iterrows():
            out, warn = build_name_row(r.to_dict())
            out_rows.append({"NamingConvention": out, "Warnings": warn})

        out_df = edited.copy()
        out_df["NamingConvention"] = [x["NamingConvention"] for x in out_rows]
        out_df["Warnings"] = [x["Warnings"] for x in out_rows]

        st.markdown("### Results")
        st.dataframe(out_df, use_container_width=True)

        # Downloads
        csv_bytes = out_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download output CSV",
            data=csv_bytes,
            file_name="naming_conventions_output.csv",
            mime="text/csv",
            use_container_width=True
        )

        # Optional: quick copy block for just the names
        st.markdown("### Copy-ready list (one per line)")
        st.code("\n".join(out_df["NamingConvention"].astype(str).tolist()), language=None)
