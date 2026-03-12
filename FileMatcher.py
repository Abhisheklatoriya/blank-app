import streamlit as st
import pandas as pd
import zipfile
import io
import os

# DO NOT use st.set_page_config here as it's already in Main_App.py

# -----------------------------
# Reset Logic
# -----------------------------
def reset_app():
    st.session_state["file_uploader_key"] += 1
    st.session_state["data_editor_key"] += 1
    st.session_state["preview_index"] = 0
    st.session_state["zip_inner_index"] = 0

if "file_uploader_key" not in st.session_state:
    st.session_state["file_uploader_key"] = 0
if "data_editor_key" not in st.session_state:
    st.session_state["data_editor_key"] = 100
if "preview_index" not in st.session_state:
    st.session_state["preview_index"] = 0
if "zip_inner_index" not in st.session_state:
    st.session_state["zip_inner_index"] = 0

# -----------------------------
# Helpers
# -----------------------------
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
VIDEO_EXTS = {".mp4", ".mov", ".webm", ".m4v"}
ZIP_EXTS = {".zip"}

def get_extension(filename: str) -> str:
    return os.path.splitext(filename.lower())[1]

def safe_file_list(uploaded_files):
    return uploaded_files if uploaded_files else []

def preview_regular_file(file_name: str, file_bytes: bytes):
    ext = get_extension(file_name)

    st.markdown(f"**Previewing:** `{file_name}`")

    if ext in IMAGE_EXTS:
        st.image(file_bytes, use_container_width=True)

    elif ext in VIDEO_EXTS:
        st.video(file_bytes)

    elif ext in ZIP_EXTS:
        preview_zip_file(file_name, file_bytes)

    else:
        st.info("Preview is not supported for this file type.")
        st.write(f"Detected extension: `{ext or 'unknown'}`")
        st.download_button(
            "Download file",
            data=file_bytes,
            file_name=file_name,
            mime="application/octet-stream",
            key=f"download_{file_name}"
        )

def preview_zip_file(file_name: str, file_bytes: bytes):
    st.markdown(f"**ZIP archive:** `{file_name}`")

    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes), "r") as zf:
            all_names = [n for n in zf.namelist() if not n.endswith("/")]

            if not all_names:
                st.warning("This zip file is empty.")
                return

            st.write(f"Files inside zip: **{len(all_names)}**")

            previewable = []
            for name in all_names:
                ext = get_extension(name)
                if ext in IMAGE_EXTS or ext in VIDEO_EXTS:
                    previewable.append(name)

            if previewable:
                st.success(f"{len(previewable)} previewable file(s) found inside the zip.")

                # Keep index in range
                if st.session_state["zip_inner_index"] >= len(previewable):
                    st.session_state["zip_inner_index"] = 0

                zc1, zc2, zc3 = st.columns([1, 3, 1])

                with zc1:
                    if st.button("⬅️ Prev inside zip", key=f"zip_prev_{file_name}"):
                        st.session_state["zip_inner_index"] = (
                            st.session_state["zip_inner_index"] - 1
                        ) % len(previewable)

                with zc2:
                    selected_inner = st.selectbox(
                        "Select file inside zip",
                        options=list(range(len(previewable))),
                        format_func=lambda i: previewable[i],
                        index=st.session_state["zip_inner_index"],
                        key=f"zip_select_{file_name}"
                    )
                    st.session_state["zip_inner_index"] = selected_inner

                with zc3:
                    if st.button("Next inside zip ➡️", key=f"zip_next_{file_name}"):
                        st.session_state["zip_inner_index"] = (
                            st.session_state["zip_inner_index"] + 1
                        ) % len(previewable)

                inner_name = previewable[st.session_state["zip_inner_index"]]
                inner_bytes = zf.read(inner_name)
                inner_ext = get_extension(inner_name)

                st.markdown(f"**Inner preview:** `{inner_name}`")

                if inner_ext in IMAGE_EXTS:
                    st.image(inner_bytes, use_container_width=True)
                elif inner_ext in VIDEO_EXTS:
                    st.video(inner_bytes)

            else:
                st.info("No directly previewable image/video files found inside this zip.")

            with st.expander("View zip contents"):
                for item in all_names:
                    st.write(f"• `{item}`")

    except Exception as e:
        st.error(f"Could not open zip file: {e}")

# -----------------------------
# Top Header & Controls
# -----------------------------
top_col1, top_col2, top_col3 = st.columns([3, 2, 1])

with top_col1:
    st.title("📁 Dynamic File Matcher")

with top_col2:
    num_cols = st.number_input("Number of Columns to Paste", min_value=1, max_value=20, value=4)

with top_col3:
    st.write(" ")
    if st.button("🔄 Reset All", use_container_width=True, on_click=reset_app):
        st.rerun()

st.write(f"Paste your {num_cols} columns of filenames below and upload your files.")

# -----------------------------
# UI Layout
# -----------------------------
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("1. Upload Files")
    uploaded_files = st.file_uploader(
        "Upload files here",
        accept_multiple_files=True,
        key=f"uploader_{st.session_state['file_uploader_key']}"
    )

    uploaded_files = safe_file_list(uploaded_files)
    uploaded_names = set([f.name for f in uploaded_files]) if uploaded_files else set()

    if uploaded_names:
        st.success(f"✅ {len(uploaded_names)} files uploaded.")

with col2:
    st.subheader(f"2. Paste Expected Names ({num_cols} Columns)")
    column_names = [f"Col {i+1}" for i in range(num_cols)]
    init_df = pd.DataFrame([["" for _ in range(num_cols)]] * 10, columns=column_names)

    pasted_df = st.data_editor(
        init_df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key=f"editor_{st.session_state['data_editor_key']}_{num_cols}"
    )

st.divider()

# -----------------------------
# Process the comparison
# -----------------------------
has_uploaded = len(uploaded_names) > 0
has_pasted = not pasted_df.replace('', pd.NA).dropna(how='all').empty

if not has_uploaded and not has_pasted:
    st.info("Waiting for file uploads and pasted data...")
else:
    raw_pasted_names = pasted_df.values.flatten()
    expected_names = set([str(name).strip() for name in raw_pasted_names if str(name).strip()])

    matched = expected_names.intersection(uploaded_names)
    missing = expected_names - uploaded_names
    extra = uploaded_names - expected_names

    st.subheader("3. Match Analysis")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Expected", len(expected_names))
    m2.metric("Successfully Matched", len(matched))
    m3.metric("Missing Files", len(missing))
    m4.metric("Extra Uploads", len(extra))

    st.write("---")

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

# -----------------------------
# File Previewer (Bottom)
# -----------------------------
st.divider()
st.subheader("4. File Previewer")

if uploaded_files:
    # Keep preview index valid
    if st.session_state["preview_index"] >= len(uploaded_files):
        st.session_state["preview_index"] = 0

    p1, p2, p3 = st.columns([1, 3, 1])

    with p1:
        if st.button("⬅️ Previous File", use_container_width=True):
            st.session_state["preview_index"] = (
                st.session_state["preview_index"] - 1
            ) % len(uploaded_files)

    with p2:
        selected_index = st.selectbox(
            "Choose uploaded file",
            options=list(range(len(uploaded_files))),
            index=st.session_state["preview_index"],
            format_func=lambda i: uploaded_files[i].name
        )
        st.session_state["preview_index"] = selected_index

    with p3:
        if st.button("Next File ➡️", use_container_width=True):
            st.session_state["preview_index"] = (
                st.session_state["preview_index"] + 1
            ) % len(uploaded_files)

    current_file = uploaded_files[st.session_state["preview_index"]]
    current_bytes = current_file.getvalue()

    st.caption(
        f"File {st.session_state['preview_index'] + 1} of {len(uploaded_files)}"
    )

    info1, info2, info3 = st.columns(3)
    info1.metric("Filename", current_file.name)
    info2.metric("Type", current_file.type if current_file.type else "Unknown")
    info3.metric("Size (KB)", round(len(current_bytes) / 1024, 2))

    preview_regular_file(current_file.name, current_bytes)

else:
    st.info("Upload files to use the previewer.")
