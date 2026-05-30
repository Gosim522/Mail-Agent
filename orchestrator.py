from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional

import classifier
import config
import config_store
import llm as llm_factory
import mail_store
import tools

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def _route(email: Dict[str, Any], result: Dict[str, Any], account: str = "") -> List[str]:
    actions: List[str] = []
    category = result["category"]

    if category == "spam":
        actions.append(tools.register_spam(email, account))

        return actions

    has_sched = result.get("has_schedule") and result.get("schedule")

    if category == "decision_needed":

        msg = "사람 검토 필요 (의사결정 대기)"
        if has_sched:
            msg += " · 수락 시 일정 등록 예정"
        actions.append(msg)
        return actions

    if has_sched:
        actions.append(tools.update_schedule(email, result["schedule"], account))

    if category == "auto_reply":

        body = result.get("reply_body") or (
            f"안녕하세요,\n\n보내주신 메일 잘 확인했습니다. 감사합니다.\n\n{config.USER_SIGNATURE}"
        )
        actions.append(tools.send_reply(email, body, account))
    else:
        actions.append("읽음 처리 (별도 조치 없음)")

    return actions

def _result_envelope(
    email: Dict[str, Any], account: str, provider: str, note: str, result: Dict[str, Any],
    started: float,
) -> Dict[str, Any]:
    actions = _route(email, result, account)
    return {
        "account": account,
        "provider": provider,
        "note": note,
        "msg_id": email.get("msg_id"),
        "subject": email.get("subject"),
        "sender_name": email.get("sender_name"),
        "sender_email": email.get("sender_email"),
        "category": result["category"],
        "category_label": config.CATEGORIES.get(result["category"], result["category"]),
        "reason": result.get("reason", ""),
        "confidence": result.get("confidence", 0.0),
        "has_schedule": bool(result.get("has_schedule")),
        "schedule": result.get("schedule", {}),
        "actions": actions,
        "elapsed": round(time.perf_counter() - started, 2),
    }

def build_chain() -> List[Dict[str, Any]]:
    store = config_store.load()
    chain: List[Dict[str, Any]] = []
    for p in store["ai_providers"]:
        if p.get("provider") == "ollama":
            continue
        if not p.get("api_key"):
            continue
        try:
            chain.append({"name": p["name"], "llm": llm_factory.build_llm(p), "fallback": False})
        except Exception:
            continue
    try:
        chain.append(
            {"name": "Ollama (폴백)", "llm": llm_factory.build_ollama_fallback(), "fallback": True}
        )
    except Exception:
        pass
    return chain

def process_one(
    email: Dict[str, Any],
    chain: List[Dict[str, Any]],
    account: str = "",
) -> Dict[str, Any]:
    started = time.perf_counter()

    if mail_store.is_known_spammer(email.get("sender_email", "")):
        result = {"category": "spam", "reason": "이미 등록된 스팸 발신자",
                  "confidence": 1.0, "has_schedule": False, "schedule": {}, "reply_body": ""}
        return _result_envelope(email, account, "규칙 기반", "스팸 리스트", result, started)

    failed: List[str] = []
    for step in chain:
        try:
            result = classifier.classify(email, step["llm"])
            note = (", ".join(failed) + " 실패 → " + step["name"]) if failed else ""
            return _result_envelope(email, account, step["name"], note, result, started)
        except Exception as exc:
            failed.append(f"{step['name']}({type(exc).__name__})")
            continue

    fail = {"category": "decision_needed",
            "reason": "사용 가능한 AI 없음" if not failed else (", ".join(failed) + " 모두 실패"),
            "confidence": 0.0, "has_schedule": False, "schedule": {}, "reply_body": ""}
    out = _result_envelope(email, account, "-", " → ".join(failed), fail, started)
    out["actions"] = ["처리 보류 (AI 모두 사용 불가)"]
    return out

def process_inbox(
    emails: Optional[List[Dict[str, Any]]] = None,
    max_workers: Optional[int] = None,
    on_done: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> List[Dict[str, Any]]:
    emails = emails if emails is not None else mail_store.load_inbox()
    workers = max_workers or config.MAX_WORKERS
    chain = build_chain()
    results: List[Dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(process_one, e, chain, ""): e for e in emails}
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            if on_done:
                on_done(res)

    order = {e.get("msg_id"): i for i, e in enumerate(emails)}
    results.sort(key=lambda r: order.get(r["msg_id"], 0))
    return results

def build_tasks() -> List[Dict[str, Any]]:
    store = config_store.load()
    tasks: List[Dict[str, Any]] = []
    seen = set()
    for acc in store["mail_accounts"]:
        try:
            emails = mail_store.account_emails(acc)
        except Exception:
            emails = []
        for e in emails:
            key = mail_store.email_key(e)
            if key in seen:
                continue
            seen.add(key)
            tasks.append({"email": e, "account": acc.get("name", "")})
    return tasks

def process_accounts(
    max_workers: Optional[int] = None,
    on_done: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> List[Dict[str, Any]]:
    tasks = build_tasks()
    workers = max_workers or config.MAX_WORKERS
    chain = build_chain()
    results: List[Dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [
            pool.submit(process_one, t["email"], chain, t["account"]) for t in tasks
        ]
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            if on_done:
                on_done(res)
    return results

if __name__ == "__main__":
    wall_start = time.perf_counter()
    inbox = mail_store.load_inbox()
    print(f"받은편지함 {len(inbox)}건 병렬 처리 시작 (워커 {config.MAX_WORKERS}개)...\n")

    def _progress(r: Dict[str, Any]) -> None:
        print(f"  - [{r['category_label']}] {r['subject']} ({r['elapsed']}s)")

    out = process_inbox(inbox, on_done=_progress)
    wall = time.perf_counter() - wall_start

    print("\n=== 처리 결과 ===")
    for r in out:
        print(f"\n[{r['category_label']}] {r['subject']}")
        print(f"  발신: {r['sender_name']} <{r['sender_email']}>")
        print(f"  근거: {r['reason']} (확신도 {r['confidence']})")
        for a in r["actions"]:
            print(f"  - {a}")

    serial_sum = sum(r["elapsed"] for r in out)
    print(f"\n총 소요(벽시계): {wall:.2f}s / 누적 처리시간: {serial_sum:.2f}s")
    print("(벽시계 < 누적 이면 병렬 처리가 동작한 것)")
