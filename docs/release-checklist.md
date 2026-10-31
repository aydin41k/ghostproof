# Release gates and verification

## Later live local feature checks

The separate `local/` application is a later change than the historical 30 October delivery below. The source allowlist now names 45 files, including the new local runtime/UI and offline tests. The public site remains exactly its five original assets; static content and historical reference hashes remain pinned. No model weights, runtime retrievals/responses or private records are packaged, and no remote DEV draft is modified.

Validation includes source/model rejection and evidence-contract tests, five distinct synthetic discovered sources across continuation/new hunt, server-owned choosing/grade projections, late-completion isolation, one active pipeline, real ephemeral loopback Host/Origin/token/framing/routing checks, actual local client rendering/polling/recovery and deterministic extracted-package smoke. CI requires no Ollama or NASA access; these synthetic tests are not evidence of real-model semantic accuracy. Root's real-model/browser QA and the same Astra planner's independent approval are additional delivery gates, not replaced by the tests or this document. The live contract uses an exact source statement and model-selected single-value substitution plus a separate blinded same-model automated check; it remains fallible and source-specific.

On 31 October 2026, root played five accepted rounds using the installed local `gemma4-e4b-local:latest` model, the explicit raw Gemma adapter, live NASA retrieval and the actual loopback browser UI. Four consecutive rounds reached 4/4, demonstrating continuation beyond three; New hunt reset the score to 0/0 and a fifth distinct source reached 1/1. All five completed without a manual Retry. Root checked the claims against their displayed source evidence, including these source IDs and mutations: Cat's Eye Nebula `1203573` (distance), Aurorae on a Brown Dwarf `892395` (polarity), Pelican Nebula `1295149` ("is slowly being transformed" to "is not slowly being transformed"), Bubble Nebula `1259991` (diameter 10 to 30 light-years), and Great Lacerta Nebula `1248684` (distance 1200 to 3600 light-years). The fifth source was retrieved at `2026-10-31T11:31:57Z` and its round generated at `2026-10-31T11:32:01Z`. This is a five-sample live check, not a guarantee of future generation accuracy or continuous availability.

That five-round runtime already enforced three distinct source sentence IDs and bounded automatic second-query recovery. The subsequent final source revision additionally rejects embedded/reporting polarity substitutions, requires exactly one finite copula for a polarity toggle, and rejects Boötes/Bootes spelling-alias substitutions. Offline validation of that narrower revision passes 58 Node tests and 51 Python tests, including rejection before a permissive model reviewer. The extracted child skips only recursive extraction. A restarted final-runtime smoke and the same Astra planner's independent approval remain required; the five-round record does not claim those later guards were running during that sample. No live retrieval/model-response records or new screenshots are included in the source package.

## Historical release evidence

This document distinguishes local preparation, verified public delivery, and the still-unpublished DEV submission. Last checked: 30 October 2026, Australia/Sydney. It is not the independent planner's approval record.

Historical preparation status: the independent Astra planner approved the initial local release, which was pushed to [aydin41k/ghostproof](https://github.com/aydin41k/ghostproof) as commit `3024470de084122d73fe2bb4989d0281c059e1aa` while the repository was **private** and Actions were **disabled**. After the owner authorized public visibility, MIT for original code/art, and free GitHub Pages/standard public Actions, the same planner approved the public-release source revision. Root verified the exact 36-file tree, committed and pushed `433ea2542f459e4a407788d99cbb72d3f1420996`, then verified public visibility before enabling Actions. The public repository and [live demo](https://aydin41k.github.io/ghostproof/) are anonymously accessible. The DEV article remains unpublished. Evidence-only documentation revisions follow the same independent-review-before-push process.

## Local release checks

- Exact accepted public export: three topics/nine claims, no new source/model requests; content SHA-256 pinned in browser and release validator.
- State tests: all eight outcome sequences, locking/idempotence, stale/cross-round IDs, shuffle, next/replay and score formula `3 + answered - 2 * score`.
- Actual client tests: correct and wrong sprite outcomes, full fake/correction pairing in visible feedback and live status, exact quote/context, locked controls, replay, delayed-loading isolation and recovery.
- Content tests: missing/corrupt/oversized data, schema/types/topic/source/scene/category restrictions, invalid dates, malformed evidence, unsafe text/URLs and checksum drift.
- Publishing boundary tests: exact five-file site, explicit 36-file source ZIP allowlist including the full MIT licence, carried scoped HTML notice/link, required package licence/private metadata, symlinks/path escape rejected, secret/private-path scanning, fixed historical reference hashes, deterministic fresh-extraction test/build/repack.
- [Earlier local browser QA and subsequent hosted checks](browser-qa.md): desktop perfect hunt and 320px reduced-motion mixed replay, both sprite feedback paths, keyboard/focus, source trail, no horizontal overflow, 16px claim text, empty captured page warning/error logs, only initial content load and no replay requests. The four packaged screenshots remain earlier app-only local evidence, not hosted screenshots or exhaustive security/accessibility coverage.
- Original prototype and all historical/private records are outside the release. Root's original 82-test suite passed; the 39 historical and 16 final preservation inventories are checked separately before and after implementation. The original preview and user-owned model service are not replaced by this package.

Re-run the README commands before handing off. `dist/source-manifest.sha256` enumerates exact packaged source files; the ZIP checksum belongs to that particular build and changes when documentation/screenshots change. Generated `site/` and `dist/` are ignored by Git; they are rebuilt by the package tools.

## CI and hosting facts

Official action tags were resolved read-only from their official Git repositories on 30 October 2026:

| Action | Verified tag | Full commit pin |
| --- | --- | --- |
| actions/checkout | v4.2.2 | `11bd71901bbe5b1630ceea73d27597364c9af683` |
| actions/setup-node | v4.4.0 | `49933ea5288caeca8642d1e84afbd3f7d6820020` |
| actions/setup-python | v5.6.0 | `a26af69be951a213d495a4c3e4e4022e16d87065` |
| actions/configure-pages | v5.0.0 | `983d7736d9b0ae728b81ab479565c72886d7745b` |
| actions/upload-pages-artifact | v3.0.1 | `56afc609e74202658d3ffba0e8f6dda462b719fa` |
| actions/deploy-pages | v4.0.5 | `d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e` |

CI uses read-only repository permissions, no secrets, no privileged PR trigger, no dependency install and no model/source downloads. It still validates, builds, packages and rehearses extraction, but no longer uploads an optional retained source artifact. Standard runner/actions setup can acquire the declared language runtimes; “no downloads” is not a promise that hosted runner setup never transfers bytes. Standard public-runner compute and Pages are the confirmed free route, not a guarantee that arbitrary artifacts or account-wide usage are free. The [hosted CI run](https://github.com/aydin41k/ghostproof/actions/runs/41054856320) succeeded for `433ea2542f459e4a407788d99cbb72d3f1420996` on 30 October 2026 (created 12:22:32 UTC; final update 12:23:08 UTC). Logs show 53 passing Node tests and 17 passing Python tests, with only recursive extraction skipped in the extracted child suite. Validation covered 36 source files. This is demonstrated Actions use, not guaranteed prize eligibility or a Copilot-generation claim.

Root verified Actions were restricted to selected GitHub-owned actions, with verified-third-party actions disabled and no extra allowed patterns; default workflow tokens were read-only and PR approval was disabled. Successful runs included non-blocking notices about the pinned actions' Node 20 metadata being forced onto Node 24 and an `ubuntu-latest` image migration. These are not zero-warning CI claims; updating action pins is outside this evidence-only revision.

[Render static-site docs](https://render.com/docs/static-sites) and [Blueprint specification](https://render.com/docs/blueprint-spec) were checked read-only. The blueprint uses `type: web`, `runtime: static`, `staticPublishPath: ./site`, and `autoDeployTrigger: 'off'`; it has no dynamic runtime, secret, paid plan or account creation. Its headers permit the game's inline style properties while constraining scripts and connections to same origin. Connecting a repository may create a service/initial deployment despite auto-deploy being off, so do not apply the blueprint without owner authorization. Verify current free limits and payment/overage controls in the chosen account. Prepared configuration is not deployment or settled Render eligibility.

The Pages workflow remains **manual-only**. Its [hosted build and deployment](https://github.com/aydin41k/ghostproof/actions/runs/41055015797) succeeded for the same application commit on 30 October 2026 (created 12:23:49 UTC; final update 12:24:29 UTC). The [official custom-workflow guide](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages) informed the separate build/deploy jobs, deploy `needs: build`, `github-pages` environment, and `pages: write`/`id-token: write` only on deployment. The required uploaded artifact is only `site/`, with one-day retention. The Pages API returned the canonical [HTTPS demo URL](https://aydin41k.github.io/ghostproof/), workflow build type, public visibility and enforced HTTPS. Its status field was null; successful run results and live HTTP/browser checks establish delivery. Pages does not apply the optional Render blueprint's headers. No tunnel or connection to the builder's laptop is needed.

Anonymous HTTPS checks fetched all five assets with HTTP 200 and bytes identical to the reviewed build. Requests beneath the Pages project path for `.env`, `data/private.json`, `reference/local-preparation/server.py`, and `api/start` returned HTTP 404. Source is intentionally public in GitHub, but is not in the Pages artifact. The [deployed browser record](browser-qa.md#public-github-pages-verification--30-october-2026) records actual desktop 3/3 and reduced-motion mobile 2/3 hunts. Later documentation-only commits do not alter the five deployed assets or retroactively become the deployed application commit.

## Completed delivery and remaining gates

1. Completed: independent source approval, exact Git-tree/history/destination review, approved commit and push while Actions were disabled, then public visibility and anonymous access verified before Actions were enabled.
2. Completed: successful hosted CI and manually dispatched Pages for the recorded application commit; canonical HTTPS URL, five asset bytes, excluded routes and actual desktop/320px gameplay verified.
3. Ongoing release rule: the same planner reviews evidence-only documentation revisions before root commits/pushes them and verifies each new CI run. Corrections return to the same executor/planner loop. Generated output and private records must remain untracked; no history rewrite.
4. Keep the existing DEV article unpublished. Update it only from reviewed, pushed documentation and retain the accurate AI disclosure. Publishing requires explicit owner permission. Do not export a conversation or manufacture Entire evidence.
5. The original-code/art MIT grant is operative; third-party rights and personal eligibility remain the owner's responsibility. No paid resources or account-wide billing changes are authorized; Render, sponsor redemption, domain obligations and voice generation remain outside this route.

## Submission timing and personal checks

Required tags: `devchallenge`, `hf26challenge`. Template: What I Built; Demo; Code; How I Built It; Why Does Open Innovation Matter?; optional The Spirit of It; Prize Categories. My Agent Session is omitted because no transcript sharing is authorized.

The formal cutoff is **31 October 2026, 23:59 PDT = 1 November, 17:59 Sydney**. Event API `ends_at` is **31 October, 06:59 UTC = 31 October, 17:59 Sydney**, one day earlier. Use the earlier time as an operational buffer; no organizer clarification is claimed. Sources: [challenge](https://dev.to/challenges/hacktoberfest-week4-2026-10-26), [rules](https://dev.to/page/hacktoberfest-week4-2026-10-26-contest-rules), [categories](https://dev.to/challenges/hf26).

The owner must confirm age/country/rights eligibility, new work within the challenge window, and any personal assertions. One entry/one win. The owner selected MIT for original code/art; that does not establish third-party rights or category eligibility. Writing carries the most weight; a genuine walkthrough and clear explanation are more useful than unverified last-minute integrations.
