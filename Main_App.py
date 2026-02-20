import streamlit as st
import os

# --- 1. Global Page Config ---
st.set_page_config(page_title="Badger Tools Hub", page_icon="🦡", layout="wide")

# Custom CSS for the Home Page cards
st.markdown("""
    <style>
    .main { background-color: #f9f9f9; }
    div.stButton > button {
        width: 100%;
        height: 150px;
        font-size: 20px;
        font-weight: bold;
        border-radius: 15px;
        border: 1px solid #ddd;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        border-color: #FF4B4B;
        color: #FF4B4B;
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. Initialize Session State ---
if 'page' not in st.session_state:
    st.session_state.page = 'home'

# --- 3. App Definitions ---
APPS = {
    "Asset Matrix Creator": {"file": "streamlit_app.py", "icon": "🦡", "desc": "Generate naming conventions and matrix files."},
    "Ad & Creative Matcher": {"file": "AdMatcher.py", "icon": "📦", "desc": "Sync Word documents with Dropbox assets."},
    "File Matcher": {"file": "FileMatcher.py", "icon": "📁", "desc": "Bulk match and verify asset files."}
}

def run_app(file_path):
    """Executes a sub-app while handling page config errors."""
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
            try:
                # We use a clean globals dictionary to prevent apps from leaking into each other
                exec(code, globals())
            except st.errors.StreamlitAPIException as e:
                if "set_page_config" in str(e):
                    pass
                else:
                    raise e
    else:
        st.error(f"File not found: {file_path}")

# --- 4. TOP NAVIGATION BAR ---
if st.session_state.page != 'home':
    col1, col2 = st.columns([1, 8])
    with col1:
        if st.button("🏠 Home"):
            st.session_state.page = 'home'
            st.rerun()
    with col2:
        st.subheader(f"Running: {st.session_state.page}")
    st.divider()

# --- 5. PAGE LOGIC ---
if st.session_state.page == 'home':
    st.title("🦡 Badger Tools Hub")
    st.write("Welcome! Select a tool below to get started.")
    st.write("")

    # Create 3 columns for the 3 apps
    col1, col2, col3 = st.columns(3)

    cols = [col1, col2, col3]
    for idx, (app_name, info) in enumerate(APPS.items()):
        with cols[idx]:
            st.markdown(f"### {info['icon']} {app_name}")
            st.write(info['desc'])
            if st.button(f"Launch {app_name}", key=app_name):
                st.session_state.page = app_name
                st.rerun()

else:
    # Run the selected sub-app
    target_file = APPS[st.session_state.page]["file"]
    run_app(target_file)
