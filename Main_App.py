import streamlit as st
import os

# --- 1. Global Page Config ---
st.set_page_config(page_title="Badger Tools", page_icon="🦡", layout="wide")

# Custom CSS for a clean, professional look and "App Cards"
st.markdown("""
    <style>
    /* Hide the default Streamlit sidebar and header for a cleaner look */
    [data-testid="stSidebar"] {display: none;}
    [data-testid="stHeader"] {display: none;}
    
    .main { background-color: #ffffff; }
    
    /* Card Styles */
    .app-card {
        border: 1px solid #e6e6e6;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        background-color: #fcfcfc;
        transition: 0.3s;
    }
    
    /* Button Styling */
    div.stButton > button {
        border-radius: 10px;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. Initialize Session State ---
if 'page' not in st.session_state:
    st.session_state.page = 'home'

# --- 3. App Definitions ---
# Ensure these filenames match your GitHub exactly
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
                # Use current globals so Streamlit functions work correctly
                exec(code, globals())
            except st.errors.StreamlitAPIException as e:
                if "set_page_config" in str(e):
                    pass # Ignore if the sub-app has its own config
                else:
                    raise e
    else:
        st.error(f"⚠️ File not found: {file_path}")

# --- 4. TOP NAVIGATION BAR (Always Visible) ---
nav_col1, nav_col2, nav_col3 = st.columns([1, 4, 1])

with nav_col1:
    if st.session_state.page != 'home':
        if st.button("⬅️ Back to Home"):
            st.session_state.page = 'home'
            st.rerun()

with nav_col2:
    if st.session_state.page == 'home':
        st.markdown("<h2 style='text-align: center; margin-top:-10px;'>🦡 Badger Tools Hub</h2>", unsafe_allow_html=True)
    else:
        st.markdown(f"<h3 style='text-align: center; margin-top:-10px;'>Running: {st.session_state.page}</h3>", unsafe_allow_html=True)

st.divider()

# --- 5. PAGE LOGIC ---
if st.session_state.page == 'home':
    st.write("") # Padding
    
    # Create 3 columns for the Dashboard layout
    col1, col2, col3 = st.columns(3)
    app_list = list(APPS.items())

    # Launch Buttons in Cards
    for i, col in enumerate([col1, col2, col3]):
        name, info = app_list[i]
        with col:
            st.markdown(f"<div class='app-card'>", unsafe_allow_html=True)
            st.markdown(f"## {info['icon']}")
            st.markdown(f"**{name}**")
            st.write(info['desc'])
            if st.button(f"Open {name}", key=f"launch_{i}"):
                st.session_state.page = name
                st.rerun()
            st.markdown(f"</div>", unsafe_allow_html=True)

else:
    # Get the file for the selected app and run it
    target_file = APPS[st.session_state.page]["file"]
    run_app(target_file)
