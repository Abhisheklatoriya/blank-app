import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dynamic File Matcher", layout="wide")

# --- Reset Logic ---
def reset_app():
    st.session_state["file_uploader_key"] += 1
    st.session_state["data_editor_key"] += 1

if "file_uploader_key" not in st.session_state:
    st.session_state["file_uploader_key"] = 0
if "data_editor_key" not in st.session_state:
    st.session_state["data_editor_key"] = 100

# --- Top Header & Controls ---
top_col1, top_col2, top_col3 = st.columns([3, 2, 1])

with top_col1:
    st.title("📁 Dynamic File Matcher")

with top_col2:
    # Use a number input to let users expand or shrink columns
    num_cols = st.number_input("Number of Columns to Paste", min_value=1, max_value=20, value=4)

with top_col3:
    st.write(" ") # Padding
    if st.button("🔄 Reset All", use_container_width=True, on_click=reset_app):
        st.rerun()

st.write(f"Paste your {num_cols} columns of filenames below and upload your files.")

# --- UI Layout ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("1. Upload Files")
    uploaded_files = st.file_uploader(
        "Upload files here", 
        accept_multiple_files=True,
        key=f"uploader_{st.session_state['file_uploader_key']}"
    )
    uploaded_names = set([f.name for f in uploaded_files]) if uploaded_files else set()
    
    if uploaded_names:
        st.success(f"✅ {len(uploaded_names)} files uploaded.")

with col2:
    st.subheader(f"2. Paste Expected Names ({num_cols} Columns)")
    
    # Dynamically create the column list based on user input
    column_names = [f"Col {i+1}" for i in range(num_cols)]
    
    # Initialize the table with the dynamic number of columns
    init_df = pd.DataFrame([["" for _ in range(num_cols)]] * 10, columns=column_names)
    
    pasted_df = st.data_editor(
        init_df, 
        num_rows="dynamic", 
        use_container_width=True,
        hide_index=True,
        key=f"editor_{st.session_state['data_editor_key']}_{num_cols}" # Key changes if col count changes
    )

st.divider()

# --- Process the comparison ---
has_uploaded = len(uploaded_names) > 0
has_pasted = not pasted_df.replace('', pd.NA).dropna(how='all').empty

if not has_uploaded and not has_pasted:
    st.info("Waiting for file uploads and pasted data...")
else:
    # Flatten all dynamic columns into a single list
    raw_pasted_names = pasted_df.values.flatten()
    expected_names = set([str(name).strip() for name in raw_pasted_names if str(name).strip()])

    st.subheader("3. Match Analysis")
    
    missing = expected_names - uploaded_names
    extra = uploaded_names - expected_names

    if not missing and expected_names:
        st.success("✨ All pasted filenames were found in the uploaded batch!")
        if not extra:
            st.balloons()
    
    res_a, res_b = st.columns(2)
    
    with res_a:
        if missing:
            st.error(f"❌ Missing Files ({len(missing)})")
            for m in sorted(missing):
                st.write(f"• `{m}`")
        elif has_pasted:
            st.success("✅ All listed files are present.")

    with res_b:
        if extra:
            st.warning(f"➕ Extra Files ({len(extra)})")
            for e in sorted(extra):
                st.write(f"• `{e}`")
