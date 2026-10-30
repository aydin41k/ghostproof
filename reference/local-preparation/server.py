"""Loopback-only throwaway game server; serves an explicit asset allowlist."""
import json
import copy
import argparse
import logging
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from catalogue import CatalogueError, strict_json
from article_rounds import ArticleError
from spooky_rounds import generate_round

TTL = 900
MAX_SESSIONS = 16
ABSTENTION = "The reviewed spooky-topic round could not be accepted. No round was accepted."
ASSETS = {"/": ("index.html", "text/html; charset=utf-8"), "/app.js": ("app.js", "text/javascript; charset=utf-8"), "/styles.css": ("styles.css", "text/css; charset=utf-8")}


class GameStore:
    def __init__(self, generator=generate_round, clock=time.monotonic):
        self.generator = generator; self.clock = clock; self.lock = threading.RLock()
        self.sessions = {}; self.active = None; self.recent = []

    def prune(self):
        for sid, session in list(self.sessions.items()):
            if self.clock() - session["touched"] > TTL:
                if session.get("cancel"): session["cancel"].set()
                del self.sessions[sid]

    def get(self, sid):
        self.prune()
        if not isinstance(sid, str) or sid not in self.sessions: raise ValueError("Session expired or unknown. Start a fresh hunt.")
        session = self.sessions[sid]; session["touched"] = self.clock(); return session

    def begin(self, session):
        if self.active: raise RuntimeError("Another cached round is being prepared. Retry when it is free.")
        token = secrets.token_urlsafe(18); cancel = threading.Event()
        session.update(phase="generating", job=token, cancel=cancel, started=self.clock(), detail="Reading reviewed ghost-lore, UFO and storm-light rounds", error=None)
        self.active = token
        thread = threading.Thread(target=self.work, args=(session["id"], token, cancel), daemon=True); thread.start()

    def work(self, sid, token, cancel):
        def phase(detail):
            with self.lock:
                if sid in self.sessions and self.sessions[sid].get("job") == token and not cancel.is_set(): self.sessions[sid]["detail"] = detail
        try:
            with self.lock: exclusions = [packet["topic"] for packet in self.sessions[sid]["rounds"]] if sid in self.sessions else []
            packet = self.generator(exclusions, phase, cancel.is_set)
            with self.lock:
                if cancel.is_set() or sid not in self.sessions or self.sessions[sid].get("job") != token: return
                session = self.sessions[sid]
                packet["id"] = secrets.token_urlsafe(18)
                for claim in packet["claims"]: claim["id"] = secrets.token_urlsafe(12)
                packet["selected"] = None
                session["rounds"].append(packet); session["phase"] = "choosing"
                self.recent.append(packet["topic"]); self.recent = self.recent[-12:]
        except Exception as error:
            with self.lock:
                if sid in self.sessions and self.sessions[sid].get("job") == token and not cancel.is_set():
                    self.sessions[sid].update(phase="error", error=str(error) if isinstance(error, (CatalogueError, ArticleError)) else ABSTENTION, diagnostic=str(error))
                logging.warning("Cached round rejected: %s", error)
        finally:
            with self.lock:
                if self.active == token: self.active = None

    def public(self, session):
        result = {"session": session["id"], "phase": session["phase"], "number": min(len(session["rounds"]) + (session["phase"] in {"generating", "error", "cancelled"}), 3), "score": sum(1 for packet in session["rounds"] if any(claim["id"] == packet["selected"] and claim["is_false"] for claim in packet["claims"])), "answered": sum(packet["selected"] is not None for packet in session["rounds"]), "busy": self.active is not None}
        result['story'] = {'haunting_level': 3 + result['answered'] - 2 * result['score'], 'cleared': result['score'], 'missed': result['answered'] - result['score']}
        if session["phase"] == "generating": result.update(detail=session["detail"], elapsed=round(self.clock() - session["started"]))
        if session["phase"] in {"error", "cancelled"}: result["error"] = session.get("error") or "Cancelled. Retry this cached round or start a fresh hunt."
        if session["phase"] in {"choosing", "revealed"}:
            packet = session["rounds"][-1]
            result["round"] = {"id": packet["id"], "topic": packet["topic"], "claims": [{"id": claim["id"], "text": claim["text"]} for claim in packet["claims"]], "clue": "Two claims match the source article; one directly conflicts with it. Read carefully: a missing detail alone does not make a claim false.", "pool_size": packet["pool_size"], "prepared_at": packet["prepared_at"], "sources": [{key: source[key] for key in ("id", "title", "publisher", "url", "retrieved_at")} for source in packet["sources"]]}
            if 'scene' in packet:
                if packet['scene'] not in {'church', 'ufo', 'storm', 'cave', 'forest', 'stars'}: raise ValueError('Invalid trusted scene.')
                result['round']['scene'] = packet['scene']
            if 'scope' in packet:
                if packet.get('category') not in {'ghost_lore', 'ufo_reports', 'eerie_phenomena'}: raise ValueError('Invalid trusted topic category.')
                result['round']['scope'] = packet['scope']
                result['round']['category'] = packet['category']
            if session["phase"] == "revealed":
                result["reveal"] = {"selected": packet["selected"], "claims": [{**{key: claim[key] for key in ("id", "text", "is_false", "explanation", "correction", "source_id")}, "evidence": copy.deepcopy(claim["evidence"])} for claim in packet["claims"]], "generation_seconds": packet["seconds"]}
        return result

    def action(self, route, body):
        with self.lock:
            self.prune()
            if route == "/api/start":
                if self.active: raise RuntimeError("Another cached round is being prepared. Please retry shortly.")
                if len(self.sessions) >= MAX_SESSIONS: raise RuntimeError("Too many active hunts. Wait for an old session to expire.")
                sid = secrets.token_urlsafe(24); session = {"id": sid, "phase": "intro", "rounds": [], "touched": self.clock(), "retries": 0}
                self.sessions[sid] = session; self.begin(session); return self.public(session)
            session = self.get(body.get("session"))
            if route == "/api/cancel":
                if session["phase"] == "generating": session["cancel"].set(); session["phase"] = "cancelled"
                elif session["phase"] == "choosing":
                    # The worker may finish between the client's last poll and cancel.
                    # Discard that unseen, ungraded round rather than silently keeping it.
                    session["rounds"].pop(); session["phase"] = "cancelled"
            elif route == "/api/retry":
                if session["phase"] not in {"error", "cancelled"}: raise ValueError("This round is not waiting for retry.")
                if session["retries"] >= 2: raise ValueError("Retry limit reached. Start a new hunt.")
                self.begin(session); session["retries"] += 1
            elif route == "/api/grade":
                if session["phase"] not in {"choosing", "revealed"}: raise ValueError("There is no unlocked round to grade.")
                packet = session["rounds"][-1]
                if body.get("round_id") != packet["id"]: raise ValueError("That round is no longer current.")
                chosen = next((claim for claim in packet["claims"] if claim["id"] == body.get("claim_id")), None)
                if not chosen: raise ValueError("Choose one of the current claims.")
                if packet["selected"] is not None and packet["selected"] != chosen["id"]: raise RuntimeError("This answer is already locked.")
                packet["selected"] = chosen["id"]; session["phase"] = "revealed"
            elif route == "/api/next":
                if session["phase"] != "revealed": raise ValueError("Answer the current round before continuing.")
                if len(session["rounds"]) == 3: session["phase"] = "results"
                else: self.begin(session)
            else: raise ValueError("Unknown action.")
            return self.public(session)


class Handler(BaseHTTPRequestHandler):
    store = GameStore()
    root = Path(__file__).resolve().parent

    def reply(self, code, payload, content="application/json; charset=utf-8"):
        raw = json.dumps(payload).encode() if content.startswith("application/json") else payload
        self.send_response(code); self.send_header("Content-Type", content); self.send_header("Content-Length", str(len(raw))); self.send_header("Cache-Control", "no-store"); self.send_header("X-Content-Type-Options", "nosniff"); self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"); self.end_headers(); self.wfile.write(raw)

    def valid_host(self):
        return len(self.headers.get_all("Host", [])) == 1 and self.headers.get("Host") in {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}

    def do_GET(self):
        if not self.valid_host(): self.reply(403, {"error": "Loopback host required."}); return
        path = urlsplit(self.path)
        if path.path in ASSETS and not path.query:
            filename, content = ASSETS[path.path]; self.reply(200, (self.root / filename).read_bytes(), content); return
        if path.path == "/api/status":
            try:
                query = parse_qs(path.query, keep_blank_values=True, strict_parsing=True, max_num_fields=1)
                if set(query) != {"session"} or len(query["session"]) != 1: raise ValueError("Only one session parameter is allowed.")
                sid = query["session"][0]
                with self.store.lock: result = self.store.public(self.store.get(sid))
                self.reply(200, result)
            except ValueError as error: self.reply(404, {"error": str(error)})
            return
        self.reply(404, {"error": "Not found."})

    def do_POST(self):
        origin = self.headers.get("Origin")
        if not self.valid_host() or len(self.headers.get_all("Origin", [])) != 1 or origin != f"http://{self.headers.get('Host')}": self.reply(403, {"error": "Same-origin loopback requests only."}); return
        if len(self.headers.get_all("Content-Type", [])) != 1 or self.headers.get("Content-Type") != "application/json": self.reply(415, {"error": "JSON required."}); return
        try:
            if self.headers.get("Transfer-Encoding") is not None or len(self.headers.get_all("Content-Length", [])) != 1: raise ValueError("One fixed JSON body length is required.")
            length = int(self.headers.get("Content-Length", "0"))
            if not 1 <= length <= 2048: raise ValueError("Invalid request size.")
            try:
                body = strict_json(self.rfile.read(length))
            except CatalogueError as error:
                raise ValueError("Invalid JSON request (duplicate keys/non-finite numbers forbidden).") from error
            if not isinstance(body, dict): raise ValueError("JSON object required.")
            allowed = {"session", "round_id", "claim_id"} if self.path == "/api/grade" else {"session"} if self.path in {"/api/next", "/api/retry", "/api/cancel"} else set()
            if set(body) - allowed: raise ValueError("Unsupported request fields.")
            result = self.store.action(self.path, body); self.reply(200, result)
        except (ValueError, json.JSONDecodeError) as error: self.reply(400, {"error": str(error)})
        except RuntimeError as error: self.reply(409, {"error": str(error)})


def main():
    argparse.ArgumentParser(description="Cached ghost-lore, UFO and storm-light game; frozen preparation lives in spooky_rounds.py.").parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("GhostProof: http://127.0.0.1:8765/ · fictional ghost, source-reviewed ghost lore/UFOs/storm lights · no inference during play", flush=True)
    server.serve_forever()


if __name__ == "__main__": main()
