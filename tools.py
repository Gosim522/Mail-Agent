from __future__ import annotations

from typing import Any, Dict

import config
import mail_store

def register_spam(email: Dict[str, Any], account: str = "") -> str:
    record = dict(email)
    record["account"] = account
    mail_store.add_spam(record)
    return f"스팸 DB 등록 + 발신자 차단: {email.get('sender_email')}"

def send_reply(email: Dict[str, Any], reply_body: str, account: str = "") -> str:
    reply = {
        "sender_name": config.USER_NAME,
        "sender_email": config.MY_EMAIL,
        "subject": f"Re: {email.get('subject', '')}",
        "body": reply_body,
        "to": email.get("sender_email"),
        "cc": [],
        "in_reply_to": email.get("msg_id"),
        "thread_id": email.get("thread_id"),
        "account": account,
    }
    mail_store.append_sent(reply)
    return f"자동 답장 발송(저장): {reply['to']}"

def decision_reply(email: Dict[str, Any], accept: bool) -> str:
    if accept:
        return (
            "안녕하세요,\n\n보내주신 내용 잘 확인했습니다. 제안해 주신 일정/요청을 "
            "수락합니다. 일정에 맞춰 진행하겠습니다.\n\n" + config.USER_SIGNATURE
        )
    return (
        "안녕하세요,\n\n보내주신 내용 잘 확인했습니다. 검토 결과 이번에는 일정이 맞지 "
        "않아 어렵습니다. 양해 부탁드립니다.\n\n" + config.USER_SIGNATURE
    )

def update_schedule(email: Dict[str, Any], schedule: Dict[str, Any], account: str = "") -> str:
    dt = schedule.get("datetime", "")
    conflict = mail_store.schedule_conflict(dt)
    event = {
        "title": schedule.get("title") or email.get("subject", "(제목 없음)"),
        "datetime": dt,
        "source_msg_id": email.get("msg_id"),
        "from": email.get("sender_email"),
        "account": account,
        "conflict": bool(conflict),
        "conflict_with": conflict.get("title") if conflict else "",
    }
    mail_store.add_schedule(event)
    msg = f"스케줄 추가: {event['title']} @ {dt}"
    if conflict:
        msg += f" (충돌: '{conflict.get('title')}' {conflict.get('datetime')})"
    return msg
