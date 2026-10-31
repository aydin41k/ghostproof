"""Dependency-free, loopback-only GhostProof live local game."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import socket
import threading

try:
    from .generation import OllamaModel, RoundGenerator
    from .sources import PreparationError, strict_json
except ImportError:
    from generation import OllamaModel, RoundGenerator
    from sources import PreparationError, strict_json


ASSETS = {'/': ('index.html', 'text/html; charset=utf-8'), '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
          '/styles.css': ('styles.css', 'text/css; charset=utf-8')}


class GameError(ValueError):
    def __init__(self, message, status=409):
        super().__init__(message)
        self.status = status


class Game:
    """One hunt, one inference pipeline; novelty belongs to the generator, not hunt."""
    def __init__(self, generator):
        self.generator = generator
        self.lock = threading.Lock()
        self.busy = False
        self.session = None
        self.round = None
        self.status = 'idle'
        self.error = None
        self.answer = None
        self.score = self.answered = 0

    def public(self):
        with self.lock:
            return self._public()

    def _public(self):
        packet = {'session_id': self.session, 'status': self.status, 'busy': self.busy,
                  'score': self.score, 'answered': self.answered, 'error': self.error}
        if self.round:
            packet['round'] = {'id': self.round['id'], 'topic': self.round['topic'],
                               'claims': [{'id': claim['id'], 'text': claim['text']} for claim in self.round['claims']]}
        if self.answer:
            packet['reveal'] = self.answer
        return packet

    def start(self):
        with self.lock:
            # Reset is allowed while preparing, but never starts a second pipeline.
            self.session = secrets.token_urlsafe(18)
            self.round = self.answer = self.error = None
            self.score = self.answered = 0
            self.status = 'idle'
            if self.busy:
                self.error = 'Previous preparation is still finishing. Retry when it stops.'
            else:
                self._begin()
            return self._public()

    def next(self, session, round_id):
        with self.lock:
            self._session(session)
            if self.busy:
                raise GameError('One round is already being prepared. Please wait.')
            if self.round and (round_id != self.round['id'] or not self.answer):
                raise GameError('Reveal the current round before continuing.')
            if not self.round and round_id is not None:
                raise GameError('That round is no longer current.')
            self._begin()
            return self._public()

    def _session(self, session):
        if not self.session or session != self.session:
            raise GameError('This hunt is no longer current. Start a new hunt.')

    def _begin(self):
        self.busy = True
        self.status = 'preparing'
        self.error = None
        self.round = self.answer = None
        session = self.session
        threading.Thread(target=self._prepare, args=(session,), daemon=True).start()

    def _prepare(self, session):
        result, error = None, None
        try:
            result = self.generator.generate()
        except PreparationError as exc:
            error = str(exc)
        except Exception:
            error = 'Preparation could not finish safely. Check Ollama and internet access, then retry.'
        with self.lock:
            self.busy = False
            if self.session != session:
                return
            self.error = error
            self.round = result
            self.status = 'error' if error else 'choosing'

    def grade(self, session, round_id, claim_id):
        with self.lock:
            self._session(session)
            if not self.round or round_id != self.round['id']:
                raise GameError('That round is no longer current.')
            claims = self.round['claims']
            selected = next((i for i, claim in enumerate(claims) if claim['id'] == claim_id), None)
            if selected is None:
                raise GameError('Choose one of the current claims.', 400)
            if self.answer:
                if self.answer['selected_id'] != claim_id:
                    raise GameError('Your answer is already locked.')
                return self._public()
            correct = selected == self.round['false_index']
            self.answered += 1
            self.score += int(correct)
            self.status = 'revealed'
            self.answer = {'selected_id': claim_id, 'correct': correct, 'fake_id': claims[self.round['false_index']]['id'],
                           'fake_text': claims[self.round['false_index']]['text'], 'correction': self.round['correction'],
                           'correction_passage': self.round['correction_passage'], 'correction_quote': self.round['correction_quote'],
                           'claims': claims, 'source': self.round['source'], 'model': self.round['model'],
                           'contract': self.round['contract'], 'generated_at': self.round['generated_at'], 'review': self.round['review']}
            return self._public()


class LocalServer(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 8

    def __init__(self, port, generator):
        self.game = Game(generator)
        self.token = secrets.token_urlsafe(32)
        self.slots = threading.BoundedSemaphore(16)
        super().__init__(('127.0.0.1', port), Handler)

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.slots.release()


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.0'
    server_version = 'GhostProof'
    sys_version = ''

    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def log_message(self, *_):
        pass

    def reply(self, status, data, content='application/json; charset=utf-8'):
        raw = data if isinstance(data, bytes) else json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'same-origin')
        self.send_header('Cross-Origin-Resource-Policy', 'same-origin')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Content-Security-Policy', "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
        self.end_headers()
        try:
            self.wfile.write(raw)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def guard(self, mutate=False):
        host = self.headers.get_all('Host', [])
        expected = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
        if len(host) != 1 or host[0] not in expected:
            raise GameError('Loopback Host required.', 403)
        metadata = self.headers.get_all('Sec-Fetch-Site', [])
        if len(metadata) > 1 or (metadata and metadata[0] not in ('same-origin', 'none')):
            raise GameError('Same-origin requests only.', 403)
        origins = self.headers.get_all('Origin', [])
        if len(origins) > 1 or (origins and origins[0] != 'http://' + host[0]) or (mutate and not origins):
            raise GameError('Same-origin Origin required.', 403)
        if mutate:
            tokens = self.headers.get_all('X-GhostProof-Token', [])
            if len(tokens) != 1 or not tokens[0].isascii() or len(tokens[0]) > 100 or not secrets.compare_digest(tokens[0], self.server.token):
                raise GameError('Missing or invalid local request token.', 403)

    def do_GET(self):
        try:
            self.guard()
            if self.path in ASSETS:
                filename, content = ASSETS[self.path]
                self.reply(200, (Path(__file__).parent / filename).read_bytes(), content)
            elif self.path == '/api/health':
                try:
                    readiness = self.server.game.generator.ready()
                except PreparationError as exc:
                    readiness = {'ready': False, 'model': self.server.game.generator.model.name, 'error': str(exc)}
                except Exception:
                    readiness = {'ready': False, 'error': 'Local model readiness failed. Start Ollama and check the installed Gemma model.'}
                self.reply(200, {'token': self.server.token, **readiness})
            elif self.path == '/api/state':
                self.reply(200, self.server.game.public())
            else:
                self.reply(404, {'error': 'Not found.'})
        except GameError as exc:
            self.reply(exc.status, {'error': str(exc)})

    def do_POST(self):
        try:
            self.guard(True)
            if self.path not in ('/api/start', '/api/next', '/api/grade'):
                raise GameError('Not found.', 404)
            if self.headers.get_all('Content-Type', []) != ['application/json']:
                raise GameError('application/json required.', 415)
            lengths = self.headers.get_all('Content-Length', [])
            if len(lengths) != 1 or not lengths[0].isdigit() or self.headers.get_all('Transfer-Encoding', []):
                raise GameError('Unambiguous Content-Length required.', 400)
            length = int(lengths[0])
            if not 2 <= length <= 2048:
                raise GameError('Request body exceeds its budget.', 413)
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise GameError('Incomplete request body.', 400)
            data = strict_json(raw.decode('utf-8'))
            fields = {'/api/start': set(), '/api/next': {'session_id', 'round_id'}, '/api/grade': {'session_id', 'round_id', 'claim_id'}}[self.path]
            if not isinstance(data, dict) or set(data) != fields or any(value is not None and (not isinstance(value, str) or len(value) > 100) for value in data.values()):
                raise GameError('Invalid request fields.', 400)
            if self.path == '/api/start':
                result = self.server.game.start()
            elif self.path == '/api/next':
                result = self.server.game.next(data['session_id'], data['round_id'])
            else:
                result = self.server.game.grade(data['session_id'], data['round_id'], data['claim_id'])
            self.reply(200, result)
        except (PreparationError, UnicodeError, socket.timeout):
            self.reply(400, {'error': 'Invalid or incomplete JSON request.'})
        except GameError as exc:
            self.reply(exc.status, {'error': str(exc)})

    def do_HEAD(self):
        try:
            self.guard()
            self.reply(405, {'error': 'Method not allowed.'})
        except GameError as exc:
            self.reply(exc.status, {'error': str(exc)})

    do_OPTIONS = do_HEAD
    do_PUT = do_HEAD
    do_DELETE = do_HEAD
    do_PATCH = do_HEAD


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8766)
    parser.add_argument('--model', default='gemma4:e4b', help='Installed local Gemma model name; never downloaded automatically')
    parser.add_argument('--ollama', default='http://127.0.0.1:11434', help='Explicit loopback HTTP origin')
    parser.add_argument('--raw-gemma', action='store_true', help='Explicit Gemma turn adapter for custom empty-template models only')
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('port must be 1..65535')
    try:
        model = OllamaModel(args.model, args.ollama, args.raw_gemma)
        server = LocalServer(args.port, RoundGenerator(model))
    except (PreparationError, OSError) as exc:
        parser.error(str(exc))
    print(f'GhostProof live local: http://127.0.0.1:{server.server_port}/ (Ctrl+C to stop)', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
