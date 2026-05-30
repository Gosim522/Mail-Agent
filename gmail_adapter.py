from __future__ import annotations

import base64
import json
from email.utils import getaddresses, parseaddr
from typing import Any, Dict, List, Tuple

import config

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def start_oauth(credentials_json: str) -> str:
    from google_auth_oauthlib.flow import InstalledAppFlow

    cfg = json.loads(credentials_json)
    flow = InstalledAppFlow.from_client_config(cfg, SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent")
    return creds.to_json()

def _creds_from_token(token_json: str):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds

def _decode(data: str) -> str:
    return base64.urlsafe_b64decode(data.encode("utf-8")).decode("utf-8", "replace")

def _extract_body(payload: Dict[str, Any]) -> str:
    mime = payload.get("mimeType", "")
    body = payload.get("body", {})
    if mime == "text/plain" and body.get("data"):
        return _decode(body["data"])
    html_fallback = ""
    for part in payload.get("parts", []) or []:
        text = _extract_body(part)
        if text:
            if part.get("mimeType") == "text/plain":
                return text
            html_fallback = html_fallback or text
    if mime == "text/html" and body.get("data"):
        return _decode(body["data"])
    return html_fallback

def _to_email(service, msg_id: str) -> Dict[str, Any]:
    m = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    headers = {h["name"].lower(): h["value"] for h in m.get("payload", {}).get("headers", [])}
    name, addr = parseaddr(headers.get("from", ""))
    cc = [a for _, a in getaddresses([headers.get("cc", "")]) if a]
    body = _extract_body(m.get("payload", {})).strip()
    return {
        "sender_name": name or addr,
        "sender_email": addr,
        "subject": headers.get("subject", "(제목 없음)"),
        "body": body,
        "to": headers.get("to", ""),
        "cc": cc,
        "date": headers.get("date", ""),
        "is_read": False,
        "thread_id": m.get("threadId"),
        "msg_id": m.get("id"),
    }

def fetch_unread(token_json: str, max_count: int | None = None) -> Tuple[List[Dict[str, Any]], str, int]:
    cap = max_count or config.GMAIL_MAX_UNREAD
    creds = _creds_from_token(token_json)

    from googleapiclient.discovery import build

    service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    ids: List[str] = []
    page_token = None
    while True:
        resp = (
            service.users()
            .messages()
            .list(userId="me", q="is:unread in:inbox", maxResults=100, pageToken=page_token)
            .execute()
        )
        ids.extend(msg["id"] for msg in resp.get("messages", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    total = len(ids)
    emails = [_to_email(service, mid) for mid in ids[:cap]]
    return emails, creds.to_json(), total
