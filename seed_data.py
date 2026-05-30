from __future__ import annotations

import json
import sys

import config

sys.stdout.reconfigure(encoding="utf-8")

EMAILS = [

    {
        "sender_name": "이벤트팀",
        "sender_email": "promo@spam123.com",
        "subject": "[축하] 당신이 당첨되었습니다!",
        "body": "축하합니다! 100만원 상금에 당첨되셨습니다. 지금 바로 아래 링크를 "
        "클릭하세요. 기회를 놓치지 마세요! http://bit.ly/win-now",
        "to": config.MY_EMAIL,
        "cc": [],
        "date": "Thu, 28 May 2026 09:00:00 +0900",
        "is_read": False,
        "thread_id": "19e6ad2ba502bffb1",
        "msg_id": "19e6ad2ba502bffb1",
    },

    {
        "sender_name": "쇼핑특가",
        "sender_email": "sale@unknown-shop.com",
        "subject": "오늘만 무료배송! 놓치면 후회하는 특가",
        "body": "안녕하세요 고객님. 오늘 하루만 전 상품 무료배송 이벤트를 진행합니다. "
        "지금 바로 구매하시면 추가 할인 쿠폰도 드립니다. 수신거부는 여기를 클릭하세요.",
        "to": config.MY_EMAIL,
        "cc": [],
        "date": "Thu, 28 May 2026 08:00:00 +0900",
        "is_read": False,
        "thread_id": "19e6ad2ba502bfb2",
        "msg_id": "19e6ad2ba502bfb2",
    },

    {
        "sender_name": "GitHub",
        "sender_email": "noreply@github.com",
        "subject": "[GitHub] Pull request #142 merged",
        "body": "이용자님, pull request #142 'Fix login bug'가 main 브랜치에 "
        "성공적으로 merge되었습니다. 추가 조치는 필요하지 않습니다.",
        "to": config.MY_EMAIL,
        "cc": [],
        "date": "Thu, 28 May 2026 07:30:00 +0900",
        "is_read": False,
        "thread_id": "19e6ad2ba502bfb3",
        "msg_id": "19e6ad2ba502bfb3",
    },

    {
        "sender_name": "테크 뉴스레터",
        "sender_email": "weekly@technews.com",
        "subject": "이번 주 개발자 소식 5가지",
        "body": "안녕하세요! 이번 주 주요 기술 뉴스를 정리했습니다. 1. 파이썬 3.14 "
        "출시 2. AI 에이전트 트렌드 ... 즐거운 한 주 되세요. (읽기 전용 소식지)",
        "to": config.MY_EMAIL,
        "cc": [],
        "date": "Thu, 28 May 2026 07:00:00 +0900",
        "is_read": False,
        "thread_id": "19e6ad2ba502bfb4",
        "msg_id": "19e6ad2ba502bfb4",
    },

    {
        "sender_name": "김교수",
        "sender_email": "prof.kim@pcu.ac.kr",
        "subject": "졸업 프로젝트 면담 일정 조율",
        "body": "고승범 학생, 졸업 프로젝트 진행 상황을 논의하고 싶습니다. "
        "6월 2일 화요일 오후 2시에 연구실에서 면담 가능한가요? 어려우면 가능한 시간을 알려주세요.",
        "to": config.MY_EMAIL,
        "cc": [],
        "date": "Thu, 28 May 2026 10:15:00 +0900",
        "is_read": False,
        "thread_id": "19e6ad2ba502bfb5",
        "msg_id": "19e6ad2ba502bfb5",
    },

    {
        "sender_name": "이수민",
        "sender_email": "sumin.lee@company.com",
        "subject": "[회의] 6월 3일 오전 10시 프로젝트 킥오프",
        "body": "안녕하세요 고승범님, 6월 3일 수요일 오전 10시에 프로젝트 킥오프 회의를 "
        "진행하려 합니다. 참석 가능 여부 회신 부탁드립니다. 장소는 3층 회의실입니다.",
        "to": config.MY_EMAIL,
        "cc": [],
        "date": "Thu, 28 May 2026 11:00:00 +0900",
        "is_read": False,
        "thread_id": "19e6ad2ba502bfb6",
        "msg_id": "19e6ad2ba502bfb6",
    },

    {
        "sender_name": "박지훈",
        "sender_email": "jihoon.park@partner.com",
        "subject": "자료 잘 받았습니다",
        "body": "고승범님, 어제 보내주신 발표 자료 잘 받았습니다. 큰 도움이 되었어요. "
        "감사합니다!",
        "to": config.MY_EMAIL,
        "cc": [],
        "date": "Thu, 28 May 2026 12:30:00 +0900",
        "is_read": False,
        "thread_id": "19e6ad2ba502bfb7",
        "msg_id": "19e6ad2ba502bfb7",
    },

    {
        "sender_name": "정민지",
        "sender_email": "minji.jung@vendor.com",
        "subject": "[승인 요청] 연간 라이선스 계약 갱신 건",
        "body": "고승범님, 연간 소프트웨어 라이선스 계약 갱신 비용이 작년 대비 15% 인상되었습니다. "
        "총 480만원입니다. 갱신을 진행할지 결정해 주시면 계약서를 보내드리겠습니다.",
        "to": config.MY_EMAIL,
        "cc": [],
        "date": "Thu, 28 May 2026 13:45:00 +0900",
        "is_read": False,
        "thread_id": "19e6ad2ba502bfb8",
        "msg_id": "19e6ad2ba502bfb8",
    },
]

EMAILS2 = [
    {
        "sender_name": "당첨센터",
        "sender_email": "noreply@lotto-win.net",
        "subject": "[광고] 1등 당첨 번호 무료 공개",
        "body": "이번 주 1등 당첨 번호를 무료로 공개합니다. 지금 가입하고 확인하세요. "
        "수신거부는 하단 링크.",
        "to": "team@gmail.com",
        "cc": [],
        "date": "Fri, 29 May 2026 09:00:00 +0900",
        "is_read": False,
        "thread_id": "1a01b2c3d4e5f001",
        "msg_id": "1a01b2c3d4e5f001",
    },
    {
        "sender_name": "AWS 결제",
        "sender_email": "billing@aws.amazon.com",
        "subject": "5월 사용 요금 영수증",
        "body": "고객님의 5월 AWS 사용 요금 영수증이 발행되었습니다. 총 $42.10. "
        "자동 결제 완료. 별도 조치는 필요하지 않습니다.",
        "to": "team@gmail.com",
        "cc": [],
        "date": "Fri, 29 May 2026 08:00:00 +0900",
        "is_read": False,
        "thread_id": "1a01b2c3d4e5f002",
        "msg_id": "1a01b2c3d4e5f002",
    },
    {
        "sender_name": "최서연",
        "sender_email": "seoyeon.choi@client.com",
        "subject": "회의록 공유 감사합니다",
        "body": "보내주신 회의록 잘 확인했습니다. 깔끔하게 정리해 주셔서 감사합니다.",
        "to": "team@gmail.com",
        "cc": [],
        "date": "Fri, 29 May 2026 14:00:00 +0900",
        "is_read": False,
        "thread_id": "1a01b2c3d4e5f003",
        "msg_id": "1a01b2c3d4e5f003",
    },
    {
        "sender_name": "한지원",
        "sender_email": "jiwon.han@client.com",
        "subject": "[검토 요청] 신규 예산안 승인 필요",
        "body": "다음 분기 마케팅 예산안을 첨부합니다. 총 1,200만원 규모이며 승인 여부를 "
        "회신해 주셔야 집행 가능합니다. 검토 부탁드립니다.",
        "to": "team@gmail.com",
        "cc": [],
        "date": "Fri, 29 May 2026 15:30:00 +0900",
        "is_read": False,
        "thread_id": "1a01b2c3d4e5f004",
        "msg_id": "1a01b2c3d4e5f004",
    },
]

_SCHED = [
    ("이수민", "sumin.lee@company.com", "[회의] 주간 스탠드업 안내", "6월 1일 월요일 오전 10시에 주간 스탠드업 회의를 진행합니다. 장소는 3층 회의실 A입니다. 참석 부탁드립니다.", "Mon, 25 May 2026 09:00:00 +0900"),
    ("박도윤", "doyoon.park@company.com", "디자인 리뷰 일정", "6월 2일 화요일 오후 2시에 신규 페이지 디자인 리뷰가 있습니다. 시안 미리 확인 부탁드려요.", "Mon, 25 May 2026 10:00:00 +0900"),
    ("김교수", "prof.kim@pcu.ac.kr", "졸업 프로젝트 면담", "고승범 학생, 6월 3일 수요일 오전 9시 30분에 연구실에서 면담 가능할까요? 진행 상황을 보고해 주세요.", "Mon, 25 May 2026 11:00:00 +0900"),
    ("최서연", "seoyeon.choi@client.com", "고객 미팅 요청", "6월 4일 목요일 오후 3시에 신규 계약 관련 미팅을 요청드립니다. 가능 여부 회신 바랍니다.", "Mon, 25 May 2026 12:00:00 +0900"),
    ("정민지", "minji.jung@company.com", "1:1 미팅", "6월 5일 금요일 오전 11시에 1:1 미팅 잡았습니다. 이번 분기 목표 같이 점검해요.", "Mon, 25 May 2026 13:00:00 +0900"),
    ("한지원", "jiwon.han@company.com", "스프린트 플래닝", "6월 8일 월요일 오후 1시에 다음 스프린트 플래닝 회의가 있습니다. 백로그 정리해 오세요.", "Tue, 26 May 2026 09:00:00 +0900"),
    ("이준호", "junho.lee@partner.com", "제품 데모 일정", "6월 9일 화요일 오후 4시에 파트너사 대상 제품 데모를 진행합니다. 데모 환경 점검 부탁드립니다.", "Tue, 26 May 2026 10:00:00 +0900"),
    ("인사팀", "hr@company.com", "채용 인터뷰 안내", "6월 10일 수요일 오전 10시에 신입 개발자 채용 인터뷰가 예정되어 있습니다. 면접관으로 참석 부탁드립니다.", "Tue, 26 May 2026 11:00:00 +0900"),
    ("교육팀", "edu@company.com", "사내 워크샵", "6월 11일 목요일 오전 9시부터 사내 AI 활용 워크샵이 열립니다. 노트북 지참 바랍니다.", "Tue, 26 May 2026 12:00:00 +0900"),
    ("팀장", "lead@company.com", "팀 회식 공지", "6월 12일 금요일 오후 6시 30분에 팀 회식이 있습니다. 장소는 추후 공지하겠습니다.", "Tue, 26 May 2026 13:00:00 +0900"),
    ("경영지원", "ops@company.com", "분기 보고회", "6월 15일 월요일 오후 2시에 2분기 실적 보고회가 진행됩니다. 발표 자료 사전 제출 바랍니다.", "Wed, 27 May 2026 09:00:00 +0900"),
    ("강하늘", "haneul.kang@partner.com", "점심 약속", "6월 16일 화요일 오전 11시 30분에 같이 점심 어떠세요? 회사 근처로 예약해두겠습니다.", "Wed, 27 May 2026 10:00:00 +0900"),
    ("건강검진센터", "noreply@checkup.co.kr", "건강검진 예약 확인", "예약하신 건강검진은 6월 17일 수요일 오전 10시입니다. 전날 저녁 9시 이후 금식해 주세요.", "Wed, 27 May 2026 11:00:00 +0900"),
    ("윤서아", "seoa.yoon@vendor.com", "파트너사 미팅", "6월 18일 목요일 오후 3시 30분에 협업 건으로 미팅 요청드립니다. 안건 정리해서 공유드릴게요.", "Wed, 27 May 2026 12:00:00 +0900"),
    ("학회사무국", "office@conf.org", "세미나 초대", "6월 19일 금요일 오후 1시에 열리는 AI 에이전트 세미나에 초대합니다. 사전 등록 부탁드립니다.", "Wed, 27 May 2026 13:00:00 +0900"),
    ("출장지원", "travel@company.com", "부산 출장 일정", "6월 22일 월요일 오전 9시 30분 부산 지사에서 미팅이 잡혔습니다. KTX 예약 안내 드립니다.", "Thu, 28 May 2026 09:00:00 +0900"),
    ("법무팀", "legal@company.com", "계약 협의 일정", "6월 23일 화요일 오후 2시에 라이선스 계약 협의 미팅이 있습니다. 검토 의견 준비 바랍니다.", "Thu, 28 May 2026 10:00:00 +0900"),
    ("발표준비", "present@company.com", "발표 리허설", "6월 24일 수요일 오후 4시에 컨퍼런스 발표 리허설을 진행합니다. 슬라이드 최종본 가져오세요.", "Thu, 28 May 2026 11:00:00 +0900"),
    ("컨퍼런스", "info@techconf.io", "컨퍼런스 참가 안내", "6월 25일 목요일 오전 10시 개막하는 테크 컨퍼런스 참가 확정되었습니다. 입장 QR을 첨부합니다.", "Thu, 28 May 2026 12:00:00 +0900"),
    ("프로젝트관리", "pmo@company.com", "마감 리뷰 미팅", "6월 26일 금요일 오후 5시에 프로젝트 최종 마감 리뷰가 있습니다. 산출물 점검 부탁드립니다.", "Thu, 28 May 2026 13:00:00 +0900"),
]

EMAILS3 = [
    {
        "sender_name": s[0], "sender_email": s[1], "subject": s[2], "body": s[3],
        "to": "team@gmail.com", "cc": [], "date": s[4], "is_read": False,
        "thread_id": f"1b{i:02d}c3d4e5f6a7b8", "msg_id": f"1b{i:02d}c3d4e5f6a7b8",
    }
    for i, s in enumerate(_SCHED)
]

def _write(path, emails) -> None:
    path.write_text(
        json.dumps({"emails": emails}, ensure_ascii=False, indent=2), encoding="utf-8"
    )

def _ensure_account(name: str, inbox_file: str) -> None:
    import config_store

    store = config_store.load()
    if not any(m.get("inbox_file") == inbox_file for m in store["mail_accounts"]):
        config_store.upsert_mail({"name": name, "source": "dummy", "inbox_file": inbox_file})

def main() -> None:
    config.DATA_DIR.mkdir(exist_ok=True)
    _write(config.INBOX_PATH, EMAILS)
    _write(config.DATA_DIR / "inbox2.json", EMAILS2)
    _write(config.DATA_DIR / "inbox3.json", EMAILS3)
    print(
        f"샘플 받은편지함 생성: inbox.json({len(EMAILS)}), "
        f"inbox2.json({len(EMAILS2)}), inbox3.json({len(EMAILS3)})"
    )

    _ensure_account("팀 받은편지함", "inbox2.json")
    _ensure_account("일정 테스트", "inbox3.json")
    print("계정 구성 확인 완료 (기존 설정 보존)")

if __name__ == "__main__":
    main()
