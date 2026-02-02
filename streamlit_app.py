import streamlit as st
import pandas as pd
from datetime import date
import itertools
import re

# ------------------------
# 1. Page Configuration & Professional Styling
# ------------------------
st.set_page_config(page_title="Badger | Asset Matrix", page_icon="🦡", layout="wide")

st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #FF4B4B; margin-bottom: 0.5rem; }
    
    /* Selection tags remain large and adapt to text width */
    div[data-baseweb="tag"] {
        background-color: #FF4B4B !important;
        color: white !important;
        border-radius: 4px !important;
        padding: 6px 12px !important;
        height: auto !important;
        max-width: fit-content !important;
    }
    div[data-baseweb="tag"] span {
        font-size: 0.95rem !important;
        font-weight: 600 !important;
    }
    .stMultiSelect div[data-baseweb="select"] > div {
        min-height: 48px !important;
    }
    
    /* Standard button sizing (not full width) */
    div.stButton > button {
        width: auto !important;
        padding-left: 30px !important;
        padding-right: 30px !important;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------
# 1b. Assistant Utilities
# ------------------------
WAKE_PHRASE = "hey badger"

def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())

def extract_field(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(1).strip() if match else None

def parse_bot_message(message: str) -> dict:
    normalized = normalize_text(message).lower()
    parsed: dict[str, object] = {}

    lob_match = extract_field(r"(?:lob|line of business)\s*[:\-]?\s*([a-z0-9 &]+)", normalized)
    if lob_match:
        for lob in LOB_DATA:
            if lob.lower() in lob_match:
                parsed["lob_choice"] = lob
                break

    matrix_match = extract_field(r"(?:matrix type|matrix)\s*[:\-]?\s*(social|display)", normalized)
    if matrix_match:
        parsed["matrix_type"] = matrix_match.title()

    campaign_match = extract_field(r"(?:campaign|title)\s*[:\-]?\s*([a-z0-9 &]+)", normalized)
    if campaign_match:
        parsed["camp_title"] = campaign_match.title()

    region_match = extract_field(r"(?:region|regions)\s*[:\-]?\s*([a-z, &]+)", normalized)
    if region_match:
        parsed["regions"] = [r.strip().upper() for r in region_match.split(",") if r.strip()]

    lang_match = extract_field(r"(?:language|languages)\s*[:\-]?\s*([a-z, &]+)", normalized)
    if lang_match:
        parsed["langs"] = [l.strip().upper() for l in lang_match.split(",") if l.strip()]

    duration_match = extract_field(r"(?:duration|durations)\s*[:\-]?\s*([a-z0-9, &]+)", normalized)
    if duration_match:
        parsed["durations"] = [d.strip() for d in duration_match.split(",") if d.strip()]

    message_match = extract_field(r"(?:message|messaging)\s*[:\-]?\s*([a-z0-9 &]+)", normalized)
    if message_match:
        parsed["messages"] = [message_match.title()]

    funnel_match = extract_field(r"(?:funnel|funnels)\s*[:\-]?\s*([a-z0-9, &]+)", normalized)
    if funnel_match:
        parsed["funnels"] = [f.strip().upper() for f in funnel_match.split(",") if f.strip()]

    size_match = extract_field(r"(?:size|sizes)\s*[:\-]?\s*([a-z0-9x, &]+)", normalized)
    if size_match:
        parsed["sizes"] = [s.strip() for s in size_match.split(",") if s.strip()]

    suffix_match = extract_field(r"(?:suffix|variant)\s*[:\-]?\s*([a-z0-9 &]+)", normalized)
    if suffix_match:
        parsed["custom_suffix"] = suffix_match.title()

    return parsed

def bot_next_question(state: dict) -> str:
    if not state.get("matrix_type"):
        return "Do you want a Social or Display matrix?"
    if not state.get("lob_choice"):
        return "Which line of business should I use?"
    if not state.get("camp_title"):
        return "What campaign title should I use?"
    if not state.get("funnels"):
        return "Which funnel stages should I include?"
    if not state.get("regions"):
        return "Which regions should I include?"
    if not state.get("langs"):
        return "Which languages should I include?"
    if not state.get("durations"):
        return "Which durations should I include?"
    if not state.get("sizes"):
        return "Which sizes should I include?"
    if not state.get("messages"):
        return "What messaging lines should I use?"
    return "Ready to generate. Say 'generate' to build the matrix."

def apply_bot_updates(state: dict, updates: dict) -> dict:
    for key, value in updates.items():
        if value:
            state[key] = value
    return state

def sync_inputs_from_bot(bot_state: dict) -> None:
    st.session_state.matrix_type = bot_state.get("matrix_type", st.session_state.get("matrix_type", "Social"))
    st.session_state.lob_choice = bot_state.get("lob_choice", st.session_state.get("lob_choice", list(LOB_DATA.keys())[0]))
    st.session_state.camp_title = bot_state.get("camp_title", st.session_state.get("camp_title", "Q3 Comwave QC"))
    st.session_state.funnels = bot_state.get("funnels", st.session_state.get("funnels", ["COS"]))
    st.session_state.regions = bot_state.get("regions", st.session_state.get("regions", ["ATL"]))
    st.session_state.langs = bot_state.get("langs", st.session_state.get("langs", ["EN"]))
    st.session_state.durations = bot_state.get("durations", st.session_state.get("durations", ["15s"]))
    suggested_sizes = []
    if st.session_state.matrix_type == "Social":
        platforms = st.session_state.get("platforms", ["Meta", "Pinterest"])
        for platform in platforms:
            suggested_sizes.extend(PLATFORM_SIZES.get(platform, []))
    else:
        suggested_sizes = PLATFORM_SIZES["Display"]
    allowed_sizes = sorted(list(set(suggested_sizes + ["16x9"])))
    requested_sizes = bot_state.get("sizes", st.session_state.get("sizes", []))
    st.session_state.sizes = [s for s in requested_sizes if s in allowed_sizes]
    st.session_state.messages = bot_state.get("messages", st.session_state.get("messages", ["Internet Offer V1"]))
    st.session_state.msg_input = "\n".join(st.session_state.messages)
    st.session_state.custom_suffix = bot_state.get("custom_suffix", st.session_state.get("custom_suffix", ""))

# ------------------------
# 2. Reference Data (LOB, Client, Product)
# ------------------------
# Mappings sourced from taxonomy reference image
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
    """Format: XXXdd.yyyy (e.g., Jun.27.2025)"""
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    return f"{months[d.month-1]}.{d.day:02d}.{d.year}"

def clean_val(s: str) -> str:
    """Taxonomy Rule: No Underscores Allowed in free-form segments"""
    return (s or "").replace("_", " ").strip()

# ------------------------
# 3. Sidebar / Input Panel
# ------------------------
st.markdown('<div class="main-header">🦡 Badger | 2026 Asset Matrix</div>', unsafe_allow_html=True)

if "bot_state" not in st.session_state:
    st.session_state.bot_state = {
        "matrix_type": "Social",
        "lob_choice": list(LOB_DATA.keys())[0],
        "camp_title": "Q3 Comwave QC",
        "funnels": ["COS"],
        "regions": ["ATL"],
        "langs": ["EN"],
        "durations": ["15s"],
        "sizes": [],
        "messages": ["Internet Offer V1"],
        "custom_suffix": "",
    }

if "bot_history" not in st.session_state:
    st.session_state.bot_history = [
        {"role": "assistant", "content": "Say 'hey badger' to start building an asset matrix."}
    ]
if "bot_active" not in st.session_state:
    st.session_state.bot_active = False
if "bot_generate" not in st.session_state:
    st.session_state.bot_generate = False

left, right = st.columns([1.2, 2.8], gap="large")

with left:
    with st.container(border=True):
        st.markdown("### 🤖 Badger Assistant")
        st.caption("Use “hey badger” and describe what you want. I’ll ask follow-up questions.")

        for message in st.session_state.bot_history[-6:]:
            if message["role"] == "assistant":
                st.markdown(f"**Badger:** {message['content']}")
            else:
                st.markdown(f"**You:** {message['content']}")

        bot_input = st.text_input("Talk to Badger", placeholder="Hey Badger, build me an asset matrix...", key="bot_input")
        if st.button("Send to Badger"):
            user_message = normalize_text(bot_input)
            if not user_message:
                st.session_state.bot_history.append({"role": "assistant", "content": "Share a request so I can help."})
            else:
                st.session_state.bot_history.append({"role": "user", "content": user_message})

                if WAKE_PHRASE in user_message.lower():
                    st.session_state.bot_active = True

                if st.session_state.bot_active:
                    updates = parse_bot_message(user_message)
                    st.session_state.bot_state = apply_bot_updates(st.session_state.bot_state, updates)
                    sync_inputs_from_bot(st.session_state.bot_state)
                    next_question = bot_next_question(st.session_state.bot_state)
                    st.session_state.bot_history.append({"role": "assistant", "content": next_question})
                elif "generate" in user_message.lower():
                    st.session_state.bot_generate = True
                    st.session_state.bot_history.append({"role": "assistant", "content": "On it. Generating your matrix now."})
                else:
                    st.session_state.bot_history.append(
                        {"role": "assistant", "content": "Start with “hey badger” so I can capture your request."}
                    )

    # --- SECTION 1: Matrix Type ---
    with st.container(border=True):
        st.markdown("### 🛠️ 1. Matrix Configuration")
        matrix_type = st.radio(
            "Asset Matrix Type",
            ["Social", "Display"],
            horizontal=True,
            key="matrix_type",
        )
        
        suggested_sizes = []
        if matrix_type == "Social":
            platforms = st.multiselect(
                "Platforms",
                ["Meta", "Pinterest", "Reddit"],
                default=["Meta", "Pinterest"],
                key="platforms",
            )
            for p in platforms:
                suggested_sizes.extend(PLATFORM_SIZES[p])
        else:
            suggested_sizes = PLATFORM_SIZES["Display"]

    # --- SECTION 2: Identity (LOB Intelligence Restored) ---
    with st.container(border=True):
        st.markdown("### 📋 2. Identity")
        # Restored LOB Selector
        lob_choice = st.selectbox(
            "Line of Business",
            options=list(LOB_DATA.keys()),
            index=list(LOB_DATA.keys()).index(st.session_state.get("lob_choice", list(LOB_DATA.keys())[0])),
            key="lob_choice",
        )
        
        # Pre-filled based on LOB choice
        c1, c2 = st.columns(2)
        client_code = c1.text_input("Client Code", value=LOB_DATA[lob_choice]["client"], key="client_code")
        product_code = c2.selectbox(
            "Product Code",
            options=PRODUCT_LIST,
            index=PRODUCT_LIST.index(LOB_DATA[lob_choice]["product"]),
            key="product_code",
        )
        
        d1, d2 = st.columns(2)
        start_date = d1.date_input("Start Date", value=date.today(), key="start_date")
        end_date = d2.date_input("End Date", value=date(2026, 3, 31), key="end_date")
        delivery_date = st.date_input("Delivery Date", value=date.today(), key="delivery_date")

    # --- SECTION 3: Campaign Builder ---
    with st.container(border=True):
        st.markdown("### 🏗️ 3. Campaign Builder")
        camp_title = st.text_input("Campaign Title (Free Form)", value="Q3 Comwave QC", key="camp_title")
        
        funnels = st.multiselect(
            "Funnel",
            ["COS", "AWR", "COV", "D3B", "D3Y", "PNX"],
            default=["COS"],
            key="funnels",
        )
        regions = st.multiselect(
            "Region",
            ["ATL", "ROC", "QC", "Halifax"],
            default=["ATL"],
            key="regions",
        )
        langs = st.multiselect("Language", ["EN", "FR"], default=["EN"], key="langs")
        
        msg_input = st.text_area("Messaging (one per line)", value="Internet Offer V1", key="msg_input")

    # --- SECTION 4: Asset Specs ---
    with st.container(border=True):
        st.markdown("### 🎨 4. Asset Specs")
        durations = st.multiselect(
            "Durations",
            ["6s", "10s", "15s", "30s", "Static"],
            default=["15s"],
            key="durations",
        )
        selected_sizes = st.multiselect(
            "Sizes",
            options=sorted(list(set(suggested_sizes + ["16x9"]))),
            default=suggested_sizes,
            key="sizes",
        )
        custom_suffix = st.text_input("Custom Suffix (Free Form)", placeholder="e.g. V1, Final", key="custom_suffix")

# ------------------------
# 4. Processing & Pivot Logic
# ------------------------
generate_clicked = st.button("🚀 Generate Asset Matrix", type="primary")
if generate_clicked or st.session_state.bot_generate:
    st.session_state.bot_generate = False
    st.session_state.bot_state.update(
        {
            "matrix_type": matrix_type,
            "lob_choice": lob_choice,
            "camp_title": camp_title,
            "funnels": funnels,
            "regions": regions,
            "langs": langs,
            "durations": durations,
            "sizes": selected_sizes,
            "messages": [m.strip() for m in msg_input.splitlines() if m.strip()],
            "custom_suffix": custom_suffix,
        }
    )
    messages = [m.strip() for m in msg_input.splitlines() if m.strip()]
    combos = itertools.product(funnels, messages, regions, langs, durations, selected_sizes)
    flat_data = []

    for f, m, r, l, dur, siz in combos:
        full_campaign = f"{camp_title}-{f}-{r}-{l}"
        size_code = siz.split()[0]
        
        # Taxonomy Construction
        name_parts = [
            "2026",
            client_code,
            product_code,
            l,
            clean_val(full_campaign),
            clean_val(m),
            size_code,
            fmt_date(start_date),
            clean_val(dur)
        ]
        
        creative_name = "_".join(name_parts)
        if custom_suffix:
            creative_name += f"_{clean_val(custom_suffix)}"
        
        flat_data.append({
            "FUNNEL": f, "MESSAGING": m, "REGION": r, "LANGUAGE": l, "DURATION": dur,
            "SizeLabel": siz, "Creative Name": creative_name
        })

    if flat_data:
        df = pd.DataFrame(flat_data)
        pivot_df = df.pivot_table(
            index=["FUNNEL", "MESSAGING", "REGION", "LANGUAGE", "DURATION"],
            columns="SizeLabel", values="Creative Name", aggfunc="first"
        ).reset_index()

        # Metadata Columns
        pivot_df["DELIVERY DATE"] = fmt_date(delivery_date)
        pivot_df["START DATE"] = fmt_date(start_date)
        pivot_df["END DATE"] = fmt_date(end_date)
        pivot_df["URL"] = "" 
        
        st.session_state.matrix_df = pivot_df

# ------------------------
# 5. Output with Editable Data Editor
# ------------------------
with right:
    if "matrix_df" in st.session_state:
        st.markdown(f"### 📊 Generated {matrix_type} Matrix")
        st.caption("Editable: Click cells to adjust names or paste URLs before downloading.")
        
        # Display editable table
        edited_df = st.data_editor(
            st.session_state.matrix_df, 
            use_container_width=True, 
            hide_index=True,
            num_rows="dynamic"
        )
        
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download Final Sheet", 
            data=csv, 
            file_name=f"Asset_Matrix_{lob_choice}_{matrix_type}.csv",
            mime='text/csv'
        )
    else:
        st.info("Fill out the identity and campaign sections to generate your matrix.")
