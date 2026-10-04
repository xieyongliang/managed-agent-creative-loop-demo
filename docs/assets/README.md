# Documentation Asset Inventory

## Walkthrough

`walkthrough/walkthrough.mp4` is a screen recording of the app, compressed to 1280x696 for the repository. `walkthrough/poster.jpg` is one frame of it.

## September 28 Cloud Run

These files come from a real cloud run of the earlier, single-design version of this demo. Round 1 scored 3.333333/5 and failed the required checks. After prompt revision, round 2 scored 5/5 and passed all eight required checks.

| Files | Source / role |
| --- | --- |
| `retest-20260928/round-1-design.jpg`, `round-2-design.jpg` | Original Seedream output |
| `retest-20260928/round-1-mockup.jpg`, `round-2-mockup.jpg` | Original Seedream output |
| `retest-20260928/round-1-video.mp4`, `round-2-video.mp4` | Original Seedance output, generated without sound |
| `retest-20260928/round-2-video-poster.jpg` | First frame extracted from the round 2 video |
| `retest-20260928/result.json` | Sanitized run export with prompts, criteria, reports, file sizes and SHA-256 checksums |

Both videos were independently probed: 720x1280, 5.041667 seconds, no audio stream. Scores are model judgments, not printing, rights, or publication approval.

The current sample campaign reuses some of these files. `tools/sample/media/README.md` says which, and how the other sample media were made. The helper's MP4 inspection is tested against `round-2-video.mp4`.

Do not add raw Campaign JSON, credentials, Session IDs, or signed URLs here. Reviewed customer briefs and evaluation text still need appropriate sharing permission.
