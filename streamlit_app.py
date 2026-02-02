import streamlit as st
import pandas as pd
from datetime import date
import itertools
from groq import Groq
import json

# 1. PAGE SETUP
st.set_page_config(page_title="Badger Turbo | Groq AI", page_icon="🦡", layout="wide")

st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #FF4B4B; margin-bottom: 1rem; }
    .stChatMessage { border-radius: 12px; border: 1px solid #f0f2f6; background-color: #fafafa; }
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
def run_matrix_logic(params):
    """Local Python logic to build the CSV data based on AI-extracted params."""
    lob = params.get("lob", "Connected Home")
    m_type = params.get("matrix_type", "Social")
    platforms = params.get("platforms", ["Meta"])
    title = params.get("camp_title", "Campaign")
    
    # Get LOB Codes
    codes = LOB_DATA.get(lob, {"client": "ROG", "product": "GEN"})
    
    # Resolve Sizes
    sizes = []
    if m_type.lower() == "social":
        for p in platforms: sizes.extend(PLATFORM_SIZES.get(p, []))
    else:
        sizes = PLATFORM_SIZES["Display"]

    # Combinations
    rows = []
    today = date.today().strftime("%b.%d.%Y")
    
    # Loops based on AI parameters
    for f, m, r, l, dur, siz in itertools.product(
        params.get("funnels", ["COS"]),
        params.get("messages", ["Offer V1"]),
        params.get("regions", ["ATL"]),
        params.get("langs", ["EN"]),
        params.get("durations", ["15s"]),
        sizes
    ):
        name = f"2026_{codes['client']}_{codes['product']}_{l}_{title}-{f}-{r}_{m}_{siz.split()[0]}_{today}_{dur}"
        rows.append({
            "FUNNEL": f, "MESSAGING": m, "REGION": r, "LANGUAGE": l, 
            "DURATION": dur, "SizeLabel": siz, "Creative Name": name.replace(" ", "")
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        pivot = df.pivot_table(index=["FUNNEL", "MESSAGING", "REGION", "LANGUAGE", "DURATION"], 
                               columns="SizeLabel", values="Creative Name", aggfunc="first").reset_index()
        pivot["URL"] = ""
        st.session_state.matrix_data = pivot
        return True
    return False

# 5. UI & CHAT LOGIC
st.markdown('<div class="main-header">🦡 Badger Turbo (Groq-Powered)</div>', unsafe_allow_html=True)

chat_col, table_col = st.columns([1, 1.8], gap="large")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [{"role": "assistant", "content": "Badger here. Ready to build. What LOB are we focusing on?"}]

with chat_col:
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]): st.write(msg["content"])

    if prompt := st.chat_input("Ex: Build a Meta social matrix for Rogers Business, title 'Spring Biz'..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)

        # AI EXTRACTION CALL
        sys_msg = f"""
        Extract marketing parameters from: "{prompt}". 
        Available LOBs: {list(LOB_DATA.keys())}.
        Return a JSON object ONLY with: 
        lob, matrix_type (Social/Display), platforms (list), camp_title, funnels (list), regions (list), langs (list), messages (list), durations (list).
        Use defaults if missing.
        """
        
        try:
            # We use Llama 3.3 for high-speed reasoning
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}],
                response_format={"type": "json_object"}
            )
            
            extracted_data = json.loads(completion.choices[0].message.content)
            
            if run_matrix_logic(extracted_data):
                bot_res = f"⚡ Matrix generated for **{extracted_data['lob']}**! Check the table."
            else:
                bot_res = "I understood the request, but couldn't generate the rows. Try adding more detail."
            
            st.session_state.chat_history.append({"role": "assistant", "content": bot_res})
            st.rerun()

        except Exception as e:
            st.error(f"Groq is checking its cooling vents. Error: {str(e)}")

with table_col:
    if "matrix_data" in st.session_state:
        st.subheader("📊 Live Asset Matrix")
        edited = st.data_editor(st.session_state.matrix_data, use_container_width=True, hide_index=True)
        st.download_button("📥 Download Final CSV", data=edited.to_csv(index=False).encode('utf-8'), file_name="Badger_Turbo_Matrix.csv")
    else:
        st.info("Your asset matrix will appear here once Badger processes your request.")
