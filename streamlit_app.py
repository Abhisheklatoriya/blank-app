import streamlit as st
import pandas as pd
from datetime import date
import itertools
from groq import Groq
import json

# 1. PAGE SETUP
st.set_page_config(page_title="Badger AI | Smart Matrix", page_icon="🦡", layout="wide")

st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #FF4B4B; }
    .stChatMessage { border-radius: 12px; background-color: #f9f9f9; }
</style>
""", unsafe_allow_html=True)

# 2. CLIENT SETUP (Using your key)
# We use the key you provided earlier
client = Groq(api_key="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")

# 3. KNOWLEDGE BASE (The "Brain")
# We define this here so we can inject it into the AI's prompts later
LOB_KNOWLEDGE = {
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

# 4. HELPER: PYTHON TABLE BUILDER
def build_matrix_from_json(data):
    """Takes the AI's JSON output and converts it to a Pandas DataFrame."""
    try:
        lob = data.get("lob", "Connected Home")
        client_code = LOB_KNOWLEDGE.get(lob, {}).get("client", "ROG")
        prod_code = LOB_KNOWLEDGE.get(lob, {}).get("product", "GEN")
        
        # Determine sizes
        sizes = []
        if data.get("matrix_type", "Social") == "Social":
            for p in data.get("platforms", ["Meta"]):
                sizes.extend(PLATFORM_SIZES.get(p, []))
        else:
            sizes = PLATFORM_SIZES["Display"]

        # Generate rows
        rows = []
        today = date.today().strftime("%b.%d.%Y")
        
        combos = itertools.product(
            data.get("funnels", ["COS"]),
            data.get("messages", ["Offer_V1"]),
            data.get("regions", ["ATL"]),
            data.get("langs", ["EN"]),
            data.get("durations", ["15s"]),
            sizes
        )

        for f, m, r, l, dur, siz in combos:
            camp_title = data.get("camp_title", "Campaign").replace(" ", "-")
            size_code = siz.split()[0]
            # The Naming Logic
            name = f"2026_{client_code}_{prod_code}_{l}_{camp_title}-{f}-{r}_{m}_{size_code}_{today}_{dur}"
            name = name.replace(" ", "") # Clean spaces
            
            rows.append({
                "FUNNEL": f, "MESSAGING": m, "REGION": r, "LANGUAGE": l, 
                "DURATION": dur, "Size": siz, "Creative Name": name
            })

        return pd.DataFrame(rows)
    except Exception as e:
        return pd.DataFrame()

# 5. UI & CHAT LOGIC
st.markdown('<div class="main-header">🦡 Badger AI</div>', unsafe_allow_html=True)
st.caption("Powered by Groq Llama 3.3")

chat_col, table_col = st.columns([1, 1.5], gap="large")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I'm Badger. I know the taxonomy for Connected Home, Wireless, Bank, and more. What do you need?"}]

with chat_col:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.write(msg["content"])

    if prompt := st.chat_input("Ex: Build a Meta Matrix for Rogers Bank, Fall Campaign..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)

        # --- THE CORE AI LOGIC (Your Snippet Adapted) ---
        
        # We inject the knowledge into the system prompt
        system_instruction = f"""
        You are an expert Asset Matrix builder.
        You have this knowledge about Lines of Business (LOB): {json.dumps(LOB_KNOWLEDGE)}
        
        Your Goal: Extract the user's intent into a JSON object.
        Required JSON Keys: 
        - lob (Must match one of the keys in the LOB knowledge exactly)
        - matrix_type ("Social" or "Display")
        - platforms (List, e.g. ["Meta", "Pinterest"])
        - camp_title (String)
        - funnels (List of strings)
        - regions (List of strings)
        - langs (List of strings)
        - messages (List of strings)
        - durations (List of strings)
        
        If the user doesn't specify something, use smart defaults based on the context.
        """

        try:
            with st.spinner("Badger is thinking..."):
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile", # Swapped to valid Groq model
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1, # Keep it low for JSON precision
                    response_format={"type": "json_object"}, # Force JSON output
                    stop=None
                )
                
                # Get the JSON string content
                ai_content = completion.choices[0].message.content
                
                # Turn it into a Python Dictionary
                extracted_data = json.loads(ai_content)
                
                # Generate the DataFrame using our Python Helper
                df = build_matrix_from_json(extracted_data)
                
                if not df.empty:
                    # Save to session state to display on the right
                    pivot = df.pivot_table(
                        index=["FUNNEL", "MESSAGING", "REGION", "LANGUAGE", "DURATION"], 
                        columns="Size", values="Creative Name", aggfunc="first"
                    ).reset_index()
                    pivot["URL"] = ""
                    st.session_state.matrix_df = pivot
                    
                    response_msg = f"✅ I've generated the **{extracted_data['lob']}** matrix with **{len(df)}** assets. Check the right panel!"
                else:
                    response_msg = "I understood your request, but I couldn't match the LOB name. Please try again with the exact LOB name (e.g., 'Connected Home')."

                st.session_state.messages.append({"role": "assistant", "content": response_msg})
                st.rerun()
                
        except Exception as e:
            st.error(f"Error: {e}")

with table_col:
    if "matrix_df" in st.session_state:
        st.subheader("📊 Live Matrix")
        edited_df = st.data_editor(st.session_state.matrix_df, use_container_width=True, hide_index=True)
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV", data=csv, file_name="Badger_Matrix.csv", use_container_width=True)
    else:
        st.info("Chat with Badger to generate a matrix.")
