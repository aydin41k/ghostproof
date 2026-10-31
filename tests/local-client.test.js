// Exercise the actual local browser client using a DOM double, not a duplicate state model.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createClient } from '../local/app.js';

class Element {
  constructor(tag = 'div') { this.tagName = tag; this.children = []; this.dataset = {}; this.listeners = {}; this.textContent = ''; this.style = { setProperty(name, value) { this[name] = value; } }; }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children = nodes; }
  addEventListener(name, callback) { this.listeners[name] = callback; }
  focus() { this.focused = true; }
  async fire(name = 'click') { await this.listeners[name]?.(); }
}
function dom() { const ids = new Map(); return { body: new Element('body'), getElementById(id) { if (!ids.has(id)) ids.set(id, new Element()); return ids.get(id); }, createElement(tag) { return new Element(tag); } }; }
const all = element => [element, ...element.children.flatMap(all)];
const response = (packet, ok = true) => ({ ok, async json() { return packet; } });
function choosing(n = 1, session = 'hunt') {
  return { session_id: session, status: 'choosing', busy: false, error: null, score: n - 1, answered: n - 1,
    round: { id: `round-${n}`, topic: `Ghost source ${n}`, claims: [0, 1, 2].map(i => ({ id: `${n}-${i}`, text: `Source ${n} claim ${i}` })) } };
}
function revealed(state, selected) {
  const source = { id: state.answered + 1, title: state.round.topic, url: 'https://science.nasa.gov/ghost/', retrieved_at: '2026-10-31T00:00:00Z', digest: 'abc123', passages: [{ id: 1, text: 'Full source context with names and qualifiers.' }] };
  return { ...state, status: 'revealed', answered: state.answered + 1, score: state.score + 1,
    reveal: { correct: true, selected_id: selected, fake_id: state.round.claims[0].id, fake_text: state.round.claims[0].text,
      correction: 'The sourced correction.', correction_passage: 1, correction_quote: 'sourced correction',
      source, model: 'gemma4:e4b', contract: 'ghostproof-live-1', generated_at: source.retrieved_at,
      review: { label: 'Separate blinded automated check by the same local model; not human editorial review' },
      claims: state.round.claims.map(c => ({ ...c, passage: 1, quote: 'names and qualifiers' })) } };
}
function backend() {
  const calls = []; let n = 0, session = 0, current;
  return { calls, async fetch(path, options) {
    calls.push([path, options]);
    if (path === '/api/health') return response({ ready: true, token: 'fixture-token', model: 'gemma4:e4b' });
    if (path === '/api/start') { session++; current = choosing(++n, `hunt-${session}`); }
    if (path === '/api/next') current = choosing(++n, `hunt-${session}`);
    if (path === '/api/grade') current = revealed(current, JSON.parse(options.body).claim_id);
    return response(current);
  } };
}

test('five fresh rooms, reveal pairing, source context, keyboard locking and new hunt', async () => {
  const document = dom(), api = backend(), client = createClient(document, api.fetch);
  await client.start();
  for (let n = 1; n <= 5; n++) {
    const get = id => document.getElementById(id);
    assert.equal(get('round-title').textContent, `Ghost source ${n}`);
    assert.equal(get('intro').hidden, true); assert.equal(get('reveal').hidden, true); assert.equal(get('lock').disabled, true);
    assert.equal(all(get('cards')).some(e => e.tagName === 'blockquote'), false);
    assert.equal(get('round-title').focused, true);
    const input = all(get('cards')).find(e => e.tagName === 'input'); await input.fire('change');
    assert.equal(get('lock').disabled, false); await get('lock').fire();
    assert.equal(get('feedback-copy').textContent, `The fabricated claim: “Source ${n} claim 0” Correction: The sourced correction.`);
    assert.equal(get('feedback-title').focused, true); assert.equal(get('next').hidden, false);
    assert.equal(get('source-details').open, false);
    assert.ok(all(get('cards')).filter(e => e.tagName === 'input').every(e => e.disabled));
    assert.ok(all(get('evidence')).some(e => e.textContent === 'Full source context with names and qualifiers.'));
    const link = all(get('evidence')).find(e => e.tagName === 'a'); assert.equal(link.rel, 'noopener noreferrer'); assert.equal(link.target, '_blank');
    if (n === 3) await get('new').fire(); else if (n !== 5) await get('next').fire();
  }
  const mutations = api.calls.filter(([, options]) => options.method === 'POST');
  assert.ok(mutations.every(([, options]) => options.headers['X-GhostProof-Token'] === 'fixture-token'));
  assert.equal(api.calls.filter(([path]) => path === '/api/start').length, 2);
});

test('preparing polling, visible honest failure and explicit retry without fallback', async () => {
  const document = dom(); let attempts = 0, polls = 0;
  const client = createClient(document, async path => {
    if (path === '/api/health') return response({ ready: true, token: 't', model: 'gemma4:e4b' });
    if (path === '/api/start') return response({ ...choosing(), round: undefined, busy: true, status: 'preparing' });
    if (path === '/api/state') { polls++; return response({ ...choosing(), round: undefined, status: 'error', error: 'No suitable source. Retry.', busy: false }); }
    if (path === '/api/next') { attempts++; return response(choosing(4)); }
  }, async () => { assert.equal(document.getElementById('lock').disabled, true); assert.match(document.getElementById('status').textContent, /no canned fallback/); });
  await client.start(); assert.equal(polls, 1); assert.equal(document.getElementById('error').hidden, false);
  assert.equal(document.getElementById('error-copy').textContent, 'No suitable source. Retry.');
  await document.getElementById('retry').fire(); assert.equal(attempts, 1); assert.equal(document.getElementById('round-title').textContent, 'Ghost source 4');
});

test('late responses cannot replace a newer hunt', async () => {
  const document = dom(); const resolvers = []; let starts = 0;
  const client = createClient(document, async path => {
    if (path === '/api/health') return response({ ready: true, model: 'gemma4:e4b', token: 't' });
    if (path === '/api/start') { starts++; return new Promise(resolve => resolvers.push(resolve)); }
  });
  const old = client.start(); await new Promise(resolve => setImmediate(resolve));
  const newer = client.start(); await new Promise(resolve => setImmediate(resolve));
  assert.equal(starts, 2); resolvers[1](response(choosing(5, 'newer'))); await newer;
  resolvers[0](response(choosing(1, 'old'))); await old;
  assert.equal(document.getElementById('round-title').textContent, 'Ghost source 5');
});

test('missing model and transport errors are shown with recovery', async () => {
  const document = dom(); let healthCalls = 0;
  const client = createClient(document, async path => {
    if (path === '/api/health') return response(++healthCalls === 1 ? { ready: false, token: 't', error: 'Install local Gemma.' } : { ready: true, token: 't', model: 'gemma4:e4b' });
    return response({ error: 'One preparation is busy.' }, false);
  });
  await client.start(); assert.equal(document.getElementById('readiness').textContent, 'Install local Gemma.');
  await document.getElementById('retry').fire(); assert.equal(healthCalls, 2); assert.equal(document.getElementById('error-copy').textContent, 'One preparation is busy.');
  assert.equal(document.getElementById('status').focused, true);
});

test('local renderer has no unsafe HTML sinks, storage or direct upstream/browser model calls', async () => {
  const code = await readFile(new URL('../local/app.js', import.meta.url), 'utf8');
  assert.doesNotMatch(code, /innerHTML|outerHTML|insertAdjacentHTML|localStorage|sessionStorage|sendBeacon|https?:\/\//);
  const html = await readFile(new URL('../local/index.html', import.meta.url), 'utf8');
  assert.match(html, /aria-live="polite"/); assert.match(html, /verifyit\.app/); assert.match(html, /chromewebstore\.google\.com/);
  assert.match(html, /<details id="source-details"><summary>Show source evidence<\/summary>/);
});
