from __future__ import annotations

import json
import threading
import uuid
from typing import Any, Dict, List

import config

_LOCK = threading.Lock()

def _default_store() -> Dict[str, Any]:
    ai_ollama = {
        "id": "ollama",
        "name": "로컬 Ollama (무료·폴백)",
        "provider": "ollama",
        "model": config.LLM_MODEL,
        "api_key": "",
        "builtin": True,
    }
    mail = {
        "id": uuid.uuid4().hex[:8],
        "name": "기본 받은편지함",
        "source": "dummy",
        "inbox_file": "inbox.json",
    }
    return {"ai_providers": [ai_ollama], "mail_accounts": [mail]}

def load() -> Dict[str, Any]:
    path = config.CONFIG_STORE_PATH
    if not path.exists():
        store = _default_store()
        _save(store)
        return store
    return json.loads(path.read_text(encoding="utf-8"))

def _save(store: Dict[str, Any]) -> None:
    config.DATA_DIR.mkdir(exist_ok=True)
    config.CONFIG_STORE_PATH.write_text(
        json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8"
    )

def _mask(key: str) -> Dict[str, Any]:
    if not key:
        return {"has_key": False, "hint": ""}
    tail = key[-4:] if len(key) >= 4 else key
    return {"has_key": True, "hint": "****" + tail}

def public_view() -> Dict[str, Any]:
    store = load()
    providers = []
    for p in store["ai_providers"]:
        item = {k: v for k, v in p.items() if k != "api_key"}
        item["key"] = _mask(p.get("api_key", ""))
        providers.append(item)
    mails = []
    for m in store["mail_accounts"]:
        item = {k: v for k, v in m.items() if k not in ("credentials_json", "token_json")}
        item["has_credentials"] = bool(m.get("credentials_json"))
        item["connected"] = bool(m.get("token_json"))
        mails.append(item)
    return {"ai_providers": providers, "mail_accounts": mails}

def upsert_ai(data: Dict[str, Any]) -> Dict[str, Any]:
    if data.get("provider") == "ollama":
        return provider_by_id("ollama") or {}
    with _LOCK:
        store = load()
        pid = data.get("id")
        record = {
            "name": data.get("name", "이름 없음"),
            "provider": data.get("provider", "openai"),
            "model": data.get("model", ""),
            "api_key": data.get("api_key", ""),
        }
        for p in store["ai_providers"]:
            if p["id"] == pid:
                if not record["api_key"]:
                    record["api_key"] = p.get("api_key", "")
                p.update(record)
                _save(store)
                return p
        record["id"] = uuid.uuid4().hex[:8]
        store["ai_providers"].append(record)
        _save(store)
        return record

def delete_ai(pid: str) -> None:
    if pid == "ollama":
        return
    with _LOCK:
        store = load()
        store["ai_providers"] = [
            p for p in store["ai_providers"]
            if p["id"] != pid or p.get("provider") == "ollama"
        ]
        _save(store)

def upsert_mail(data: Dict[str, Any]) -> Dict[str, Any]:
    with _LOCK:
        store = load()
        mid = data.get("id")
        record = {
            "name": data.get("name", "이름 없음"),
            "source": data.get("source", "dummy"),
            "inbox_file": data.get("inbox_file", "inbox.json"),
        }

        if data.get("credentials_json"):
            record["credentials_json"] = data["credentials_json"]
        for m in store["mail_accounts"]:
            if m["id"] == mid:

                if not record.get("credentials_json") and m.get("credentials_json"):
                    record["credentials_json"] = m["credentials_json"]
                if m.get("token_json"):
                    record["token_json"] = m["token_json"]
                m.clear()
                m["id"] = mid
                m.update(record)
                _save(store)
                return m
        record["id"] = uuid.uuid4().hex[:8]
        store["mail_accounts"].append(record)
        _save(store)
        return record

def get_mail(mid: str) -> Dict[str, Any] | None:
    for m in load()["mail_accounts"]:
        if m["id"] == mid:
            return m
    return None

def set_mail_token(mid: str, token_json: str) -> None:
    with _LOCK:
        store = load()
        for m in store["mail_accounts"]:
            if m["id"] == mid:
                m["token_json"] = token_json
                _save(store)
                return

def delete_mail(mid: str) -> None:
    with _LOCK:
        store = load()
        store["mail_accounts"] = [m for m in store["mail_accounts"] if m["id"] != mid]
        _save(store)

def provider_by_id(pid: str) -> Dict[str, Any] | None:
    for p in load()["ai_providers"]:
        if p["id"] == pid:
            return p
    return None
