import { createGame, loadContent } from './game.js';

export function createClient(document, load = loadContent) {
  const $ = id => document.getElementById(id);
  let current = null, selected = null, epoch = 0, pending = false, game = null, content = null;
  const stages = ['intro', 'loading', 'game', 'error', 'results'];
  function show(stage) { stages.forEach(id => { $(id).hidden = id !== stage; }); }
  function say(text) { $('status').textContent = text; }
  function node(tag, text, cls) { const n = document.createElement(tag); if (text) n.textContent = text; if (cls) n.className = cls; return n; }
  function link(source) { const a = node('a', `${source.publisher}: ${source.title}`); a.href = source.url; a.target = '_blank'; a.rel = 'noopener noreferrer'; return a; }
  const challenges = { church: '“Old walls, twisted stories. Find the one I changed.”', ufo: '“A strange light, three stories. Which one did I twist?”', storm: '“The storm hides my tale. Catch the story I changed.”' };
  function story(data) {
    const level = data.story.haunting_level, world = $('world');
    const correct = data.reveal?.claims.find(item => item.id === data.reveal.selected)?.is_false;
    const outcome = data.phase === 'results' && level === 0 ? 'banished' : data.reveal ? (correct ? 'weakened' : 'grows') : 'none';
    world.dataset.level = String(level); world.dataset.outcome = outcome;
    world.dataset.scene = data.round?.scene || (data.phase === 'results' ? 'threshold' : world.dataset.scene);
    world.style.setProperty('--ghost-scale', String(.62 + level * .12));
    world.style.setProperty('--spectral-strength', String(level / 6));
    $('haunting-state').textContent = `${outcome === 'banished' ? 'Ghost banished. ' : outcome === 'weakened' ? 'Haunting weakened · scene cleared. ' : outcome === 'grows' ? 'Haunting grows · scene still haunted. ' : ''}Haunting: ${level} / 6 · ${data.story.cleared} scenes cleared`;
    $('ghost-dialogue').textContent = data.phase === 'results' ? (level === 0 ? '“No lies left to hide behind… you have banished me.”' : `“${level} sparks of haunting remain. Dare to try again?”`) : data.reveal ? (correct ? '“You caught my lie! This room slips from my grasp.”' : '“You believed me. Another wisp joins my haunting.”') : challenges[data.round?.scene] || '“Three rooms await. I have hidden one false story in each.”';
  }
  function error(message) { document.body.classList.remove('revealed'); show('error'); $('error-copy').textContent = message; $('error-title').focus(); say(message); }
  function render(data) {
    const oldPhase = current?.phase; const oldRound = current?.round?.id;
    current = data; pending = false;
    story(data);
    document.body.classList.toggle('revealed', data.phase === 'revealed');
    if (data.phase === 'results') {
      show('results'); $('final-score').textContent = `${data.score} / 3`;
      $('takeaway').textContent = data.score === 3 ? 'Every scene cleared. The ghost is banished. Keep checking real-world stories against their sources.' : `${data.score} scenes cleared; ${data.story.missed} still haunted. The ghost remains — replay to challenge its lies again.`;
      $('result-title').focus(); say(`Hunt complete. ${data.score} of 3 correct.`); return;
    }
    if (!['choosing', 'revealed'].includes(data.phase)) return;
    show('game'); $('progress').textContent = `ROUND ${data.number} / 3`; $('score').textContent = `${data.score} / ${data.answered} CORRECT`;
    $('round-title').textContent = data.round.topic;
    $('round-scope').textContent = data.round.scope;
    if (oldRound !== data.round.id || oldPhase !== data.phase) {
      selected = data.reveal?.selected || null; $('posts').replaceChildren();
      data.round.claims.forEach((claim, index) => {
        const label = node('label', '', 'post'); label.dataset.id = claim.id;
        const top = node('span', '', 'post-top'), input = node('input'); input.type = 'radio'; input.name = 'claim'; input.value = claim.id; input.checked = selected === claim.id; input.disabled = data.phase === 'revealed';
        input.addEventListener('change', () => { if (current.phase !== 'choosing' || pending) return; selected = claim.id; $('lock').disabled = false; });
        top.append(input, node('span', `CLAIM 0${index + 1}`)); label.append(top, node('span', claim.text, 'claim'));
        if (data.reveal) {
          const evidence = data.reveal.claims.find(item => item.id === claim.id), source = data.round.sources.find(item => item.id === evidence.source_id);
          label.append(node('span', `${evidence.is_false ? 'FALSE' : 'SUPPORTED'}${selected === claim.id ? ' · YOUR PICK' : ''}`, 'truth'), node('span', evidence.explanation, 'explanation'));
          if (evidence.correction) label.append(node('span', `Correction: ${evidence.correction}`, 'explanation'));
          const citation = node('span', '', 'source'); citation.append(link(source)); label.append(citation);
          const record = evidence.evidence;
          const structured = node('div', '', 'article-evidence');
          structured.append(node('p', `Exact ${source.publisher} article excerpt`), node('blockquote', record.quote),
            node('p', `Source saved ${source.retrieved_at.slice(0, 10)} (UTC). ${record.review}`));
          if (record.editorial_context) structured.append(node('p', `Editorial context — exact containing ${source.publisher} passage`), node('blockquote', record.editorial_context.text));
          label.append(structured);
        }
        $('posts').append(label);
      });
      $('clue').open = false; $('clue-content').replaceChildren(node('p', data.round.clue));
      data.round.sources.forEach(source => { const p = node('p'); p.append(link(source)); $('clue-content').append(p, node('p', `Source saved ${source.retrieved_at.slice(0, 10)} (UTC), not a publication date. Local-Gemma rounds prepared ${data.round.prepared_at.slice(0, 10)} (UTC) · ${data.round.pool_size} curator-selected topics · cached and remixed for instant play. Opening the source is an optional free clue; its current article may differ from the saved copy.`)); });
    }
    $('lock').hidden = data.phase !== 'choosing'; $('lock').disabled = !selected; $('next').hidden = data.phase !== 'revealed'; $('next').textContent = data.number === 3 ? 'See my result' : 'Summon next round';
    $('feedback').hidden = data.phase !== 'revealed';
    if (data.reveal) {
      const pick = data.reveal.claims.find(item => item.id === data.reveal.selected); const fake = data.reveal.claims.find(item => item.is_false);
      $('feedback-title').textContent = pick.is_false ? 'Haunting weakened. Scene cleared.' : 'Haunting grows. The ghost fooled you.';
      const pairedCorrection = `The fabricated claim: “${fake.text}” Correction: ${fake.correction}`;
      $('feedback-copy').textContent = pairedCorrection;
      $('feedback-title').focus(); say(`${pick.is_false ? 'Correct.' : 'Not this time.'} ${pairedCorrection}`);
    } else { $('round-title').focus(); say(`Round ${data.number}. Three claims ready. Find the fabricated one.`); }
  }
  async function act(action, body) {
    if (pending && action !== 'start') return; pending = true; const token = ++epoch;
    $('lock').disabled = true;
    try {
      let data;
      if (action === 'start') {
        show('loading'); $('loading-title').focus(); say('Loading the reviewed static content.');
        const loaded = content || await load();
        if (token !== epoch) return;
        content = loaded;
        if (!game) game = createGame(content);
        current = null; data = game.start();
      } else { data = game[action](body); }
      if (token === epoch) render(data);
    }
    catch (failure) { if (token === epoch) { pending = false; error(failure.message); } }
  }
  const start = () => { selected = null; $('world').dataset.scene = 'threshold'; return act('start', {}); };
  $('start').addEventListener('click', start); $('replay').addEventListener('click', start); $('fresh').addEventListener('click', start);
  $('retry').addEventListener('click', start);
  $('cancel').addEventListener('click', () => { ++epoch; pending = false; show('intro'); $('start').focus(); say('Content loading cancelled. Start a fresh hunt when ready.'); });
  $('lock').addEventListener('click', () => { if (current?.phase === 'choosing' && selected) return act('grade', { session: current.session, round_id: current.round.id, claim_id: selected }); });
  $('next').addEventListener('click', () => { if (current?.phase === 'revealed') return act('next', { session: current.session }); });
  return { start };
}

if (typeof document !== 'undefined') createClient(document);
