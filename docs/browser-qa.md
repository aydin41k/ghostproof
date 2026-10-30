# Static release browser smoke test

Earlier local tests, 30 October 2026, by the root assistant in the Codex in-app browser. These are actual UI interactions with the packaged static site, not the original Python game server and not a claim of exhaustive accessibility/security testing. The later public deployment checks are recorded separately below.

## Desktop: 1280 × 720

- Started from the introduction and completed all three rooms: sprites, NASA UAP study, St Paul's ghost stories.
- Chose the fabricated claim each time: result **3 / 3**, haunting **0 / 6**, ghost banished.
- Opened the UAP source trail; verified its saved-source date, scope note and NASA link. Used Space to choose a radio and Enter to lock the answer.
- Locked choices were disabled; focus moved to feedback after grading and to the result heading at completion.
- Sprite feedback and the live region paired the complete fabricated claim with “Sprites occur far above those cloud tops.” The exact NASA quote and containing passage remained available.
- Network observation from before the first Start through results recorded only the same-origin `content.json` load; no API, Ollama or upstream-source requests. No console warnings/errors were recorded.

## Mobile replay: 320 × 740, reduced motion

- Replayed from results without reloading. Score reset to **0 / 0** and haunting to **3 / 6**.
- Intentionally picked a supported sprite claim: haunting grew to **4 / 6**. The full fabricated claim and its paired correction were present in visible feedback and the live region.
- Correctly answered UAP and ghost-story rooms: final result **2 / 3**, haunting **2 / 6**, two scenes cleared and one still haunted.
- Claim text computed to **16 px**. Checked choosing/reveal layouts had no horizontal overflow; ordinary vertical scrolling exposes evidence and footer. The four inspected ghost/bat/fog animation names were `none` with reduced motion enabled.
- Replay through completion recorded **zero network requests** and no console warnings/errors.
- VerifyIt extension/site links and the fallibility/non-integration disclaimer were present. No extension was installed and no external source link was opened.

## App-only screenshots

- `media/static-intro.jpg`: desktop introduction.
- `media/static-desktop-result.jpg`: completed perfect desktop hunt.
- `media/static-mobile-reveal.jpg`: wrong sprite answer, paired correction and next-round control.
- `media/static-mobile-result.jpg`: completed mixed mobile hunt.

## Fresh ZIP and project-subpath rehearsal

The coordinating agent also extracted the source ZIP into a newly allocated directory outside the working checkout, ran its own validation and site builder, and served only the generated five browser files beneath a `/ghostproof/` URL prefix. A third actual browser hunt completed **3 / 3**, with all three topics and no console warnings/errors. Replay reset to round one, **0 / 0** and haunting **3 / 6**. This checks relative assets and real play from the extracted package rather than relying on files in the original project. The application bytes matched those used for the desktop/mobile screenshots; subsequent documentation-only package updates do not change this application test.

The browser's mobile/reduced-motion overrides are temporary test settings and are reset before handoff. This is a local static-build test, not evidence of a public deployment or GitHub Actions run.

## Public GitHub Pages verification — 30 October 2026

The coordinating agent tested the actual [public HTTPS game](https://aydin41k.github.io/ghostproof/) in the Codex in-app browser after the [successful Pages run](https://github.com/aydin41k/ghostproof/actions/runs/41055015797). Deployed application commit: `433ea2542f459e4a407788d99cbb72d3f1420996`; [hosted CI](https://github.com/aydin41k/ghostproof/actions/runs/41054856320) also succeeded for that commit. Subsequent evidence-only documentation updates leave all five deployed assets unchanged. The four screenshots above remain historical local evidence; none is relabelled as a hosted screenshot.

### Public delivery boundary

- Anonymous HTTPS requests returned HTTP 200 for `index.html`, `styles.css`, `app.js`, `game.js`, and `content.json`, with all bytes matching the reviewed local build at the `/ghostproof/` project subpath.
- Requests beneath that path for `.env`, `data/private.json`, `reference/local-preparation/server.py`, and `api/start` returned HTTP 404. The source repository is intentionally public, but source/private routes are not in the five-file Pages artifact.
- The Pages API identified the canonical HTTPS URL, workflow build type, public visibility, and enforced HTTPS. Its null status field was not treated as proof; the successful deployment run, live HTTP responses and actual play supply the evidence.

### Hosted desktop: 1280 × 720

- Completed St Paul's, UAP and sprite rooms with all fabricated claims correctly selected: **3 / 3**, haunting **0 / 6**.
- Opened the source trail and exercised keyboard Space/Enter selection and locking. Locked radios were disabled; focus moved to feedback and then the result heading.
- Sprite feedback and the live region paired the full fabricated claim with “Sprites occur far above those cloud tops.”
- Network observation from before Start through results recorded exactly one request, the same-origin `content.json`; no model/API/upstream-source requests and no captured page warnings/errors.

### Hosted mobile replay: 320 × 740, reduced motion

- Replayed directly from results: score reset to **0 / 0**, haunting to **3 / 6**. Correct UAP and St Paul's answers were followed by a deliberately wrong supported sprite choice about powerful lightning events.
- Wrong-answer feedback and the live region preserved the complete fabricated sprite claim and paired correction. Final result: **2 / 3**, haunting **2 / 6**.
- Claim text computed to **16 px**. Document client and scroll widths both measured **305 px** within the 320px viewport (scrollbar excluded), with no horizontal overflow. All footer links, including **Code & licences**, fit alongside the retained VerifyIt links and disclaimers.
- Inspected ghost, bat and fog animations were `none` under reduced motion. Replay through completion recorded **zero requests** and no captured page warnings/errors.
- Temporary viewport/reduced-motion overrides were reset and the public page returned to the introduction. These browser observations do not imply zero hosted-CI notices or exhaustive accessibility, security or legal assurance.
