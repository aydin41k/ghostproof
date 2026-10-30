// Actual client module + DOM test double. Real browser QA is recorded separately.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createClient } from '../demo/app.js';
const content = JSON.parse(await readFile(new URL('../demo/content.json', import.meta.url)));

class Element {
  constructor(tag = 'div') { this.tagName = tag; this.children = []; this.dataset = {}; this.listeners = {}; this.textContent = ''; this.style = { setProperty() {} }; this.classList = { toggle() {}, remove() {} }; }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children = nodes; }
  addEventListener(name, action) { this.listeners[name] = action; }
  focus() { this.focused = true; }
  async fire(name = 'click') { await this.listeners[name]?.(); }
}
function dom() { const ids = new Map(); return { ids, body: new Element('body'), getElementById(id) { if (!ids.has(id)) ids.set(id, new Element()); return ids.get(id); }, createElement(tag) { return new Element(tag); } }; }
function all(element) { return [element, ...element.children.flatMap(all)]; }
function choose(document, correct) {
  const title = document.getElementById('round-title').textContent;
  const topic = content.topics.find(t => t.topic === title);
  const wanted = topic.claims.find(c => c.is_false === correct).text;
  const card = document.getElementById('posts').children.find(c => all(c).some(n => n.textContent === wanted));
  return { topic, input: all(card).find(n => n.tagName === 'input') };
}

for (const correct of [true, false]) {
  test(`actual sprite ${correct ? 'correct' : 'wrong'} render preserves paired feedback, evidence, locking and reset`, async () => {
    const document = dom(); let loads = 0; const app = createClient(document, async () => { loads++; return content; });
    await app.start();
    for (let round = 0; round < 3; round++) {
      const { topic, input } = choose(document, correct); const get = id => document.getElementById(id);
      assert.equal(all(get('posts')).some(n => n.tagName === 'blockquote'), false);
      await input.fire('change'); await get('lock').fire();
      assert.equal(get('next').hidden, false); assert.ok(all(get('posts')).filter(n => n.tagName === 'input').every(n => n.disabled));
      const fake = topic.claims.find(c => c.is_false);
      const pair = `The fabricated claim: “${fake.text}” Correction: ${fake.correction}`;
      assert.equal(get('feedback-copy').textContent, pair);
      assert.equal(get('status').textContent, `${correct ? 'Correct.' : 'Not this time.'} ${pair}`);
      assert.equal(get('feedback-title').focused, true);
      for (const claim of topic.claims) {
        const quotes = all(get('posts')).filter(n => n.tagName === 'blockquote').map(n => n.textContent);
        assert.ok(quotes.includes(claim.evidence.quote)); assert.ok(quotes.includes(claim.evidence.editorial_context.text));
      }
      for (const link of all(get('posts')).filter(n => n.tagName === 'a')) {
        assert.ok(link.href.startsWith('https://')); assert.equal(link.rel, 'noopener noreferrer');
      }
      await get('next').fire();
    }
    assert.equal(document.getElementById('final-score').textContent, correct ? '3 / 3' : '0 / 3');
    await document.getElementById('replay').fire();
    assert.equal(document.getElementById('progress').textContent, 'ROUND 1 / 3');
    assert.equal(document.getElementById('score').textContent, '0 / 0 CORRECT');
    assert.equal(loads, 1); assert.equal(document.getElementById('world').dataset.level, '3');
  });
}

test('late content completion cannot replace a newer hunt or cancellation', async () => {
  const document = dom(); const resolvers = []; const app = createClient(document, () => new Promise(resolve => resolvers.push(resolve)));
  const old = app.start(); const newer = app.start(); resolvers[1](content); await newer;
  const title = document.getElementById('round-title').textContent;
  await choose(document, true).input.fire('change'); await document.getElementById('lock').fire();
  resolvers[0](content); await old;
  assert.equal(document.getElementById('round-title').textContent, title); assert.equal(document.getElementById('feedback').hidden, false);
  const another = dom(); let finish; const pending = createClient(another, () => new Promise(resolve => { finish = resolve; })).start();
  await another.getElementById('cancel').fire(); finish(content); await pending;
  assert.equal(another.getElementById('intro').hidden, false); assert.equal(another.getElementById('game').hidden, true);
});

test('honest loading errors recover via fresh hunt, with no invented fallback', async () => {
  const document = dom(); let attempts = 0;
  const app = createClient(document, async () => { if (++attempts === 1) throw new Error('Missing verified content'); return content; });
  await app.start(); assert.equal(document.getElementById('error').hidden, false);
  assert.equal(document.getElementById('error-copy').textContent, 'Missing verified content');
  await document.getElementById('fresh').fire(); assert.equal(document.getElementById('game').hidden, false); assert.equal(attempts, 2);
});

test('renderer has no HTML injection, transport calls, storage or analytics', async () => {
  const code = await readFile(new URL('../demo/app.js', import.meta.url), 'utf8');
  assert.doesNotMatch(code, /innerHTML|outerHTML|insertAdjacentHTML|\/api\/|fetch\(|localStorage|sessionStorage|sendBeacon/);
});
