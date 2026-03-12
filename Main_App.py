import streamlit as st
import os

# --- 1. Global Page Config ---
st.set_page_config(page_title="Badger Workflows", page_icon="🦡", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    [data-testid="stSidebar"] {display: none;}
    [data-testid="stHeader"] {display: none;}

    .main {
        background-color: #ffffff;
    }

    .app-card {
        border: 1px solid #e6e6e6;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        background-color: #fcfcfc;
        transition: 0.3s;
        min-height: 220px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    div.stButton > button {
        border-radius: 10px;
        font-weight: 600;
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. Initialize Session State ---
if "page" not in st.session_state:
    st.session_state.page = "home"

# --- 3. App Definitions ---
# Make sure the filenames match exactly
APPS = {
    "Asset Matrix Creator": {
        "file": "streamlit_app.py",
        "icon": "🦡",
        "desc": "Generate naming conventions and matrix files."
    },
    "Ad & Creative Matcher": {
        "file": "AdMatcher.py",
        "icon": "📦",
        "desc": "Sync ad codes with assets."
    },
    "File Matcher": {
        "file": "FileMatcher.py",
        "icon": "📁",
        "desc": "Bulk match and verify asset files."
    },
    "Bulk Creative Renamer": {
        "file": "BulkCreativeRenamer.py",
        "icon": "✏️",
        "desc": "Upload files and bulk rename creatives by filename components, dates, and versions."
    }
}

def run_app(file_path):
    """Executes a sub-app while handling page config conflicts."""
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
            try:
                exec(code, globals())
            except st.errors.StreamlitAPIException as e:
                if "set_page_config" in str(e):
                    pass
                else:
                    raise e
    else:
        st.error(f"⚠️ File not found: {file_path}")

# --- 4. Top Navigation ---
nav_col1, nav_col2, nav_col3 = st.columns([1, 4, 1])

with nav_col1:
    if st.session_state.page != "home":
        if st.button("⬅️ Back to Home"):
            st.session_state.page = "home"
            st.rerun()

with nav_col2:
    if st.session_state.page == "home":
        st.markdown(
            "<h2 style='text-align: center; margin-top:-10px;'>🦡 Badger Tools Hub</h2>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<h3 style='text-align: center; margin-top:-10px;'>Running: {st.session_state.page}</h3>",
            unsafe_allow_html=True
        )

st.divider()

# --- 5. Home Page ---
if st.session_state.page == "home":
    st.write("")

    app_items = list(APPS.items())
    cards_per_row = 3

    for row_start in range(0, len(app_items), cards_per_row):
        row_apps = app_items[row_start:row_start + cards_per_row]
        cols = st.columns(cards_per_row)

        for col_idx, col in enumerate(cols):
            with col:
                if col_idx < len(row_apps):
                    name, info = row_apps[col_idx]

                    st.markdown("<div class='app-card'>", unsafe_allow_html=True)
                    st.markdown(f"## {info['icon']}")
                    st.markdown(f"**{name}**")
                    st.write(info["desc"])

                    if st.button(f"Open {name}", key=f"launch_{row_start}_{col_idx}"):
                        st.session_state.page = name
                        st.rerun()

                    st.markdown("</div>", unsafe_allow_html=True)

# --- 6. App Runner ---
else:
    target_file = APPS[st.session_state.page]["file"]
    run_app(target_file)
