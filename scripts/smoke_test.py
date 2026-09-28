"""End-to-end smoke test against a running SlopTotal instance.

Exercises every public route with real inference and fails loudly if any engine
reports a load or runtime failure. Run it after changing dependencies, engines
or the Docker image:

    uvicorn app.main:app --port 8000 &
    python scripts/smoke_test.py                       # http://localhost:8000
    python scripts/smoke_test.py --base https://api.sloptotal.com --no-urls

`--no-urls` skips the checks that fetch live web pages.
"""

import argparse
import json
import sys
import time

import httpx

AI_TEXT = (
    "In today's rapidly evolving digital landscape, it's important to note that "
    "artificial intelligence plays a crucial role in fostering innovation across "
    "industries. Let's delve into the multifaceted tapestry of opportunities it "
    "offers. By leveraging cutting-edge tools, organizations can navigate complex "
    "challenges and unlock transformative, holistic outcomes.\n\n"
    "Moreover, it is essential to recognize that responsible adoption requires a "
    "comprehensive approach. Stakeholders must collaborate to ensure robust "
    "governance, transparency and ethical safeguards. Ultimately, embracing this "
    "paradigm shift is pivotal for building a sustainable and inclusive future."
)

HUMAN_TEXT = (
    "Missed the bus again this morning, so I walked. Took forty minutes and my "
    "left shoe has a hole I keep forgetting about until it rains, which it did, "
    "obviously. Stopped at the bakery on Elm - they were out of the rye again - "
    "and grabbed a coffee that was mostly foam.\n\n"
    "Honestly? Not the worst walk. Saw a guy by the river trying to teach his dog "
    "to ride a skateboard. The dog was not into it. I stood there way too long "
    "watching and was late anyway, so the bus thing didn't even matter in the end."
)

URL = "https://en.wikipedia.org/wiki/Alan_Turing"
FAILURE_MARKERS = ("model loading failed", "engine error")

failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))
    if not ok:
        failures.append(name)


def engine_failures(results: list[dict]) -> list[str]:
    return [
        r["engine_name"]
        for r in results
        if any(m in (r.get("details") or "").lower() for m in FAILURE_MARKERS)
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8000")
    ap.add_argument("--no-urls", action="store_true", help="skip live web fetches")
    args = ap.parse_args()
    c = httpx.Client(base_url=args.base, timeout=300)

    print(f"SlopTotal smoke test -> {args.base}")

    r = c.get("/health")
    check("GET /health", r.status_code == 200 and r.json()["status"] == "healthy")

    r = c.get("/api/engines")
    body = r.json()
    engines = body["engines"] if isinstance(body, dict) else body
    check("GET /api/engines lists 23", r.status_code == 200 and len(engines) == 23)

    scores = {}
    for label, text in (("ai", AI_TEXT), ("human", HUMAN_TEXT)):
        t0 = time.perf_counter()
        r = c.post("/api/analyze", json={"text": text})
        ms = (time.perf_counter() - t0) * 1000
        rep = r.json()
        res = rep.get("engine_results", [])
        bad = engine_failures(res)
        check(
            f"POST /api/analyze ({label})",
            r.status_code == 200 and len(res) == 23 and not bad,
            f"{rep.get('overall_score')} {rep.get('overall_verdict')!r}, {len(res)} engines, "
            f"{ms:.0f} ms" + (f", FAILED: {bad}" if bad else ""),
        )
        scores[label] = rep
    check(
        "AI sample scores above human sample",
        scores["ai"]["overall_score"] > scores["human"]["overall_score"],
    )

    rid = scores["ai"]["id"]
    r = c.get(f"/api/report/{rid}")
    check("GET /api/report/{id}", r.status_code == 200 and r.json()["id"] == rid)
    r = c.get(f"/report/{rid}")
    check("GET /report/{id} renders", r.status_code == 200 and "SlopTotal" in r.text)
    r = c.get("/api/recent")
    check("GET /api/recent", r.status_code == 200)

    r = c.post("/api/quick-score", json={"text": AI_TEXT})
    q = r.json()
    check(
        "POST /api/quick-score",
        r.status_code == 200 and 0 <= q["score"] <= 100,
        f"{q.get('score')} {q.get('verdict')}",
    )

    r = c.post("/api/paragraph-score", json={"text": AI_TEXT + "\n\n" + HUMAN_TEXT})
    check("POST /api/paragraph-score", r.status_code == 200, f"{len(r.text)} bytes")

    r = c.post(
        "/api/scan/snippets",
        json={
            "snippets": [
                {"id": "a", "text": AI_TEXT[:300]},
                {"id": "h", "text": HUMAN_TEXT[:300]},
            ]
        },
    )
    check("POST /api/scan/snippets", r.status_code == 200, f"{len(r.text)} bytes")

    r = c.post(
        "/api/extract", files={"file": ("essay.txt", AI_TEXT.encode(), "text/plain")}
    )
    check(
        "POST /api/extract (upload)",
        r.status_code == 200 and r.json()["text"] == AI_TEXT,
    )

    r = c.get("/api/queue/status")
    check("GET /api/queue/status", r.status_code == 200)

    # Browser flow: home page, JSON start, then the live SSE stream.
    r = c.get("/")
    check("GET / renders", r.status_code == 200 and "<form" in r.text)
    fresh = HUMAN_TEXT + f" (smoke {time.time():.0f})"
    r = c.post("/api/web/analyze", json={"text": fresh})
    started = r.json()
    check("POST /api/web/analyze", r.status_code == 200 and "report_id" in started)
    events = []
    with c.stream("GET", f"/api/stream/{started.get('report_id', 'x')}") as s:
        for line in s.iter_lines():
            if line.startswith("data: "):
                ev = json.loads(line[6:])
                if ev.get("done"):
                    break
                events.append(ev)
    bad = engine_failures(events)
    check(
        "GET /api/stream/{id} streams all engines",
        len({e.get("key") or e.get("engine_name") for e in events}) == 23 and not bad,
        f"{len(events)} events" + (f", FAILED: {bad}" if bad else ""),
    )

    r = c.post("/analyze", data={"text": "too short"})
    check("POST /analyze rejects short text", "at least 50 characters" in r.text)

    if not args.no_urls:
        r = c.post("/api/analyze", json={"url": URL})
        rep = r.json()
        bad = engine_failures(rep.get("engine_results", []))
        check(
            "POST /api/analyze (url)",
            r.status_code == 200 and rep.get("source_type") == "url" and not bad,
            f"{rep.get('overall_score')} {rep.get('overall_verdict')!r}",
        )
        r = c.post("/api/scan/urls", json={"urls": [{"id": "1", "url": URL}]})
        check("POST /api/scan/urls", r.status_code == 200, f"{len(r.text)} bytes")
        r = c.post("/api/scan/site", json={"url": URL})
        site = r.json()
        check(
            "POST /api/scan/site",
            r.status_code == 200 and site["site"]["builders"] == [] and site["text"],
            f"{site.get('site', {}).get('verdict')!r}, text {site.get('text', {}).get('score')}",
        )
        r = c.post("/api/scan/site", json={"url": "http://169.254.169.254/"})
        check("URL scans refuse private addresses", r.status_code == 400)

    print(f"\n{'OK' if not failures else 'FAILED'}: {len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
