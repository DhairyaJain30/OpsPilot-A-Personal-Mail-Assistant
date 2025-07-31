import streamlit as st
from datetime import datetime, date
from app.email_handler import process_mail
from app.attachment_rag import ingest_files_to_vector_db,query_vector_db
from langchain.document_loaders import PyPDFLoader
import glob,os
# Set Streamlit page config
st.set_page_config(page_title="SmartMail Tasks", layout="wide")

# ------------------------------
# 🎯 Title + Tagline (Centered)
# ------------------------------
st.markdown("""
    <h1 style='text-align: center; color: #003153;'>📬 SmartMail Task Extractor</h1>
    <p style='text-align: center; font-size: 18px;'>Automatically extract to-do items from your emails, organize them smartly, and even query attachments with AI.</p>
""", unsafe_allow_html=True)

st.markdown("---")

# ------------------------------
# 📅 Sidebar: Filters and Date
# ------------------------------
with st.sidebar:

    st.header("🔐 Email Login")

    email_provider = st.selectbox(
        "Choose Email Provider",
        ["Gmail", "Yahoo", "Custom IMAP"]
    )

    email_user = st.text_input("Email Address")
    email_pass = st.text_input("App Password", type="password")
    st.session_state.email_user = email_user
    if email_provider == "Custom IMAP":
        custom_imap = st.text_input("Custom IMAP Server", placeholder="e.g. imap.yourdomain.com")
    else:
        custom_imap = None
    st.header("📅 Filter Emails")
    from_date = st.date_input("From Date", value=date.today())
    to_date = st.date_input("To Date (optional)", value=None)

    st.header("🧹 Filter Options")
    show_only_with_tasks = st.checkbox("✅ Only emails with extracted tasks", value=False)
    show_only_with_attachments = st.checkbox("📎 Only emails with attachments", value=False)

    fetch_btn = st.button("🔄 Fetch Emails")

# ------------------------------
# 📥 Main Area: Process and Display
# ------------------------------

if not fetch_btn:
    st.markdown("### 👋 Welcome to SmartMail Task Extractor")
    st.markdown("""
    Use the sidebar to:
    - 🔐 Log in securely with your email and app password
    - 📅 Select a date range
    - 📎 Soon: Query attachments with RAG

    Then click **Fetch Emails** to get started.
    """)
    st.image("https://cdn-icons-png.flaticon.com/512/561/561127.png", width=40)
    
tab1, tab2 = st.tabs(["📬 Email Tasks", "📎 RAG over Attachments"])

with tab1:
    if fetch_btn:
        with st.spinner("Fetching and processing emails..."):
            from_str = from_date.strftime("%d-%b-%Y")
            to_str = to_date.strftime("%d-%b-%Y") if to_date else None
            imap_map = {
            "Gmail": "imap.gmail.com",
            "Yahoo": "imap.mail.yahoo.com"
            }

            email_host = imap_map.get(email_provider, custom_imap)
            results = process_mail(from_date=from_str,to_date=to_str,email_host=email_host,email_user=email_user,email_pass=email_pass)
        if results and "error" in results[0]:
            st.error(results[0]["error"])
            st.stop()
        
        if not results:
            st.warning("No emails found in this range.")
        else:
            st.success("✅ Emails processed successfully!")

            for idx, res in enumerate(results):
                if show_only_with_tasks and not res["extraction"]:
                    continue
                if show_only_with_attachments and not res["attachments"]:
                    continue

                with st.expander(f"📨 {res['subject']} — {res['from']}"):
                    col1, col2 = st.columns(2)
                    col1.markdown(f"**🧑 From:** `{res['from']}`")
                    col2.markdown(f"**📅 Date:** `{res['date']}`")

                    st.markdown("**📝 Extracted Task:**")
                    if res["extraction"]:
                        st.success(res["extraction"])
                    else:
                        st.info("No task found.")

                    st.markdown("**📎 Attachments:**")
                    if res["attachments"]:
                        for a in res["attachments"]:
                            st.markdown(f"- `{a}`")
                    else:
                        st.text("None")

with tab2:
    email_user = st.session_state.get("email_user")
    st.header("📎 Ask Questions about Attachments")

    user_folder = f"attachments/{email_user}"
    all_files = glob.glob(f"{user_folder}/*.pdf")
    file_names = [os.path.basename(f) for f in all_files]
    selected_file = st.selectbox("📄 Choose a file:", file_names)

    if selected_file:
        file_path = os.path.join(user_folder, selected_file)

        # Ingest on selection
        with st.spinner("🔁 Ingesting document..."):
            result = ingest_files_to_vector_db(user_folder)

        if result["status"] == "success":
            st.success(f"Added {selected_file} successfully")
        else:
            st.error(f"Ingestion error: {result['error_message']}")
            
        try:
            loader = PyPDFLoader(file_path)
            preview_doc = loader.load()
            preview_text = preview_doc[0].page_content[:500]
            st.markdown("### 📘 Preview:")
            st.markdown(f"""
            <div style="
            background-color: #f9f9fb;
            border-left: 5px solid #4A90E2;
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 6px;
            font-family: 'Segoe UI', sans-serif;
            color: #333;
            ">
            <strong>Preview (first 500 characters):</strong><br><br>
            {preview_text}
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"Could not load preview: {e}")

        # Ask user question
        user_query = st.text_input("❓ What do you want to know?")
        if st.button("Ask"):
            with st.spinner("🤖 Generating response..."):
                result = query_vector_db(user_query)
                
            if result["status"] == "success":
                st.markdown("### ✅ Answer")
                st.markdown(f"""
                    <div style="background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; color: #333;">
                    {result["answer"]}
                    </div>
                    """, unsafe_allow_html=True)

                if result["source_chunks"]:
                    st.markdown("### 📚 Source Chunks (Context used)")
                    first_chunk = result["source_chunks"][0]
                    with st.expander("📄 View Source Context"):
                        st.code(first_chunk, language="markdown")

            elif result["status"] == "no_results":
                st.info("No relevant chunks found in the documents.")

            else:
                st.error(f"Error: {result.get('error_message', 'Unknown error')}")
                
                
st.markdown("""
<hr style='margin-top: 3rem;'>
<p style='text-align: center; font-size: 14px; color: gray;'>Built with ❤️ using LangChain & Streamlit</p>
""", unsafe_allow_html=True)
