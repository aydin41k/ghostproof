// The browser receives choosing claims only; evidence arrives after server grading.
export function createClient(document, transport, wait = ms => new Promise(resolve => setTimeout(resolve, ms))) {
  const get = id => document.getElementById(id);
  let token = null, state = null, selected = null, epoch = 0, pending = false;
  const request = async (path, body) => {
    const response = await transport(path, body === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-GhostProof-Token': token }, body: JSON.stringify(body) });
    const packet = await response.json();
    if (!response.ok) throw new Error(packet.error || 'Local request failed. Please retry.');
    return packet;
  };
  function node(tag, text) { const result = document.createElement(tag); if (text !== undefined) result.textContent = text; return result; }
  function render(packet) {
    state = packet; selected = null;
    get('intro').hidden = !!packet.session_id;
    get('game').hidden = !packet.session_id;
    get('progress').textContent = packet.round ? `ROOM ${packet.answered + (packet.reveal ? 0 : 1)}` : 'PREPARING A FRESH ROOM';
    get('score').textContent = `${packet.score} / ${packet.answered} CORRECT`;
    document.body.style.setProperty('--level', String(Math.max(0, Math.min(6, 3 + packet.answered - 2 * packet.score))));
    get('round-title').textContent = packet.round?.topic || 'Retrieving, drafting and checking…';
    get('cards').replaceChildren(); get('evidence').replaceChildren();
    get('source-details').open = false;
    get('reveal').hidden = !packet.reveal; get('next').hidden = !packet.reveal;
    get('lock').disabled = true; get('lock').hidden = !packet.round || !!packet.reveal;
    get('error').hidden = !packet.error;
    if (packet.error) get('error-copy').textContent = packet.error;
    get('retry').disabled = packet.busy;
    get('status').textContent = packet.busy ? 'Preparing a genuinely fresh source-backed round. Local inference may take a minute; no canned fallback is used.' : packet.error || '';
    for (const claim of packet.round?.claims || []) {
      const label = node('label'); label.className = 'card';
      const input = node('input'); input.type = 'radio'; input.name = 'claim'; input.value = claim.id; input.disabled = !!packet.reveal;
      input.addEventListener('change', () => { if (!pending && !state.reveal) { selected = claim.id; get('lock').disabled = false; } });
      label.append(input, node('span', claim.text));
      if (packet.reveal) { label.dataset.fake = String(claim.id === packet.reveal.fake_id); input.checked = claim.id === packet.reveal.selected_id; }
      get('cards').append(label);
    }
    if (packet.reveal) {
      const reveal = packet.reveal;
      get('feedback-title').textContent = reveal.correct ? 'You caught the fabrication.' : 'The ghost slipped past.';
      get('feedback-copy').textContent = `The fabricated claim: “${reveal.fake_text}” Correction: ${reveal.correction}`;
      get('status').textContent = get('feedback-title').textContent + ' ' + get('feedback-copy').textContent;
      for (const claim of reveal.claims) {
        const section = node('section'); section.className = 'evidence-item';
        section.append(node('h4', claim.text), node('p', claim.id === reveal.fake_id ? 'Directly contradicted by this source:' : 'Supported by this source:'), node('blockquote', claim.quote));
        section.append(node('p', `Containing paragraph ${claim.passage}:`), node('blockquote', reveal.source.passages.find(p => p.id === claim.passage).text));
        get('evidence').append(section);
      }
      get('evidence').append(node('p', 'Correction evidence:'), node('blockquote', reveal.correction_quote), node('blockquote', reveal.source.passages.find(p => p.id === reveal.correction_passage).text));
      const link = node('a', reveal.source.title + ' — NASA ↗'); link.href = reveal.source.url; link.target = '_blank'; link.rel = 'noopener noreferrer'; get('evidence').append(link);
      get('evidence').append(node('p', `Retrieved ${reveal.source.retrieved_at} · Model ${reveal.model} · ${reveal.contract} · ${reveal.review.label}`), node('p', `Canonical prose SHA-256: ${reveal.source.digest}`));
      get('feedback-title').focus();
    } else if (packet.round) get('round-title').focus();
  }
  async function action(path, body) {
    const ticket = ++epoch; pending = true; get('lock').disabled = true; get('next').disabled = true;
    get('error').hidden = true;
    try {
      let packet = await request(path, body);
      if (ticket !== epoch) return;
      render(packet);
      while (packet.busy) {
        await wait(1000); if (ticket !== epoch) return;
        packet = await request('/api/state'); if (ticket !== epoch) return;
        render(packet);
      }
    } catch (error) {
      if (ticket !== epoch) return;
      get('error-copy').textContent = error.message; get('error').hidden = false;
      get('status').textContent = error.message; get('status').focus();
    } finally { if (ticket === epoch) { pending = false; get('next').disabled = false; get('retry').disabled = false; } }
  }
  async function start() {
    const ticket = ++epoch;
    try {
      const health = await request('/api/health'); if (ticket !== epoch) return;
      token = health.token; get('readiness').textContent = health.ready ? `Ready: ${health.model}. Each round retrieves public NASA text.` : health.error;
      if (!health.ready) { get('error-copy').textContent = health.error; get('error').hidden = false; return; }
      await action('/api/start', {});
    } catch (error) { if (ticket === epoch) { get('readiness').textContent = error.message; get('error-copy').textContent = error.message; get('error').hidden = false; } }
  }
  get('start').addEventListener('click', start); get('new').addEventListener('click', start);
  get('next').addEventListener('click', () => pending ? undefined : action('/api/next', { session_id: state.session_id, round_id: state.round?.id || null }));
  get('retry').addEventListener('click', () => state?.session_id && token ? action('/api/next', { session_id: state.session_id, round_id: state.round?.id || null }) : start());
  get('lock').addEventListener('click', () => selected && !pending ? action('/api/grade', { session_id: state.session_id, round_id: state.round.id, claim_id: selected }) : undefined);
  async function check() { try { const health = await request('/api/health'); token = health.token; get('readiness').textContent = health.ready ? `Ready: ${health.model}` : health.error; } catch { get('readiness').textContent = 'Local server unavailable. Start it and reload.'; } }
  return { start, check, render };
}
if (typeof window !== 'undefined') createClient(document, (path, options) => fetch(path, options)).check();
