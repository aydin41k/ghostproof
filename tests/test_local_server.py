"""Real ephemeral loopback handler + server-owned continuous state, no network models."""
import copy
import http.client
import json
from pathlib import Path
import socket
import threading
import time
import unittest

from local.generation import RoundGenerator
from local.server import Game, GameError, LocalServer, ASSETS
from local.sources import PreparationError
from test_local_generation import FakeModel, FakeSources


def settle(game):
    until = time.monotonic() + 2
    while game.public()['busy'] and time.monotonic() < until:
        time.sleep(.005)
    assert not game.public()['busy'], 'fixture generation did not finish'
    return game.public()


class StateTests(unittest.TestCase):
    def test_continuation_beyond_three_has_no_total_round_or_score_cap(self):
        game = Game(RoundGenerator(FakeModel(), FakeSources())); game.start()
        for index in range(7):
            state = settle(game)
            revealed = game.grade(state['session_id'], state['round']['id'], state['round']['claims'][game.round['false_index']]['id'])
            self.assertEqual(revealed['answered'], index + 1)
            self.assertEqual(revealed['score'], index + 1)
            if index < 6: game.next(state['session_id'], state['round']['id'])
        self.assertEqual(len(game.generator.used_sources), 7)

    def test_concurrent_clicks_do_not_queue_generation(self):
        entered, release = threading.Event(), threading.Event()
        class Blocked:
            calls = 0
            def generate(self):
                self.calls += 1; entered.set(); release.wait(2)
                raise PreparationError('Stopped fixture.')
        adapter = Blocked(); game = Game(adapter); state = game.start(); self.assertTrue(entered.wait(1))
        results = []
        def click():
            try: game.next(state['session_id'], None)
            except GameError as exc: results.append(exc.status)
        workers = [threading.Thread(target=click) for _ in range(8)]
        for worker in workers: worker.start()
        for worker in workers: worker.join(1)
        self.assertEqual(results, [409] * 8); self.assertEqual(adapter.calls, 1)
        release.set(); settle(game)

    def test_five_rounds_reset_history_projection_grading_and_score(self):
        generator = RoundGenerator(FakeModel(), FakeSources())
        game = Game(generator); game.start()
        ids = []
        for n in range(5):
            choosing = settle(game)
            serialized = json.dumps(choosing)
            for private in ('false_index', 'correction', 'quote', 'source', 'review', 'passages', 'model', 'is_false'):
                self.assertNotIn('"' + private + '"', serialized)
            ids.append(game.round['source']['id'])
            with self.assertRaises(GameError): game.next(choosing['session_id'], choosing['round']['id'])
            with self.assertRaises(GameError): game.grade('stale', choosing['round']['id'], choosing['round']['claims'][0]['id'])
            claim = choosing['round']['claims'][game.round['false_index']]['id']
            reveal = game.grade(choosing['session_id'], choosing['round']['id'], claim)
            self.assertTrue(reveal['reveal']['correct'])
            self.assertEqual(game.grade(choosing['session_id'], choosing['round']['id'], claim), reveal)
            with self.assertRaises(GameError): game.grade(choosing['session_id'], choosing['round']['id'], choosing['round']['claims'][(game.round['false_index'] + 1) % 3]['id'])
            if n == 2: game.start()
            elif n != 4: game.next(choosing['session_id'], choosing['round']['id'])
        self.assertEqual(ids, [1, 2, 3, 4, 5]); self.assertEqual(game.score, 2); self.assertEqual(game.answered, 2)

    def test_wrong_invalid_claim_and_round(self):
        game = Game(RoundGenerator(FakeModel(), FakeSources())); game.start(); state = settle(game)
        for rid, cid in [('old', 'invalid'), (state['round']['id'], 'invalid')]:
            with self.assertRaises(GameError): game.grade(state['session_id'], rid, cid)
        answer = game.grade(state['session_id'], state['round']['id'], state['round']['claims'][(game.round['false_index'] + 1) % 3]['id'])
        self.assertFalse(answer['reveal']['correct']); self.assertEqual(answer['score'], 0); self.assertEqual(answer['answered'], 1)

    def test_reset_late_completion_busy_and_failure_recovery(self):
        entered, release = threading.Event(), threading.Event()
        class Blocked:
            calls = 0
            def generate(self):
                self.calls += 1; entered.set(); release.wait(2)
                raise PreparationError('Fixture failure. Retry.')
        adapter = Blocked(); game = Game(adapter)
        old = game.start(); self.assertTrue(entered.wait(1))
        with self.assertRaises(GameError): game.next(old['session_id'], None)
        newer = game.start(); self.assertNotEqual(newer['session_id'], old['session_id']); self.assertEqual(adapter.calls, 1)
        release.set(); state = settle(game)
        self.assertEqual(state['status'], 'idle'); self.assertIsNone(game.round)
        game.generator = RoundGenerator(FakeModel(), FakeSources())
        game.next(newer['session_id'], None); self.assertEqual(settle(game)['status'], 'choosing')
        game.generator = adapter; game.start(); self.assertEqual(settle(game)['status'], 'error')
        game.generator = RoundGenerator(FakeModel(), FakeSources()); game.next(game.session, None)
        self.assertEqual(settle(game)['status'], 'choosing')


class HandlerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = LocalServer(0, RoundGenerator(FakeModel(), FakeSources()))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True); cls.thread.start()
        cls.port = cls.server.server_port
        cls.origin = f'http://127.0.0.1:{cls.port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(2)

    def request(self, path, method='GET', body=None, headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.port, timeout=3)
        raw = json.dumps(body) if body is not None else None
        supplied = {'Origin': self.origin, 'X-GhostProof-Token': self.server.token, 'Content-Type': 'application/json'} if method == 'POST' else {}
        supplied.update(headers or {})
        connection.request(method, path, raw, supplied)
        response = connection.getresponse(); result = (response.status, response.read(), dict(response.getheaders())); connection.close()
        return result

    def raw(self, request):
        with socket.create_connection(('127.0.0.1', self.port), timeout=3) as client:
            client.sendall(request.encode()); client.shutdown(socket.SHUT_WR)
            chunks = []
            while True:
                chunk = client.recv(4096)
                if not chunk: break
                chunks.append(chunk)
            return b''.join(chunks)

    def test_exact_assets_and_headers(self):
        self.assertEqual(self.server.server_address[0], '127.0.0.1')
        for path, (name, _) in ASSETS.items():
            status, raw, headers = self.request(path)
            self.assertEqual(status, 200); self.assertEqual(raw, (Path(__file__).parents[1] / 'local' / name).read_bytes())
            self.assertEqual(headers['Cache-Control'], 'no-store'); self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
            self.assertIn("frame-ancestors 'none'", headers['Content-Security-Policy']); self.assertNotIn('Access-Control-Allow-Origin', headers)
        for path in ('/.git/config', '/.env', '/local/server.py', '/reference/local-preparation/server.py', '/../README.md', '/%2e%2e/README.md', '/data/sources.json', '/?x=1', '/app.js/extra'):
            self.assertEqual(self.request(path)[0], 404)

    def test_health_and_valid_mutation(self):
        status, raw, _ = self.request('/api/health'); health = json.loads(raw)
        self.assertEqual(status, 200); self.assertEqual(health['token'], self.server.token); self.assertTrue(health['ready'])
        self.assertEqual(self.request('/api/start', 'POST', {})[0], 200); state = settle(self.server.game)
        status, raw, _ = self.request('/api/grade', 'POST', {'session_id': state['session_id'], 'round_id': state['round']['id'], 'claim_id': state['round']['claims'][0]['id']})
        self.assertEqual(status, 200); self.assertIn('reveal', json.loads(raw))

    def test_origin_host_token_metadata_and_type_rejections(self):
        for headers, expected in [({'Host': 'evil.test'}, 403), ({'Origin': 'null'}, 403), ({'Origin': 'https://evil.test'}, 403),
            ({'Origin': ''}, 403), ({'X-GhostProof-Token': ''}, 403), ({'X-GhostProof-Token': 'wrong'}, 403),
            ({'Sec-Fetch-Site': 'cross-site'}, 403), ({'Sec-Fetch-Site': 'same-site'}, 403), ({'Content-Type': 'text/plain'}, 415),
            ({'Content-Type': 'application/json; charset=utf-8'}, 415)]:
            with self.subTest(headers=headers): self.assertEqual(self.request('/api/start', 'POST', {}, headers)[0], expected)
        for path in ('/', '/api/health', '/api/state'):
            self.assertEqual(self.request(path, headers={'Sec-Fetch-Site': 'cross-site'})[0], 403)
            self.assertEqual(self.request(path, headers={'Origin': 'null'})[0], 403)

    def test_duplicate_headers_framing_missing_host_and_json_fields(self):
        common = f'Host: 127.0.0.1:{self.port}\r\nOrigin: {self.origin}\r\nX-GhostProof-Token: {self.server.token}\r\nContent-Type: application/json\r\n'
        for duplicate in (f'Host: 127.0.0.1:{self.port}\r\n', f'Origin: {self.origin}\r\n', f'X-GhostProof-Token: {self.server.token}\r\n', 'Content-Type: application/json\r\n', 'Content-Length: 2\r\n', 'Transfer-Encoding: chunked\r\n'):
            result = self.raw('POST /api/start HTTP/1.1\r\n' + common + duplicate + 'Content-Length: 2\r\n\r\n{}')
            self.assertNotIn(b' 200 ', result.split(b'\r\n')[0])
        self.assertIn(b' 403 ', self.raw('GET /api/health HTTP/1.0\r\n\r\n').split(b'\r\n')[0])
        for missing in (f'Origin: {self.origin}\r\n', f'X-GhostProof-Token: {self.server.token}\r\n'):
            self.assertIn(b' 403 ', self.raw('POST /api/start HTTP/1.1\r\n' + common.replace(missing, '') + 'Content-Length: 2\r\n\r\n{}').split(b'\r\n')[0])
        for body, length in [('{}', '3000'), ('{bad}', '5'), ('{"x":1,"x":2}', '13')]:
            result = self.raw('POST /api/start HTTP/1.1\r\n' + common + f'Content-Length: {length}\r\n\r\n' + body)
            self.assertNotIn(b' 200 ', result.split(b'\r\n')[0])
        self.assertEqual(self.request('/api/start', 'POST', {'extra': 1})[0], 400)
        self.assertEqual(self.request('/unknown', 'POST', {})[0], 404)
        for method in ('PUT', 'DELETE', 'OPTIONS', 'PATCH'):
            self.assertEqual(self.request('/api/start', method)[0], 405)

    def test_missing_model_health_is_safe_and_recoverable(self):
        original = self.server.game.generator
        class Missing:
            model = FakeModel()
            def ready(self): raise PreparationError('Ollama unavailable. Start Ollama, then retry.')
        self.server.game.generator = Missing()
        try:
            status, raw, _ = self.request('/api/health')
            self.assertEqual(status, 200); self.assertFalse(json.loads(raw)['ready']); self.assertIn('Start Ollama', json.loads(raw)['error'])
        finally: self.server.game.generator = original


if __name__ == '__main__': unittest.main()
