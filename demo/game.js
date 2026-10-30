// Public answers are inspectable. This is a local game, not an anti-cheat service.
export const CONTENT_SHA256 = '76d943680f1008b283d31c3dbb5baa3ff8658c88ebe94619dc57a57395447360';
export const MAX_CONTENT_BYTES = 24000;
const PREPARED = '2026-10-29T23:40:55Z';
const REGISTRY = {
  ghosts: ["St Paul's ghost stories", 'church', 'ghost_lore', 'The history behind local ghost stories; this article does not prove a haunting.', 'National Park Service', 'https://www.nps.gov/articles/000/thomas-standard-the-colonial-era-minister-buried-beneath-st-paul-s-church.htm', 'b863af936b34cccdd69cfd2fce686bd55181b388b985e7623594ae19e1284681'],
  sprites: ['Sprites: strange storm lights', 'storm', 'eerie_phenomena', 'An observed atmospheric phenomenon, not a supernatural spirit.', 'NASA', 'https://science.nasa.gov/earth/earth-observatory/sprites-camera-action-153422/', '16babc0972fac6714c41bfd358bb2a479456a367f3d9bc215699db10e9d55cd8'],
  uap: ["UFOs and NASA's UAP study", 'ufo', 'ufo_reports', 'Recorded observations and a specific NASA study; unexplained does not identify an origin.', 'NASA', 'https://science.nasa.gov/uap/faqs/', '3d04111d45d42763eff5a6995add9c56ee1dfd56716113ddacc7c53f1c844b0a'],
};
function require(condition, message = 'The reviewed content is missing or invalid. Reload a verified build.') {
  if (!condition) throw new Error(message);
}
function keys(value, allowed) {
  require(value !== null && typeof value === 'object' && !Array.isArray(value));
  require(Object.keys(value).sort().join('|') === allowed.split(' ').sort().join('|'));
}
function text(value, max = 1500, empty = false) {
  require(typeof value === 'string' && value.length <= max && (empty || value.length > 0));
  require(!/[<>\u0000-\u001f\u007f]|\[INST\]|\[\/INST\]|javascript:|data:text\/html/i.test(value));
}
function date(value) {
  require(typeof value === 'string' && /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$/.test(value));
  require(Number.isFinite(Date.parse(value)) && new Date(value).toISOString().replace('.000Z', 'Z') === value && value <= PREPARED);
}
function hash(value) { require(typeof value === 'string' && /^[0-9a-f]{64}$/.test(value)); }

// Structural checks describe this finite release, not semantic truth.
export function validateContent(content) {
  keys(content, 'schema model contract prepared_at provenance topics');
  require(content.schema === 'ghostproof-public-v1' && content.model === 'gemma4-e4b-local:latest' && content.contract === 'spooky-source-paraphrases-1' && content.prepared_at === PREPARED);
  keys(content.provenance, 'source_hash ledger_hash review_hash');
  Object.values(content.provenance).forEach(hash);
  require(Array.isArray(content.topics) && content.topics.length === 3);
  const ids = new Set(); const claimTexts = new Set();
  for (const topic of content.topics) {
    keys(topic, 'topic scene category scope claims prepared_at pool_size topic_id candidate_hash sources');
    require(Object.hasOwn(REGISTRY, topic.topic_id) && !ids.has(topic.topic_id)); ids.add(topic.topic_id);
    const [title, scene, category, scope, publisher, url, candidate] = REGISTRY[topic.topic_id];
    require(topic.topic === title && topic.scene === scene && topic.category === category && topic.scope === scope && topic.candidate_hash === candidate && topic.prepared_at === PREPARED && topic.pool_size === 3);
    require(Array.isArray(topic.sources) && topic.sources.length === 1);
    const source = topic.sources[0]; keys(source, 'id title publisher url retrieved_at');
    require(source.id === `S-${topic.topic_id}` && source.publisher === publisher && source.url === url);
    text(source.title, 200); date(source.retrieved_at);
    require(Array.isArray(topic.claims) && topic.claims.length === 3);
    require(topic.claims.filter(c => c.is_false === true).length === 1);
    const passages = new Set();
    for (const claim of topic.claims) {
      keys(claim, 'text is_false correction explanation source_id evidence');
      text(claim.text, 140); require(!claimTexts.has(claim.text)); claimTexts.add(claim.text);
      require(typeof claim.is_false === 'boolean' && claim.source_id === source.id);
      text(claim.correction, 140, !claim.is_false); require(claim.is_false || claim.correction === '');
      text(claim.explanation, 650);
      keys(claim.evidence, 'kind quote review editorial_context');
      const evidence = claim.evidence; require(evidence.kind === 'article');
      text(evidence.quote, 650); require(evidence.quote.length >= 20); text(evidence.review, 180);
      keys(evidence.editorial_context, 'text passage_id');
      const context = evidence.editorial_context; text(context.text);
      require(['P1', 'P2', 'P3'].includes(context.passage_id) && !passages.has(context.passage_id)); passages.add(context.passage_id);
      require(context.text.includes(evidence.quote));
    }
  }
  return content;
}

export async function decodeContent(raw, cryptoProvider = globalThis.crypto) {
  require(typeof raw === 'string' && new TextEncoder().encode(raw).length <= MAX_CONTENT_BYTES);
  require(cryptoProvider?.subtle, 'Content verification needs a modern browser on HTTPS or localhost. Use the documented local preview, then reload.');
  const digest = await cryptoProvider.subtle.digest('SHA-256', new TextEncoder().encode(raw));
  const actual = Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('');
  require(actual === CONTENT_SHA256, 'The reviewed content checksum does not match this release. Reload a verified build.');
  return validateContent(JSON.parse(raw));
}

export async function loadContent(fetcher = globalThis.fetch, cryptoProvider = globalThis.crypto) {
  const response = await fetcher(new URL('./content.json', import.meta.url), { cache: 'no-store', credentials: 'omit', redirect: 'error' });
  require(response.ok, 'The reviewed content could not be loaded. Check the static files, then start a fresh hunt.');
  const declared = response.headers?.get('content-length');
  require(declared === null || declared === undefined || (Number.isFinite(Number(declared)) && Number(declared) <= MAX_CONTENT_BYTES));
  // Bound streamed bytes before decoding, including responses without Content-Length.
  require(response.body?.getReader, 'This browser cannot safely load the content. Use a current browser, then reload.');
  const reader = response.body.getReader(); const chunks = []; let size = 0;
  try {
    for (;;) {
      const { done, value } = await reader.read(); if (done) break;
      size += value.byteLength; require(size <= MAX_CONTENT_BYTES); chunks.push(value);
    }
  } catch (failure) { await reader.cancel(); throw failure; }
  const bytes = new Uint8Array(size); let offset = 0;
  chunks.forEach(chunk => { bytes.set(chunk, offset); offset += chunk.byteLength; });
  return decodeContent(new TextDecoder('utf-8', { fatal: true }).decode(bytes), cryptoProvider);
}

export function createGame(content, { random = Math.random, makeId } = {}) {
  validateContent(content);
  const canonical = structuredClone(content); let serial = 0;
  const id = makeId || (() => `local-${++serial}`); const issued = new Set();
  const nextId = () => { const value = id(); require(typeof value === 'string' && value && !issued.has(value), 'Duplicate game identifier. Start a fresh hunt.'); issued.add(value); return value; };
  function shuffle(items) {
    const copy = structuredClone(items);
    for (let i = copy.length - 1; i > 0; i--) {
      const draw = random(); require(Number.isFinite(draw) && draw >= 0 && draw < 1, 'Invalid shuffle source.');
      const j = Math.floor(draw * (i + 1)); [copy[i], copy[j]] = [copy[j], copy[i]];
    }
    return copy;
  }
  let session, rounds, index, phase;
  function status() {
    require(session, 'Start a fresh hunt.');
    const answered = rounds.filter(r => r.selected !== null).length;
    const score = rounds.filter(r => r.claims.some(c => c.id === r.selected && c.is_false)).length;
    const result = { session, phase, number: index + 1, score, answered, busy: false, story: { haunting_level: 3 + answered - 2 * score, cleared: score, missed: answered - score } };
    if (phase !== 'results') {
      const packet = rounds[index];
      result.round = { ...Object.fromEntries(['id', 'topic', 'scene', 'category', 'scope', 'pool_size', 'prepared_at', 'sources'].map(key => [key, packet[key]])), claims: packet.claims.map(({ id, text }) => ({ id, text })), clue: 'Two claims match the source article; one directly conflicts with it. Read carefully: a missing detail alone does not make a claim false.' };
      if (phase === 'revealed') result.reveal = { selected: packet.selected, claims: packet.claims };
    }
    return structuredClone(result);
  }
  return {
    start() {
      session = nextId(); index = 0; phase = 'choosing';
      rounds = shuffle(canonical.topics).map(topic => ({ ...topic, id: nextId(), claims: shuffle(topic.claims).map(claim => ({ ...claim, id: nextId() })), selected: null }));
      return status();
    },
    status,
    grade({ session: sid, round_id, claim_id }) {
      require(session && sid === session, 'That hunt is no longer current.');
      require(['choosing', 'revealed'].includes(phase), 'There is no current round to grade.');
      const packet = rounds[index]; require(packet.id === round_id, 'That round is no longer current.');
      require(packet.claims.some(c => c.id === claim_id), 'Choose one of the current claims.');
      require(packet.selected === null || packet.selected === claim_id, 'This answer is already locked.');
      packet.selected = claim_id; phase = 'revealed'; return status();
    },
    next({ session: sid }) {
      require(session && sid === session, 'That hunt is no longer current.');
      require(phase === 'revealed', 'Answer the current round before continuing.');
      if (index === 2) phase = 'results'; else { index++; phase = 'choosing'; }
      return status();
    },
  };
}
