# POD Creative Studio

A demo for print-on-demand gift businesses. A customer writes one brief; a Managed Agent (MA) in the cloud studies the market, designs five directions in different styles, and turns the customer's favourites into product mockups and short videos with sound. Independent reviewers score every result against the brief, and the agent revises what did not pass.

The interface is in English. Everything the agent writes (research, rationales, review findings) is delivered in the campaign's report language, Vietnamese by default.

```text
Browser -> local bridge -> MA Cloud Session
                            |
   PHASE 1  Explore         +-- read the brief: market, buyer, occasion
                            +-- research: marketplaces, competitor stores, social video, gifting calendar
                            +-- acceptance criteria, checked by an independent auditor, then frozen
                            +-- five design variants in different styles -> Seedream
                            +-- independent reviewer ranks the five designs
                            v
   the customer chooses up to three designs in the browser
                            |
   PHASE 2  Produce         +-- per chosen design: mockup (Seedream), 5 s 9:16 video with sound (Seedance)
                            +-- helper inspects each video file: sound track, length, frame
                            +-- independent evaluation -> audit -> adjudication on conflict
                            +-- agent revises what failed, up to the round limit
                            +-- verified result for every design, best one marked
```

The local bridge only creates the Session, sends the brief and the customer's choice, observes events and renders the verified result. It never calls a generation or evaluation API.

## Try it without the cloud

Requires Node 22+ and Python 3.

```bash
npm ci
npm run rehearse
```

Open [the workspace](http://127.0.0.1:8790). Rehearsal mode replaces the cloud with a scripted agent that drives the real helper scripts and the real bridge, using bundled sample media. A whole campaign takes about two minutes, calls no model and costs nothing. Use it to learn the flow, to rehearse a presentation, or as a fallback when the network is poor.

Without rehearsal mode and without cloud IDs, the app still opens and **Explore the sample** shows one finished campaign.

Set another port with `PORT=8795 npm run rehearse` if 8790 is taken.

## What a campaign contains

### Market research

The agent works through five channels and reports honestly what each one gave it.

| Channel | How it is read | What it yields |
| --- | --- | --- |
| Amazon | Category Best Sellers and New Releases pages | Ranked titles, prices, rating counts |
| Etsy | Trend reports and news; search pages refuse automated reads | Named trends, price bands |
| Competitor stores | `research.py storefront` reads the public catalog feed of Shopify stores | Merchant best-seller collection, newest launches, title keywords, prices, share of personalized products |
| TikTok | Official creative guidance and current coverage | Formats, hooks, sound use |
| Seasonal trends | `research.py calendar` plus seasonal spending reports | Upcoming US occasions, selling windows, spending figures |

Rules the helper enforces before anything is generated:

- Every source is recorded with URL, channel, retrieval date and how it was read: page read, search result only, or catalog feed.
- Every source links to a page a person can open, never a JSON data feed.
- Every competitor design, keyword, opportunity and seasonal focus cites recorded sources, or is marked as a hypothesis.
- The customer's own store (the optional **Your store** field) may be studied for style but is never listed as a competitor.
- A channel counts as covered only if it has a recorded source. Blocked channels are reported as limited or unavailable.
- Fewer than 8 sources or 3 channels means the study is labelled limited, with the reason.
- Numbers appear only as the source states them. Ranks and catalog positions are never converted into sales.

The agent does not work around login walls, CAPTCHAs, rate limits or `robots.txt`. `research.py storefront` checks `robots.txt`, identifies itself, reads at most five pages per store and never reads sorted collection URLs, which Shopify disallows. For deeper data in production, connect official sources with the customer's own credentials, for example the Etsy Open API v3, which needs an API key. Amazon, TikTok and Google Trends restrict programmatic access; check each provider's current API terms before relying on them.

The gifting calendar is computed by the helper, not recalled by a model. Its planning windows (list by, ads from, order cutoff) are rules of thumb; print providers publish real cutoffs each season.

### Design exploration and the customer's choice

The agent proposes five variants (configurable, 3 to 6), each in a visibly different style with a rationale, palette, typography and the sources that inspired it. An independent reviewer that sees only the images ranks them and checks the spelling of the printed text. The customer then chooses up to three (configurable, 1 to 3) in order of preference. Only chosen designs cost further generation.

Designs appear in the browser one by one while the agent is still working, marked as previews.

### Production

Each chosen design gets a mockup that uses the design as reference and a 5-second 9:16 video that uses the mockup as reference. Videos are requested with `generate_audio: true` unless the customer switches sound off. A revision keeps the customer's chosen artwork unless a failed check points at the artwork itself.

After each video is rendered, the helper downloads the file and reads its container: whether an audio track exists, its length and its frame size. These measured facts are given to the reviewers and also act as checks of their own, so a silent video cannot be accepted when sound was requested.

### Evaluation and iteration

The agent derives acceptance criteria from the brief before generation. An independent auditor compares them with the brief; gaps go back to the agent up to twice before the criteria are frozen. Reviewers then inspect the actual media in separate model contexts that never see the agent's reasoning: evaluation, then audit, then adjudication when the audit finds a conflict. These are model API calls inside MA Cloud, not separate Sessions.

The helper computes the weighted score `sum(score x weight) / sum(weight)`. A design is accepted only when every required check passes, every measured check passes and the score reaches the target. Optional preferences affect the score but never block. An unverified required check blocks. The reviewer models cannot listen yet, so the agent writes no criteria about how the audio sounds; only the presence of a sound track is checked. Connect an audio-capable review model to add them.

Defaults: up to 2 rounds per design, target 4.5 / 5. Both are editable when creating a campaign; the maximum is 5 rounds. A design stops as soon as it passes. At the round limit the helper keeps the highest-scoring round that passed the required checks, otherwise the highest-scoring round; ties keep the earlier round. The top result is the accepted design with the highest score.

One failed design never stops the others. Model acceptance is not rights clearance, print approval or platform approval, and nothing is published automatically.

## Run live

Requires authenticated BytePlus ArkCLI. Live runs incur model, MA runtime and search charges.

```bash
npm ci
cp .env.example .env
# Set CLOUD_AGENT_ID, CLOUD_ENVIRONMENT_ID and ENABLE_PAID_RUNS=true.
npm start
```

Create a campaign and press **Start research & designs**. Expect 8 to 15 minutes for phase 1 and 10 to 20 minutes for phase 2, depending on the models and the number of revisions. Keep the app running to collect results. If the local observer stops, **Resume watching** re-attaches to the same Session without sending anything again.

Temporary signed media URLs expire. Archive a finished campaign while they are valid:

```bash
node archive-campaign.mjs <CAMPAIGN_ID> <ARCHIVE_NAME>
```

Set `STUDIO_NAME` and `WORKSPACE_NAME` in `.env` to show a customer's own name in the interface.

## Deploy

1. Authenticate with `arkcli auth login`; check `arkcli auth status --format json`.
2. Create a dedicated Cloud Environment. `deploy-environment.mjs` reads the key from its process environment, creates a private temporary config, withholds credential-bearing output and removes the temporary file. `IMAGE_MODEL`, `VIDEO_MODEL` and `EVAL_MODEL` are passed through when set.

   ```bash
   read -r -s -p 'BytePlus demo API key: ' ARK_API_KEY && export ARK_API_KEY
   node deploy-environment.mjs
   unset ARK_API_KEY
   ```

3. List the models your account can use with `arkcli agent model list --format json`, then package the Skill, upload it and create the Agent:

   ```bash
   node deploy-agent.mjs <MA_MODEL_ID>
   ```

   This script has been checked with `--dry-run` previews but not yet run against a live account. If it cannot read an ID from a response, it prints the response and stops; continue by hand as below.

   To do it by hand: zip `skills/pod-creative-loop/` with its `SKILL.md`, `scripts/` and `references/`, upload it with `arkcli agent skill create --zip <ZIP> --display-title 'POD Creative Loop' --format json`, and create the Agent with `cloud-system.md` as system prompt, the returned Skill ID and version, and the default tools.
4. Put the Agent and Environment IDs into `.env`. Enable paid execution only with authorization.

Research and planning are demanding. Choose the most capable MA model available to the account for the Agent. Existing Sessions keep the Skill version they started with; start a new campaign after deploying an update.

`config.env` is NOT a secret vault: configuration readers and code in the Agent environment can access its values. Use a scoped test key, restricted access and an approved secret design before production. Never put keys into a Skill ZIP, prompt, source code or screenshot.

Default models: `seedream-4-5-251128` for images, `dreamina-seedance-2-5-260628` for video, `seed-2-0-lite-260428` for reviewers. Availability is account-specific.

## Helper and recovery

`skills/pod-creative-loop/scripts/` uses only Python's standard library.

| Script | Commands |
| --- | --- |
| `creative.py` | `init --input plan.json`, `step`, `select --input selection.json`, `revise --input prompts.json`, `status`, `export [--part N] [--chunk SIZE]`, `retry-silent-video --variant ID` |
| `research.py` | `calendar`, `storefront --store DOMAIN`, `validate --input research.json` |
| `evaluation.py`, `media.py` | Acceptance contract and reviewer prompts; MP4 inspection |

State persists at `/mnt/session/creative-loop/state.json`.

- Generation requests are never blindly repeated. A refused request fails that design with the provider's code. A request with an unknown outcome is marked and not resubmitted, to avoid duplicate charges. Rate-limited requests are repeated because the provider refused them.
- A video task that fails with a known transient error is replaced at most twice per round, reusing the images. Policy and unknown errors stop that design. A video rejected for its generated audio can be replaced by a silent one only with `retry-silent-video`, when the customer authorizes it.
- Video polling reuses the task ID and stops after 30 minutes; it does not cancel the provider task.
- Responses SSE requires an explicit `response.completed` event. Each screening, evaluation, audit or adjudication permits at most two attempts. A failed design ranking degrades to "ranking unavailable"; a failed review fails that design.
- State is HMAC-signed to detect accidental direct edits. This is a consistency check, not a security boundary against code with access to the same key. The bridge also rejects runs in which the agent wrote to protected state or Skill files.
- Large results travel in checksummed parts. The bridge accepts only output printed by `creative.py export`, reassembles and verifies it, rebuilds every review from the reviewers' own reports and refuses a result that disagrees. If the agent stops early, the bridge reminds it up to three times, then reports an error.
- The interface is localhost-only, without production authentication or multi-tenant isolation.

## Verify

```bash
npm test
```

This runs 43 Node.js tests and 78 Python tests. They use stand-ins rather than paid model calls, and include a walk through a whole campaign over the real HTTP interface and a run of the helper's command line against a local stand-in for the model API.

**Not yet verified in the cloud.** This version changes the Skill, the helper and the bridge substantially. Every path is covered by local tests and by rehearsal mode, but no paid MA Cloud run of this version has been made. Treat the first live run as a test: watch the Session, and expect to adjust the Skill wording to the MA model you deploy.

## The sample and rehearsal content

- The 14 market sources are real pages read on 30 September 2026: Amazon in a browser, four competitor stores through their public catalogs, the rest as web pages or search results. The sample is set up for a Macorner demo, so Macorner is the customer's store and not a competitor.
- The design of variant 1, its mockup and two of the videos come from an earlier real run of this demo. The other designs are drawn artwork, the other mockups are composites on that run's mug photo, and the other videos are slow camera moves over those mockups. Sound tracks are synthesized tones.
- Reviewer comments, scores and rationales are written examples.

`tools/sample/` holds the content and the scripts that produced the media. `npm run sample` rebuilds `public/sample/campaign.json` through the real helper and bridge.

## Security and distribution

Private credentials, raw run data and signed URLs are excluded from Git. Never commit `.env`, `data/`, authentication caches, or complete Environment configurations. Campaign exports may contain private briefs and signed media URLs; review them before sharing. Competitor names and listings in a research report are public information, but check them before showing a report to a third party. This repository is a demo, not a production security or compliance solution.

## Layout

```text
server.mjs, cloud.mjs, core.mjs     local bridge and its validation
public/                             interface; public/sample/ holds the sample campaign and media
cloud-system.md                     system prompt of the Managed Agent
skills/pod-creative-loop/           Skill: SKILL.md, scripts/, references/pod-playbook.md
deploy-environment.mjs, deploy-agent.mjs, archive-campaign.mjs
tools/rehearsal/                    stand-in for ArkCLI used by rehearsal mode
tools/sample/                       sample content, scripted agent, media scripts
test.mjs, test-server.mjs, test-cloud.py, test-e2e.py, test-fixtures.py
```
