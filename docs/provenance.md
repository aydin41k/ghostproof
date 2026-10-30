# What this release can substantiate

GhostProof has one finite, reviewed pool, not an open-ended fact generator. Its three subjects were selected by the curator: NPS's account of St Paul's ghost stories; NASA's independent UAP study; and NASA's account of atmospheric sprites. Lore attribution, study-specific scope, lightning association and photographed-jellyfish-instance qualifications stay attached to the claims.

```text
Private retained sources → local Gemma attempts → separate agent editorial decisions
                                                   ↓ accepted-only export
                                            reviewed public content
                                                   ↓
                                        static browser game + local/CI tests
```

There is no browser-to-model arrow. The source package reproduces the released game, content validation, site build and packaging. It does not reconstruct the private preparation history from scratch.

## Actual preparation

The model identity was `gemma4-e4b-local:latest`, using frozen contract `spooky-source-paraphrases-1`. Five real calls—ghosts two, UAP one, sprites two—used **32.13823349300219 seconds** cumulative request time. The final pool was prepared **2026-10-29T23:40:55Z**. These are historical observations, not release/build timestamps. Rejected and repaired attempts remain in the private ledger; rejected model responses are not redistributed. Separate candidate-bound agent editorial decisions accepted one candidate per topic; they are not human fact-checking or a theorem of correctness.

Lifetime source request counts were NPS 1 / UAP 2 / sprites 1. The first UAP response body was lost by the initial parser; its original bytes, hash, size and retrieval time are unknown, not reconstructed from a later response. One explicit UAP recovery retained the current evidence. No additional source or model call was made to export this release.

## Public export contract

`demo/content.json` contains three topics, nine accepted claim texts, one fake per topic, exact corrections/explanations, exact returned quotations and selected containing passages, source titles/canonical URLs/retrieval times, prepared time, model/contract identities and selected provenance hashes. Output is deterministically sorted. Only the original whitespace normalization was applied; the exporter did not improve claim wording.

The private pool fully validated before export. The root-local equality check compared every exported field with the real accepted provider projection while outbound socket connections were forbidden. The helper and private records are not part of this distribution. This is evidence of the audited export operation, not an independently reconstructable private chain for a reader who has only this package.

Public file raw-byte SHA-256:

`76d943680f1008b283d31c3dbb5baa3ff8658c88ebe94619dc57a57395447360`

Accepted candidate hashes (the original canonical-JSON hash of each accepted attempt, **not** a raw-file digest):

| Topic | Candidate hash |
| --- | --- |
| ghosts | `b863af936b34cccdd69cfd2fce686bd55181b388b985e7623594ae19e1284681` |
| sprites | `16babc0972fac6714c41bfd358bb2a479456a367f3d9bc215699db10e9d55cd8` |
| uap | `3d04111d45d42763eff5a6995add9c56ee1dfd56716113ddacc7c53f1c844b0a` |

The public `provenance` object retains canonical-JSON hashes of the private source envelope (`1e43c2fdf1fcf47837deeaeaba43e57e58897e837f0fca15ce126d358041f559`), attempt ledger (`5e997c10ed7b1109b605ed397cb55d86d62d3343d7c96b71edf82d54fc55b676`), and review envelope (`6aa34d65639e1a9fc67146edaa811ff491b7e92bc16ad8d3759730888689e3b2`). The exact serialization routine is in the historical `article_rounds.py`. Hashes identify the audited versions; they are not cryptographic proof that a claim is true, and the private inputs are not supplied here.

## Context is part of the answer

The accepted correction “Sprites occur far above those cloud tops.” is context-bound. Both visible feedback and the live-status announcement present it immediately after:

> The fabricated claim: “Sprites are positioned near the tops of cumulonimbus clouds.” Correction: Sprites occur far above those cloud tops.

The false-claim card also retains the fake and its exact source context. The correction is never advertised as an independently standalone sentence. The UAP claims concern the specific independent study, not every NASA activity; NPS's local ghost stories are recorded lore, not evidence of a haunting. Absence of information alone is not treated as a contradiction.

## What stays private / what remains limited

No full HTML, transport bodies, credentials, raw responses, rejected text, transcripts, request/fetch ledgers, local paths, source photographs or model weights are shipped. Original preparation code is a historical source-audit snapshot with hashes, not runnable regeneration instructions. Original records remain untouched.

The public static bundle includes answers; a player can inspect or change their own local state. No leaderboard, anti-cheat, production-security or universal-truth claim is made. Automated checks and browser smoke tests are scoped evidence, not an exhaustive accessibility/security audit. Source pages may change after the recorded retrieval times.
