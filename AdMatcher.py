import streamlit as st
import dropbox
import re
try:
    from docx import Document
except ImportError:
    st.error("Missing library: Please add 'python-docx' to your requirements.txt")
    st.stop()

try:
    st.set_page_config(page_title="Ad Matcher: Parent Brands", layout="wide")
except st.errors.StreamlitAPIException:
    pass

st.title("🎯 Ad Matcher")

try:
    dbx = dropbox.Dropbox(st.secrets["dropbox"]["refresh_token"])
except Exception as e:
    st.error("🔑 Dropbox Configuration Error. Check your Streamlit Secrets.")
    st.stop()

uploaded_docx = st.file_uploader("📂 Upload Word Document (.docx)", type=["docx"], key="admatcher_uploader")

if uploaded_docx:
    with st.spinner("🔍 Indexing Dropbox Assets..."):
        try:
            result = dbx.files_list_folder('', recursive=True)
            all_files = result.entries
            while result.has_more:
                result = dbx.files_list_folder_continue(result.cursor)
                all_files.extend(result.entries)
        except Exception as e:
            st.error(f"Dropbox Access Error: {e}")
            st.stop()

    # --- EXTRACT & MAP BRANDS ---
    doc = Document(uploaded_docx)
    full_text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    chunks = re.split(r'(\b\d{8}\b)', full_text)

    ad_data = []

    def get_parent_brand(text):
        text = text.lower()
        if any(x in text for x in ["bell", "bce", "ctv"]): return "Bell"
        if "telus" in text: return "Telus"
        if "fizz" in text: return "Fizz"
        if "videotron" in text or "quebecor" in text: return "Videotron"
        if "freedom" in text: return "Freedom"
        return "Other"

    for i in range(1, len(chunks), 2):
        code = chunks[i]
        details = chunks[i+1] if i+1 < len(chunks) else ""

        brand_match = re.search(r'Brand[s]?:\s*(.*)', details)
        original_brand = brand_match.group(1).strip() if brand_match else "Unknown"
        parent_brand = get_parent_brand(original_brand)

        media_match = re.search(r'Media Outlet:\s*(.*)', details)
        media_name = media_match.group(1).strip() if media_match else "Unknown"

        ad_data.append({
            "code": code,
            "parent_brand": parent_brand,
            "original_brand": original_brand,
            "media": media_name,
            "details": details.strip()
        })

    # --- SIDEBAR FILTERS ---
    st.sidebar.header("🔍 Filter Settings")
    brand_filter = st.sidebar.selectbox(
        "Select Parent Brand:",
        ["All", "Bell", "Telus", "Fizz", "Videotron", "Freedom"],
        key="admatcher_brand_filter"
    )

    filtered_ads = [ad for ad in ad_data if brand_filter == "All" or ad['parent_brand'] == brand_filter]

    st.divider()
    st.subheader(f"Found {len(filtered_ads)} ads for {brand_filter}")

    # --- DISPLAY RESULTS ---
    for idx, ad in enumerate(filtered_ads):
        code = ad['code']
        uid = f"{idx}_{code}"  # unique prefix for all keys in this row

        with st.container(border=True):
            col_text, col_media = st.columns([1, 1])

            with col_text:
                st.markdown(f"### {ad['parent_brand']}")
                st.caption(f"**Original Brand:** {ad['original_brand']} | **Outlet:** {ad['media']}")
                st.info(ad['details'])

                copy_content = f"Ad Code: {code}\n{ad['details']}"
                st.text_area(
                    "Copy Details (Ctrl+C):",
                    value=copy_content,
                    height=100,
                    key=f"admatcher_textarea_{uid}"
                )

            with col_media:
                match = next(
                    (f for f in all_files if isinstance(f, dropbox.files.FileMetadata) and code in f.name),
                    None
                )
                if match:
                    try:
                        link = dbx.files_get_temporary_link(match.path_lower).link
                        fname = match.name.lower()

                        if fname.endswith(('.mp3', '.wav', '.m4a')):
                            st.write("🎵 **Radio Audio Preview:**")
                            st.audio(link, format="audio/mp3")
                        elif fname.endswith(('.mp4', '.mov')):
                            st.video(link)
                        else:
                            st.image(link)

                        st.link_button(f"📥 Download {code}", link, key=f"admatcher_dl_{uid}")
                    except Exception as e:
                        st.error(f"Error generating temporary Dropbox link: {e}")
                else:
                    st.warning(f"⚠️ Code {code} not found in Dropbox.")
