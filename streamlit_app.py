import streamlit as st
import pandas as pd
from datetime import date, datetime
import itertools
from urllib.parse import urlparse
import streamlit.components.v1 as components

# ------------------------
# Aesthetic Feature: Eye-Tracking Badger
# ------------------------
def add_tracking_badger():
    badger_html = """
    <div id="badger-container" style="display: flex; justify-content: center; align-items: center; padding: 10px; background: #f0f2f6; border-radius: 15px;">
        <svg width="180" height="140" viewBox="0 0 200 160" xmlns="http://www.w3.org/2000/svg">
            <circle cx="60" cy="50" r="15" fill="#222" />
            <circle cx="140" cy="50" r="15" fill="#222" />
            <path d="M40 80 Q100 20 160 80 Q160 140 100 150 Q40 140 40 80" fill="#222" />
            <path d="M65 80 Q100 45 135 80 Q135 110 100 125 Q65 110 65 80" fill="white" />
            <circle cx="85" cy="85" r="10" fill="white" stroke="#333" stroke-width="1"/>
            <circle cx="115" cy="85" r="10" fill="white" stroke="#333" stroke-width="1"/>
            <circle id="left-pupil" cx="85" cy="85" r="4" fill="black" />
            <circle id="right-pupil" cx="115" cy="85" r="4" fill="black" />
            <ellipse cx="100" cy="108" rx="8" ry="5" fill="#111" />
        </svg>
    </div>
    <script>
        const leftPupil = document.getElementById('left-pupil');
        const rightPupil = document.getElementById('right-pupil');
        const leftEyePos = { x: 85, y: 85 };
        const rightEyePos = { x: 115, y: 85 };
        document.addEventListener('mousemove', (e) => {
            const mouseX = e.clientX;
            const mouseY = e.clientY;
            function movePupil(pupil, origin) {
                const rect = pupil.getBoundingClientRect();
                const eyeX = rect.left + rect.width / 2;
                const eyeY = rect.top + rect.height / 2;
                const angle = Math.atan2(mouseY - eyeY, mouseX - eyeX);
                const distance = 3.5; 
                const newX = origin.x + Math.cos(angle) * distance;
                const newY = origin.y + Math.sin(angle) * distance;
                pupil.setAttribute('cx', newX);
                pupil.setAttribute('cy', newY);
            }
            movePupil(leftPupil, leftEyePos);
            movePupil(rightPupil, rightEyePos);
        });
    </script>
    """
    components.html(badger_html, height=160)

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
    return name, ""

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
    current_year = date.today().year # Automatically detect year
    for funnel, msg, region, lang, dur, size in combos:
        name, _ = build_name(
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

with st.sidebar:
    st.markdown("### Badger Guardian")
    add_tracking_badger()
    st.divider()
    st.markdown("### Settings")
    delimiter = st.text_input("Delimiter", value="_")

st.title("🦡 Badger")

left, right = st.columns([1, 1.35], gap="large")

with left:
    st.subheader("Shared fields")
    # Year input removed; code now uses date.today().year automatically
    client_code = st.text_input("Client Code", value="RNS")
    product_code = st.text_input("Product Code", value="BRA")
    start_date = st.date_input("Start date", value=date.today())
    end_date = st.date_input("End date", value=date.today())
    delivery_tag = st.text_input("Delivery tag (optional)")
    additional_info = st.text_input("Additional info (optional)")

    st.divider()
    st.subheader("Variants")
    funnels = st.multiselect("Funnel", ["AWR", "COS", "COV"], default=["AWR", "COS", "COV"])
    regions = st.multiselect("Region", ["ROC", "QC", "ATL"], default=["ROC"])
    languages = st.multiselect("Language", ["EN", "FR"], default=["EN", "FR"])
    durations = st.multiselect("Duration", ["6s", "15s", "30s"], default=["6s", "15s"])
    sizes = st.multiselect("Sizes", ["1x1", "9x16Story", "9x16Reel", "16x9"], default=["1x1", "9x16Story"])
    messages_text = st.text_area("Messaging", value="Lower Costs\nSupport\nTransparent Pricing")
    messages = [line.strip() for line in messages_text.splitlines() if line.strip()]

config = {
    "client_code": client_code, "product_code": product_code, 
    "start_date": start_date, "end_date": end_date,
    "delivery_tag": delivery_tag, "additional_info": additional_info, "delimiter": delimiter,
    "funnels": funnels, "regions": regions, "languages": languages, 
    "durations": durations, "sizes": sizes, "messages": messages
}

with right:
    st.subheader("Generate")
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
                column_config={"URL": st.column_config.TextColumn("URL", help="Paste row-specific URLs here", width="large")},
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
