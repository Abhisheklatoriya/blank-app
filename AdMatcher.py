import streamlit as st
import dropbox
import re

try:
    from docx import Document
except ImportError:
    st.error("Missing library: Please add 'python-docx' to your requirements.txt")
    st.stop()

# ----------------------------
# Page setup
# ----------------------------
try:
    st.set_page_config(page_title="Ad Matcher: Parent Brands", layout="wide")
except st.errors.StreamlitAPIException:
    # If rerun / already set, ignore
    pass

st.title("🎯 Ad Matcher")

# ----------------------------
# Dropbox client
# ----------------------------
# NOTE:
# If your secret is truly a refresh_token, Dropbox SDK usually needs an OAuth flow.
# Many setups actually store an ACCESS TOKEN here. We'll keep your naming but add a helpful error.
try:
    DROPBOX_TOKEN = st.secrets["dropbox"]["refresh_token"]
except Exception:
    st.error("🔑 Dropbox Configuration Error. Missing st.secrets['dropbox']['refresh_token'].")
    st.stop()

try:
    dbx = dropbox.Dropbox(DROPBOX_TOKEN)
    # Lightweight check
    dbx.users_get_current_account()
except Exception as e:
    st.error(
        "🔑 Dropbox Authentication Error.\n\n"
        "Your token may be invalid or it might be a *refresh token* being used as an *access token*.\n"
        f"Details: {e}"
    )
    st.stop()

# ----------------------------
# Upload
# ----------------------------
uploaded_docx = st.file_uploader(
    "📂 Upload Word Document (.docx)",
    type=["docx"],
    key="admatcher_uploader"
)

if uploaded_docx:
    # ----------------------------
    # Index Dropbox once
    # ----------------------------
    with st.spinner("🔍 Indexing Dropbox Assets..."):
        try:
            result = dbx.files_list_folder("", recursive=True)
            all_files = list(result.entries)
            while result.has_more:
                result = dbx.files_list_folder_continue(result.cursor)
                all_files.extend(result.entries)
        except Exception as e:
            st.error(f"Dropbox Access Error: {e}")
            st.stop()

    # ----------------------------
    # Parse DOCX into ads
    # ----------------------------
    doc = Document(uploaded_docx)
    full_text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])

    # Split where an 8-digit code occurs, keeping the delimiter
    chunks = re.split(r"(\b\d{8}\b)", full_text)

    ad_data = []

    def get_parent_brand(text: str) -> str:
        text = (text or "").lower()
        if any(x in text for x in ["bell", "bce", "ctv"]):
            return "Bell"
        if "telus" in text:
            return "Telus"
        if "fizz" in text:
            return "Fizz"
        if "videotron" in text or "quebecor" in text:
            return "Videotron"
        if "freedom" in text:
            return "Freedom"
        return "Other"

    for i in range(1, len(chunks), 2):
        code = chunks[i].strip()
        details = chunks[i + 1] if i + 1 < len(chunks) else ""

        brand_match = re.search(r"Brand[s]?:\s*(.*)", details)
        original_brand = brand_match.group(1).strip() if brand_match else "Unknown"
        parent_brand = get_parent_brand(original_brand)

        media_match = re.search(r"Media Outlet:\s*(.*)", details)
        media_name = media_match.group(1).strip() if media_match else "Unknown"

        ad_data.append(
            {
                "code": code,
                "parent_brand": parent_brand,
                "original_brand": original_brand,
                "media": media_name,
                "details": details.strip(),
            }
        )

    # ----------------------------
    # Sidebar filters
    # ----------------------------
    st.sidebar.header("🔍 Filter Settings")
    brand_filter = st.sidebar.selectbox(
        "Select Parent Brand:",
        ["All", "Bell", "Telus", "Fizz", "Videotron", "Freedom", "Other"],
        key="admatcher_brand_filter",
    )

    filtered_ads = [
        ad for ad in ad_data
        if brand_filter == "All" or ad["parent_brand"] == brand_filter
    ]

    st.divider()
    st.subheader(f"Found {len(filtered_ads)} ads for {brand_filter}")

    # ----------------------------
    # Helper: find file by code
    # ----------------------------
    def find_dropbox_file_for_code(code: str):
        # Looks for file name containing the 8-digit code anywhere
        for f in all_files:
            if isinstance(f, dropbox.files.FileMetadata) and code in f.name:
                return f
        return None

    # ----------------------------
    # Display results
    # ----------------------------
    for idx, ad in enumerate(filtered_ads):
        code = ad["code"]
        uid = f"{idx}_{code}"

        with st.container(border=True):
            col_text, col_media = st.columns([1, 1])

            with col_text:
                st.markdown(f"### {ad['parent_brand']}")
                st.caption(f"**Original Brand:** {ad['original_brand']} | **Outlet:** {ad['media']}")
                st.info(ad["details"])

                copy_content = f"Ad Code: {code}\n{ad['details']}"
                st.text_area(
                    "Copy Details (Ctrl+C):",
                    value=copy_content,
                    height=100,
                    key=f"admatcher_textarea_{uid}",
                )

            with col_media:
                match = find_dropbox_file_for_code(code)

                if not match:
                    st.warning(f"⚠️ Code {code} not found in Dropbox.")
                    continue

                # Step 1: get temp link (separate try so UI errors don't look like Dropbox errors)
                try:
                    temp_link = dbx.files_get_temporary_link(match.path_lower).link
                except Exception as e:
                    st.error(f"Dropbox temp link error for {code}: {e}")
                    continue

                # Step 2: preview media
                fname = (match.name or "").lower()
                try:
                    if fname.endswith((".mp3", ".wav", ".m4a")):
                        st.write("🎵 **Radio Audio Preview:**")
                        st.audio(temp_link, format="audio/mp3")
                    elif fname.endswith((".mp4", ".mov")):
                        st.video(temp_link)
                    else:
                        st.image(temp_link)
                except Exception as e:
                    st.warning(f"Preview failed for {code}: {e}")

                # Step 3: download link button (NO st.link_button to avoid key/version issues)
                # Works on all Streamlit versions:
                st.markdown(f"[📥 Download {code}]({temp_link})")
