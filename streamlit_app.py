import streamlit as st
import pandas as pd
from datetime import date
import itertools
import google.generativeai as genai
import time

# 1. SETUP & STYLING
st.set_page_config(page_title="Badger AI (Free Tier)", page_icon="🦡", layout="wide")

st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #FF4B4B; }
    .stChatMessage { border-radius: 10px; border: 1px solid #e0e0e0; }
</style>
""", unsafe_allow_html=True)

# 2. CONFIGURE API (Using your key)
API_KEY = "AIzaSyBbxigz5xivYy4ZbCZUH82qL7qqkRB9nI0" 
genai.configure(api_key=API_KEY)

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

# 4. GENERATION FUNCTION
def run_matrix_logic(params):
    """The engine that builds the table once the AI extracts the data."""
    try:
        lob = params.get("lob", "Connected Home")
        matrix_type = params.get("matrix_type", "Social")
        platforms = params.get("platforms", ["Meta"])
        
        client = LOB_DATA.get(lob, {}).get("client", "ROG")
        product = LOB_DATA.get(lob, {}).get("product", "GEN")
        
        sizes = []
        if matrix_type == "Social":
            for p in platforms: sizes.extend(PLATFORM_SIZES.get(p, []))
        else:
            sizes = PLATFORM_SIZES["Display"]

        # Default fallback values for demo stability
        f_list = params.get("funnels", ["COS"])
        m_list = params.get("messages", ["Offer V1"])
        r_list = params.get("regions", ["ATL"])
        l_list = params.get("langs", ["EN"])
        d_list = params.get("durations", ["15s"])
        title = params.get("camp_title", "Campaign")

        rows = []
        today = date.today().strftime("%b.%d.%Y")
        for f, m, r, l, dur, siz in itertools.product(f_list, m_list, r_list, l_list, d_list, sizes):
            name = f"2026_{client}_{product}_{l}_{title}-{f}-{r}_{m}_{siz.split()[0]}_{today}_{dur}"
            rows.append({"FUNNEL": f, "MESSAGING": m, "REGION": r, "LANGUAGE": l, "DURATION": dur, "Size": siz, "Creative Name": name})

        df = pd.DataFrame(rows)
        pivot = df.pivot_table(index=["FUNNEL", "MESSAGING", "REGION", "LANGUAGE", "DURATION"], columns="Size", values="Creative Name", aggfunc="first").reset_index()
        pivot["URL"] = ""
        st.session_state.matrix_data = pivot
        return True
    except:
        return False

# 5. UI LAYOUT
st.title("🦡 Badger AI (Free Edition)")
chat_col, table_col = st.columns([1, 1.8], gap="large")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "I'm Badger. Tell me your LOB and campaign details, and I'll generate the matrix!"}]

with chat_col:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.write(msg["content"])

    if prompt := st.chat_input("Ex: Connected Home, Social (Meta), Q3 Promo..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)

        # LIGHTWEIGHT CALL (Gemini 1.5 Flash is the cheapest/fastest)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # System instructions to extract data as JSON
        sys_prompt = f"""
        Extract marketing details from the user's request. 
        Return ONLY a JSON object with these keys: 
        lob, matrix_type, platforms (list), camp_title, funnels (list), regions (list), langs (list), messages (list), durations (list).
        If information is missing, use reasonable defaults.
        User said: {prompt}
        """
        
        try:
            response = model.generate_content(sys_prompt)
            # Find JSON in response and parse it
            raw_text = response.text.strip().replace("```json", "").replace("```", "")
            data_params = pd.read_json(raw_text, typ='series').to_dict()
            
            if run_matrix_logic(data_params):
                msg = "Matrix generated! Check the preview. Anything you want to change?"
            else:
                msg = "I understood you, but couldn't build the table. Try being more specific!"
                
            st.session_state.messages.append({"role": "assistant", "content": msg})
            with st.chat_message("assistant"): st.write(msg)
            
        except Exception as e:
            st.warning("Whoops, API is busy. Wait 10 seconds and try again!")

with table_col:
    if "matrix_data" in st.session_state:
        st.subheader("📊 Live Asset Matrix")
        edited = st.data_editor(st.session_state.matrix_data, use_container_width=True, hide_index=True)
        st.download_button("📥 Download CSV", data=edited.to_csv(index=False).encode('utf-8'), file_name="Badger_Matrix.csv")
