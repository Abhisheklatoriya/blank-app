import streamlit as st
import pandas as pd  # FIXED: Changed from 'import pd'
from datetime import date
import itertools
from groq import Groq
import json

# 1. PAGE SETUP & STYLING
st.set_page_config(page_title="Badger Turbo", page_icon="🦡", layout="wide")

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: 800; color: #FF4B4B; margin-bottom: 5px; }
    .sub-text { color: #666; margin-bottom: 20px; }
    .stChatMessage { border-radius: 12px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# 2. CONFIGURE GROQ
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

# 3. KNOWLEDGE BASE
LOB_DATA = {
    "Connected Home": {"client": "RHE", "product": "IGN"},
    "Consumer Wireless": {"client": "RCS", "product": "WLS"},
    "Rogers Business": {"client": "RNS", "product": "BRA"},
    "Rogers Bank": {"client": "RBG", "product": "RBK"},
    "Corporate Brand": {"client": "RCP", "product": "RCB"},
    "Shaw Direct": {"client": "RSH", "product": "CBL"},
}

PLATFORM_SIZES = {
    "Meta": ["1x1 Meta", "9x16 Story", "9x16 Reel"],
    "Pinterest": ["2x3 Pinterest", "1x1 Pinterest", "9x16 Pinterest"],
    "Reddit": ["1x1 Reddit", "4x5 Reddit", "16x9 Reddit"],
    "Display": ["300x250", "728x90", "160x600", "300x600", "970x250"]
}

# 4. THE MATRIX ENGINE
def generate_matrix(data):
    lob = data.get("lob", "Connected Home")
    m_type = data.get("matrix_type", "Social")
    platforms = data.get("platforms", ["Meta"])
    title = data.get("camp_title", "Campaign").replace(" ", "-")
    codes = LOB_DATA.get(lob, {"client": "ROG", "product": "GEN"})
    
    sizes = []
    if m_type.lower() == "social":
        for p in platforms:
            sizes.extend(PLATFORM_SIZES.get(p, []))
    else:
        sizes = PLATFORM_SIZES["Display"]

    rows = []
    today_str = date.today().strftime("%b.%d.%Y")
    
    combos = itertools.product(
        data.get("funnels", ["COS"]),
        data.get("messages", ["Offer_V1"]),
        data.get("regions", ["ATL"]),
        data.get("langs", ["EN"]),
        data.get("durations", ["15s"]),
        sizes
    )

    for f, m, r, l, dur, siz in combos:
        size_code = siz.split()[0]
        name_parts = ["2026", codes['client'], codes['product'], l, f"{title}-{f}-{r}", m, size_code, today_str, dur]
        creative_name = "_".join(name_parts).replace(" ", "")
        rows.append({
            "FUNNEL": f, "MESSAGING": m, "REGION": r, "LANGUAGE": l, 
            "DURATION": dur, "Size": siz, "Creative Name": creative_name
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        pivot = df.pivot_table(index=["FUNNEL", "MESSAGING", "REGION", "LANGUAGE", "DURATION"], 
                               columns="Size", values="Creative Name", aggfunc="first").reset_index()
        pivot["URL"] = ""
        st.session_state.matrix_df = pivot
        return True
    return False

# 5. UI LAYOUT
st.markdown('<div class="main-header">🦡 Badger Turbo</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-text">AI Asset Matrix Operator powered by Groq.</div>', unsafe_allow_html=True)

chat_col, table_col = st.columns([1, 1.8], gap="large")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Badger Turbo is online. What LOB and campaign title are we building today?"}]

with chat_col:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.write(msg["content"])

    if prompt := st.chat_input("Ex: Create a Social Meta matrix for Connected Home..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)

        system_prompt = f"""
        Extract marketing parameters as JSON. Available LOBs: {list(LOB_DATA.keys())}.
        Keys: lob, matrix_type, platforms (list), camp_title, funnels (list), regions (list), langs (list), messages (list), durations (list).
        """
        
        try:
            with st.spinner("Badger is calculating..."):
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                structured_data = json.loads(response.choices[0].message.content)
                if generate_matrix(structured_data):
                    bot_msg = f"⚡ Matrix live for **{structured_data['lob']}**!"
                else:
                    bot_msg = "Hmm, something went wrong with the data extraction."
                
                st.session_state.messages.append({"role": "assistant", "content": bot_msg})
                st.rerun()
        except Exception as e:
            st.error(f"API Error: {str(e)}")

with table_col:
    if "matrix_df" in st.session_state:
        st.subheader("📊 Matrix Preview")
        edited_df = st.data_editor(st.session_state.matrix_df, use_container_width=True, hide_index=True)
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV", data=csv, file_name="Badger_Matrix.csv", use_container_width=True)
    else:
        st.info("The matrix will appear here once you chat with Badger.")
