from __future__ import annotations

import sys
import time

import mail_store
import orchestrator
import tools

sys.stdout.reconfigure(encoding="utf-8")

def main() -> int:
    mail_store.reset_outputs()
    inbox = mail_store.load_inbox()
    assert inbox, "받은편지함이 비어있음 — 먼저 seed_data.py 실행"

    print(f"받은편지함 {len(inbox)}건 병렬 처리 중...\n")
    wall_start = time.perf_counter()
    results = orchestrator.process_inbox(inbox)
    wall = time.perf_counter() - wall_start

    for r in results:
        print(f"[{r['category_label']:16}] {r['subject']}")
        for a in r["actions"]:
            print(f"      - {a}")

    categories = {r["category"] for r in results}
    spam_db = mail_store.load_spam_db()
    sent = mail_store.load_sent()
    serial_sum = sum(r["elapsed"] for r in results)

    mail_store.reset_outputs()
    e = {"subject": "회의", "sender_email": "x@x.com", "msg_id": "t1"}
    tools.update_schedule(e, {"title": "회의A", "datetime": "2026-06-10 14:00"})
    conflict_msg = tools.update_schedule(e, {"title": "회의B", "datetime": "2026-06-10 14:20"})
    conflict_ok = "충돌" in conflict_msg and any(
        s.get("conflict") for s in mail_store.load_schedule()
    )
    before = len(mail_store.load_schedule())
    tools.update_schedule(e, {"title": "회의C", "datetime": "2026-06-12 09:00"})
    accept_ok = len(mail_store.load_schedule()) == before + 1
    dedup_ok = mail_store.email_key(
        {"sender_email": "A@x.com", "subject": " 안녕 ", "body": "본문"}
    ) == mail_store.email_key(
        {"sender_email": "a@x.com", "subject": "안녕", "body": "본문"}
    )
    mail_store.reset_outputs()

    checks = [
        ("스팸 분류 발생", any(c == "spam" for c in categories)),
        ("스팸 DB 등록됨", len(spam_db["messages"]) > 0),
        ("스팸 발신자 차단 리스트 채워짐", len(spam_db["senders"]) > 0),
        ("자동 답장 저장됨", len(sent) > 0),
        ("의사결정 필요 분류 발생", any(c == "decision_needed" for c in categories)),
        ("병렬 처리 동작(벽시계<누적)", wall < serial_sum),
        ("일정 충돌 감지", conflict_ok),
        ("일정 등록(수락 경로) 동작", accept_ok),
        ("중복 메일 키 동일 판별", dedup_ok),
    ]

    print("\n=== 검증 결과 ===")
    all_ok = True
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        all_ok = all_ok and ok

    print(
        f"\n총 벽시계 {wall:.2f}s / 누적 처리시간 {serial_sum:.2f}s "
        f"(워커 {orchestrator.config.MAX_WORKERS}개)"
    )
    print(f"발견 카테고리: {sorted(categories)}")
    print(f"스팸 {len(spam_db['messages'])}건 / 답장 {len(sent)}건")

    print("\n" + ("[전체 통과]" if all_ok else "[일부 실패]"))
    return 0 if all_ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
