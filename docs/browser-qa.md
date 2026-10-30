# Static release browser smoke test

Tested 30 October 2026 by the root assistant in the Codex in-app browser. These are actual UI interactions with the packaged static site, not the original Python game server and not a claim of exhaustive accessibility/security testing.

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
