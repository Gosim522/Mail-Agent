from __future__ import annotations

import json
import re
import sys
from typing import Any, Dict

import config
import llm as llm_factory

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

_THINK_RE = re.compile(r"<think>.*?</think>\s*", flags=re.DOTALL)

_JSON_RE = re.compile(r"\{.*\}", flags=re.DOTALL)

def strip_think(text: str) -> str:
    return _THINK_RE.sub("", text).strip()

CLASSIFY_PROMPT = """당신은 이메일을 분류하고 처리하는 비서 AI입니다.
아래 이메일 한 통을 분석해서 반드시 JSON 객체 하나만 출력하세요. JSON 외의 설명은 절대 쓰지 마세요.

[분류 카테고리] category 필드는 다음 중 정확히 하나 (위에서부터 순서대로 판단):
- "spam": 광고, 당첨 사칭, 피싱, 수신거부 유도 등 스팸 메일
- "no_reply_needed": 뉴스레터/소식지/마케팅 등 사람이 읽기만 하면 되는 메일
- "auto_handled": 사람이 아닌 시스템/봇이 보낸 자동 알림(빌드 결과, PR 머지, 영수증 등). 발신자가 noreply 류이고 답장이 무의미한 경우.
- "decision_needed": 사람의 판단·승인·결정이 필요한 메일 (계약/비용 승인, 일정 확정/조율 요청 등). 자동 답장하지 않는다.
- "auto_reply": 사람이 보낸 메일이지만 단순 감사/확인/수락처럼 정형적인 답장으로 충분한 경우. 판단이 필요 없고 짧은 예의상 답장이면 충분한 메일.

[중요] 사람이 직접 보낸 감사/확인 메일은 auto_handled가 아니라 auto_reply 이다. auto_handled는 오직 기계가 보낸 자동 알림에만 쓴다.

[일정 추출] 본문에 회의/면담/약속 등 날짜·시간이 있으면 has_schedule=true 로 하고 schedule 채움.
[답장 생성] category가 "auto_reply"일 때만 reply_body에 한국어 답장 본문을 작성. 그 외에는 빈 문자열.

[출력 형식]
{{
  "category": "<위 5개 중 하나>",
  "reason": "<분류 근거 한 문장>",
  "confidence": <0.0~1.0 숫자>,
  "has_schedule": <true|false>,
  "schedule": {{"title": "<일정 제목>", "datetime": "<예: 2026-06-03 10:00>"}},
  "reply_body": "<auto_reply일 때만 답장 본문, 아니면 \\"\\">"
}}

[답장 작성자] 이름: {user_name} / 서명: "{signature}"

[분석할 이메일]
보낸사람: {sender_name} <{sender_email}>
제목: {subject}
본문: {body}
"""

def _safe_result(reason: str) -> Dict[str, Any]:
    return {
        "category": config.DEFAULT_CATEGORY,
        "reason": reason,
        "confidence": 0.0,
        "has_schedule": False,
        "schedule": {},
        "reply_body": "",
    }

def classify(email: Dict[str, Any], llm=None) -> Dict[str, Any]:
    llm = llm or llm_factory.build_llm(llm_factory.default_provider())
    prompt = CLASSIFY_PROMPT.format(
        user_name=config.USER_NAME,
        signature=config.USER_SIGNATURE,
        sender_name=email.get("sender_name", ""),
        sender_email=email.get("sender_email", ""),
        subject=email.get("subject", ""),
        body=email.get("body", ""),
    )

    raw = llm.invoke(prompt)
    text = strip_think(raw.content if hasattr(raw, "content") else str(raw))

    match = _JSON_RE.search(text)
    if not match:
        return _safe_result("LLM 응답에서 JSON을 찾지 못함")

    try:
        result = json.loads(match.group(0))
    except json.JSONDecodeError:
        return _safe_result("LLM JSON 파싱 실패")

    if result.get("category") not in config.CATEGORIES:
        result["category"] = config.DEFAULT_CATEGORY
    result.setdefault("reason", "")
    result.setdefault("confidence", 0.0)
    result.setdefault("has_schedule", False)
    result.setdefault("schedule", {})
    result.setdefault("reply_body", "")
    return result

if __name__ == "__main__":

    import mail_store

    inbox = mail_store.load_inbox()
    if not inbox:
        print("받은편지함이 비어있습니다. 먼저 seed_data.py를 실행하세요.")
    else:
        sample = inbox[0]
        print(f"[분류 대상] {sample['subject']}")
        print(json.dumps(classify(sample), ensure_ascii=False, indent=2))
