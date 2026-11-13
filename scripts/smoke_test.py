"""Quick end to end check of a RUNNING server. Standard library only.

    python scripts/smoke_test.py                      # http://127.0.0.1:8000
    python scripts/smoke_test.py http://localhost:8000

Use it for the offline test: turn Wi-Fi off, start the app, run this script.
"""
import json
import sys
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")
failures = []


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def check(name, ok, detail=""):
    print(("PASS  " if ok else "FAIL  ") + name + (f"  ({detail})" if detail and not ok else ""))
    if not ok:
        failures.append(name)


s, status = call("GET", "/api/status")
check("status 200 and backend ok", s == 200 and status.get("backend") == "ok", status)
print(f"      llm={status.get('llm')} offline_mode={status.get('offline_mode')} "
      f"documents_indexed={status.get('documents_indexed')} last_data_update={status.get('last_data_update')}")
check("status labelled SIMULATED", status.get("data_label") == "SIMULATED")

s, profile = call("GET", "/api/profile")
check("profile has mission_day", s == 200 and isinstance(profile.get("mission_day"), int), profile)

s, readings = call("GET", "/api/readings?days=14")
check("readings: 14 rows, SIMULATED", s == 200 and len(readings.get("readings", [])) == 14
      and readings.get("data_label") == "SIMULATED", readings)

s, alerts = call("GET", "/api/alerts")
a = alerts.get("alerts", [])
check("alerts: demo heart-rate alert present", s == 200 and any(x["metric"] == "heart_rate_bpm" for x in a), alerts)

alert_id = a[0]["id"] if a else None
s, ans = call("POST", "/api/assistant/ask", {"question": "Why was this flagged?", "alert_id": alert_id})
check("assistant answers with mode, citations, disclaimer",
      s == 200 and ans.get("mode") in ("llm", "retrieval_only") and "citations" in ans and ans.get("disclaimer"), ans)
print(f"      assistant mode={ans.get('mode')} citations={len(ans.get('citations', []))}")

s, err = call("POST", "/api/assistant/ask", {"question": "x", "alert_id": "does-not-exist"})
check("unknown alert gives 404 error shape", s == 404 and err.get("error", {}).get("code") == "NOT_FOUND", err)

print("\nALL CHECKS PASSED" if not failures else f"\n{len(failures)} CHECK(S) FAILED: {failures}")
sys.exit(1 if failures else 0)
