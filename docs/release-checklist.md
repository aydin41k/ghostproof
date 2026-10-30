# Release gates and verification

This document distinguishes a locally tested package from external publication. Last prepared: 30 October 2026, Australia/Sydney. It is not the independent planner's approval record.

Historical preparation status: the independent Astra planner approved the initial local release, which was pushed to [aydin41k/ghostproof](https://github.com/aydin41k/ghostproof) as commit `3024470de084122d73fe2bb4989d0281c059e1aa` while the repository was **private** and Actions were **disabled**. The owner has now authorized public visibility, MIT for original code/art, and free GitHub Pages/standard public Actions. This public-release revision requires a fresh independent approval before external changes. Public access, hosted CI, and deployment remain pending verification; no live demo is claimed.

## Local release checks

- Exact accepted public export: three topics/nine claims, no new source/model requests; content SHA-256 pinned in browser and release validator.
- State tests: all eight outcome sequences, locking/idempotence, stale/cross-round IDs, shuffle, next/replay and score formula `3 + answered - 2 * score`.
- Actual client tests: correct and wrong sprite outcomes, full fake/correction pairing in visible feedback and live status, exact quote/context, locked controls, replay, delayed-loading isolation and recovery.
- Content tests: missing/corrupt/oversized data, schema/types/topic/source/scene/category restrictions, invalid dates, malformed evidence, unsafe text/URLs and checksum drift.
- Publishing boundary tests: exact five-file site, explicit 36-file source ZIP allowlist including the full MIT licence, carried scoped HTML notice/link, required package licence/private metadata, symlinks/path escape rejected, secret/private-path scanning, fixed historical reference hashes, deterministic fresh-extraction test/build/repack.
- [Root's fresh static browser QA](browser-qa.md): desktop perfect hunt and 320px reduced-motion mixed replay, both sprite feedback paths, keyboard/focus, source trail, no horizontal overflow, 16px claim text, empty captured warning/error logs, only initial content load and no replay requests. Screenshots are app-only, not proof of a deployment or exhaustive security/accessibility coverage.
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

CI uses read-only repository permissions, no secrets, no privileged PR trigger, no dependency install and no model/source downloads. It still validates, builds, packages and rehearses extraction, but no longer uploads an optional retained source artifact. Standard runner/actions setup can acquire the declared language runtimes; “no downloads” is not a promise that hosted runner setup never transfers bytes. Standard public-runner compute and Pages are the confirmed free route, not a guarantee that arbitrary artifacts or account-wide usage are free. The workflow has not run remotely. Root must verify public visibility before enabling Actions. A workflow file alone is not a successful GitHub Actions category demonstration.

[Render static-site docs](https://render.com/docs/static-sites) and [Blueprint specification](https://render.com/docs/blueprint-spec) were checked read-only. The blueprint uses `type: web`, `runtime: static`, `staticPublishPath: ./site`, and `autoDeployTrigger: 'off'`; it has no dynamic runtime, secret, paid plan or account creation. Its headers permit the game's inline style properties while constraining scripts and connections to same origin. Connecting a repository may create a service/initial deployment despite auto-deploy being off, so do not apply the blueprint without owner authorization. Verify current free limits and payment/overage controls in the chosen account. Prepared configuration is not deployment or settled Render eligibility.

The Pages workflow is **manual-only** and has not run. The [official custom-workflow guide](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages) was checked: separate build/deploy jobs, deploy `needs: build`, `github-pages` environment, and `pages: write`/`id-token: write` only on deployment. The required uploaded artifact is only `site/`, with one-day retention. The owner authorized this free public route. After independent approval and verified public visibility, root selects GitHub Actions in repository Pages settings and explicitly dispatches “Manually deploy static demo to Pages.” The workflow is not proof of a successful deployment. Pages does not apply the optional Render blueprint's headers. No tunnel or connection to the builder's laptop is needed.

## Root-only external gates

1. Obtain the same independent Astra planner's explicit `APPROVED` verdict for this public-release snapshot. Corrections return to the executor and then the planner; the historical approval is not approval of these changes.
2. Verify the exact 36-file Git tree, index, reachable history and destination, then commit and push only the reviewed release while Actions are still disabled. Generated output and private records must not be tracked. Do not initialize Git at the broader workspace root or rewrite history.
3. Set and verify public visibility and anonymous code access before enabling Actions. The original-code/art MIT grant is operative; third-party rights and personal eligibility remain the owner's responsibility, not automatically cleared by public authorization.
4. Enable standard public Actions, capture a real successful CI run and commit, then configure and manually dispatch Pages. Verify its canonical HTTPS URL, deployed commit, five asset bytes, excluded routes and actual desktop/320px browser play. No paid resources or account-wide billing changes are authorized; Render, sponsor redemption, domain obligations and voice generation remain outside this route.
5. Return measured hosted evidence to the executor and planner for a reviewed documentation update. Keep the existing DEV article unpublished, update it only after approval and verified push, and retain the accurate AI disclosure. Publishing requires explicit owner permission. Do not export a conversation or manufacture Entire evidence.

## Submission timing and personal checks

Required tags: `devchallenge`, `hf26challenge`. Template: What I Built; Demo; Code; How I Built It; Why Does Open Innovation Matter?; optional The Spirit of It; Prize Categories. My Agent Session is omitted because no transcript sharing is authorized.

The formal cutoff is **31 October 2026, 23:59 PDT = 1 November, 17:59 Sydney**. Event API `ends_at` is **31 October, 06:59 UTC = 31 October, 17:59 Sydney**, one day earlier. Use the earlier time as an operational buffer; no organizer clarification is claimed. Sources: [challenge](https://dev.to/challenges/hacktoberfest-week4-2026-10-26), [rules](https://dev.to/page/hacktoberfest-week4-2026-10-26-contest-rules), [categories](https://dev.to/challenges/hf26).

The owner must confirm age/country/rights eligibility, new work within the challenge window, and any personal assertions. One entry/one win. The owner selected MIT for original code/art; that does not establish third-party rights or category eligibility. Writing carries the most weight; a genuine walkthrough and clear explanation are more useful than unverified last-minute integrations.
