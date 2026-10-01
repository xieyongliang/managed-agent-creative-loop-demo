"""MA-resident creative loop: design exploration, customer selection, production and independent review."""
import argparse
from datetime import date
import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.request
import evaluation as ev
import media
import research as rs

BASE = os.getenv("ARK_BASE_URL", "https://ark.ap-southeast.bytepluses.com/api/v3").rstrip("/")
ROOT = Path(os.getenv("CREATIVE_WORKDIR", "/mnt/session/creative-loop"))
VIDEO_RETRIES = 2
REVIEW_ATTEMPTS = 2
CONTRACT_AUDITS = 3
EXPORT_CHUNK = 16000
AUDIO_REJECTION = "OutputAudioSensitiveContentDetected.PolicyViolation"
# Conservative application policy: unknown and policy errors require inspection.
TRANSIENT_VIDEO_ERRORS = {"InternalError", "InternalServerError", "ServiceUnavailable", "ServerOverloaded"}
TERMINAL = ("completed", "max_rounds", "blocked", "failed")
# Outcomes after which the same step call may keep working inside its time budget.
CONTINUE = ("design_completed", "design_failed", "screening_retry", "mockup_completed", "video_submitted", "video_completed",
            "retrying_video", "review_retry", "needs_audit", "needs_adjudication", "variant_reviewed", "variant_failed")
NEXT = {
    "contract_gaps": "Nothing is frozen or generated yet. Add or correct criteria in the plan so every listed requirement is covered, then run init again.",
    "awaiting_selection": "Run creative.py export and return its exact output. Stop here: the customer chooses which designs continue.",
    "needs_revision": "For every variant listed under revise, write revised prompts to /mnt/session/revised-prompts.json, run creative.py revise --input /mnt/session/revised-prompts.json, then continue step.",
    "completed": "Run creative.py export and return its exact output.",
    "max_rounds": "Run creative.py export and return its exact output; do not claim the target was met.",
    "blocked": "Run creative.py export, explain which requirements the frozen criteria omit, and stop. Do not edit the frozen criteria.",
    "failed": "Run creative.py export and report the recorded errors. Do not retry submissions that were not confirmed.",
}


class ApiError(RuntimeError):
    def __init__(self, message, certain=True, code=None):
        super().__init__(message)
        self.certain = certain
        self.code = code


def save(state):
    ROOT.mkdir(parents=True, exist_ok=True)
    tmp = ROOT / "state.tmp"
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    tmp.chmod(0o600)
    tmp.replace(ROOT / "state.json")
    (ROOT / "state.sig").write_text(signature(state))


def load():
    state = json.loads((ROOT / "state.json").read_text())
    if not hmac.compare_digest((ROOT / "state.sig").read_text(), signature(state)):
        raise RuntimeError("State integrity check failed. Never edit state.json directly; stop and report the failure.")
    return state


def signature(state):
    key = os.environ.get("ARK_API_KEY")
    if not key:
        raise RuntimeError("ARK_API_KEY missing")
    return hmac.new(key.encode(), json.dumps(state, sort_keys=True, ensure_ascii=False).encode(), hashlib.sha256).hexdigest()


def response_stream(lines):
    data = []
    for raw in lines:
        line = raw.decode("utf-8").rstrip("\r\n")
        if line.startswith("data:"):
            data.append(line[5:].lstrip())
        elif not line and data:
            payload = "\n".join(data)
            data = []
            if payload == "[DONE]":
                continue
            event = json.loads(payload)
            if event.get("type") in ("response.failed", "response.incomplete", "error"):
                raise RuntimeError("Responses did not complete: " + event.get("type", "error"))
            if event.get("type") == "response.completed":
                result = event.get("response", {})
                if result.get("status") != "completed":
                    raise RuntimeError("Response completion status missing")
                return result
    raise RuntimeError("SSE ended before response.completed")


def api(path, body=None, stream=False):
    key = os.environ.get("ARK_API_KEY")
    if not key:
        raise RuntimeError("ARK_API_KEY is missing from the Cloud Environment")
    request = urllib.request.Request(BASE + path, data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    for attempt in range(3):
        code = None
        try:
            with urllib.request.urlopen(request, timeout=30 if body is None else 240) as response:
                return response_stream(response) if stream else json.load(response)
        except urllib.error.HTTPError as error:
            retryable = error.code == 429 or 500 <= error.code <= 599
            # A 4xx answer means the provider refused the request, so nothing was created.
            certain = error.code < 500
            try:
                code = (json.loads(error.read().decode("utf-8", "replace")).get("error") or {}).get("code")
                error.close()
            except Exception:
                pass
            message = "Model API HTTP " + str(error.code) + (": " + str(code) if code else "")
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            retryable, certain = True, False
            message = "Model API transport failure"
        # Never repeat a POST with an unknown outcome; GET retries retain task ID.
        if not retryable or attempt == 2 or (body is not None and not certain):
            raise ApiError(message, certain, code) from None
        time.sleep(5 * (2 ** attempt))


def ask(instruction, images=(), video=None):
    """One fresh reviewer context: no creator reasoning, no conversation history."""
    content = [{"type": "input_text", "text": instruction}] + [{"type": "input_image", "image_url": url} for url in images]
    if video:
        content.append({"type": "input_video", "video_url": video, "fps": 1})
    result = api("/responses", {"model": os.getenv("EVAL_MODEL", os.getenv("VISION_MODEL", "seed-2-0-lite-260428")), "stream": True,
                                "input": [{"role": "user", "content": content}]}, stream=True)
    text = "\n".join(c["text"] for item in result.get("output", []) for c in item.get("content", []) if c.get("type") == "output_text")
    return ev.parse(text), result


def prompts(value):
    if not isinstance(value, dict) or any(not isinstance(value.get(k), str) or not value[k].strip() or len(value[k]) > 10000 for k in ("design", "mockup", "video")):
        raise ValueError("Three nonempty prompts are required")
    return {k: value[k] for k in ("design", "mockup", "video")}


def assert_contract(state):
    expected = ev.contract_hash(state["brief"], state["criteria"], state.get("watermark"), state.get("generate_audio"))
    if state.get("evidence_contract") != 3 or state.get("contract_hash") != expected:
        raise ValueError("Frozen acceptance contract is missing or changed; use a new Session")


def chosen(state):
    """Selected variants in the customer's order of preference."""
    by_id = {v["id"]: v for v in state["variants"]}
    return [by_id[x] for x in state.get("selected", [])]


def evaluated(variant):
    return [r for r in variant.get("rounds", []) if "review" in r]


def selected_round(variant):
    rounds = evaluated(variant)
    if not rounds:
        return None
    return rounds[-1] if variant["status"] == "completed" else max(rounds, key=lambda r: (r["review"]["quality_gate"] == "passed", r["review"]["score"]))


def winner(state):
    ranked = [v for v in chosen(state) if evaluated(v)]
    if not ranked:
        return None
    return max(ranked, key=lambda v: (v["status"] == "completed", selected_round(v)["review"]["quality_gate"] == "passed", selected_round(v)["review"]["score"]))


def result_summary(state):
    rows = []
    for v in chosen(state):
        best = selected_round(v)
        review = best["review"] if best else None
        rows.append({"id": v["id"], "status": v["status"], "selected_round": best["number"] if best else None,
                     "score": review["score"] if review else None, "met_target": v["status"] == "completed",
                     "score_gap": max(0, round(state["target_score"] - review["score"], 6)) if review else None,
                     "failed_checks": [c["id"] for c in review["checks"] if c["status"] == "fail"] if review else [],
                     "unverified_checks": [c["id"] for c in review["checks"] if c["status"] == "unverified"] if review else [],
                     "uncovered_requirements": review["uncovered_requirements"] if review else [],
                     "error": v.get("error")})
    best = winner(state)
    return {"winner": best["id"] if best else None, "stop_reason": state["status"], "met_target": state["status"] == "completed", "variants": rows}


def fail(variant, reason, code=None):
    variant["status"] = "failed"
    variant["error"] = reason
    if code:
        variant["error_code"] = code
    if variant.get("rounds"):
        variant["rounds"][-1].pop("inflight", None)
    variant.pop("inflight", None)


def submit(state, holder, phase, path, body):
    """POST once. A refused request is a known failure; an unanswered one is never repeated."""
    holder["inflight"] = phase
    save(state)
    try:
        result = api(path, body)
    except ApiError as error:
        if not error.certain:
            raise
        del holder["inflight"]
        save(state)
        return None, error
    del holder["inflight"]
    return result, None


def image_body(state, prompt, phase, reference=None):
    requirements = [c["description"] for c in state["criteria"] if phase in c["asset_refs"]]
    body = {"model": os.getenv("IMAGE_MODEL", "seedream-4-5-251128"), "prompt": prompt + " Deliverable requirements: " + json.dumps(requirements, ensure_ascii=False),
            "size": "2K", "response_format": "url", "watermark": state["watermark"]}
    if reference:
        body["image"] = reference
    return body


def note(log, unit, variant, result, detail=None, number=None, **shown):
    """Record one unit of work. A finished asset carries its URL so the customer can watch results arrive."""
    entry = (("unit", unit), ("variant", variant), ("round", number), ("result", result), ("detail", detail)) + tuple(shown.items())
    log.append({k: v for k, v in entry if v is not None})


def explore(state, log):
    for v in state["variants"]:
        if v.get("inflight"):
            fail(v, "Design submission was not confirmed; it is not resubmitted to avoid a duplicate charge")
            note(log, "design", v["id"], "failed", v["error"])
            save(state)
    for v in state["variants"]:
        if "design" in v or v.get("error"):
            continue
        result, error = submit(state, v, "design", "/images/generations", image_body(state, v["prompts"]["design"], "design"))
        if error:
            fail(v, "Design generation was refused: " + str(error), error.code)
        else:
            v["design"] = {"url": result["data"][0]["url"], "usage": result.get("usage")}
        save(state)
        note(log, "design", v["id"], "failed" if error else "ok", v.get("error"), url=v.get("design", {}).get("url"), title=v["title"], style=v["style"])
        return "design_failed" if error else "design_completed"
    designed = [v for v in state["variants"] if "design" in v]
    if not designed:
        state["status"] = "failed"
        state["error"] = "No design could be generated"
        save(state)
        return "failed"
    if "screening" not in state:
        attempts = state.get("screening_attempts", 0)
        if attempts >= REVIEW_ATTEMPTS:
            # Screening is advice for the customer, not an acceptance gate.
            state["screening"] = {"status": "unavailable"}
        else:
            state["screening_attempts"] = attempts + 1
            save(state)
            try:
                report, result = ask(ev.screening_instruction(state["brief"], state["criteria"], designed, state["language"], state["select_max"]),
                                     [v["design"]["url"] for v in designed])
                ev.validate_screening(report, [v["id"] for v in designed], state["select_max"])
            except (RuntimeError, ValueError, KeyError) as error:
                note(log, "screening", None, "retry", str(error)[:200])
                return "screening_retry"
            state["screening"] = {"status": "completed", "report": report, "response_id": result["id"], "usage": result.get("usage")}
            note(log, "screening", None, "ok")
    state["status"] = "awaiting_selection"
    save(state)
    return "awaiting_selection"


def finish_round(state, variant):
    r = variant["rounds"][-1]
    r["technical"] = ev.technical_checks(r.get("probe"), r.get("generate_audio", state["generate_audio"]))
    r["review"] = ev.effective_review(state["criteria"], r["evaluation"]["report"], r["audit"]["report"],
                                      r.get("adjudication", {}).get("report"), r["technical"], state["language"])
    review = r["review"]
    r["evidence"] = {"response_id": r.get("adjudication", r["evaluation"])["response_id"], "source": review["review_source"]}
    passed = review["quality_gate"] == "passed" and review["score"] >= state["target_score"]
    variant["status"] = "blocked" if review["uncovered_requirements"] else "completed" if passed else "max_rounds" if len(variant["rounds"]) >= state["max_rounds"] else "needs_revision"
    if variant["status"] == "blocked":
        variant["error"] = "Reviewers found requirements that the frozen criteria omit; start a corrected campaign rather than changing the contract"
    variant["best_round"] = selected_round(variant)["number"]
    save(state)


def review_step(state, variant, log):
    r = variant["rounds"][-1]
    stage = "evaluation" if "evaluation" not in r else "audit" if "audit" not in r else "adjudication" if r["audit"]["report"]["conflicts"] and "adjudication" not in r else None
    if stage is None:
        finish_round(state, variant)
        note(log, "review", variant["id"], variant["status"], "score %s" % r["review"]["score"], r["number"])
        return "variant_reviewed"
    attempts = r.get(stage + "_attempts", 0)
    if attempts >= REVIEW_ATTEMPTS:
        fail(variant, stage + " exhausted its two attempts without a valid report")
        save(state)
        note(log, stage, variant["id"], "failed", variant["error"], r["number"])
        return "variant_failed"
    r[stage + "_attempts"] = attempts + 1
    save(state)
    try:
        # Each role uses a fresh model context, with no creator reasoning or history.
        report, result = ask(ev.instruction(stage, state["brief"], state["criteria"], r, state["watermark"], state["language"], r.get("generate_audio", state["generate_audio"])),
                             [r["design"]["url"], r["mockup"]["url"]], r["video"]["url"])
        if stage == "audit":
            ev.validate_audit(report, state["criteria"])
        elif stage == "adjudication":
            ev.validate_adjudication(report, state["criteria"], r["audit"]["report"])
        else:
            ev.validate_report(report, state["criteria"])
    except (RuntimeError, ValueError, KeyError) as error:
        note(log, stage, variant["id"], "retry", str(error)[:200], r["number"])
        return "review_retry"
    r[stage] = {"report": report, "response_id": result["id"], "usage": result.get("usage")}
    save(state)
    note(log, stage, variant["id"], "ok", None, r["number"])
    if stage == "evaluation":
        return "needs_audit"
    if stage == "audit" and report["conflicts"]:
        return "needs_adjudication"
    finish_round(state, variant)
    note(log, "review", variant["id"], variant["status"], "score %s" % r["review"]["score"], r["number"])
    return "variant_reviewed"


def poll(state, log):
    deadline = time.time() + float(os.getenv("POLL_SECONDS", "120"))
    while True:
        waiting = retrying = False
        for v in chosen(state):
            r = v["rounds"][-1]
            if v["status"] != "running" or "video" in r or "task" not in r:
                continue
            if time.time() - r["submitted_at"] > 1800:
                fail(v, "Video observation exceeded 30 minutes; retained task: " + r["task"])
                note(log, "video", v["id"], "failed", v["error"], r["number"])
                continue
            result = api("/contents/generations/tasks/" + r["task"])
            if result["status"] == "succeeded":
                r["video"] = {"url": result["content"]["video_url"], "task": r["task"], "usage": result.get("usage")}
                note(log, "video", v["id"], "ok", None, r["number"], url=r["video"]["url"])
            elif result["status"] in ("failed", "expired", "cancelled"):
                problem = result.get("error") or {}
                retries = r.get("video_retries", 0)
                r.setdefault("failed_tasks", []).append({"id": r["task"], "error": problem, "reason": "transient_retry"})
                if result["status"] == "failed" and problem.get("code") in TRANSIENT_VIDEO_ERRORS and retries < VIDEO_RETRIES:
                    r["video_retries"] = retries + 1
                    r["video_retry_after"] = time.time() + 5 * (2 ** retries)
                    del r["task"]
                    r.pop("submitted_at", None)
                    retrying = True
                    note(log, "video", v["id"], "retry", problem.get("code"), r["number"])
                else:
                    r["failed_tasks"][-1]["reason"] = "stopped"
                    fail(v, "Video task " + result["status"] + ": " + str(problem.get("code", "unknown")), problem.get("code"))
                    note(log, "video", v["id"], "failed", v["error"], r["number"])
            else:
                waiting = True
        save(state)
        if not waiting or time.time() >= deadline:
            return "retrying_video" if retrying else "waiting_video" if waiting else "video_completed"
        time.sleep(float(os.getenv("POLL_INTERVAL", "10")))


def settle(state):
    statuses = [v["status"] for v in chosen(state)]
    for status in ("needs_revision", "completed", "max_rounds", "blocked", "failed"):
        if status in statuses:
            state["status"] = status
            break
    save(state)
    return state["status"]


def produce(state, log):
    for v in chosen(state):
        r = v["rounds"][-1]
        if v["status"] == "running" and r.get("inflight"):
            phase = r["inflight"]
            fail(v, phase.capitalize() + " submission was not confirmed; it is not resubmitted to avoid a duplicate charge")
            note(log, phase, v["id"], "failed", v["error"], r["number"])
            save(state)
    live = [v for v in chosen(state) if v["status"] == "running"]
    for phase in ("design", "mockup"):
        for v in live:
            r = v["rounds"][-1]
            if phase in r:
                continue
            result, error = submit(state, r, phase, "/images/generations",
                                   image_body(state, r["prompts"][phase], phase, r["design"]["url"] if phase == "mockup" else None))
            if error:
                fail(v, phase.capitalize() + " generation was refused: " + str(error), error.code)
            else:
                r[phase] = {"url": result["data"][0]["url"], "usage": result.get("usage")}
            save(state)
            note(log, phase, v["id"], "failed" if error else "ok", v.get("error"), r["number"], url=r.get(phase, {}).get("url"))
            return "variant_failed" if error else phase + "_completed"
    for v in live:
        r = v["rounds"][-1]
        if "task" in r or "video" in r:
            continue
        time.sleep(max(0, r.get("video_retry_after", 0) - time.time()))
        result, error = submit(state, r, "video", "/contents/generations/tasks", {
            "model": os.getenv("VIDEO_MODEL", "dreamina-seedance-2-5-260628"),
            "content": [{"type": "text", "text": r["prompts"]["video"] + " Exactly 5 seconds. No added marketing overlays, invented claims or testimonials. Preserve reference product print."},
                        {"type": "image_url", "image_url": {"url": r["mockup"]["url"]}, "role": "reference_image"}],
            "omni_reference_task_type": "reference", "duration": 5, "ratio": "9:16",
            "generate_audio": r.get("generate_audio", state["generate_audio"]), "watermark": state["watermark"]})
        if error:
            fail(v, "Video submission was refused: " + str(error), error.code)
        else:
            r["task"] = result["id"]
            r["submitted_at"] = time.time()
        save(state)
        note(log, "video_submit", v["id"], "failed" if error else "ok", v.get("error"), r["number"])
        return "variant_failed" if error else "video_submitted"
    if any("video" not in v["rounds"][-1] for v in live):
        return poll(state, log)
    for v in live:
        r = v["rounds"][-1]
        if "probe" not in r:
            r["probe"] = media.probe(r["video"]["url"])
            save(state)
        return review_step(state, v, log)
    return settle(state)


def advance(state, log):
    assert_contract(state)
    if state["status"] != "running":
        return state["status"]
    return explore(state, log) if state["phase"] == "designs" else produce(state, log)


def run(state):
    budget = float(os.getenv("STEP_BUDGET_SECONDS", "120"))
    started = time.time()
    log = []
    while True:
        outcome = advance(state, log)
        if outcome not in CONTINUE or time.time() - started >= budget:
            return outcome, log


def contract_audit(plan, rubric, settings):
    path = ROOT / "contract-audit.json"
    ROOT.mkdir(parents=True, exist_ok=True)
    record = json.loads(path.read_text()) if path.exists() else {"attempts": 0}
    if record["attempts"] >= CONTRACT_AUDITS:
        return {**record, "status": record.get("status", "unavailable"), "exhausted": True}
    record["attempts"] += 1
    try:
        report, result = ask(ev.contract_instruction(plan["brief"], rubric, plan["language"], settings))
        ev.validate_contract_audit(report, rubric)
        record.update(status="completed", report=report, response_id=result["id"])
    except (RuntimeError, ValueError, KeyError) as error:
        record.update(status="unavailable", error=str(error)[:200])
        record.pop("report", None)
    path.write_text(json.dumps(record, ensure_ascii=False))
    return record


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError("%s must be an integer from %d to %d" % (name, low, high))
    return value


def freeze(value):
    if (ROOT / "state.json").exists():
        raise ValueError("Existing loop: resume with step/status; never replace state")
    if not isinstance(value, dict) or not ev.nonempty(value.get("brief")):
        raise ValueError("The plan needs the original brief")
    limit = integer(value.get("max_rounds", 2), 1, 5, "max_rounds")
    count = integer(value.get("design_count", 5), 3, 6, "design_count")
    picks = integer(value.get("select_max", 3), 1, 3, "select_max")
    target = value.get("target_score", 4.5)
    if type(target) not in (int, float) or not math.isfinite(target) or not 0 <= target <= 5:
        raise ValueError("Invalid loop limits")
    audio, watermark, language = value.get("generate_audio", True), value.get("watermark", True), value.get("language", "vi")
    if type(audio) is not bool:
        raise ValueError("generate_audio must be boolean")
    if type(watermark) is not bool:
        raise ValueError("watermark must be boolean")
    if language not in ev.LANGUAGES:
        raise ValueError("language must be one of " + ", ".join(ev.LANGUAGES))
    insights = value.get("insights")
    if not isinstance(insights, dict) or not ev.nonempty(insights.get("market")) or not ev.nonempty(insights.get("audience")):
        raise ValueError("insights must state the market and audience extracted from the brief")
    own_store = value.get("own_store") or None
    if own_store is not None and not ev.nonempty(own_store):
        raise ValueError("own_store must be the customer's store domain, or omitted")
    coverage = rs.validate(value.get("research"), own_store)
    sources = {s["id"] for s in value["research"]["sources"]}
    rubric = ev.criteria(value.get("criteria"))
    drafts = value.get("variants")
    if not isinstance(drafts, list) or len(drafts) != count:
        raise ValueError("Provide exactly %d design variants" % count)
    variants = []
    for i, d in enumerate(drafts):
        if not isinstance(d, dict) or not all(ev.nonempty(d.get(k)) for k in ("title", "style", "rationale")):
            raise ValueError("Each variant needs title, style and rationale")
        palette, cited = d.get("palette", []), d.get("inspired_by", [])
        if not isinstance(palette, list) or len(palette) > 6 or any(not isinstance(x, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", x) for x in palette):
            raise ValueError("palette must list at most six #RRGGBB colours")
        if not isinstance(cited, list) or any(x not in sources for x in cited):
            raise ValueError("inspired_by must cite recorded research source ids")
        variants.append({"id": "v%d" % (i + 1), "title": d["title"].strip(), "style": d["style"].strip(), "rationale": d["rationale"].strip(),
                         "palette": palette, "typography": d.get("typography") if ev.nonempty(d.get("typography")) else None,
                         "inspired_by": cited, "prompts": prompts(d.get("prompts")), "status": "candidate"})
    if len({v["style"].lower() for v in variants}) != count or len({v["prompts"]["design"] for v in variants}) != count:
        raise ValueError("Every variant must use a different style and a different design prompt")
    plan = {"brief": value["brief"], "language": language}
    audit = contract_audit(plan, rubric, {"watermark": watermark, "generate_audio": audio})
    gaps = audit.get("report", {}).get("gaps", [])
    if gaps and not audit.get("exhausted") and audit["attempts"] < CONTRACT_AUDITS:
        return {"status": "contract_gaps", "gaps": gaps, "unsupported": audit["report"]["unsupported"], "summary": audit["report"]["summary"],
                "audits_left": CONTRACT_AUDITS - audit["attempts"], "next_action": NEXT["contract_gaps"]}
    research = dict(value["research"], coverage_summary=coverage, seasonal_calendar=rs.calendar(date.today()))
    state = {"status": "running", "phase": "designs", "execution": "ma_cloud_skill", "schema": 3, "evidence_contract": 3,
             "brief": value["brief"], "language": language, "insights": insights, "research": research, "criteria": rubric,
             "contract_audit": {k: audit[k] for k in ("status", "attempts", "report", "response_id") if k in audit},
             "max_rounds": limit, "target_score": target, "generate_audio": audio, "watermark": watermark, "design_count": count, "select_max": picks,
             "contract_hash": ev.contract_hash(value["brief"], rubric, watermark, audio), "variants": variants, "selected": []}
    save(state)
    return state


def select(state, value):
    if state["status"] != "awaiting_selection":
        raise ValueError("Selection is only possible while awaiting the customer's choice")
    ids = value.get("selected") if isinstance(value, dict) else None
    ready = {v["id"] for v in state["variants"] if "design" in v}
    if not isinstance(ids, list) or not 1 <= len(ids) <= state["select_max"] or len(set(ids)) != len(ids) or any(x not in ready for x in ids):
        raise ValueError("Select 1-%d distinct variants that have a generated design" % state["select_max"])
    for v in state["variants"]:
        if v["id"] in ids:
            v.update(selected=True, status="running", rounds=[{"number": 1, "prompts": v["prompts"], "design": dict(v["design"], reused=True)}])
    state.update(selected=ids, phase="production", status="running")
    save(state)


def revise(state, value):
    need = [v for v in chosen(state) if v["status"] == "needs_revision"]
    if state["status"] != "needs_revision" or not need:
        raise ValueError("Revision not permitted")
    if not isinstance(value, dict) or set(value) != {v["id"] for v in need}:
        raise ValueError("Provide revised prompts for exactly these variants: " + ", ".join(v["id"] for v in need))
    rounds = []
    for v in need:
        item, last = value[v["id"]], v["rounds"][-1]
        if not isinstance(item, dict):
            raise ValueError("Each revision is an object with mockup and video prompts, plus design only when the artwork must change")
        fresh = prompts({k: item.get(k) or last["prompts"][k] for k in ("design", "mockup", "video")})
        if fresh == last["prompts"]:
            raise ValueError("Revision for %s changes nothing" % v["id"])
        entry = {"number": len(v["rounds"]) + 1, "prompts": fresh, "changes": item["changes"].strip() if ev.nonempty(item.get("changes")) else None}
        # The customer chose this artwork: keep it unless the revision rewrites the design prompt.
        if fresh["design"] == last["prompts"]["design"]:
            entry["design"] = dict(last["design"], reused=True)
            if fresh["mockup"] == last["prompts"]["mockup"]:
                entry["mockup"] = dict(last["mockup"], reused=True)
        rounds.append((v, entry))
    for v, entry in rounds:
        v["rounds"].append(entry)
        v["status"] = "running"
    state["status"] = "running"
    save(state)


def retry_silent(state, variant_id):
    v = next((x for x in chosen(state) if x["id"] == variant_id), None)
    if not v or v["status"] != "failed" or v.get("error_code") != AUDIO_REJECTION or v["rounds"][-1].get("silent_retry_used"):
        raise ValueError("Silent replacement is limited to one retry of a video rejected for its generated audio")
    r = v["rounds"][-1]
    r.update(silent_retry_used=True, generate_audio=False)
    r.pop("task", None)
    r.pop("submitted_at", None)
    v["status"] = "running"
    v.pop("error", None)
    v.pop("error_code", None)
    state["status"] = "running"
    save(state)


def manifest(state):
    shared = {k: state[k] for k in ("execution", "schema", "evidence_contract", "status", "language", "contract_hash", "max_rounds", "target_score",
                                    "generate_audio", "watermark", "design_count", "select_max")}
    if state["phase"] == "designs":
        if state["status"] not in ("awaiting_selection", "failed"):
            raise ValueError("Design exploration has not finished")
        fields = ("id", "title", "style", "rationale", "palette", "typography", "inspired_by", "prompts", "design", "error")
        return {**shared, "stage": "designs", "brief": state["brief"], "insights": state["insights"], "research": state["research"],
                "criteria": state["criteria"], "contract_audit": state["contract_audit"], "screening": state.get("screening", {"status": "unavailable"}),
                "variants": [{k: v[k] for k in fields if k in v} for v in state["variants"]], "error": state.get("error")}
    if state["status"] not in TERMINAL:
        raise ValueError("Loop has not finished")
    variants = []
    for v in chosen(state):
        if v["status"] not in TERMINAL or not 1 <= len(v["rounds"]) <= state["max_rounds"]:
            raise ValueError("Variant %s has not finished within the round limit" % v["id"])
        rounds = []
        for r in v["rounds"]:
            entry = {k: r[k] for k in ("number", "prompts", "changes", "design", "mockup", "video", "probe", "technical", "evaluation", "audit",
                                       "adjudication", "evidence", "failed_tasks", "video_retries", "generate_audio") if r.get(k) is not None}
            if "review" in r:
                if not all(r.get(p, {}).get("url") for p in ("design", "mockup", "video")) or not r.get("evidence", {}).get("response_id"):
                    raise ValueError("Completed assets and actual-media evidence are mandatory")
                if not r["evaluation"].get("response_id") or not r["audit"].get("response_id") or (r["audit"]["report"]["conflicts"] and not r.get("adjudication", {}).get("response_id")):
                    raise ValueError("Independent review provenance is missing")
                expected = ev.effective_review(state["criteria"], r["evaluation"]["report"], r["audit"]["report"], r.get("adjudication", {}).get("report"),
                                               ev.technical_checks(r.get("probe"), r.get("generate_audio", state["generate_audio"])), state["language"])
                if r["review"] != expected:
                    raise ValueError("Review differs from independent evaluation; cannot export")
                # Per-check detail already travels in the reviewer reports; the bridge rebuilds and verifies it.
                entry["review"] = {k: r["review"][k] for k in ("score", "quality_gate", "blocking_checks", "uncovered_requirements", "priority_fix", "review_source", "summary")}
            rounds.append(entry)
        best = selected_round(v)
        if (best["number"] if best else None) != v.get("best_round"):
            raise ValueError("Selected round does not match return policy")
        if v["status"] == "completed" and (best["review"]["quality_gate"] != "passed" or best["review"]["score"] < state["target_score"]):
            raise ValueError("Completed state does not satisfy evidence gate and target")
        variants.append({"id": v["id"], "status": v["status"], "best_round": v.get("best_round"), "error": v.get("error"), "rounds": rounds})
    if state["status"] == "completed" and not any(v["status"] == "completed" for v in variants):
        raise ValueError("Completed state requires an accepted variant")
    return {**shared, "stage": "final", "selected": state["selected"], "variants": variants,
            "return_policy": "required_pass_then_score_or_early_pass", "result_summary": result_summary(state)}


def export(state, part, chunk=None):
    size = chunk or EXPORT_CHUNK
    if not 1000 <= size <= 60000 and chunk:
        raise ValueError("chunk must be between 1000 and 60000 characters")
    text = json.dumps(manifest(state), ensure_ascii=False, separators=(",", ":"))
    if part is None and chunk is None and len(text) <= size:
        return json.loads(text)
    pieces = [text[i:i + size] for i in range(0, len(text), size)]
    digest = hashlib.sha256(text.encode()).hexdigest()
    option = " --chunk %d" % chunk if chunk else ""
    if part is None:
        return {"status": state["status"], "execution": "ma_cloud_skill", "export": "chunked", "stage": "designs" if state["phase"] == "designs" else "final",
                "parts": len(pieces), "sha256": digest,
                "next_action": "The manifest travels in parts. Run creative.py export%s --part N once for every N from 1 to %d, each as its own command, "
                               "then reply with exactly this JSON object. Do not paste or summarise the parts." % (option, len(pieces))}
    if not 1 <= part <= len(pieces):
        raise ValueError("Export has parts 1-%d" % len(pieces))
    return {"export_part": part, "of": len(pieces), "sha256": digest, "data": pieces[part - 1]}


def findings(state):
    rows = []
    for v in chosen(state):
        if v["status"] != "needs_revision":
            continue
        review = v["rounds"][-1]["review"]
        rows.append({"id": v["id"], "title": v["title"], "round": len(v["rounds"]), "rounds_left": state["max_rounds"] - len(v["rounds"]),
                     "score": review["score"], "priority_fix": review["priority_fix"], "blocking_checks": review["blocking_checks"],
                     "findings": [{k: c[k] for k in ("id", "status", "score", "asset_refs", "evidence", "improvement")}
                                  for c in review["checks"] if c["status"] != "pass" or c["score"] < state["target_score"]],
                     "technical": [t for t in review["technical_checks"] if t["status"] != "pass"]})
    return rows


def report(state, outcome, log):
    return {"status": outcome, "phase": state["phase"], "round": max([len(v.get("rounds", [])) for v in state["variants"]] + [0]) or 1,
            "log": log, "state_path": str(ROOT / "state.json"),
            "variants": [{k: v for k, v in (("id", x["id"]), ("status", x["status"]), ("round", len(x.get("rounds", [])) or None),
                                            ("score", (selected_round(x) or {}).get("review", {}).get("score")), ("error", x.get("error"))) if v is not None}
                         for x in (chosen(state) or state["variants"])],
            "revise": findings(state),
            "next_action": NEXT.get(outcome, "Run creative.py step again. Reviews run in independent model contexts; do not supply your own review.")}


def execute(command, value=None, variant=None, part=None, chunk=None):
    if command == "init":
        state = freeze(value)
        if state.get("status") == "contract_gaps":
            return state
        return report(state, "running", [])
    state = load()
    assert_contract(state)
    log = []
    outcome = None
    if command == "step":
        outcome, log = run(state)
    elif command == "review":
        raise ValueError("Manual review is disabled; run step for independent evaluation and audit")
    elif command == "select":
        select(state, value)
    elif command == "revise":
        revise(state, value)
    elif command == "retry-silent-video":
        retry_silent(state, variant)
    elif command == "export":
        return export(state, part, chunk)
    return report(state, outcome or state["status"], log)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["init", "step", "status", "review", "select", "revise", "export", "retry-silent-video"])
    parser.add_argument("--input")
    parser.add_argument("--variant")
    parser.add_argument("--part", type=int)
    parser.add_argument("--chunk", type=int)
    args = parser.parse_args()
    try:
        value = json.loads(Path(args.input).read_text()) if args.input else None
        print(json.dumps(execute(args.command, value, args.variant, args.part, args.chunk), ensure_ascii=False))
    except Exception as error:
        message = str(error).replace(os.environ.get("ARK_API_KEY", "__NO_KEY__"), "[redacted]")
        print(json.dumps({"status": "error", "error": message[:1000], "state_path": str(ROOT / "state.json")}))
        sys.exit(1)
