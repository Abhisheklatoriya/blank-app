import streamlit as st
import pandas as pd
from datetime import date
import itertools
import google.generativeai as genai

# 1. PAGE SETUP & STYLING
st.set_page_config(page_title="Badger AI Operator", page_icon="🦡", layout="wide")

st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #FF4B4B; margin-bottom: 1rem; }
    /* Style for the chat interface */
    .stChatMessage { border-radius: 10px; margin-bottom: 10px; }
    /* Tags styling */
    div[data-baseweb="tag"] { background-color: #FF4B4B !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

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

# 4. THE CORE ENGINE (The Tool Gemini Calls)
def generate_matrix(lob, matrix_type, platforms, camp_title, funnels, regions, langs, messages, durations, custom_suffix=""):
    """
    Triggers the generation of the asset matrix. 
    LOB: Connected Home, Consumer Wireless, etc.
    Matrix Type: Social or Display.
    Platforms: List containing Meta, Pinterest, or Reddit.
    Messages: List of strings.
    """
    client = LOB_DATA.get(lob, {}).get("client", "ROG")
    product = LOB_DATA.get(lob, {}).get("product", "GEN")
    
    # Gather sizes based on type
    selected_sizes = []
    if matrix_type.lower() == "social":
        for p in platforms:
            selected_sizes.extend(PLATFORM_SIZES.get(p, []))
    else:
        selected_sizes = PLATFORM_SIZES["Display"]
    
    # Logic to build the dataframe
    rows = []
    today_fmt = date.today().strftime("%b.%d.2026")

    combos = itertools.product(funnels, messages, regions, langs, durations, selected_sizes)
    for f, m, r, l, dur, siz in combos:
        full_camp = f"{camp_title}-{f}-{r}-{l}"
        size_code = siz.split()[0]
        
        # 2026 Taxonomy
        parts = ["2026", client, product, l, full_camp.replace("_"," "), m.replace("_"," "), size_code, today_fmt, dur]
        name = "_".join(parts)
        if custom_suffix:
            name += f"_{custom_suffix.replace('_',' ')}"
            
        rows.append({
            "FUNNEL": f, "MESSAGING": m, "REGION": r, "LANGUAGE": l, "DURATION": dur,
            "SizeLabel": siz, "Creative Name": name
        })

    df = pd.DataFrame(rows)
    pivot = df.pivot_table(index=["FUNNEL", "MESSAGING", "REGION", "LANGUAGE", "DURATION"],
                           columns="SizeLabel", values="Creative Name", aggfunc="first").reset_index()
    
    # Metadata for the final sheet
    pivot["DELIVERY DATE"] = today_fmt
    pivot["URL"] = ""

    st.session_state.matrix_data = pivot
    return f"I've generated the matrix for {lob} with {len(pivot)} rows. You can see it on the right!"

# 5. UI LAYOUT
st.markdown('<div class="main-header">🦡 Badger AI Operator</div>', unsafe_allow_html=True)

chat_col, table_col = st.columns([1, 1.8], gap="large")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hey! I'm Badger. Tell me what LOB and campaign you're working on, and I'll build your matrix for you."}
    ]

with chat_col:
    # Display Chat
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    if prompt := st.chat_input("Ex: Build a Meta social matrix for Connected Home..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Gemini Logic with Tool Call
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash',
            tools=[generate_matrix],
            system_instruction=(
                "You are Badger, the AI operator for a marketing asset matrix tool. "
                "Your goal is to collect: LOB, Matrix Type (Social/Display), Platforms, Campaign Title, "
                "Funnels (e.g. COS, AWR), Regions (e.g. ATL, QC), Languages (EN, FR), Messages (List), "
                "and Durations. Be conversational. If info is missing, ask. Once you have enough info, "
                "call generate_matrix. Ensure you use the provided LOB names exactly."
            )
        )
        
        # We use a chat session that automatically handles tool calling
        chat = model.start_chat(enable_automatic_function_calling=True)
        response = chat.send_message(prompt)
        
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        with st.chat_message("assistant"):
            st.markdown(response.text)

with table_col:
    if "matrix_data" in st.session_state:
        st.subheader("📊 Generated Asset Matrix")
        st.caption("You can edit the naming conventions or paste URLs directly into the table.")
        
        # Use Data Editor for Editability
        edited_df = st.data_editor(
            st.session_state.matrix_data, 
            use_container_width=True, 
            hide_index=True,
            num_rows="dynamic"
        )
        
        # Download Button
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Final Sheet", data=csv, file_name="Badger_AI_Matrix.csv", use_container_width=True)
    else:
        st.info("Your matrix will appear here once you've provided the details to Badger.")
