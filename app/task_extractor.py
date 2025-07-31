import google.generativeai as genai
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from langchain.tools import StructuredTool
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Annotated
import os 

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

# Prompt Template for extarcting To-Do from the Email
email_task_prompt = PromptTemplate(
    input_variables=["sender", "subject", "date", "email_body","attachments"],
    template="""
You are a highly accurate email task and information extraction assistant.

Below is the detailed content of an email the user received. Your job is to extract the following clearly and concisely:

1 **Sender:** Confirm the sender's name or organization from the email.  
2 **To-Do Task:** Is there any clear, actionable task for the user? If yes, list it simply. Example tasks: reply to someone, complete an assignment, attend a meeting, check an app. If none, write "None".  
3 **Important Information / Notifications:** Any important non-actionable info the user should note? E.g., meetings scheduled, upcoming deadlines, notifications from apps, policy updates. If none, write "None".  
4 **Ignore irrelevant content:** Completely ignore ads, newsletters, promotions if they contain no useful task or info.

---

### 📄 **Output Format (Strictly follow this structure):**
 
To-Do Task: <Actionable task or "None">  
Important Information: <Important info or "None">

---

### **Email Details:**

Sender: {sender}  
Subject: {subject}  
Date: {date}  

Body:
--------
{email_body}
--------
Attachments:
{attachments}

-----
### **Your Output (Follow the format strictly):**
"""
)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    max_tokens=None,
)

task_chain = email_task_prompt | llm

# Gemini Based Function for extracting
def extract_todo_from_email(email_data: dict) -> str:
    """
    📌 Extracts actionable tasks from a given email body.
    Returns a clear, numbered list of tasks.
    """
    input_prompt ={
        'sender': email_data["from"],
        'subject':email_data["subject"],
        'date':email_data["date"],
        'email_body':email_data["body"],
        'attachments':email_data["attachments"]
    }
    return task_chain.invoke(input_prompt).content
    
