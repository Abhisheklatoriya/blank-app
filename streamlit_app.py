import streamlit as st
import pandas as pd
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
    /* Data Editor Styling */
    .stDataEditor { border: 1px solid #ff4b4b; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# 2. CONFIGURE GROQ
# Your provided API Key
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

# 3. KNOWLEDGE BASE (Reference Data)
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
    """Local logic to process the JSON data from AI and build the DataFrame."""
    lob = data.get("lob", "Connected Home")
    m_type = data.get("matrix_type", "Social")
    platforms = data.get("platforms", ["Meta"])
    title = data.get("camp_title", "Campaign").replace(" ", "-")
    
    # Get Naming Codes
    codes = LOB_DATA.get(lob, {"client": "ROG", "product": "GEN"})
    
    # Build Size List
    sizes = []
    if m_type.lower() == "social":
        for p in platforms:
            sizes.extend(PLATFORM_SIZES.get(p, []))
    else:
        sizes = PLATFORM_SIZES["Display"]

    # Generate Combinations
    rows = []
    today_str = date.today().strftime("%b.%d.%Y")
    
    # Cartestian product of all variables
    combos = itertools.product(
        data.get("funnels", ["COS"]),
        data.get("messages", ["Offer_V1"]),
        data.get("regions", ["ATL"]),
        data.get("langs", ["EN"]),
        data.get("durations", ["15s"]),
        sizes
    )

    for f, m, r, l, dur, siz in combos:
        # 2026 Taxonomy Format
        size_code = siz.split()[0]
        name_parts = ["2026", codes['client'], codes['product'], l, f"{title}-{f}-{r}", m, size_code, today_str, dur]
        creative_name = "_".join(name_parts).replace(" ", "")
        
        rows.append({
            "FUNNEL": f, "MESSAGING": m, "REGION": r, "LANGUAGE": l, 
            "DURATION": dur, "Size": siz, "Creative Name": creative_name
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        # Pivot into a Matrix view
        pivot = df.pivot_table(index=["FUNNEL", "MESSAGING", "REGION", "LANGUAGE", "DURATION"], 
                               columns="Size", values="Creative Name", aggfunc="first").reset_index()
        pivot["URL"] = "" # Placeholder for user to paste links
        st.session_state.matrix_df = pivot
        return True
    return False

# 5. UI LAYOUT
st.markdown('<div class="main-header">🦡 Badger Turbo</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-text">The ultra-fast AI Asset Matrix Operator. Powered by Groq LPU.</div>', unsafe_allow_html=True)

chat_col, table_col = st.columns([1, 1.8], gap="large")

# Initialize Session
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "I'm ready. Tell me what campaign we're building today (LOB, Type, Platforms, etc.)"}]

with chat_col:
    # Display History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.write(msg["content"])

    # Chat Input
    if prompt := st.chat_input("Ex: Build a Meta and Pinterest social matrix for Rogers Bank..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)

        # AI Extraction
        system_prompt = f"""
        You are an expert data extractor. Identify marketing parameters for an asset matrix.
        Available LOBs: {list(LOB_DATA.keys())}.
        
        Return ONLY a JSON object. No prose.
        Keys: lob, matrix_type (Social/Display), platforms (list), camp_title, funnels (list), regions (list), langs (list), messages (list), durations (list).
        
        If specific funnels or regions aren't mentioned, use common ones like ['COS', 'AWR'] and ['ATL', 'ON'].
        """
        
        try:
            with st.spinner("Badger is thinking..."):
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                
                # Parse & Execute
                structured_data = json.loads(response.choices[0].message.content)
                success = generate_matrix(structured_data)
                
                if success:
                    bot_msg = f"Done! I've built a **{structured_data['matrix_type']}** matrix for **{structured_data['lob']}**. Check the preview!"
                else:
                    bot_msg = "I extracted the data but couldn't generate the table. Check your LOB name?"
                
                st.session_state.messages.append({"role": "assistant", "content": bot_msg})
                st.rerun()

        except Exception as e:
            st.error(f"Groq API Error: {str(e)}")

with table_col:
    if "matrix_df" in st.session_state:
        st.subheader("📊 Live Asset Matrix Preview")
        
        # Interactive Editor
        edited_df = st.data_editor(
            st.session_state.matrix_df, 
            use_container_width=True, 
            hide_index=True,
            num_rows="dynamic"
        )
        
        # Action Buttons
        c1, c2 = st.columns(2)
        with c1:
            csv = edited_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download CSV", data=csv, file_name="Badger_Output.csv", use_container_width=True)
        with c2:
            if st.button("🗑️ Clear Matrix", use_container_width=True):
                del st.session_state.matrix_df
                st.rerun()
    else:
        st.info("Your matrix will appear here once Badger has enough info.")
