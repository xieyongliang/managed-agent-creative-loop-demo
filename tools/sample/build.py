"""Prints the Session events of the bundled sample campaign: both phases, with the sample's own design choice."""
from datetime import datetime, timedelta, timezone
import json
import tempfile

import studio
from studio import content

TODAY = "2026-09-30"


def stamped(events, start):
    return [dict({k: v for k, v in e.items() if k != "offset"}, created_at=(start + timedelta(seconds=e["offset"])).isoformat().replace("+00:00", "Z")) for e in events]


with tempfile.TemporaryDirectory() as tmp:
    opened = datetime(2026, 9, 30, 2, 5, tzinfo=timezone.utc)
    first = studio.run("explore", tmp, {"brief": content.BRIEF["brief"], "limits": content.LIMITS}, TODAY)
    chosen = opened + timedelta(seconds=first[-1]["offset"], minutes=6)
    second = studio.run("produce", tmp, {"selection": content.SELECTION}, TODAY)
print(json.dumps({"brief": content.BRIEF, "limits": content.LIMITS, "selection": content.SELECTION,
                  "explore": stamped(first, opened), "produce": stamped(second, chosen)}, ensure_ascii=False))
