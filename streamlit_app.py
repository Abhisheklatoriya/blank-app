import streamlit as st
import pandas as pd
from datetime import date
import itertools
import google.generativeai as genai
from google.api_core import retry # Added for error handling

# 1. PAGE SETUP
st.set_page_config(page_title="Badger AI Operator", page_icon="🦡", layout="wide")

# 2. CONFIGURE GEMINI
API_KEY = "AIzaSyBbxigz5xivYy4ZbCZUH82qL7qqkRB9nI0" 
genai.configure(api_key=API_KEY)

# 3. REFERENCE DATA
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

# 4. ENGINE
def generate_matrix(lob, matrix_type, platforms, camp_title, funnels, regions, langs, messages, durations, custom_suffix=""):
    client = LOB_DATA.get(lob, {}).get("client", "ROG")
    product = LOB_DATA.get(lob, {}).get("product", "GEN")
    
    selected_sizes = []
    if matrix_type.lower() == "social":
        for p in platforms:
            selected_sizes.extend(PLATFORM_SIZES.get(p, []))
    else:
        selected_sizes = PLATFORM_SIZES["Display"]
    
    rows = []
    today_fmt = date.today().strftime("%b.%d.%Y")
    combos = itertools.product(funnels, messages, regions, langs, durations, selected_sizes)
    
    for f, m, r, l, dur, siz in combos:
        full_camp = f"{camp_title}-{f}-{r}-{l}"
        size_code = siz.split()[0]
        parts = ["2026", client, product, l, full_camp.replace("_"," "), m.replace("_"," "), size_code, today_fmt, dur]
        name = "_".join(parts)
        if custom_suffix:
            name += f"_{custom_suffix.replace('_',' ')}"
        rows.append({"FUNNEL": f, "MESSAGING": m, "REGION": r, "LANGUAGE": l, "DURATION": dur, "SizeLabel": siz, "Creative Name": name})

    df = pd.DataFrame(rows)
    pivot = df.pivot_table(index=["FUNNEL", "MESSAGING", "REGION", "LANGUAGE", "DURATION"], columns="SizeLabel", values="Creative Name", aggfunc="first").reset_index()
    pivot["URL"] = ""
    st.session_state.matrix_data = pivot
    return f"Success! Generated {len(pivot)} variations."

# 5. UI & CHAT
st.title("🦡 Badger AI Operator")
chat_col, table_col = st.columns([1, 1.8], gap="large")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hey! I'm Badger. Give me a campaign title and LOB to get started."}]

with chat_col:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ex: Create a Social matrix for Connected Home..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Updated Model Configuration with Retry Logic
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            tools=[generate_matrix],
            system_instruction="You are Badger. Help create marketing asset matrices. Collect all details, then call the function."
        )
        
        try:
            chat = model.start_chat(enable_automatic_function_calling=True)
            # We wrap the response in a retry to handle the 'Resource Exhausted' error
            response = chat.send_message(prompt, request_options={'retry': retry.Retry()})
            
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            with st.chat_message("assistant"):
                st.markdown(response.text)
        except Exception as e:
            st.error("Badger is a bit overwhelmed right now (API Limit). Please wait 30 seconds and try again!")

with table_col:
    if "matrix_data" in st.session_state:
        st.subheader("📊 Live Asset Matrix")
        edited_df = st.data_editor(st.session_state.matrix_data, use_container_width=True, hide_index=True)
        st.download_button("📥 Download CSV", data=edited_df.to_csv(index=False).encode('utf-8'), file_name="Badger_Matrix.csv")
