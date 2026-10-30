# GhostProof: catch the lie, clear the haunting

*Draft for [The Hacktoberfest Challenge: Week 4](https://dev.to/challenges/hacktoberfest-week4-2026-10-26). Required tags: `devchallenge`, `hf26challenge`. AI disclosure for the mostly agent-written draft: `fully_autonomous`. Not published or a declaration of personal eligibility.*

## What I Built

GhostProof is a three-room Halloween game about reading carefully. A fictional ghost hides one fabricated claim among two source-supported claims. Catch its lie and the haunting weakens; believe it and the ghost grows.

The rooms explore the history behind St Paul's ghost stories, NASA's independent UAP study, and sprites above thunderstorms. “Supported” has a deliberately narrow meaning: supported by the cited passage in its stated scope. Recorded folklore does not prove ghosts. An unexplained observation does not identify an alien origin.

After each answer, the game puts the fabrication, correction, exact quotation and containing passage in front of you. The aim is not to reward blind trust in an AI answer. It is to make checking the evidence the interesting part.

## Demo

**Authorized primary route: free GitHub Pages, pending independent release review and verified deployment. There is no live URL yet.** The manual-only workflow publishes just the static site after public visibility is verified. The rules also permit a recorded walkthrough; the [shot outline and narration](narration-script.md) cover a full hunt, a wrong answer with evidence, and replay. No video has been recorded/uploaded and no deployment is claimed. Add the verified playable URL before submission.

The earlier local static build was played by the coordinating agent at desktop and 320px mobile widths: a perfect 3/3 hunt and a mixed 2/3 replay. [App-only screenshots and the scoped QA record](browser-qa.md) are included in the source package. This is local browser smoke evidence, not hosted verification or an exhaustive accessibility audit.

The public-demo design is intentionally simple: cached content, no accounts and no live inference. Answers are inspectable in the browser bundle. It is a learning game, not a secure competition or a fact-checking service.

## Code

Repository: [aydin41k/ghostproof](https://github.com/aydin41k/ghostproof). The initial release was pushed privately with Actions disabled. The owner has authorized public visibility and the free standard public Actions/Pages route; anonymous judge access is pending verification. This draft is incomplete until that access and the demo are verified.

The source package contains the static application, exact accepted public content, dependency-free tests, a five-file site builder, deterministic ZIP tooling, and the original preparation modules as labelled historical source references. Private transport bodies and model responses are excluded. Original code and SVG/CSS artwork are offered under MIT; [licensing scope and third-party exclusions](../LICENSING.md) explain why attributed excerpts and unestablished generated-text rights are not covered by that grant.

## How I Built It

Local Gemma did the claim writing: `gemma4-e4b-local:latest`, under a frozen source-paraphrase contract. Five real calls produced the three accepted topics after explicit rejected-and-repaired attempts and separate agent editorial review. The game now shuffles that finite pool; it does not call a model every time a player presses Next.

The hardest part was deciding what a false claim means. A missing detail is not a contradiction. The fabricated UAP claim must reverse what the *independent study* used, not make a sweeping statement about all NASA work. The sprite correction says “those cloud tops,” so it must stay immediately beside the complete fabrication that supplies its referent. Those details are tested in the actual client rendering, including a wrong pick.

Packaging exposed a second boundary: the private preparation validator correctly needs private evidence, but a clean public demo must not. The release therefore exports only accepted claims and selected contextual evidence into a separate versioned schema. The original validator stays strict. The browser checks the content digest and shape; neither check pretends to prove truth.

Vanilla JavaScript modules, Node's built-in tests and Python's standard library keep the released game reproducible without an install step. Tests cover all eight win/loss sequences, answer locking, replay, malformed content, source URL restrictions and archive allowlists. An extracted-package rehearsal runs the game/client tests and rebuilds outside the original checkout. GitHub Actions is prepared for these checks; the free public route is authorized but review and verified public visibility must precede enabling it. **No hosted CI run is claimed yet.**

Codex agents materially planned, implemented, tested and drafted this entry; the owner directed the project. Editorial review of model output was performed by a separate agent, not passed off as human fact-checking. Fresh browser QA was performed by the coordinating agent using the actual app controls.

## Why Does Open Innovation Matter?

An inspectable model workflow makes it possible to ask more useful questions than “did the AI sound convincing?” Which sources were allowed? What qualified as a contradiction? Which outputs were rejected? Where does the evidence stop?

GhostProof makes one small part of that process tangible. Readers can inspect the accepted text, its exact source context, and the code that keeps the game honest about its limits. Local open-model preparation also separates experimentation from a paid inference request on every click. The release is candid about its boundaries: private historical source/response records are not included, and the original-code MIT grant does not relicense third-party material or establish rights in generated text.

Open innovation is strongest when reusable work carries its boundaries with it—not just its success story.

## The Spirit of It

The ghost is theatrical; the evidence is not. A church, a UFO scene and a storm turn source reading into a short haunted-house visit. The apparition shrinks when caught, grows when believed, and disappears after three correct answers. Reduced-motion play keeps every answer and correction immediate.

## Prize Categories

**Gemma:** implemented. The accepted claims were actually generated by local Gemma and separately source-reviewed. No inference occurs during play; final category eligibility is the judges' decision.

**GitHub Copilot category via GitHub Actions:** prepared workflow and locally executed checks only. The category permits Actions automation; no Copilot generation or successful hosted Actions run is claimed. A verified run is still needed before presenting this as completed category use.

Render hosting, ElevenLabs narration, Entire session tooling and a `.tech` domain are not claimed as used. The [category checklist](bonus-checklist.md) separates useful prepared work from integrations that do not exist.

---

### Author checklist — remove before publishing

- Add the real walkthrough/demo URL and confirm the repository contains the pushed release and is accessible to judges. Before staging the article, use the first heading as its title and replace repository-relative document links with verified repository document links or concise prose; private links still require access.
- Review the narrative and source/contractor-text rights, and verify the authorized MIT/public release is represented accurately. Authorization is not third-party legal clearance. Add a personal perspective only if it is genuinely yours; no biographical or eligibility claim was invented here.
- Confirm challenge-window/new-work and personal age/country/rights eligibility against the official rules. One entry/one win; no guarantee of category eligibility is made.
- Required tags are `devchallenge` and `hf26challenge`. Retain `fully_autonomous` unless meaningful human rewriting changes the appropriate disclosure. No session transcript is shared.
- Formal rules say 31 October 2026, 23:59 PDT (1 November, 17:59 Sydney); the API ends_at is 31 October, 06:59 UTC (31 October, 17:59 Sydney). Use the earlier time as the operational buffer; this discrepancy has not been resolved by an organizer.
- Keep the existing DEV article unpublished. The coordinating agent may update it from the reviewed draft only after release approval and a verified push. Publishing still requires an explicit owner yes.
