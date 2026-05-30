from __future__ import annotations

import json
import re
import threading
from pathlib import Path
from typing import Any, Dict, List

import config

_DT_RE = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})(?:[ T](\d{1,2}):(\d{2}))?")

def email_key(e: Dict[str, Any]) -> tuple:
    return (
        (e.get("sender_email") or "").strip().lower(),
        (e.get("subject") or "").strip(),
        (e.get("body") or "").strip()[:300],
    )

def _parse_dt(s: str):
    m = _DT_RE.search(s or "")
    if not m:
        return None
    date = (int(m[1]), int(m[2]), int(m[3]))
    minute = int(m[4]) * 60 + int(m[5]) if m[4] is not None else None
    return (date, minute)

def schedule_conflict(datetime_str: str) -> Dict[str, Any] | None:
    nd = _parse_dt(datetime_str)
    if not nd:
        return None
    ndate, nmin = nd
    for ev in load_schedule():
        ed = _parse_dt(ev.get("datetime", ""))
        if not ed:
            continue
        edate, emin = ed
        if edate != ndate:
            continue
        if nmin is None or emin is None or abs(nmin - emin) < 60:
            return ev
    return None

_LOCK = threading.Lock()

def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))

def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def load_inbox(inbox_file: str | None = None) -> List[Dict[str, Any]]:
    path = (config.DATA_DIR / inbox_file) if inbox_file else config.INBOX_PATH
    data = _read_json(path, {"emails": []})
    return data.get("emails", [])

def account_emails(acc: Dict[str, Any]) -> List[Dict[str, Any]]:
    if acc.get("source") == "gmail":
        import config_store
        import gmail_adapter

        token = acc.get("token_json")
        if not token:
            return []
        emails, new_token, _total = gmail_adapter.fetch_unread(token)
        if new_token and new_token != token:
            config_store.set_mail_token(acc["id"], new_token)
        return emails
    return load_inbox(acc.get("inbox_file"))

def append_sent(reply: Dict[str, Any]) -> None:
    with _LOCK:
        data = _read_json(config.SENT_PATH, {"emails": []})
        data["emails"].append(reply)
        _write_json(config.SENT_PATH, data)

def load_sent() -> List[Dict[str, Any]]:
    return _read_json(config.SENT_PATH, {"emails": []}).get("emails", [])

def add_spam(email: Dict[str, Any]) -> None:
    with _LOCK:
        data = _read_json(config.SPAM_DB_PATH, {"messages": [], "senders": []})
        msg_id = email.get("msg_id")
        if not any(m.get("msg_id") == msg_id for m in data["messages"]):
            data["messages"].append(
                {
                    "msg_id": msg_id,
                    "sender_email": email.get("sender_email"),
                    "subject": email.get("subject"),
                    "date": email.get("date"),
                }
            )
        sender = email.get("sender_email")
        if sender and sender not in data["senders"]:
            data["senders"].append(sender)
        _write_json(config.SPAM_DB_PATH, data)

def load_spam_db() -> Dict[str, Any]:
    return _read_json(config.SPAM_DB_PATH, {"messages": [], "senders": []})

def is_known_spammer(sender_email: str) -> bool:
    return sender_email in load_spam_db().get("senders", [])

def add_schedule(event: Dict[str, Any]) -> None:
    with _LOCK:
        data = _read_json(config.SCHEDULE_PATH, {"events": []})
        data["events"].append(event)
        _write_json(config.SCHEDULE_PATH, data)

def load_schedule() -> List[Dict[str, Any]]:
    return _read_json(config.SCHEDULE_PATH, {"events": []}).get("events", [])

def reset_outputs() -> None:
    with _LOCK:
        for path in (config.SENT_PATH, config.SPAM_DB_PATH, config.SCHEDULE_PATH):
            if path.exists():
                path.unlink()
