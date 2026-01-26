import streamlit as st
import pandas as pd
from datetime import date
import itertools

# ------------------------
# 1. Helper Functions
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
# 2. Configuration Data (Presets)
# ------------------------
LOB_PRESETS = {
    "Business": {"client_code": "RNS", "product_code": "BRA"},
    "Wireless": {"client_code": "RCS", "product_code": "WLS"},
    "Connected Home": {"client_code": "RHE", "product_code": "IGN"},
    "Rogers Bank": {"client_code": "RBG", "product_code": "RBK"},
    "Corporate Brand": {"client_code": "RCP", "product_code": "RCB"},
    "Shaw Direct": {"client_code": "RSH", "product_code": "CBL"},
    "Custom": {"client_code": "", "product_code": ""},
}

SOCIAL_PLATFORM_SIZES = {
    "Meta": ["1x1", "9x16Story", "9x16Reel"],
    "Pinterest": ["2x3"],
    "Reddit": ["1x1"],
    "TikTok": ["9x16Reel"],
}

ASSET_MATRIX_PRESETS = {
    "Social": {
        "durations": ["6s", "15s"],
        "sizes": [] # Dynamic based on platform
    },
    "Display": {
        "durations": ["Static"], # Often static or standard HTML5 length
        "sizes": ["300x250", "300x600", "728x90", "160x600", "970x250"]
    },
    "Video": {
        "durations": ["6s", "15s", "30s"],
        "sizes": ["16x9", "9x16"]
    },
    "Custom": {
        "durations": [],
        "sizes": []
    }
}

def union_sizes(platforms: list[str]) -> list[str]:
    out = []
    for p in platforms:
        for s in SOCIAL_PLATFORM_SIZES.get(p, []):
            if s not in out:
                out.append(s)
    return out

# ------------------------
# 3. State Management
# ------------------------
st.set_page_config(page_title="Badger – Asset Matrix Generator", page_icon="🦡", layout="wide")

# Initialize session state for inputs if not present
if "client_code_input" not in st.session_state: st.session_state.client_code_input = "RNS"
if "product_code_input" not in st.session_state: st.session_state.product_code_input = "BRA"
if "asset_type" not in st.session_state: st.session_state.asset_type = "Social"
if "social_platforms" not in st.session_state: st.session_state.social_platforms = ["Meta"]
if "sizes_input" not in st.session_state: st.session_state.sizes_input = union_sizes(["Meta"])
if "durations_input" not in st.session_state: st.session_state.durations_input = ["6s", "15s"]

# Callbacks
def apply_lob_preset():
    preset = LOB_PRESETS.get(st.session_state.lob_select)
    if preset and st.session_state.lob_select != "Custom":
        st.session_state.client_code_input = preset["client_code"]
        st.session_state.product_code_input = preset["product_code"]

def apply_asset_type():
    atype = st.session_state.asset_type
    if atype == "Social":
        # Default back to Meta if social is selected
        st.session_state.social_platforms = ["Meta"]
        st.session_state.sizes_input = union_sizes(["Meta"])
        st.session_state.durations_input = ASSET_MATRIX_PRESETS["Social"]["durations"]
    elif atype != "Custom":
        st.session_state.sizes_input = ASSET_MATRIX_PRESETS[atype]["sizes"]
        st.session_state.durations_input = ASSET_MATRIX_PRESETS[atype]["durations"]

def apply_social_platforms():
    if st.session_state.asset_type == "Social":
        st.session_state.sizes_input = union_sizes(st.session_state.social_platforms)

# ------------------------
# 4. UI Layout
# ------------------------
st.title("🦡 Badger")

left, right = st.columns([1, 1.35], gap="large")

with left:
    st.subheader("Shared fields")
    
    # LOB Selection
    st.selectbox(
        "LOB (Prefills codes)", 
        options=list(LOB_PRESETS.keys()), 
        key="lob_select", 
        on_change=apply_lob_preset
    )
    
    col_a, col_b = st.columns(2)
    with col_a:
        client_code = st.text_input("Client Code", key="client_code_input")
    with col_b:
        product_code = st.text_input("Product Code", key="product_code_input")

    col_c, col_d = st.columns(2)
    with col_c:
        start_date = st.date_input("Start date", value=date.today())
    with col_d:
        end_date = st.date_input("End date", value=date.today())
        
    delivery_tag = st.text_input("Delivery tag (optional)")
    additional_info = st.text_input("Additional info (optional)")
    delimiter = st.text_input("Delimiter", value="_")

    st.divider()
    st.subheader("Variants")

    # Asset Matrix Type Selection
    st.selectbox(
        "Asset Matrix Type (Prefills Sizes/Durations)",
        options=list(ASSET_MATRIX_PRESETS.keys()),
        key="asset_type",
        on_change=apply_asset_type
    )

    # Conditional Social Platforms
    if st.session_state.asset_type == "Social":
        st.multiselect(
            "Social Platforms",
            options=list(SOCIAL_PLATFORM_SIZES.keys()),
            key="social_platforms",
            on_change=apply_social_platforms
        )

    # Variant Selectors
    funnels = st.multiselect("Funnel", ["AWR", "COS", "COV"], default=["AWR", "COS", "COV"])
    regions = st.multiselect("Region", ["ROC", "QC", "ATL"], default=["ROC"])
    languages = st.multiselect("Language", ["EN", "FR"], default=["EN", "FR"])
    
    # Durations & Sizes (Populated by state)
    durations = st.multiselect(
        "Duration", 
        ["Static", "6s", "10s", "15s", "30s", "60s"], 
        key="durations_input"
    )
    
    all_possible_sizes = set(st.session_state.sizes_input + [
        "1x1", "2x3", "4x5", "9x16", "9x16Story", "9x16Reel", "16x9",
        "300x250", "300x600", "728x90", "160x600", "970x250"
    ])
    
    sizes = st.multiselect(
        "Sizes", 
        options=sorted(list(all_possible_sizes)),
        key="sizes_input"
    )
    
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
    st.info(f"Generating **{total_names:,}** creative names for **{date.today().year}**.")
    
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
