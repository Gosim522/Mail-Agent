from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"

INBOX_PATH = DATA_DIR / "inbox.json"
SENT_PATH = DATA_DIR / "sent.json"
SPAM_DB_PATH = DATA_DIR / "spam_db.json"
SCHEDULE_PATH = DATA_DIR / "schedule.json"

CONFIG_STORE_PATH = DATA_DIR / "accounts.json"

LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-r1:8b")
DEFAULT_TEMPERATURE = float(os.getenv("TEMPERATURE", "0.0"))
DEFAULT_NUM_CTX = int(os.getenv("NUM_CTX", "8192"))

MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))

MY_EMAIL = os.getenv("MY_EMAIL", "me@gmail.com")

GMAIL_MAX_UNREAD = int(os.getenv("GMAIL_MAX_UNREAD", "50"))

USER_NAME = os.getenv("USER_NAME", "고승범")
USER_SIGNATURE = os.getenv("USER_SIGNATURE", "감사합니다.\n고승범 드림")

CATEGORIES = {
    "spam": "스팸 메일",
    "no_reply_needed": "응답 불필요",
    "decision_needed": "의사결정 필요",
    "auto_handled": "의사결정 불필요(자동 처리)",
    "auto_reply": "자동 답장 가능",
}
DEFAULT_CATEGORY = "decision_needed"
