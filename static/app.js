"use strict";

const $ = (sel) => document.querySelector(sel);
const el = (tag, cls, html) => {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (html != null) n.innerHTML = html;
  return n;
};
const esc = (s) =>
  String(s == null ? "" : s).replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])
  );

let CATEGORIES = {};
let ACCOUNTS = [];
let CONFIG = { ai_providers: [], mail_accounts: [] };
let PROVIDER_TYPES = {};
let evtSource = null;
let ROWS = [];
let filterAccount = "all";

const rowKey = (account, msgId) => account + "||" + msgId;

function badge(category, label) {
  const text = label || CATEGORIES[category] || category;
  return `<span class="badge ${category}">${esc(text)}</span>`;
}

async function init() {
  setupTheme();
  setupNav();
  setupControls();
  setupModal();
  setupSettingsForms();
  await loadProviderTypes();
  await loadInbox();
  await loadConfig();
  await refreshState();
}

async function loadProviderTypes() {
  PROVIDER_TYPES = await fetch("/api/provider-types").then((r) => r.json());
  const provSel = $("#ai_provider");
  provSel.innerHTML = "";
  Object.entries(PROVIDER_TYPES).forEach(([kind, meta]) =>
    provSel.insertAdjacentHTML("beforeend", `<option value="${kind}">${esc(meta.label)}</option>`)
  );
  provSel.addEventListener("change", fillModelSelect);
  fillModelSelect();
}

function fillModelSelect() {
  const kind = $("#ai_provider").value;
  const models = (PROVIDER_TYPES[kind] || {}).models || [];
  const sel = $("#ai_model");
  sel.innerHTML = "";
  models.forEach((m) =>
    sel.insertAdjacentHTML("beforeend", `<option value="${esc(m)}">${esc(m)}</option>`)
  );
}

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  $("#themeBtn").textContent = theme === "dark" ? "라이트 모드" : "다크 모드";
}
function setupTheme() {
  const saved = localStorage.getItem("theme") || "light";
  applyTheme(saved);
  $("#themeBtn").addEventListener("click", () => {
    const next =
      document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
    localStorage.setItem("theme", next);
    applyTheme(next);
  });
}

function setupModal() {
  const modal = $("#settingsModal");
  const open = () => (modal.hidden = false);
  const close = () => (modal.hidden = true);
  $("#settingsBtn").addEventListener("click", open);
  $("#settingsClose").addEventListener("click", close);
  modal.addEventListener("click", (e) => {
    if (e.target === modal) close();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !modal.hidden) close();
  });
}

async function loadInbox() {
  const data = await fetch("/api/inbox").then((r) => r.json());
  CATEGORIES = data.categories || {};
  ACCOUNTS = data.accounts || [];
  const total = ACCOUNTS.reduce((n, a) => n + a.emails.length, 0);
  $("#statInbox").textContent = total;
  const base = "상태별로 묶어 보여줍니다. 결정이 필요한 메일만 펼쳐서 처리하세요.";
  $("#dashSub").textContent =
    data.deduped > 0 ? `${base} (중복 ${data.deduped}건 자동 제외)` : base;
  buildRows();
  renderFilter();
  renderBoard();
}

function buildRows() {
  ROWS = [];
  ACCOUNTS.forEach((acc) =>
    acc.emails.forEach((e) =>
      ROWS.push({ account: acc.name, email: e, result: null, decided: null,
                  key: rowKey(acc.name, e.msg_id) })
    )
  );
}

function renderFilter() {
  const bar = $("#acctFilter");
  if (!bar) return;
  const names = ["all", ...ACCOUNTS.map((a) => a.name)];
  bar.innerHTML = names
    .map((n) => {
      const cnt = n === "all" ? ROWS.length : ROWS.filter((r) => r.account === n).length;
      const label = n === "all" ? "전체" : n;
      return `<button class="chip-btn${filterAccount === n ? " active" : ""}" data-acct="${esc(n)}">${esc(label)}<span class="cnt">${cnt}</span></button>`;
    })
    .join("");
}

const COLS = [
  { key: "wait", label: "대기", color: "var(--muted)" },
  { key: "spam", color: "var(--c-spam-fg)" },
  { key: "no_reply_needed", color: "var(--c-noreply-fg)" },
  { key: "auto_handled", color: "var(--c-auto-fg)" },
  { key: "decision_needed", color: "var(--c-decide-fg)" },
  { key: "auto_reply", color: "var(--c-reply-fg)" },
];

function colKey(row) {
  return row.result ? row.result.category : "wait";
}

function renderBoard() {
  const board = $("#board");
  if (!board) return;
  const rows = ROWS.filter((r) => filterAccount === "all" || r.account === filterAccount);
  const groups = {};
  rows.forEach((r) => (groups[colKey(r)] = groups[colKey(r)] || []).push(r));

  const visible = COLS.filter((c) => (groups[c.key] || []).length > 0);
  if (!visible.length) {
    board.innerHTML = `<div class="col-empty" style="padding:40px">메일이 없습니다. 위에서 '병렬 처리 시작'을 누르세요.</div>`;
    return;
  }

  if (visible.length === 1 && visible[0].key === "wait") {
    board.innerHTML = `<div class="board-grid">${groups["wait"].map(cardHtml).join("")}</div>`;
    return;
  }
  board.innerHTML = visible
    .map((c) => {

      const items = [...(groups[c.key] || [])].sort(
        (a, b) => (a.decided ? 1 : 0) - (b.decided ? 1 : 0)
      );
      const label = c.key === "wait" ? "대기" : CATEGORIES[c.key] || c.key;
      return `<div class="col">
        <div class="col-head">
          <span class="col-name"><span class="col-dot" style="background:${c.color}"></span>${esc(label)}</span>
          <span class="col-cnt">${items.length}</span>
        </div>
        <div class="col-body">${items.map(cardHtml).join("")}</div>
      </div>`;
    })
    .join("");
}

function cardHtml(row) {
  const e = row.email;
  const r = row.result;
  const preview = esc((e.body || "").slice(0, 120));
  const time = r ? `${r.elapsed}s` : "";
  const isDecision = r && r.category === "decision_needed";

  let meta = `<span class="mtag">${esc(row.account)}</span>`;
  if (r) {
    meta += `<span class="mtag">${esc(r.provider)}</span>`;
    meta += `<span class="mtag">확신도 ${Math.round((r.confidence || 0) * 100)}%</span>`;
  } else {
    meta += `<span class="mtag">대기</span>`;
  }

  let decideHtml = "";
  if (isDecision) {
    if (row.decided) {
      const rej = row.decided.decision === "reject";
      decideHtml = `<div class="decided-note${rej ? " rejected" : ""}">${rej ? "거절 처리됨" : "수락 처리됨"} · ${esc(row.decided.actions.join(", "))}</div>`;
    } else {
      const sch =
        r.has_schedule && r.schedule && r.schedule.datetime
          ? `<div class="db-detail">수락하면 <b>답장 발송</b> + 일정 등록:<br><b>${esc(r.schedule.title || e.subject)}</b> · ${esc(r.schedule.datetime)}</div>`
          : `<div class="db-detail">수락하면 <b>수락 답장</b>을, 거절하면 <b>거절 답장</b>을 보냅니다.</div>`;
      decideHtml = `<div class="decide-box" data-stop="1">
          <div class="db-title">내 결정이 필요해요</div>
          ${sch}
          <div class="decide-actions">
            <button class="btn-accept" data-row="${esc(row.key)}">수락</button>
            <button class="btn-reject" data-row="${esc(row.key)}">거절</button>
          </div>
        </div>`;
    }
  }

  return `<div class="mcard${isDecision ? " decision" : ""}" data-card="${esc(row.key)}">
    <div class="mcard-top">
      <span class="mcard-sender">${esc(e.sender_name)} &lt;${esc(e.sender_email)}&gt;</span>
      <span class="mcard-time">${esc(time)}</span>
    </div>
    <div class="mcard-subj">${esc(e.subject)}</div>
    <div class="mcard-preview">${preview}</div>
    <div class="mcard-meta">${meta}</div>
    ${decideHtml}
  </div>`;
}

function updateRowData(r) {
  const row = ROWS.find((x) => x.key === rowKey(r.account, r.msg_id));
  if (row) row.result = r;
  renderBoard();
}

function openDetail(row) {
  const e = row.email;
  const r = row.result;
  $("#dt_title").textContent = e.subject || "(제목 없음)";
  let cls = "";
  if (r) {
    cls = `<div class="dt-section">
      <div class="dt-row"><span class="dt-k">분류</span>${badge(r.category, r.category_label)}</div>
      <div class="dt-row"><span class="dt-k">처리 AI</span><span>${esc(r.provider)}${r.note ? " · " + esc(r.note) : ""}</span></div>
      <div class="dt-row"><span class="dt-k">근거</span><span>${esc(r.reason)}</span></div>
      <div class="dt-row"><span class="dt-k">수행</span><span>${(r.actions || []).map(esc).join(", ")}</span></div>
    </div>`;
  }
  let decide = "";
  if (r && r.category === "decision_needed" && !row.decided) {
    const sch =
      r.has_schedule && r.schedule && r.schedule.datetime
        ? `<div class="db-detail">수락하면 <b>답장 발송</b> + 일정 등록: <b>${esc(r.schedule.title || e.subject)}</b> · ${esc(r.schedule.datetime)}</div>`
        : `<div class="db-detail">수락/거절에 따라 답장이 저장됩니다.</div>`;
    decide = `<div class="decide-box">
        <div class="db-title">내 결정이 필요해요</div>${sch}
        <div class="decide-actions">
          <button class="btn-accept" data-row="${esc(row.key)}">수락</button>
          <button class="btn-reject" data-row="${esc(row.key)}">거절</button>
        </div>
      </div>`;
  } else if (row.decided) {
    const rej = row.decided.decision === "reject";
    decide = `<div class="decided-note${rej ? " rejected" : ""}">${rej ? "거절 처리됨" : "수락 처리됨"} · ${esc(row.decided.actions.join(", "))}</div>`;
  }
  $("#detailBody").innerHTML = `
    <div class="dt-row"><span class="dt-k">발신</span><span>${esc(e.sender_name)} &lt;${esc(e.sender_email)}&gt;</span></div>
    <div class="dt-row"><span class="dt-k">계정</span><span>${esc(row.account)}</span></div>
    <div class="dt-row"><span class="dt-k">날짜</span><span>${esc(e.date || "")}</span></div>
    <div class="dt-body">${esc(e.body || "(본문 없음)")}</div>
    ${cls}${decide}`;
  $("#detailModal").hidden = false;
}

async function refreshState() {
  paintState(await fetch("/api/state").then((r) => r.json()));
}

let LAST_STATE = { spam: { messages: [], senders: [] }, sent: [], schedule: [] };

function paintState(s) {
  LAST_STATE = {
    spam: s.spam || { messages: [], senders: [] },
    sent: s.sent || [],
    schedule: s.schedule || [],
  };
  $("#statSpam").textContent = (s.spam?.messages || []).length;
  $("#statSent").textContent = (s.sent || []).length;
  $("#statSched").textContent = (s.schedule || []).length;
  renderSent(s.sent || []);
  renderSpam(s.spam || { senders: [], messages: [] });
  renderSchedule(s.schedule || []);
}

function renderSent(sent) {
  const box = $("#sentList");
  box.innerHTML = "";
  if (!sent.length) return box.append(el("div", "empty", "자동 답장이 없습니다."));
  sent.forEach((m) => {
    box.insertAdjacentHTML(
      "beforeend",
      `<div class="reply">
        <div class="reply-head">
          <span class="reply-subj">${esc(m.subject)}</span>
          <span class="reply-to">${esc(m.account || "")} · 받는사람: ${esc(m.to)}</span>
        </div>
        <div class="reply-body">${esc(m.body)}</div>
      </div>`
    );
  });
}

function renderSpam(spam) {
  const chips = $("#spamSenders");
  chips.innerHTML = "";
  (spam.senders || []).forEach((s) =>
    chips.insertAdjacentHTML("beforeend", `<span class="chip">${esc(s)}</span>`)
  );
  const tbody = $("#spamRows");
  tbody.innerHTML = "";
  if (!(spam.messages || []).length) {
    tbody.innerHTML = `<tr><td colspan="3" class="empty">등록된 스팸이 없습니다.</td></tr>`;
    return;
  }
  spam.messages.forEach((m) =>
    tbody.insertAdjacentHTML(
      "beforeend",
      `<tr><td>${esc(m.sender_email)}</td><td>${esc(m.subject)}</td><td>${esc(m.date)}</td></tr>`
    )
  );
}

let SCHEDULE = [];
let calCentered = false;
let calYear, calMonth;
let selectedDay = null;

function renderSchedule(sched) {
  SCHEDULE = sched;
  const dates = sched.map(parseEventDate).filter(Boolean).sort((a, b) => a - b);
  if (calYear == null) {
    const base = dates[0] || new Date();
    calYear = base.getFullYear();
    calMonth = base.getMonth();
  }

  if (!calCentered && dates.length) {
    calYear = dates[0].getFullYear();
    calMonth = dates[0].getMonth();
    calCentered = true;
  }
  renderCalendar();
  renderSchedDetail();
}

function renderSchedDetail() {
  const box = $("#schedDetail");
  if (!box) return;
  let items = SCHEDULE.slice();
  if (selectedDay != null) {
    items = items.filter((ev) => {
      const d = parseEventDate(ev);
      return d && d.getFullYear() === calYear && d.getMonth() === calMonth && d.getDate() === selectedDay;
    });
    $("#schedDetailTitle").textContent = `${calMonth + 1}월 ${selectedDay}일 일정 (${items.length})`;
    $("#schedAll").hidden = false;
  } else {
    $("#schedDetailTitle").textContent = `전체 일정 (${items.length})`;
    $("#schedAll").hidden = true;
  }
  items.sort((a, b) => (a.datetime || "").localeCompare(b.datetime || ""));
  if (!items.length) {
    box.innerHTML = `<div class="empty">일정이 없습니다.</div>`;
    return;
  }
  box.innerHTML = items
    .map((e) => {
      const conflict = e.conflict
        ? `<span class="badge spam">충돌${e.conflict_with ? ": " + esc(e.conflict_with) : ""}</span>`
        : "";
      const date = selectedDay == null ? esc(e.datetime) : esc(parseEventTime(e) || e.datetime);
      return `<div class="sd-item${e.conflict ? " conflict" : ""}">
        <div class="sd-time">${esc(parseEventTime(e) || "종일")}</div>
        <div>
          <div class="sd-title">${esc(e.title)} ${conflict}</div>
          <div class="sd-meta">${date} · ${esc(e.from || "")}${e.account ? " · " + esc(e.account) : ""}</div>
        </div>
      </div>`;
    })
    .join("");
}

function parseEventDate(ev) {
  const m = String(ev.datetime || "").match(/(\d{4})-(\d{1,2})-(\d{1,2})/);
  if (!m) return null;
  return new Date(+m[1], +m[2] - 1, +m[3]);
}
function parseEventTime(ev) {
  const m = String(ev.datetime || "").match(/(\d{1,2}:\d{2})/);
  return m ? m[1] : "";
}

const DOW = ["일", "월", "화", "수", "목", "금", "토"];

function renderCalendar() {
  const cal = $("#calendar");
  if (!cal) return;
  $("#calLabel").textContent = `${calYear}년 ${calMonth + 1}월`;

  const byDay = {};
  SCHEDULE.forEach((ev) => {
    const d = parseEventDate(ev);
    if (d && d.getFullYear() === calYear && d.getMonth() === calMonth)
      (byDay[d.getDate()] = byDay[d.getDate()] || []).push(ev);
  });

  const firstDow = new Date(calYear, calMonth, 1).getDay();
  const daysInMonth = new Date(calYear, calMonth + 1, 0).getDate();
  const today = new Date();
  const isThisMonth = today.getFullYear() === calYear && today.getMonth() === calMonth;

  let html = DOW.map(
    (d, i) => `<div class="cal-dow ${i === 0 ? "sun" : i === 6 ? "sat" : ""}">${d}</div>`
  ).join("");

  for (let i = 0; i < firstDow; i++) html += `<div class="cal-cell empty"></div>`;
  for (let day = 1; day <= daysInMonth; day++) {
    const evs = byDay[day] || [];
    const chips = evs
      .map((ev) => {
        const cls = ev.conflict ? "cal-ev conflict" : "cal-ev";
        const tip = ev.conflict ? ` (충돌: ${esc(ev.conflict_with || "")})` : "";
        return `<div class="${cls}" title="${esc(ev.title)} ${esc(ev.datetime)}${tip}"><span class="ev-time">${esc(parseEventTime(ev))}</span>${esc(ev.title)}</div>`;
      })
      .join("");
    const todayCls = isThisMonth && day === today.getDate() ? " today" : "";
    const selCls = day === selectedDay ? " selected" : "";
    html += `<div class="cal-cell clickable${todayCls}${selCls}" data-day="${day}"><span class="cal-day">${day}</span>${chips}</div>`;
  }
  cal.innerHTML = html;
}

async function loadConfig() {
  CONFIG = await fetch("/api/config").then((r) => r.json());
  renderAiList();
  renderMailList();
}

function renderAiList() {
  const box = $("#aiList");
  box.innerHTML = "";
  if (!CONFIG.ai_providers.length)
    return box.append(el("div", "empty", "등록된 AI가 없습니다."));

  const sorted = [...CONFIG.ai_providers].sort(
    (a, b) => (a.provider === "ollama" ? 1 : 0) - (b.provider === "ollama" ? 1 : 0)
  );
  sorted.forEach((p) => {
    const builtin = p.provider === "ollama";
    const keyTag = builtin
      ? `<span class="tag ok">기본·항상 사용</span>`
      : p.key.has_key
      ? `<span class="tag ok">키 설정됨 ${esc(p.key.hint)}</span>`
      : `<span class="tag warn">키 없음</span>`;
    const del = builtin ? "" : `<button class="btn-del" data-ai="${esc(p.id)}">삭제</button>`;
    const item = el("div", "cfg-item");
    item.innerHTML = `
      <div class="ci-main">
        <div class="ci-name">${esc(p.name)} <span class="tag">${esc(p.provider)}</span> ${keyTag}</div>
        <div class="ci-sub">모델: ${esc(p.model || "-")}</div>
      </div>
      ${del}`;
    box.appendChild(item);
  });
  box.querySelectorAll("[data-ai]").forEach((b) =>
    b.addEventListener("click", async () => {
      await fetch("/api/config/ai/" + b.dataset.ai, { method: "DELETE" });
      await loadConfig();
    })
  );
}

function renderMailList() {
  const box = $("#mailList");
  box.innerHTML = "";
  if (!CONFIG.mail_accounts.length)
    return box.append(el("div", "empty", "등록된 메일 계정이 없습니다."));
  CONFIG.mail_accounts.forEach((m) => {
    const item = el("div", "cfg-item");
    let sub, connectBtn = "";
    if (m.source === "gmail") {
      const state = m.connected
        ? `<span class="tag ok">연결됨</span>`
        : m.has_credentials
        ? `<span class="tag warn">미연결</span>`
        : `<span class="tag warn">credentials 없음</span>`;
      sub = `Gmail · 안 읽은 메일을 실시간으로 가져옴 ${state}`;
      if (m.has_credentials)
        connectBtn = `<button class="btn-connect" data-connect="${esc(m.id)}">${m.connected ? "재연결" : "연결"}</button>`;
    } else {
      sub = `받은편지함: ${esc(m.inbox_file)}`;
    }
    item.innerHTML = `
      <div class="ci-main">
        <div class="ci-name">${esc(m.name)} <span class="tag">${esc(m.source)}</span></div>
        <div class="ci-sub">${sub}</div>
      </div>
      <div class="ci-actions">${connectBtn}<button class="btn-del" data-mail="${esc(m.id)}">삭제</button></div>`;
    box.appendChild(item);
  });
  box.querySelectorAll("[data-mail]").forEach((b) =>
    b.addEventListener("click", async () => {
      await fetch("/api/config/mail/" + b.dataset.mail, { method: "DELETE" });
      await loadConfig();
      await loadInbox();
    })
  );
  box.querySelectorAll("[data-connect]").forEach((b) =>
    b.addEventListener("click", async () => {
      b.textContent = "동의 대기...";
      b.disabled = true;
      const res = await fetch("/api/gmail/connect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: b.dataset.connect }),
      }).then((r) => r.json());
      if (res.ok) {
        alert("Gmail 연결 완료!");
      } else {
        alert("연결 실패: " + (res.error || "알 수 없는 오류"));
      }
      await loadConfig();
      await loadInbox();
    })
  );
}

function setupSettingsForms() {
  $("#aiAddBtn").addEventListener("click", async () => {
    const key = $("#ai_key").value.trim();
    if (!key) {
      alert("유료 AI는 API 키가 필요합니다. 키를 입력하세요.");
      return;
    }
    const body = {
      name: $("#ai_name").value.trim() || $("#ai_provider").value,
      provider: $("#ai_provider").value,
      model: $("#ai_model").value,
      api_key: key,
    };
    await fetch("/api/config/ai", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    $("#ai_name").value = $("#ai_key").value = "";
    await loadConfig();
  });

  const toggleMailSource = () => {
    const gmail = $("#mail_source").value === "gmail";
    $("#lbl_mail_creds").hidden = !gmail;
    $("#gmail_hint").hidden = !gmail;
    $("#lbl_mail_file").hidden = gmail;
  };
  $("#mail_source").addEventListener("change", toggleMailSource);
  toggleMailSource();

  $("#mailAddBtn").addEventListener("click", async () => {
    const source = $("#mail_source").value;
    const body = {
      name: $("#mail_name").value.trim() || "이름 없음",
      source,
      inbox_file: $("#mail_file").value.trim() || "inbox.json",
    };
    if (source === "gmail") {
      const creds = $("#mail_creds").value.trim();
      if (!creds) {
        alert("Gmail credentials JSON을 붙여넣으세요.");
        return;
      }
      try {
        JSON.parse(creds);
      } catch (e) {
        alert("credentials JSON 형식이 올바르지 않습니다.");
        return;
      }
      body.credentials_json = creds;
    }
    await fetch("/api/config/mail", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    $("#mail_name").value = $("#mail_file").value = $("#mail_creds").value = "";
    await loadConfig();
    await loadInbox();
  });
}

function runProcess() {
  const runBtn = $("#runBtn");
  runBtn.disabled = true;
  runBtn.textContent = "처리 중...";
  buildRows();
  renderBoard();
  $("#progressWrap").hidden = false;
  setProgress(0, 1, "에이전트 디스패치 중...");

  evtSource = new EventSource("/api/process?workers=" + $("#workers").value);
  evtSource.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.type === "result") {
      updateRowData(msg.result);
      setProgress(msg.done, msg.total, `처리 중... ${msg.done}/${msg.total}`);
    } else if (msg.type === "done") {
      paintState({ spam: msg.spam, sent: msg.sent, schedule: msg.schedule });
      renderBoard();
      finishProcess("처리 완료");
    } else if (msg.type === "error") {
      finishProcess("오류: " + msg.message);
    }
  };
  evtSource.onerror = () => finishProcess("연결 종료");
}

function setProgress(done, total, text) {
  const pct = total ? Math.round((done / total) * 100) : 0;
  $("#progressBar").style.width = pct + "%";
  $("#progressPct").textContent = pct + "%";
  $("#progressText").textContent = text;
}

function finishProcess(text) {
  if (evtSource) evtSource.close();
  evtSource = null;
  $("#progressText").textContent = text;
  const runBtn = $("#runBtn");
  runBtn.disabled = false;
  runBtn.textContent = "병렬 처리 시작";
}

function setupControls() {
  $("#workers").addEventListener("input", (e) => {
    $("#workerVal").textContent = e.target.value;
  });
  $("#runBtn").addEventListener("click", runProcess);
  $("#resetBtn").addEventListener("click", async () => {
    await fetch("/api/reset", { method: "POST" });
    buildRows();
    renderBoard();
    $("#progressWrap").hidden = true;
    await refreshState();
  });

  $("#acctFilter").addEventListener("click", (ev) => {
    const b = ev.target.closest(".chip-btn");
    if (!b) return;
    filterAccount = b.dataset.acct;
    renderFilter();
    renderBoard();
  });

  const dm = $("#detailModal");
  $("#detailClose").addEventListener("click", () => (dm.hidden = true));
  dm.addEventListener("click", (e) => { if (e.target === dm) dm.hidden = true; });

  $("#board").addEventListener("click", async (ev) => {
    const btn = ev.target.closest(".btn-accept, .btn-reject");
    if (btn) {
      ev.stopPropagation();
      await decide(btn);
      return;
    }
    const card = ev.target.closest(".mcard");
    if (card) {
      const row = ROWS.find((x) => x.key === card.dataset.card);
      if (row) openDetail(row);
    }
  });

  $("#detailBody").addEventListener("click", async (ev) => {
    const btn = ev.target.closest(".btn-accept, .btn-reject");
    if (btn) { await decide(btn); dm.hidden = true; }
  });

  $("#calPrev").addEventListener("click", () => {
    calMonth--; if (calMonth < 0) { calMonth = 11; calYear--; }
    selectedDay = null; renderCalendar(); renderSchedDetail();
  });
  $("#calNext").addEventListener("click", () => {
    calMonth++; if (calMonth > 11) { calMonth = 0; calYear++; }
    selectedDay = null; renderCalendar(); renderSchedDetail();
  });

  $("#calendar").addEventListener("click", (ev) => {
    const cell = ev.target.closest(".cal-cell.clickable");
    if (!cell) return;
    const day = Number(cell.dataset.day);
    selectedDay = selectedDay === day ? null : day;
    renderCalendar();
    renderSchedDetail();
  });
  $("#schedAll").addEventListener("click", () => {
    selectedDay = null; renderCalendar(); renderSchedDetail();
  });

  $("#reportBtn").addEventListener("click", downloadReport);
}

function buildReport() {
  const now = new Date();
  const ts = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")} ${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
  const done = ROWS.filter((r) => r.result);
  const counts = {};
  done.forEach((r) => (counts[r.result.category] = (counts[r.result.category] || 0) + 1));
  const s = LAST_STATE;
  const conflicts = (s.schedule || []).filter((e) => e.conflict).length;

  let md = `# 메일 처리 리포트\n\n생성: ${ts}\n\n`;
  md += `## 요약\n`;
  md += `- 받은편지함: ${ROWS.length}건\n`;
  md += `- 처리됨: ${done.length}건\n`;
  md += `- 스팸 차단: ${(s.spam.messages || []).length}건\n`;
  md += `- 자동 답장: ${(s.sent || []).length}건\n`;
  md += `- 등록 일정: ${(s.schedule || []).length}건 (충돌 ${conflicts}건)\n\n`;

  md += `## 카테고리별 분류\n\n| 카테고리 | 건수 |\n|---|---|\n`;
  Object.keys(CATEGORIES).forEach((k) => (md += `| ${CATEGORIES[k]} | ${counts[k] || 0} |\n`));

  md += `\n## 스팸 차단 발신자\n`;
  const senders = s.spam.senders || [];
  md += senders.length ? senders.map((x) => `- ${x}`).join("\n") + "\n" : "- (없음)\n";

  md += `\n## 자동 답장\n`;
  const sent = s.sent || [];
  md += sent.length
    ? sent.map((m) => `- **${m.subject}** → ${m.to}${m.account ? ` (${m.account})` : ""}`).join("\n") + "\n"
    : "- (없음)\n";

  md += `\n## 등록 일정\n`;
  const sched = s.schedule || [];
  md += sched.length
    ? sched.map((e) => `- ${e.title} · ${e.datetime}${e.account ? ` (${e.account})` : ""}${e.conflict ? ` ⚠ 충돌: ${e.conflict_with || ""}` : ""}`).join("\n") + "\n"
    : "- (없음)\n";

  const decisions = done.filter((r) => r.result.category === "decision_needed");
  if (decisions.length) {
    md += `\n## 의사결정 항목\n`;
    md += decisions
      .map((r) => {
        const d = r.decided ? (r.decided.decision === "accept" ? "수락" : "거절") : "대기";
        return `- [${d}] ${r.email.subject} (${r.account})`;
      })
      .join("\n") + "\n";
  }
  return md;
}

function downloadReport() {
  const blob = new Blob([buildReport()], { type: "text/markdown;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "mail_report.md";
  a.click();
  URL.revokeObjectURL(a.href);
}

async function decide(btn) {
  const row = ROWS.find((x) => x.key === btn.dataset.row);
  if (!row || !row.result) return;
  const accept = btn.classList.contains("btn-accept");
  btn.disabled = true;
  const res = await fetch("/api/decide", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      account: row.account,
      email: row.email,
      decision: accept ? "accept" : "reject",
      schedule: row.result.has_schedule ? row.result.schedule : null,
    }),
  }).then((r) => r.json());
  if (res.ok) {
    row.decided = { decision: accept ? "accept" : "reject", actions: res.actions };
    paintState({ spam: res.spam, sent: res.sent, schedule: res.schedule });
    renderBoard();
  } else {
    alert("처리 실패: " + (res.error || ""));
    btn.disabled = false;
  }
}

function setupNav() {
  $("#nav").addEventListener("click", (e) => {
    const btn = e.target.closest(".tab");
    if (!btn) return;
    document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".view").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    $("#view-" + btn.dataset.view).classList.add("active");
  });
}

init();
