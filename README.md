# GhostProof

Catch one fabricated claim in haunted source-reading rooms: correct answers weaken the fictional ghost; mistakes make it grow. Choose the five-file cached browser demo, or the separate **live local Gemma mode** that discovers fresh NASA articles and prepares new rounds on demand.

The historical cached demo covers **St Paul's ghost stories**, **NASA's independent UAP study**, and **sprites above thunderstorms**. Live local mode asks Gemma for spooky search subjects and retrieves the public NASA archive, rather than replaying those three assignments. All claims are source-scoped—not proof of ghosts, aliens, or universal model accuracy.

![GhostProof static demo introduction](docs/media/static-intro.jpg)

[Play the cached HTTPS demo](https://aydin41k.github.io/ghostproof/) · [Public source](https://github.com/aydin41k/ghostproof)

## Play fresh rounds with your local Gemma

Requires Python 3.10+, [Ollama](https://ollama.com/) running on your computer, an installed local [Gemma 4 model](https://ollama.com/library/gemma4), and internet access to NASA Science. No Python/package dependencies, cloud API, paid service, API key or account is required by this application. Install Ollama separately, start it (`ollama serve` if it is not already running), and explicitly download the public model yourself:

```sh
ollama pull gemma4:e4b
python3 local/server.py --port 8766
```

Open <http://127.0.0.1:8766/>. The application never installs or downloads a model automatically. Check the model's Ollama requirements and available RAM/disk first; local generation speed varies by hardware and can take a minute or longer. NASA access is needed for each new room, not just setup. Stop the application with Ctrl+C; stop a separately started Ollama process separately.

Each “Next fresh round” requests live discovery, exact article prose, a new three-claim draft and a **separate blinded automated check by the same local model**. The application numbers complete sentences from the actual article and conservatively derives exclusive constellation/size/distance slots or a guarded plain-predicate polarity toggle. Gemma selects two supported paraphrases and a third eligible sentence/property to fabricate; code applies the single substitution or exact predicate negation and preserves the original sentence as correction. The three evidence sentence IDs must differ. Modal, appearance, containment, conditional and example/list statements cannot supply a fake. A generic constellation vocabulary checks value kinds; there is no curated sentence/claim bank. Answer/evidence fields stay on the server until you lock a claim. Reveal includes the fake/correction pair, exact quotations and containing paragraphs, canonical NASA link, retrieval time, model identity and canonical prose digest. These mechanical checks plus automated checking still do **not** guarantee semantic correctness or replace human fact-checking; inspect the source yourself.

There is **no total-round or lifetime generation cap**. Individual requests share a 180-second total budget, at most two AI-selected search queries and two draft attempts. A second live query can recover automatically from unsuitable evidence; final failures show an explicit retry, never an old-card or invented fallback. Search can run out of suitable evidence: unlimited requests do not mean an infinite supply of unique facts. Accepted source IDs and cited-passage fingerprints persist in memory across “New hunt”; restarting the server resets this novelty history and can revisit articles. One hunt and one inference pipeline run per process. A hunt reset during preparation invalidates the old session, waits for that pipeline to finish, and offers retry without starting overlapping inference.

For another **already installed local Gemma** model, pass `--model name:tag`. Standard public tags use Ollama chat. The optional `--raw-gemma` is only for custom empty-template Gemma 4 models needing explicit turn framing; it is not necessary for the public default, and no private alias is required. `--ollama http://127.0.0.1:11434` can select another explicit loopback HTTP origin, not a remote host. The app binds only `127.0.0.1`; do not expose or reverse-proxy it to other people. Host/Origin/token checks protect local browser requests, not production authentication. The browser calls only its same-origin application, never Ollama or NASA directly; no storage, analytics or external scripts are used.

This live local functionality is a later change than the historical deployed demo and walkthrough. It is not claimed to have been in the earlier contest entry or to resolve any deadline/eligibility question. GitHub Pages remains the cached five-file demo and cannot connect to your laptop model.

## Play the cached demo from a clean clone or ZIP

Requires Node.js 22+ and Python 3.10+. There are no package dependencies to install, accounts to create, API keys to provide, or model weights to download. From this directory:

```sh
python3 tools/validate_release.py
python3 tools/build_site.py
python3 -m http.server 8080 --bind 127.0.0.1 --directory site
```

Open <http://127.0.0.1:8080/> in a current browser. Serve **only `site/`**, never the repository or historical reference directory. Browser integrity checking requires HTTPS or localhost; opening an HTML file directly or using an insecure remote HTTP origin is unsupported. Stop your preview with Ctrl+C. If files are missing or fail verification, restore a verified package and reload; “Start a fresh hunt” retries loading without inventing fallback content.

Public repository: [aydin41k/ghostproof](https://github.com/aydin41k/ghostproof). Anonymous source access and the [live HTTPS demo](https://aydin41k.github.io/ghostproof/) were verified on 30 October 2026. The initial release was pushed privately with Actions disabled; public visibility was verified before standard public Actions were enabled. The [release checklist](docs/release-checklist.md) records the successful hosted runs and the remaining owner submission checks.

## How the historical cached demo was prepared

The actual local model `gemma4-e4b-local:latest` prepared the claims in advance under a frozen source-paraphrase contract. Five real calls produced three accepted, separately agent-reviewed topics. Their exact accepted claim text, quotations and containing passages are exported in `demo/content.json`.

The **cached demo** is a browser-local adaptation of the earlier loopback prototype. Its browser loads five same-origin files and then plays/replays without model or upstream-source requests. Opening an optional source link is your own navigation to NASA or NPS. There is no inference during cached play, account, telemetry, storage, leaderboard or laptop connection. A fresh page load still needs the static files; offline reload is not implemented. The separate `local/` application above is not that historical prototype and does not import its records or code.

Answers live in the bundle and are inspectable. Hiding evidence from the choosing screen is a presentation choice, not anti-cheat security. A content checksum catches release drift; it does not prove truth. “Supported” always refers to the stated source scope. In particular, the sprite correction “Sprites occur far above those cloud tops.” stays paired with the full fabricated claim identifying the cloud tops.

## Validate, build and package

```sh
node --test tests/*.test.js
node --check demo/app.js
node --check demo/game.js
node --check local/app.js
python3 local/server.py --help
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test*.py' -v
python3 tools/validate_release.py
python3 tools/build_site.py
python3 tools/package_release.py
python3 tools/package_release.py --smoke
```

The last command extracts the exact source ZIP into a new temporary directory, then validates, builds, and runs the static/local Node client tests and Python generation/state/real-loopback-handler tests there. Local tests use injected synthetic adapters, without Ollama or internet; they demonstrate fifth-round continuation and new-hunt freshness, not real-model truth. Only the recursive extraction test is skipped inside that extracted child; all other tests run. Output: `dist/ghostproof-1.0.0.zip`, its SHA-256 sidecar and a per-file SHA-256 manifest. `site/` remains the smaller, original five-file web-public allowlist. Unknown or symlinked source files fail validation; generated directories, weights and runtime source/model responses are not packaged.

## Hosting and automation

Any HTTPS static host can serve the generated `site/` directory, including a project subpath. No dynamic backend is required. `render.yaml` prepares a static site with automatic deployment switched off; no Render service has been created. Check free-account limits and paid-overage settings before connecting a repository. This cached frontend's Render category eligibility is not assumed.

GitHub Actions [CI passed](https://github.com/aydin41k/ghostproof/actions/runs/41054856320) and [Pages deployment succeeded](https://github.com/aydin41k/ghostproof/actions/runs/41055015797) for application commit `433ea2542f459e4a407788d99cbb72d3f1420996` on 30 October 2026. Standard public-runner compute and GitHub Pages are the confirmed free route; this does not claim that arbitrary artifacts or account-wide usage are free. CI validates and rehearses the package without retaining an optional artifact. Pages remains **manual-only** and publishes only `site/`, using the required one-day deployment artifact, not the source package. All five hosted assets matched the reviewed build; deployed desktop and mobile hunts passed the [scoped browser checks](docs/browser-qa.md). Later evidence-only documentation updates do not change those deployed assets. See [hosting/CI evidence](docs/release-checklist.md), including non-blocking runner notices.

## Provenance and rights

[Provenance](docs/provenance.md) records accepted candidate hashes and limitations. [Historical preparation code](reference/local-preparation/README.md) is included only for source audit; private source/response ledgers are not shipped, so full historical regeneration from this package is not claimed.

Original code and SVG/CSS artwork are offered under the [MIT License](LICENSE). Attributed third-party excerpts and unestablished generated-text rights are excluded; see [LICENSING.md](LICENSING.md) and [source credits/third-party boundaries](THIRD_PARTY_NOTICES.md). Public release authorization is not third-party legal clearance. No NASA/NPS photos or logos are included. The original decorative scenery is code-native SVG/CSS, not source evidence.

The [submission draft](docs/submission-draft.md), [category status](docs/bonus-checklist.md), and [walkthrough narration](docs/narration-script.md) are preparation aids, not a published entry or eligibility guarantee.
