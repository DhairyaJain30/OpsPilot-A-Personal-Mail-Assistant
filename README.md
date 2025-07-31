# 📬 Ops Pilot — Smart Email Task Assistant

**Ops Pilot** is your personal mail assistant powered by LangChain, Gemini, and RAG.  
It reads your emails securely via IMAP, extracts tasks or summaries using LLMs, and even answers questions about attached documents using Retrieval-Augmented Generation (RAG).  
Designed for productivity, privacy, and modern AI-driven workflows.

---

## 🚀 Features

- 🔐 Secure login via IMAP (custom server or Gmail/Yahoo)
- 📥 Reads and processes your inbox mails
- ✅ Extracts To-Do tasks or summaries using LLM (Gemini Pro)
- 📎 Saves and previews attachments (PDF, DOCX)
- 🤖 RAG-based Q&A over attachments using Pinecone + Gemini
- 🧠 Intelligent chunking and indexing for smart search
- 📊 Clean and intuitive UI using Streamlit

---

## 🧱 Tech Stack

| Layer        | Tech Used |
|--------------|-----------|
| 💬 LLM       | Gemini 2.0 (via `langchain-google-genai`) |
| 🧠 Vector DB | Pinecone |
| 📥 Mail      | IMAP protocol (supports Gmail, Yahoo, Custom) |
| 🧱 Framework | LangChain |
| 🌐 Frontend  | Streamlit |

---

## 🛠️ Getting Started

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/DhairyaJain30/OpsPilot-A-Personal-Mail-Assistant.git
cd OpsPilot-A-Personal-Mail-Assistant
```
# Create a virtual environment
```bash
python -m venv email_agent_env
source email_agent_env/bin/activate  # or email_agent_env\Scripts\activate on Windows
```

# Install dependencies
```bash
pip install -r requirements.txt
```
# Configure .env
Add your API's and change .env.example to .env
```bash
GOOGLE_API_KEY=your_gemini_api_key
PINECONE_API_KEY=your_pinecone_api_key
```
## 📧 IMAP Login (Currently via App Password)
For now, login is supported using:

- ✅ Gmail (use App Passwords)

- ✅ Yahoo

- ✅ Any Custom IMAP Server

⚠️ OAuth Login is in Progress. Stay tuned for secure one-click login support in future releases.

## 📂 File Handling
Attachments are saved under:
```bash
attachments/<user_email>/
```
