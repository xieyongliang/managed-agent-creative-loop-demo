"""A scripted stand-in for the cloud agent and the model APIs.

It drives the real helper (creative.py) exactly as the agent does and records the Session events such a run leaves
behind. Nothing is generated: designs, mockups and videos are the bundled sample files and reviewer answers come
from content.py. Used to build the sample campaign and to power rehearsal mode.
"""
import argparse
from datetime import date
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

root = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(root / "skills/pod-creative-loop/scripts"), str(Path(__file__).parent)]
os.environ.setdefault("ARK_API_KEY", "rehearsal-not-a-credential")
os.environ.update(STEP_BUDGET_SECONDS="0", POLL_SECONDS="0", POLL_INTERVAL="0")
import content  # noqa: E402
import creative as c  # noqa: E402

MEDIA = "/sample/media/"
FILES = root / "public/sample/media"
HELPER = "python3 /mnt/skills/pod-creative-loop/scripts/"
# Seconds a real run typically spends on each unit of work; rehearsal replays them faster.
PACE = {"design": 24, "screening": 18, "mockup": 26, "video_submit": 5, "video": 45, "evaluation": 28, "audit": 18, "adjudication": 22, "review": 1}


class Studio:
    """Answers the helper's model calls with bundled media and scripted reviews, keyed by design."""

    def __init__(self, memory):
        self.memory = memory
        self.memory.setdefault("count", {})
        self.memory.setdefault("polls", {})

    def count(self, key):
        self.memory["count"][key] = self.memory["count"].get(key, 0) + 1
        return self.memory["count"][key]

    def variant(self, url):
        return url.rsplit("/", 1)[1].split("-")[1].split(".")[0]

    def redrawn(self, prompt):
        return next((v for v, r in content.REVISIONS.items() if "design" in r and prompt.startswith(r["design"])), None)

    def __call__(self, path, body=None, stream=False):
        if path == "/images/generations":
            if "image" in body:
                v = self.variant(body["image"])
                return {"data": [{"url": "%smockup-%s-r%d.jpg" % (MEDIA, v, self.count("mockup-" + v))}]}
            v = self.redrawn(body["prompt"])
            if v:
                return {"data": [{"url": "%sdesign-%s-r2.png" % (MEDIA, v)}]}
            n = self.count("design")
            return {"data": [{"url": "%sdesign-v%d.%s" % (MEDIA, n, "jpg" if n == 1 else "png")}]}
        if path == "/contents/generations/tasks":
            v = self.variant(body["content"][1]["image_url"]["url"])
            # A kept mockup still gets a new video, so rounds are counted per design rather than read from the file name.
            return {"id": "cgt-video-%s-r%d" % (v, self.count("video-" + v))}
        if path.startswith("/contents/generations/tasks/"):
            task = path.rsplit("/", 1)[1]
            self.memory["polls"][task] = self.memory["polls"].get(task, 0) + 1
            if self.memory["polls"][task] < 2:
                return {"status": "running"}
            return {"status": "succeeded", "content": {"video_url": MEDIA + task[4:] + ".mp4"}}
        text = body["input"][0]["content"][0]["text"]
        if text.startswith("You are an independent requirements auditor"):
            answer = content.CONTRACT_AUDITS[min(self.count("contract"), len(content.CONTRACT_AUDITS)) - 1]
        elif text.startswith("You are an independent creative reviewer"):
            answer = content.SCREENING
        else:
            role = "audit" if "Evaluation to audit" in text else "adjudication" if "Disputed reports" in text else "evaluation"
            v = self.variant(body["input"][0]["content"][3]["video_url"])
            number = int(body["input"][0]["content"][3]["video_url"].rsplit("-r", 1)[1].split(".")[0])
            answer = content.REVIEWS[v][number - 1].get(role, content.AGREE)
        return {"id": "resp-rehearsal-%d" % self.count("response"), "output": [{"content": [{"type": "output_text", "text": json.dumps(answer, ensure_ascii=False)}]}]}


def probe(url):
    return c.media.inspect((FILES / url.rsplit("/", 1)[1]).read_bytes())


class Session:
    """Collects events with the time, in seconds from the start of the turn, at which each would appear."""

    def __init__(self):
        self.events, self.offset = [], 0

    def add(self, seconds, **event):
        self.offset += seconds
        self.events.append(dict(event, offset=self.offset))
        return len(self.events)

    def tool(self, seconds, name, value, **given):
        call = "call-%d" % self.add(2, type="agent.tool_use", name=name, input=given)
        self.events[-1]["id"] = call
        self.add(seconds, type="agent.tool_result", tool_use_id=call,
                 content=[{"type": "text", "text": "exit_code: 0\n--- stdout ---\n" + json.dumps(value, ensure_ascii=False) + "\n\n--- stderr ---\n"}])

    def helper(self, seconds, command, *args, **options):
        value = c.execute(command, *args, **options)
        took = sum(PACE.get(x["unit"], 5) for x in value.get("log", [])) or seconds
        text = "creative.py " + command + "".join(" --%s %s" % (k, v) for k, v in options.items())
        if args:
            text += " --input /mnt/session/%s.json" % {"init": "campaign-plan", "select": "selection", "revise": "revised-prompts"}[command]
        self.tool(took, "bash", value, command=HELPER + text)
        return value

    def export(self):
        index = self.helper(3, "export")
        for part in range(index.get("parts", 0)):
            self.helper(2, "export", part=part + 1)
        reply = {k: index[k] for k in ("export", "sha256") if k in index} or {"status": index["status"]}
        self.add(4, type="agent.message", content=[{"type": "text", "text": json.dumps(reply)}])
        self.add(1, type="session.status_idle")

    def until(self, *statuses):
        for _ in range(200):
            result = self.helper(40, "step")
            if result["status"] in statuses:
                return result
        raise RuntimeError("never reached " + "/".join(statuses))


def plan(brief, limits, criteria):
    return dict(limits, brief=brief, own_store=content.BRIEF["store"], insights=content.INSIGHTS, research=content.RESEARCH, criteria=criteria, variants=content.VARIANTS)


def explore(session, brief, limits, today):
    session.tool(2, "bash", {"market": "US", "occasions": len(c.rs.calendar(today))}, command=HELPER + "research.py calendar")
    fetched = [s for s in content.SOURCES if s["access"] == "fetched"]
    for i, query in enumerate(content.SEARCHES):
        session.tool(9, "web_search", {"results": 10}, query=query)
        if i < len(fetched):
            session.tool(12, "web_fetch", {"status": 200}, url=fetched[i]["url"])
    for store in content.STORES:
        session.tool(11, "bash", {"store": store, "status": "ok", "products_read": 60}, command=HELPER + "research.py storefront --store " + store)
    session.helper(14, "init", plan(brief, limits, content.FIRST_CRITERIA))
    session.helper(13, "init", plan(brief, limits, content.CRITERIA))
    session.until("awaiting_selection", "failed")
    session.export()


def produce(session, selection):
    session.helper(2, "select", {"selected": selection})
    while True:
        result = session.until("needs_revision", *c.TERMINAL)
        if result["status"] != "needs_revision":
            break
        session.helper(6, "revise", {v["id"]: content.REVISIONS[v["id"]] for v in result["revise"]})
    session.export()


def run(phase, workdir, given, today=None):
    """Play one phase against the helper state kept in workdir and return its events."""
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    notes = workdir / "studio.json"
    memory = json.loads(notes.read_text()) if notes.exists() else {}
    day = date.fromisoformat(today) if today else date.today()
    calendar = c.rs.calendar
    session = Session()
    with patch.object(c, "ROOT", workdir / "loop"), patch.object(c, "api", Studio(memory)), patch.object(c.media, "probe", probe), \
            patch.object(c.rs, "calendar", lambda when, days=150: calendar(day, days)):
        if phase == "explore":
            explore(session, given["brief"], given["limits"], day)
        else:
            produce(session, given["selection"])
    notes.write_text(json.dumps(memory))
    return session.events


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["explore", "produce"])
    parser.add_argument("--workdir", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--today")
    args = parser.parse_args()
    print(json.dumps({"events": run(args.phase, args.workdir, json.loads(Path(args.input).read_text()), args.today)}, ensure_ascii=False))
