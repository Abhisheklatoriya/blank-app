import streamlit as st
import dropbox
import re
import os
try:
    from docx import Document
except ImportError:
    st.error("Missing library: Please add 'python-docx' to your requirements.txt")
    st.stop()

# --- 1. SETUP & PAGE CONFIG SAFETY ---
# This allows the app to run as a standalone OR inside the Hub
try:
    st.set_page_config(page_title="Ad Matcher: Parent Brands", layout="wide")
except st.errors.StreamlitAPIException:
    pass

st.title("🎯 Ad Matcher")

# --- 2. DROPBOX AUTHENTICATION ---
try:
    # Ensure your secrets are set in the Streamlit Cloud Dashboard
    dbx = dropbox.Dropbox(st.secrets["dropbox"]["refresh_token"])
except Exception as e:
    st.error("🔑 Dropbox Configuration Error. Check your Streamlit Secrets.")
    st.stop()

uploaded_docx = st.file_uploader("📂 Upload Word Document (.docx)", type=["docx"])

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

    # --- 3. EXTRACT & MAP BRANDS ---
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

    # --- 4. SIDEBAR FILTERS ---
    st.sidebar.header("🔍 Filter Settings")
    brand_filter = st.sidebar.selectbox("Select Parent Brand:", ["All", "Bell", "Telus", "Fizz", "Videotron", "Freedom"])
    
    filtered_ads = [ad for ad in ad_data if brand_filter == "All" or ad['parent_brand'] == brand_filter]
    
    st.divider()
    st.subheader(f"Found {len(filtered_ads)} ads for {brand_filter}")

    # --- 5. DISPLAY RESULTS ---
    for ad in filtered_ads:
        code = ad['code']
        with st.container(border=True):
            col_text, col_media = st.columns([1, 1])
            
            with col_text:
                st.markdown(f"### {ad['parent_brand']}")
                st.caption(f"**Original Brand:** {ad['original_brand']} | **Outlet:** {ad['media']}")
                st.info(ad['details'])
                
                copy_content = f"Ad Code: {code}\n{ad['details']}"
                # Standard st.text_area for compatibility across all Streamlit versions
                st.text_area("Copy Details (Ctrl+C):", value=copy_content, height=100, key=f"area_{code}")

            with col_media:
                # Find file in Dropbox list that matches the 8-digit code
                match = next((f for f in all_files if isinstance(f, dropbox.files.FileMetadata) and code in f.name), None)
                if match:
                    try:
                        link = dbx.files_get_temporary_link(match.path_lower).link
                        fname = match.name.lower()
                        
                        if fname.endswith(('.mp3', '.wav', '.m4a')):
                            st.write("🎵 **Radio Audio Preview:**")
                            st.audio(link)
                        elif fname.endswith(('.mp4', '.mov')):
                            st.video(link)
                        else:
                            st.image(link)
                            
                        st.link_button(f"📥 Download {code}", link)
                    except:
                        st.error("Error generating temporary Dropbox link.")
                else:
                    st.warning(f"⚠️ Code {code} not found in Dropbox.")
