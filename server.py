from __future__ import annotations

import json
import queue
import sys
import threading

from flask import Flask, Response, jsonify, request, send_from_directory

import config
import config_store
import llm as llm_factory
import mail_store
import orchestrator
import tools

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

app = Flask(__name__, static_folder="static", static_url_path="")

def _sse(obj: dict) -> str:
    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"

@app.get("/")
def index() -> Response:
    return send_from_directory(app.static_folder, "index.html")

@app.get("/api/inbox")
def api_inbox():
    store = config_store.load()
    accounts = []
    seen = set()
    removed = 0
    for acc in store["mail_accounts"]:
        item = {"id": acc["id"], "name": acc["name"], "source": acc.get("source", "dummy"),
                "emails": [], "status": ""}
        emails = []
        if acc.get("source") == "gmail" and not acc.get("token_json"):
            item["status"] = "미연결"
        else:
            try:
                emails = mail_store.account_emails(acc)
            except Exception as exc:
                item["status"] = f"오류: {type(exc).__name__}"

        kept = []
        for e in emails:
            key = mail_store.email_key(e)
            if key in seen:
                removed += 1
                continue
            seen.add(key)
            kept.append(e)
        item["emails"] = kept
        accounts.append(item)
    return jsonify({"accounts": accounts, "categories": config.CATEGORIES, "deduped": removed})

@app.post("/api/gmail/connect")
def api_gmail_connect():
    mid = (request.get_json(force=True) or {}).get("id", "")
    acc = config_store.get_mail(mid)
    if not acc:
        return jsonify({"ok": False, "error": "메일 계정을 찾을 수 없음"}), 404
    if not acc.get("credentials_json"):
        return jsonify({"ok": False, "error": "credentials JSON이 없습니다"}), 400
    try:
        import gmail_adapter

        token = gmail_adapter.start_oauth(acc["credentials_json"])
        config_store.set_mail_token(mid, token)
        return jsonify({"ok": True})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500

@app.get("/api/provider-types")
def api_provider_types():
    types = {
        kind: {"label": meta["label"], "models": meta["models"]}
        for kind, meta in llm_factory.PROVIDERS.items()
        if kind != "ollama"
    }
    return jsonify(types)

@app.get("/api/state")
def api_state():
    return jsonify(
        {
            "spam": mail_store.load_spam_db(),
            "sent": mail_store.load_sent(),
            "schedule": mail_store.load_schedule(),
        }
    )

@app.post("/api/reset")
def api_reset():
    mail_store.reset_outputs()
    return jsonify({"ok": True})

@app.post("/api/decide")
def api_decide():
    data = request.get_json(force=True) or {}
    email = data.get("email", {})
    account = data.get("account", "")
    decision = data.get("decision", "")
    schedule = data.get("schedule") or {}

    if decision not in ("accept", "reject"):
        return jsonify({"ok": False, "error": "decision은 accept/reject"}), 400

    actions = []
    accept = decision == "accept"
    actions.append(tools.send_reply(email, tools.decision_reply(email, accept), account))
    if accept and schedule:
        actions.append(tools.update_schedule(email, schedule, account))

    return jsonify(
        {
            "ok": True,
            "actions": actions,
            "spam": mail_store.load_spam_db(),
            "sent": mail_store.load_sent(),
            "schedule": mail_store.load_schedule(),
        }
    )

@app.get("/api/config")
def api_config():
    return jsonify(config_store.public_view())

@app.post("/api/config/ai")
def api_config_ai():
    saved = config_store.upsert_ai(request.get_json(force=True) or {})
    return jsonify({"ok": True, "id": saved["id"]})

@app.delete("/api/config/ai/<pid>")
def api_config_ai_delete(pid: str):
    config_store.delete_ai(pid)
    return jsonify({"ok": True})

@app.post("/api/config/mail")
def api_config_mail():
    saved = config_store.upsert_mail(request.get_json(force=True) or {})
    return jsonify({"ok": True, "id": saved["id"]})

@app.delete("/api/config/mail/<mid>")
def api_config_mail_delete(mid: str):
    config_store.delete_mail(mid)
    return jsonify({"ok": True})

@app.get("/api/process")
def api_process() -> Response:
    workers = request.args.get("workers", type=int) or config.MAX_WORKERS
    tasks = orchestrator.build_tasks()
    total = len(tasks)
    q: "queue.Queue" = queue.Queue()

    def run() -> None:
        try:
            orchestrator.process_accounts(max_workers=workers, on_done=q.put)
        except Exception as exc:
            q.put({"_error": str(exc)})
        finally:
            q.put(None)

    threading.Thread(target=run, daemon=True).start()

    def stream():
        yield _sse({"type": "start", "total": total, "workers": workers})
        done = 0
        while True:
            item = q.get()
            if item is None:
                break
            if "_error" in item:
                yield _sse({"type": "error", "message": item["_error"]})
                continue
            done += 1
            yield _sse({"type": "result", "done": done, "total": total, "result": item})
        yield _sse(
            {
                "type": "done",
                "spam": mail_store.load_spam_db(),
                "sent": mail_store.load_sent(),
                "schedule": mail_store.load_schedule(),
            }
        )

    return Response(stream(), mimetype="text/event-stream")

if __name__ == "__main__":
    print("관리자 콘솔: http://localhost:8000  (Ctrl+C 종료)")
    app.run(host="0.0.0.0", port=8000, threaded=True, use_reloader=False)
