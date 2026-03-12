import streamlit as st
import pandas as pd
import zipfile
import io
import re
from pathlib import PurePosixPath

st.title("Bulk Creative Renamer")
st.caption("Upload a ZIP, add version history to creative names, and download a renamed ZIP.")

# =========================================================
# Helpers
# =========================================================
VERSION_SUFFIX_PATTERN = re.compile(r"^(.*?)(?:_(v\d+))?$", re.IGNORECASE)

EXPECTED_COMPONENTS = [
    "year",
    "client",
    "lob",
    "lang",
    "campaign",
    "message",
    "size",
    "date_part",
]

def split_stem_and_ext(filename: str):
    p = PurePosixPath(filename)
    return p.stem, p.suffix

def parse_filename(filename: str):
    """
    Example:
    2026_RCI_RWI_EN_Q1 Samsung NPI Launch_Double Your Storage COV QC_320x50_Mar.10.2026_v2.jpg
    """
    stem, ext = split_stem_and_ext(filename)

    m = VERSION_SUFFIX_PATTERN.match(stem)
    if m:
        base_stem = m.group(1) or ""
        version = m.group(2) or ""
    else:
        base_stem = stem
        version = ""

    parts = base_stem.split("_")

    parsed = {k: "" for k in EXPECTED_COMPONENTS}
    parsed["ext"] = ext
    parsed["version"] = version
    parsed["base_stem"] = base_stem

    if len(parts) >= 8:
        parsed["year"] = parts[0]
        parsed["client"] = parts[1]
        parsed["lob"] = parts[2]
        parsed["lang"] = parts[3]
        parsed["campaign"] = parts[4]
        parsed["message"] = parts[5]
        parsed["size"] = parts[6]
        parsed["date_part"] = "_".join(parts[7:])
    else:
        for i, key in enumerate(EXPECTED_COMPONENTS[:len(parts)]):
            parsed[key] = parts[i]

    return parsed

def rebuild_filename(row: dict):
    parts = [
        str(row.get("year", "")).strip(),
        str(row.get("client", "")).strip(),
        str(row.get("lob", "")).strip(),
        str(row.get("lang", "")).strip(),
        str(row.get("campaign", "")).strip(),
        str(row.get("message", "")).strip(),
        str(row.get("size", "")).strip(),
        str(row.get("date_part", "")).strip(),
    ]

    parts = [p for p in parts if p]
    stem = "_".join(parts)

    version = str(row.get("version", "")).strip()
    if version:
        stem = f"{stem}_{version}"

    ext = str(row.get("ext", "")).strip()
    return f"{stem}{ext}"

def load_zip_to_records(zip_bytes: bytes):
    records = []

    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue

            rel_path = info.filename
            filename = PurePosixPath(rel_path).name
            folder = str(PurePosixPath(rel_path).parent)
            parsed = parse_filename(filename)

            records.append(
                {
                    "original_path": rel_path,
                    "folder": "" if folder == "." else folder,
                    "original_filename": filename,
                    **parsed,
                }
            )

    return pd.DataFrame(records)

def apply_filters(df, folders, exts, langs, sizes, campaigns):
    filtered = df.copy()

    if folders:
        filtered = filtered[filtered["folder"].isin(folders)]
    if exts:
        filtered = filtered[filtered["ext"].isin(exts)]
    if langs:
        filtered = filtered[filtered["lang"].isin(langs)]
    if sizes:
        filtered = filtered[filtered["size"].isin(sizes)]
    if campaigns:
        filtered = filtered[filtered["campaign"].isin(campaigns)]

    return filtered

def build_new_path(row):
    new_filename = rebuild_filename(row)
    folder = str(row.get("folder", "")).strip()
    return f"{folder}/{new_filename}" if folder else new_filename

def detect_duplicates(df):
    temp = df.copy()
    temp["new_path"] = temp.apply(lambda r: build_new_path(r.to_dict()), axis=1)
    dupes = temp[temp.duplicated("new_path", keep=False)].sort_values("new_path")
    return dupes

def safe_unique_path(path_str: str, used_paths: set):
    if path_str not in used_paths:
        used_paths.add(path_str)
        return path_str

    p = PurePosixPath(path_str)
    parent = str(p.parent)
    stem = p.stem
    suffix = p.suffix

    i = 1
    while True:
        candidate_name = f"{stem}_dup{i}{suffix}"
        candidate = f"{parent}/{candidate_name}" if parent != "." else candidate_name
        if candidate not in used_paths:
            used_paths.add(candidate)
            return candidate
        i += 1

def build_output_zip(df: pd.DataFrame, original_zip_bytes: bytes):
    input_buffer = io.BytesIO(original_zip_bytes)
    output_buffer = io.BytesIO()
    used_paths = set()

    with zipfile.ZipFile(input_buffer, "r") as zin, zipfile.ZipFile(
        output_buffer, "w", zipfile.ZIP_DEFLATED
    ) as zout:
        row_lookup = {row["original_path"]: row for _, row in df.iterrows()}

        for info in zin.infolist():
            if info.is_dir():
                continue

            raw_data = zin.read(info.filename)
            row = row_lookup.get(info.filename)

            if row is None:
                new_path = info.filename
            else:
                new_path = build_new_path(row)
                new_path = safe_unique_path(new_path, used_paths)

            zout.writestr(new_path, raw_data)

    output_buffer.seek(0)
    return output_buffer


# =========================================================
# Session state
# =========================================================
if "df_original" not in st.session_state:
    st.session_state.df_original = None

if "df_working" not in st.session_state:
    st.session_state.df_working = None

if "zip_bytes" not in st.session_state:
    st.session_state.zip_bytes = None


# =========================================================
# Upload
# =========================================================
uploaded_zip = st.file_uploader("Upload ZIP file", type=["zip"])

if uploaded_zip is not None:
    zip_bytes = uploaded_zip.read()
    df_loaded = load_zip_to_records(zip_bytes)

    st.session_state.zip_bytes = zip_bytes
    st.session_state.df_original = df_loaded.copy()
    st.session_state.df_working = df_loaded.copy()

df = st.session_state.df_working

if df is None or df.empty:
    st.info("Upload a ZIP file to begin.")
    st.stop()


# =========================================================
# Sidebar filters
# =========================================================
st.sidebar.header("Filters")

if st.sidebar.button("Reset all changes", use_container_width=True):
    st.session_state.df_working = st.session_state.df_original.copy()
    st.rerun()

folder_options = sorted([f for f in df["folder"].dropna().unique().tolist() if f != ""])
ext_options = sorted(df["ext"].dropna().unique().tolist())
lang_options = sorted([x for x in df["lang"].dropna().unique().tolist() if x != ""])
size_options = sorted([x for x in df["size"].dropna().unique().tolist() if x != ""])
campaign_options = sorted([x for x in df["campaign"].dropna().unique().tolist() if x != ""])

selected_folders = st.sidebar.multiselect("Filter by folder", folder_options)
selected_exts = st.sidebar.multiselect("Filter by extension", ext_options)
selected_langs = st.sidebar.multiselect("Filter by language", lang_options)
selected_sizes = st.sidebar.multiselect("Filter by size", size_options)
selected_campaigns = st.sidebar.multiselect("Filter by campaign", campaign_options)

filtered_df = apply_filters(
    df,
    selected_folders,
    selected_exts,
    selected_langs,
    selected_sizes,
    selected_campaigns,
)

st.sidebar.write(f"Total files: **{len(df)}**")
st.sidebar.write(f"Matching files: **{len(filtered_df)}**")


# =========================================================
# Preview
# =========================================================
st.subheader("File preview")

preview_df = filtered_df.copy()
preview_df["new_filename_preview"] = preview_df.apply(lambda r: rebuild_filename(r.to_dict()), axis=1)

st.dataframe(
    preview_df[
        [
            "original_path",
            "folder",
            "year",
            "client",
            "lob",
            "lang",
            "campaign",
            "message",
            "size",
            "date_part",
            "version",
            "ext",
            "new_filename_preview",
        ]
    ],
    use_container_width=True,
    height=350,
)


# =========================================================
# Version history tool
# =========================================================
st.subheader("Add version history")

apply_scope = st.radio(
    "Apply version to:",
    ["All files", "Filtered files"],
    horizontal=True
)

if apply_scope == "All files":
    target_mask = pd.Series(True, index=df.index)
else:
    target_mask = df["original_path"].isin(filtered_df["original_path"])

st.write(f"Files to update: {int(target_mask.sum())}")

version_value = st.selectbox(
    "Choose version",
    ["v2", "v3", "v4", "v5"]
)

c1, c2 = st.columns(2)

with c1:
    if st.button("Apply version", use_container_width=True):
        updated_df = df.copy()
        updated_df.loc[target_mask, "version"] = version_value
        st.session_state.df_working = updated_df
        st.success(f"Applied {version_value} to {int(target_mask.sum())} file(s).")
        st.rerun()

with c2:
    if st.button("Remove version history", use_container_width=True):
        updated_df = df.copy()
        updated_df.loc[target_mask, "version"] = ""
        st.session_state.df_working = updated_df
        st.success(f"Removed version history from {int(target_mask.sum())} file(s).")
        st.rerun()


# =========================================================
# Manual edit
# =========================================================
st.subheader("Manual editor")

editor_source = filtered_df.copy()
editor_source["new_filename_preview"] = editor_source.apply(lambda r: rebuild_filename(r.to_dict()), axis=1)

editable_cols = [
    "folder",
    "year",
    "client",
    "lob",
    "lang",
    "campaign",
    "message",
    "size",
    "date_part",
    "version",
    "ext",
]

edited_df = st.data_editor(
    editor_source[["original_path"] + editable_cols + ["new_filename_preview"]],
    use_container_width=True,
    num_rows="fixed",
    height=320,
    key="manual_editor",
)

if st.button("Save manual edits from filtered view", use_container_width=True):
    updated_df = df.copy()
    edit_lookup = edited_df.set_index("original_path").to_dict("index")

    for idx in updated_df.index:
        op = updated_df.at[idx, "original_path"]
        if op in edit_lookup:
            for col in editable_cols:
                updated_df.at[idx, col] = edit_lookup[op][col]

    st.session_state.df_working = updated_df
    st.success("Manual edits saved.")
    st.rerun()


# =========================================================
# Final preview
# =========================================================
st.subheader("Final output preview")

final_df = st.session_state.df_working.copy()
final_df["new_filename"] = final_df.apply(lambda r: rebuild_filename(r.to_dict()), axis=1)
final_df["new_path"] = final_df.apply(lambda r: build_new_path(r.to_dict()), axis=1)

st.dataframe(
    final_df[
        [
            "original_path",
            "new_path",
            "version",
            "ext",
        ]
    ],
    use_container_width=True,
    height=300,
)

dupes = detect_duplicates(final_df)

if not dupes.empty:
    st.warning("Duplicate output paths detected. The downloaded ZIP will auto-fix duplicates with _dup1, _dup2, etc.")
    st.dataframe(
        dupes[["original_path", "new_path"]],
        use_container_width=True,
        height=220,
    )
else:
    st.success("No duplicate output paths detected.")


# =========================================================
# Download
# =========================================================
st.subheader("Download renamed ZIP")

output_zip = build_output_zip(final_df, st.session_state.zip_bytes)

st.download_button(
    label="Download renamed ZIP",
    data=output_zip.getvalue(),
    file_name="renamed_creatives.zip",
    mime="application/zip",
    use_container_width=True,
)
