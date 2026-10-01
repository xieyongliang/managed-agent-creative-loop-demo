# Sample media

Every file in `public/sample/media/` is a stand-in for the sample campaign and rehearsal mode. Nothing here was generated for the sample by a paid model call.

| File | How it was made |
| --- | --- |
| `design-v1.jpg`, `mockup-v1-r1.jpg` | Seedream output of the 28 September cloud run (`docs/assets/retest-20260928/round-2-*`), resized |
| `mockup-v2-r1.jpg` | Seedream output of the same run (`round-1-mockup.jpg`), resized |
| `video-v1-r1.mp4`, `video-v2-r1.mp4` | Seedance output of the same run, with a synthesized sound track added |
| `design-v2.png` to `design-v5.png`, `design-v5-r2.png` | Drawn as SVG by `designs.py`, rendered with QuickLook |
| other `mockup-*.jpg` | `mockup.py` removes the print from the run's mug photo and places a drawn design on the mug |
| other `video-*.mp4` | `kenburns.swift` renders a slow camera move over a mockup; `mux.swift` adds sound |
| `video-v3-r1.mp4` | Deliberately silent, so the sample shows how a missing sound track is caught |
| `poster-*.jpg` | One frame of each video, saved by `poster.swift` |
| sound tracks | Tones synthesized by `audio.py`; nothing is sampled |

The scripts need macOS (`sips`, `qlmanage`, `afconvert`, Swift with AVFoundation) and `numpy`. They are kept for reference; running the app does not need them.
