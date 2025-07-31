
import imaplib
import email
from email.header import decode_header
from typing import List
import re
from bs4 import BeautifulSoup
from app.task_extractor import extract_todo_from_email
import json
import os 
from datetime import datetime, timedelta

def build_search_criteria(from_date: str, to_date: str = None) -> str:

    if not to_date or from_date == to_date:
        return f'(ON {from_date})'
    else:
        # Ensure to_date is strictly AFTER from_date
        from_dt = datetime.strptime(from_date, "%d-%b-%Y")
        to_dt = datetime.strptime(to_date, "%d-%b-%Y")
        if from_dt >= to_dt:
            to_dt = from_dt + timedelta(days=1)
            to_date = to_dt.strftime("%d-%b-%Y")
        return f'(SINCE {from_date} BEFORE {to_date})'

def clean_email_body(body: str) -> str:
    """
    Cleans raw email body text by removing unwanted links, logos, and boilerplate.
    """
    soup = BeautifulSoup(body, "html.parser")
    body = soup.get_text()
    
    # Remove URLs
    body = re.sub(r'https?://\S+', '', body)
    
    # Remove images, logos, etc.
    body = re.sub(r'(?i)(logo|icon|image|powered by|view in browser|calendar)', '', body)

    # Remove extra dashes or repeated chars
    body = re.sub(r'[-=]{2,}', '', body)

    # Replace \r\n and \xa0 and strip extra spaces
    body = body.replace('\r', '').replace('\n', '\n').replace('\xa0', ' ')
    body = re.sub(r'\n{3,}', '\n\n', body)  # Limit empty lines to 2

    # Optional: Remove "Manage notifications", "Privacy Policy" etc.
    cutoff_keywords = ['Manage notifications', 'Privacy policy', 'Contact us', 'Copyright']
    for kw in cutoff_keywords:
        body = body.split(kw)[0]

    return body.strip()

SEEN_UIDS_FILE = "seen_uids.json"

def load_seen_uids():
    if os.path.exists(SEEN_UIDS_FILE):
        with open(SEEN_UIDS_FILE, "r") as f:
            return set(json.load(f)["seen_uids"])
    return set()

def save_seen_uids(uids):
    with open(SEEN_UIDS_FILE, "w") as f:
        json.dump({"seen_uids": list(uids)}, f)
        

def process_mail(from_date:str,to_date:str,email_host: str, email_user: str, email_pass: str) -> List[dict]:
    """
    Fetches recent emails using IMAP protocol and returns subject + body.

    Args:
        limit (int): Number of recent emails to fetch (default is 5).

    Returns:
        List[dict]: List of emails with subject, from, date, and body.
    """

    EMAIL_HOST = email_host
    EMAIL_USER = email_user
    EMAIL_PASS = email_pass

    seen_uids = load_seen_uids()
    new_seen_uids = set()
    
    results =[]

    try:
        server = imaplib.IMAP4_SSL(EMAIL_HOST)
        try:
            server.login(EMAIL_USER, EMAIL_PASS)
        except imaplib.IMAP4.error as e:
            return [{"error": "Login failed. Please check your email and app password."}]
        server.select("inbox")

        # Fetch recent N emails
        search_criteria = build_search_criteria(from_date,to_date)
        status, messages = server.search(None, search_criteria)
        email_ids = messages[0].split()

        for eid in email_ids:
            # Get UID of this message
            _, uid_data = server.fetch(eid, "(UID)")
            uid = uid_data[0].decode().split()[2]

            if uid in seen_uids:
                continue  # skip already processed

            # Fetch message
            _, msg_data = server.fetch(eid, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8")
                    from_email = msg.get("From")
                    date = msg.get("Date")

                    # Get email body
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode()
                                break
                    else:
                        body = msg.get_payload(decode=True).decode()

                    cleaned_body = clean_email_body(body)

                    attachments = []
                    for part in msg.walk():
                        content_disposition = str(part.get("Content-Disposition"))
                        if "attachment" in content_disposition:
                            filename = part.get_filename()
                            if filename:
                                decoded_filename, enc = decode_header(filename)[0]
                                if isinstance(decoded_filename, bytes):
                                    decoded_filename = decoded_filename.decode(enc or "utf-8")
                              
                                payload = part.get_payload(decode=True)
                                if payload:  # only save non-empty payloads
                                    save_path = f"attachments/{EMAIL_USER}/"
                                    os.makedirs(save_path, exist_ok=True)

                                full_path = os.path.join(save_path, decoded_filename)
                                with open(full_path, "wb") as f:
                                    f.write(payload)

                                attachments.append(decoded_filename)
                                
                    email_data = {
                        "subject": subject,
                        "from": from_email,
                        "date": date,
                        "body": cleaned_body,
                        "attachments":attachments if attachments else None
                    }
                    
                    extraction =extract_todo_from_email(email_data)
                    results.append({
                        "subject": email_data["subject"],
                        "from": email_data["from"],
                        "date": email_data["date"],
                        "attachments": email_data["attachments"],
                        "extraction": extraction
                    })
                    new_seen_uids.add(uid)
                    
        seen_uids.update(new_seen_uids)
        save_seen_uids(seen_uids)
        server.logout()
        return results

    except Exception as e:
        return [{"error": str(e)}]
    
