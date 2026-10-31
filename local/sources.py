"""Bounded public NASA article discovery; no caller-controlled destinations."""
import hashlib
import http.client
from html.parser import HTMLParser
import json
import re
import socket
import time
from urllib.parse import urlencode, urlsplit


class PreparationError(ValueError):
    """A safe, actionable preparation failure suitable for the local UI."""


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise PreparationError('Duplicate JSON fields were rejected.')
            result[key] = value
        return result
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, TypeError, UnicodeError) as exc:
        raise PreparationError('Invalid structured response. Please retry.') from exc


def request_json(origin, path, deadline, payload=None, max_bytes=800_000, socket_wait=25):
    """Direct transport: no proxies, redirects, cookies, or decompression."""
    url = urlsplit(origin)
    connection_type = http.client.HTTPSConnection if url.scheme == 'https' else http.client.HTTPConnection
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise PreparationError('Preparation timed out. You can retry.')
    connection = connection_type(url.hostname, url.port, timeout=min(remaining, socket_wait))
    try:
        body = None if payload is None else json.dumps(payload).encode()
        headers = {'Accept': 'application/json', 'Accept-Encoding': 'identity', 'User-Agent': 'GhostProof-local/1.0'}
        if body is not None:
            headers['Content-Type'] = 'application/json'
        connection.request('GET' if body is None else 'POST', path, body, headers)
        if connection.sock:
            connection.sock.settimeout(max(0.1, min(deadline - time.monotonic(), socket_wait)))
        response = connection.getresponse()
        if response.status != 200:
            raise PreparationError(f'Upstream returned HTTP {response.status}. Check connectivity or retry another subject.')
        if response.getheader('Content-Encoding', 'identity').lower() != 'identity':
            raise PreparationError('Compressed upstream responses are not accepted.')
        if response.getheader('Content-Type', '').split(';')[0].strip().lower() != 'application/json':
            raise PreparationError('The source or local model returned an unexpected content type.')
        length = response.getheader('Content-Length')
        if length is not None and (not length.isdigit() or int(length) > max_bytes):
            raise PreparationError('The upstream response exceeded its size budget.')
        chunks, size = [], 0
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise PreparationError('Preparation timed out. You can retry.')
            response_socket = connection.sock or getattr(getattr(response.fp, 'raw', None), '_sock', None)
            if response_socket:
                response_socket.settimeout(min(remaining, socket_wait))
            chunk = response.read1(min(16_384, max_bytes + 1 - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
            if size > max_bytes:
                raise PreparationError('The upstream response exceeded its size budget.')
        return strict_json(b''.join(chunks).decode('utf-8'))
    except (OSError, socket.timeout, http.client.HTTPException, UnicodeError) as exc:
        raise PreparationError('Source retrieval or local inference failed or timed out. Check Ollama and internet access, then retry.') from exc
    finally:
        connection.close()


def canonical_url(value):
    if not isinstance(value, str):
        raise PreparationError('Invalid NASA attribution.')
    url = urlsplit(value)
    if url.scheme != 'https' or url.netloc != 'science.nasa.gov' or url.username or url.password or url.query or url.fragment or not url.path.startswith('/'):
        raise PreparationError('Invalid NASA attribution.')
    return value


class ProseParser(HTMLParser):
    OMIT = {'script', 'style', 'nav', 'form', 'figure', 'iframe', 'audio', 'video', 'footer', 'header', 'button', 'noscript'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.suppressed = 0
        self.depth = 0
        self.parts = []
        self.paragraphs = []

    def handle_starttag(self, tag, attrs):
        if tag in self.OMIT:
            self.suppressed += 1
        if tag == 'p' and not self.suppressed:
            self.depth += 1
            self.parts = []
        if tag == 'br' and self.depth and not self.suppressed:
            self.parts.append(' ')

    def handle_endtag(self, tag):
        if tag == 'p' and self.depth and not self.suppressed:
            text = re.sub(r'\s+', ' ', ''.join(self.parts)).strip()
            text = re.sub(r'^Explanation:\s*', '', text)
            boilerplate = ('Discover the cosmos!', 'Each day a different image or photograph', 'Astronomy Picture of the Day', 'Authors & editors:', 'NASA Official:', 'Specific rights apply.')
            if len(text) >= 80 and not text.endswith(('…', '...')) and not any(value in text for value in boilerplate):
                self.paragraphs.append(text)
            self.depth -= 1
            self.parts = []
        if tag in self.OMIT and self.suppressed:
            self.suppressed -= 1

    def handle_data(self, text):
        if self.depth and not self.suppressed:
            self.parts.append(text)


def extract_prose(html):
    if not isinstance(html, str) or len(html.encode('utf-8')) > 600_000:
        raise PreparationError('Article HTML exceeded the evidence budget.')
    parser = ProseParser()
    parser.feed(html)
    paragraphs, length = [], 0
    for text in parser.paragraphs:
        if len(text) > 6_000:
            continue
        if length + len(text) > 6_000 or len(paragraphs) >= 8:
            break
        paragraphs.append(text)
        length += len(text)
    if length < 160:
        raise PreparationError('The discovered article has too little usable prose.')
    return paragraphs


def fingerprint(text):
    return hashlib.sha256(re.sub(r'\W+', ' ', text.lower()).strip().encode()).hexdigest()


class NasaSources:
    ORIGIN = 'https://science.nasa.gov'
    # image-article is the observed content endpoint, not an arbitrary WP subtype.
    TYPES = {'image-article': 'image-article', 'post': 'posts', 'topic': 'topic'}

    def __init__(self, transport=request_json):
        self.transport = transport
        self.pages = {}

    def discover(self, query, excluded, deadline):
        page = self.pages.get(query, 0) + 1
        self.pages[query] = page
        try:
            results = self.transport(self.ORIGIN, '/wp-json/wp/v2/search?' + urlencode({'search': query, 'per_page': 12, 'page': page}), deadline)
        except PreparationError as exc:
            if page > 1 and 'HTTP 400.' in str(exc):
                return []  # WordPress uses 400 for pages beyond available search results.
            raise PreparationError('NASA discovery: ' + str(exc)) from exc
        if not isinstance(results, list) or len(results) > 12:
            raise PreparationError('NASA discovery returned invalid results.')
        candidates = []
        for item in results:
            if not isinstance(item, dict) or type(item.get('id')) is not int or item['id'] <= 0 or item.get('subtype') not in self.TYPES:
                continue
            if item['id'] in excluded:
                continue
            canonical_url(item.get('url'))
            candidates.append({'id': item['id'], 'type': item['subtype'], 'url': item['url']})
        # Article prose usually offers a narrower factual scope than topic landing pages.
        return sorted(candidates, key=lambda item: item['type'] == 'topic')

    def retrieve(self, candidate, deadline):
        subtype = candidate.get('type')
        identifier = candidate.get('id')
        if subtype not in self.TYPES or type(identifier) is not int or identifier <= 0:
            raise PreparationError('Invalid discovery identity.')
        try:
            article = self.transport(self.ORIGIN, f'/wp-json/wp/v2/{self.TYPES[subtype]}/{identifier}', deadline)
        except PreparationError as exc:
            raise PreparationError('NASA article retrieval: ' + str(exc)) from exc
        if not isinstance(article, dict) or type(article.get('id')) is not int or article.get('id') != identifier or article.get('type') != subtype or canonical_url(article.get('link')) != candidate['url']:
            raise PreparationError('NASA article identity did not match discovery.')
        content = article.get('content')
        title = article.get('title')
        if not isinstance(content, dict) or not isinstance(title, dict) or not isinstance(title.get('rendered'), str):
            raise PreparationError('NASA article metadata was incomplete.')
        paragraphs = extract_prose(content.get('rendered'))
        # Strip title markup without retaining article HTML.
        title_text = re.sub('<[^>]+>', '', title['rendered'])[:180]
        from html import unescape
        text = '\n\n'.join(paragraphs)
        return {'id': identifier, 'type': subtype, 'url': candidate['url'], 'title': unescape(title_text),
                'retrieved_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'digest': hashlib.sha256(text.encode()).hexdigest(),
                'passages': [{'id': i + 1, 'text': value} for i, value in enumerate(paragraphs)]}
