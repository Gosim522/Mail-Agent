# AI 이메일 분류·처리 멀티에이전트

여러 **메일 계정**의 받은편지함을 **여러 에이전트가 병렬로** 분류하고, 분류 결과에 따라
스팸 등록 · 자동 답장 · 스케줄 추가까지 자동으로 처리하는 시스템입니다.
계정마다 **다른 AI(OpenAI / 로컬 Ollama)**를 지정할 수 있어, 사람·계정별로 서로 다른
모델로 동시에 분류됩니다. 자체 제작한 관리자 콘솔(Flask + 바닐라 JS)에서 AI·메일 계정을
등록하고 결과를 실시간으로 확인합니다.

> 주말 특강 과제 (2026-05-30). 더미 메일(JSON) 모드로 동작하며, 실제 Gmail 연동은
> 선택적 확장(`gmail_adapter.py`)으로 설계되어 있습니다.

## 기능 (과제 매핑)

| 과제 요구 | 구현 |
|---|---|
| 1. 메일 연동 | 더미 메일 `data/inbox.json` (Gmail API 형식 스키마) |
| 2. 에이전트 병렬 처리 | `ThreadPoolExecutor` — 각 에이전트가 서로 다른 메일 1건 담당 |
| 3. 5개 분류 | 스팸 / 응답불필요 / 의사결정 필요 / 의사결정 불필요 / 자동답장 |
| 4-① raw→JSON | inbox 스키마가 Gmail API 형식 (`gmail_adapter.py`로 변환 가능) |
| 4-② 답장 | 더미 모드: `sent.json`에 발신 메일로 저장 |
| 4-③ 스케줄 업데이트 | 일정 추출 → `schedule.json` |
| 4-④ 스팸 리스트 | `spam_db.json` + 발신자 차단 리스트 (재실행 시 LLM 없이 즉시 차단) |
| +@ 멀티 계정/AI | 여러 메일 계정 동시 처리, 계정마다 다른 AI(OpenAI/Ollama) 지정 |

## AI 제공자 + 자동 폴백

관리자 콘솔 **설정**(우상단 버튼, 팝업)에서 유료 AI를 키와 함께 등록합니다.
등록된 **유료 AI를 등록 순서대로 우선 사용**하고, **사용량 소진·오류로 실패하면
무료 로컬 Ollama로 자동 전환**합니다(전역 우선순위 체인). Ollama는 내장 폴백이라
항상 존재하며 삭제할 수 없습니다. 모델은 종류를 고르면 해당 제공자의 모델 목록에서
선택합니다.

지원 제공자 (유료는 설정창에서 키 입력):

| 제공자 | 종류 | 키 | 기본 모델 |
|---|---|---|---|
| OpenAI | `openai` | 필요 | `gpt-4o-mini` |
| Claude | `anthropic` | 필요 | `claude-3-5-haiku-latest` |
| Gemini | `google` | 필요 | `gemini-1.5-flash` |
| Ollama (로컬·무료·폴백) | `ollama` | 불필요 | `deepseek-r1:8b` |

- 유료 AI는 빠르고(메일당 1~3초) 병렬 효과가 확실히 드러납니다. Ollama는 느리지만(15~50초) 무료.
- 처리 결과에는 **실제로 처리한 AI**가 표시됩니다 (예: `OpenAI`, 폴백 시 `Ollama (폴백)`).

> API 키는 `data/accounts.json`에 평문 저장되며 `.gitignore`로 커밋에서 제외됩니다.
> 화면에는 `****`로 마스킹되어 표시됩니다. 환경변수
> `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GOOGLE_API_KEY`도 인식합니다.

## 분류 카테고리

| 카테고리 | 의미 | 자동 동작 |
|---|---|---|
| `spam` | 광고/피싱/당첨 사칭 | 스팸 DB 등록 + 발신자 차단 |
| `no_reply_needed` | 뉴스레터/소식지 | 읽음 처리 |
| `auto_handled` | 시스템 자동 알림(머지/영수증 등) | 읽음 처리 |
| `decision_needed` | 사람의 판단·승인 필요 | 검토 플래그 (자동답장 안 함) |
| `auto_reply` | 단순 감사/확인 | LLM이 답장 생성 → 발신함 저장 |

> 카테고리와 무관하게, 본문에 회의/면담 일정이 있으면 스케줄에 자동 추가됩니다.

## 사전 요구

- **Ollama 데몬 실행 중** (`localhost:11434`), `deepseek-r1:8b` 모델 풀:
  ```powershell
  ollama pull deepseek-r1:8b
  ```
  > 7B는 한국어 품질이 불안정하므로 8B 이상 권장.
- **Python 3.12** (LangChain wheel 호환). `venv/`는 3.12로 생성.
- (선택) 에이전트 동시 추론을 빠르게 하려면 Ollama 데몬에 병렬 설정:
  ```powershell
  $env:OLLAMA_NUM_PARALLEL=4   # 데몬 재시작 후 적용
  ```

## 실행

PowerShell, 프로젝트 루트(`26.05.30/`)에서:

```powershell
# 1) 패키지 설치 (최초 1회)
.\venv\Scripts\python.exe -m pip install -r requirements.txt

# 2) 샘플 받은편지함 2개 + 기본 계정 구성 생성
.\venv\Scripts\python.exe seed_data.py

# 3) 관리자 콘솔 서버 실행 후 브라우저에서 http://localhost:8000 열기
#    (localhost로 접속 — LAN IP는 방화벽에 막힐 수 있음)
.\venv\Scripts\python.exe server.py

# (대안) CLI로 병렬 처리만 실행
.\venv\Scripts\python.exe orchestrator.py

# (검증) 엔드투엔드 회귀 테스트
.\venv\Scripts\python.exe smoke_test.py
```

## 구조

```
26.05.30/
├── config.py        # 설정 (.env fallback): 모델, 워커 수, 페르소나, 카테고리, 경로
├── config_store.py  # 멀티 계정/AI 설정 저장소 (accounts.json CRUD, 키 마스킹)
├── llm.py           # LLM 제공자 팩토리 (openai / ollama 분기)
├── seed_data.py     # 샘플 inbox.json / inbox2.json + 기본 계정 구성 생성기
├── mail_store.py    # inbox/sent/spam_db/schedule JSON I/O (스레드 락 보호)
├── classifier.py    # 분류 에이전트 (LLM 구조화 JSON + <think> 제거)
├── tools.py         # 액션: register_spam / send_reply / update_schedule
├── orchestrator.py  # 병렬 디스패치(ThreadPoolExecutor) + 멀티계정 라우팅
├── server.py        # Flask 백엔드 (REST + SSE + 설정 CRUD)
├── static/          # 관리자 콘솔 (index.html / style.css / app.js, 빌드 없음)
├── smoke_test.py    # E2E 회귀 테스트
└── data/
    ├── inbox.json    # 기본 계정 받은편지함 (커밋됨)
    ├── inbox2.json   # 두 번째 계정 받은편지함 (커밋됨)
    ├── inbox3.json   # 일정 테스트용 받은편지함 20건 (커밋됨)
    ├── accounts.json # 멀티 계정/AI 설정 — API 키 포함 (gitignore)
    ├── sent.json     # 자동 답장 (런타임 생성)
    ├── spam_db.json  # 스팸 DB + 차단 발신자 (런타임 생성)
    └── schedule.json # 추출 일정 (런타임 생성)
```

## 동작 흐름

```
inbox.json ─→ orchestrator ─┬─ agent #1 (메일 A) ─→ classify ─→ route ─→ tools
                            ├─ agent #2 (메일 B) ─→ classify ─→ route ─→ tools
                            └─ agent #N (메일 …) ─→ ...                (병렬)
                                                          │
                          spam_db.json / sent.json / schedule.json 업데이트
                                                          │
                                       server.py(SSE) → 관리자 콘솔(static/)
```

## 실제 Gmail 연동

`gmail_adapter.py`가 OAuth(읽기 전용 `gmail.readonly`)로 실제 받은편지함의
**안 읽은 메일**을 가져와 같은 `emails` 스키마로 변환합니다. 분류·툴 로직은 더미와 공통.

설정 방법:
1. Google Cloud Console → 프로젝트 생성 → **Gmail API 사용 설정**
2. **OAuth 동의 화면**(외부) 구성 + 본인 Gmail을 **테스트 사용자**로 추가
3. **사용자 인증 정보 → OAuth 클라이언트 ID → 데스크톱 앱** → credentials JSON 다운로드
4. 관리자 콘솔 **설정 → 메일 계정 추가**: 소스 `gmail` → credentials JSON **붙여넣기**(파일 불필요)
5. 목록의 **연결** 버튼 → 브라우저 동의(허용) → 토큰 저장(이후 자동)
6. **병렬 처리 시작** → 안 읽은 메일을 모두 가져와 분류

- 한 번에 가져올 상한은 `GMAIL_MAX_UNREAD`(기본 50). 답장은 실제 발송하지 않고
  `sent.json`에 저장합니다(읽기 전용 권한).
- credentials/token은 `data/accounts.json`에만 저장되고 `.gitignore`로 제외됩니다.
