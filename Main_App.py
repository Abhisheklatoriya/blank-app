import streamlit as st
import os

# --- 1. Global Page Config (This will be the master config) ---
st.set_page_config(page_title="Badger Tools Hub", page_icon="🦡", layout="wide")

# --- 2. Define your Apps ---
# Key: Name shown in sidebar, Value: The filename of your existing apps
APPS = {
    "🦡 Asset Matrix Creator": "streamlit_app.py",
    "📦 Smartly Asset Checker": "adMatcher.py",
    "📁 File Matcher": "FileMatcher.py" # Ensure this filename matches your 3rd app
}

def run_app(file_path):
    """Executes a python file while handling the set_page_config error."""
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
            
            # This is the 'magic' part: We wrap the code execution.
            # If the sub-app tries to call set_page_config, we catch the 
            # error so the rest of the app keeps running.
            try:
                exec(code, globals())
            except st.errors.StreamlitAPIException as e:
                if "set_page_config" in str(e):
                    # We ignore this error because the master config is already set
                    pass
                else:
                    raise e
    else:
        st.error(f"File not found: {file_path}")

# --- 3. Sidebar Navigation ---
st.sidebar.title("Badger Navigation")
selection = st.sidebar.radio("Go to:", list(APPS.keys()))

st.sidebar.divider()
st.sidebar.info("Switch between apps above without losing your current progress in this session.")

# --- 4. Launch the Selected App ---
target_file = APPS[selection]
run_app(target_file)
