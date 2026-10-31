"""Offline tests across the production model/source/generator interfaces."""
import copy
import http.client
import json
import time
import unittest
from unittest.mock import patch

from local.generation import (OllamaModel, RoundGenerator, TOPIC_SCHEMA, DRAFT_SCHEMA, PROPOSAL_SCHEMA,
                              loopback_origin, validate_draft, validate_review)
from local.sources import (NasaSources, PreparationError, canonical_url, extract_prose,
                           fingerprint, request_json, strict_json)


def article(identifier=1):
    text = f'Cloud {identifier} lies in the constellation Cepheus. Cloud {identifier} contains oxygen. Cloud {identifier} lies 500 light-years from Earth. Astronomers describe its ghostly shape as a natural gas formation, not a supernatural apparition.'
    return {'id': identifier, 'type': 'image-article', 'url': f'https://science.nasa.gov/test-{identifier}/',
            'title': f'Ghost Cloud {identifier}', 'retrieved_at': '2026-10-31T00:00:00Z', 'digest': fingerprint(text),
            'passages': [{'id': 1, 'text': text}]}


def draft(source):
    n = source['id']
    return {'topic': f'Ghost Cloud {n}', 'claims': [
        {'text': f'Cloud {n} lies in the constellation Orion.', 'passage': 1, 'quote': f'Cloud {n} lies in the constellation Cepheus.'},
        {'text': f'Cloud {n} contains oxygen.', 'passage': 1, 'quote': f'Cloud {n} contains oxygen'},
        {'text': f'Cloud {n} lies 500 light-years from Earth.', 'passage': 1, 'quote': f'Cloud {n} lies 500 light-years from Earth.'}],
        'false_index': 0, 'correction': f'Cloud {n} lies in the constellation Cepheus.', 'correction_passage': 1, 'correction_quote': f'Cloud {n} lies in the constellation Cepheus.', 'source_value': 'Cepheus', 'fake_value': 'Orion'}


REVIEW = {'classifications': ['contradicted', 'supported', 'supported'], 'correction_supported': True, 'scope_preserved': True, 'distinct': True}


class FakeModel:
    name = 'gemma-fixture:local'
    def __init__(self):
        self.calls = []
        self.bad = None

    def ready(self, deadline=None):
        return {'model': self.name, 'ready': True}

    def complete(self, instruction, data, schema, deadline, tokens=1100):
        self.calls.append((schema, copy.deepcopy(data), deadline))
        if schema == TOPIC_SCHEMA:
            return {'query': 'ghost'}
        if schema == PROPOSAL_SCHEMA:
            n = int(data['title'].split()[-1])
            value = {'fact_a_text': f'Cloud {n} contains oxygen.', 'fact_a_sentence_id': 2,
                     'fact_b_text': f'Cloud {n} lies 500 light-years from Earth.', 'fact_b_sentence_id': 3,
                     'mutation_sentence_id': 1, 'source_value': 'Cepheus', 'fake_value': 'Orion'}
            if self.bad:
                self.bad(value)
            return value
        return {**copy.deepcopy(REVIEW), 'classifications': ['contradicted' if 'constellation Orion' in text else 'supported' for text in data['claims']]}


class FakeSources:
    def __init__(self):
        self.searches = []
        self.retrieved = []

    def discover(self, query, excluded, deadline):
        self.searches.append((query, set(excluded), deadline))
        return [{'id': n, 'type': 'image-article', 'url': article(n)['url']} for n in range(1, 30) if n not in excluded][:12]

    def retrieve(self, candidate, deadline):
        self.retrieved.append(candidate['id'])
        return article(candidate['id'])


class GenerationTests(unittest.TestCase):
    def test_six_planner_value_escapes_rejected_before_permissive_review(self):
        from local.generation import build_draft
        cases = [('The nebula is not in the constellation Orion.', 'Orion', 'Cepheus'),
            ('If the nebula lies in the constellation Orion, a telescope is useful.', 'Orion', 'Cepheus'),
            ('The nebula is 50–100 light-years across.', '100 light-years', '200 light-years'),
            ('The nebula is larger than 100 light-years across.', '100 light-years', '200 light-years'),
            ('The nebula is more than about 100 light-years across.', '100 light-years', '300 light-years'),
            ('The nebula is visible after October 1, 2026.', 'October 1, 2026', 'October 2, 2026')]
        for statement, original, fake in cases:
            source = article(); source['passages'][0]['text'] = statement + ' Cloud 1 contains oxygen. Cloud 1 lies 500 light-years from Earth.'
            proposal = {'fact_a_text': 'Cloud 1 contains oxygen.', 'fact_a_sentence_id': 2,
                'fact_b_text': 'Cloud 1 lies 500 light-years from Earth.', 'fact_b_sentence_id': 3,
                'mutation_sentence_id': 1, 'source_value': original, 'fake_value': fake}
            with self.subTest(statement=statement), self.assertRaises(PreparationError): build_draft(proposal, source)
            class Permissive(FakeModel):
                review_calls = 0
                def complete(self, instruction, data, schema, deadline, tokens=1100):
                    if schema == TOPIC_SCHEMA: return {'query': 'ghost'}
                    if schema == PROPOSAL_SCHEMA: return proposal
                    self.review_calls += 1; return copy.deepcopy(REVIEW)
            sources = FakeSources(); sources.retrieve = lambda candidate, deadline: {**source, 'id': candidate['id']}
            model = Permissive()
            with self.assertRaises(PreparationError): RoundGenerator(model, sources).generate()
            self.assertEqual(model.review_calls, 0)

    def test_plain_predicate_polarity_only_exact_toggle_is_allowed(self):
        from local.generation import build_draft, exclusive_slots
        for statement, original, fake in [('The nebula is a stellar nursery.', 'is', 'is not'),
                ('The nebula is not a galaxy.', 'is not', 'is'), ('The missions were scientific expeditions.', 'were', 'were not')]:
            source = article(); source['passages'][0]['text'] = statement + ' Cloud 1 contains oxygen. Cloud 1 lies 500 light-years from Earth.'
            proposal = {'fact_a_text': 'Cloud 1 contains oxygen.', 'fact_a_sentence_id': 2,
                'fact_b_text': 'Cloud 1 lies 500 light-years from Earth.', 'fact_b_sentence_id': 3,
                'mutation_sentence_id': 1, 'source_value': original, 'fake_value': fake}
            self.assertEqual(build_draft(proposal, source)['correction'], statement)
            with self.assertRaises(PreparationError): build_draft({**proposal, 'fake_value': 'is never'}, source)
        for statement in ('The nebula is not only a stellar nursery.', 'The nebula is a cloud and a stellar nursery.', 'If the nebula is a stellar nursery, stars form there.', 'Is the nebula a stellar nursery?', 'The nebula might be a stellar nursery.', 'Some stars are red.', 'A star is red.'):
            self.assertFalse(any(slot['kind'] == 'polarity' for slot in exclusive_slots(statement)))

    def test_embedded_polarity_and_constellation_aliases_reject_before_review(self):
        from local.generation import build_draft, exclusive_slots, validate_alternative
        cases = [('The idea that aliens are real is widespread.', 'are', 'are not'),
            ('NASA says Venus is a flying saucer.', 'is', 'is not'),
            ('The report that Venus was a flying saucer remains popular.', 'was', 'was not'),
            ('NASA believes Venus is a flying saucer.', 'is', 'is not'),
            ('The astronomer who studies Venus is famous.', 'is', 'is not'),
            ('The nebula lies in the constellation Boötes.', 'Boötes', 'Bootes'),
            ('The nebula lies in the constellation Bootes.', 'Bootes', 'Boötes')]
        for statement, original, fake in cases:
            source = article(); source['passages'][0]['text'] = statement + ' Cloud 1 contains oxygen. Cloud 1 lies 500 light-years from Earth.'
            proposal = {'fact_a_text': 'Cloud 1 contains oxygen.', 'fact_a_sentence_id': 2,
                'fact_b_text': 'Cloud 1 lies 500 light-years from Earth.', 'fact_b_sentence_id': 3,
                'mutation_sentence_id': 1, 'source_value': original, 'fake_value': fake}
            with self.subTest(statement=statement), self.assertRaises(PreparationError): build_draft(proposal, source)
            class Permissive(FakeModel):
                review_calls = 0
                def complete(self, instruction, data, schema, deadline, tokens=1100):
                    if schema == TOPIC_SCHEMA: return {'query': 'ghost'}
                    if schema == PROPOSAL_SCHEMA: return proposal
                    self.review_calls += 1; return copy.deepcopy(REVIEW)
            sources = FakeSources(); sources.retrieve = lambda candidate, deadline: {**source, 'id': candidate['id']}
            model = Permissive()
            with self.assertRaises(PreparationError): RoundGenerator(model, sources).generate()
            self.assertEqual(model.review_calls, 0)
        self.assertTrue(any(slot['kind'] == 'polarity' for slot in exclusive_slots('Venus is a planet.')))
        cepheus = exclusive_slots('The nebula lies in the constellation Cepheus.')[0]
        self.assertTrue(validate_alternative(cepheus, 'Boötes'))

    def test_duplicate_sentence_id_rejected_even_when_paraphrases_differ(self):
        from local.generation import build_draft
        proposal = {'fact_a_text': 'Cloud 1 lies in Cepheus.', 'fact_a_sentence_id': 1,
            'fact_b_text': 'Cloud 1 contains oxygen.', 'fact_b_sentence_id': 2,
            'mutation_sentence_id': 1, 'source_value': 'Cepheus', 'fake_value': 'Orion'}
        with self.assertRaises(PreparationError): build_draft(proposal, article())

    def test_two_ai_queries_share_deadline_and_recover_in_one_request(self):
        class Searching(FakeModel):
            queries = 0
            def complete(self, instruction, data, schema, deadline, tokens=1100):
                if schema == TOPIC_SCHEMA:
                    self.queries += 1; self.calls.append((schema, data, deadline))
                    return {'query': 'uap' if self.queries == 1 else 'ghost'}
                return super().complete(instruction, data, schema, deadline, tokens)
        class Sources(FakeSources):
            def discover(self, query, excluded, deadline):
                if query == 'uap': self.searches.append((query, set(excluded), deadline)); return []
                return super().discover(query, excluded, deadline)
        model, sources = Searching(), Sources()
        result = RoundGenerator(model, sources).generate()
        self.assertEqual(result['source']['id'], 1); self.assertEqual(model.queries, 2)
        self.assertEqual([call[0] for call in sources.searches], ['uap', 'uap', 'ghost'])
        self.assertEqual(len({call[2] for call in model.calls} | {call[2] for call in sources.searches}), 1)
        empty = FakeSources(); empty.discover = lambda *args: []
        model = Searching()
        with self.assertRaises(PreparationError): RoundGenerator(model, empty).generate()
        self.assertEqual(model.queries, 2)

    def test_modal_nasa_fake_rejected_even_with_permissive_reviewer(self):
        from local.generation import build_draft, exclusive_slots
        source = article()
        bad = 'Satellites in formation can appear as a group of strange lights in the night sky.'
        source['passages'][0]['text'] = bad + ' Cloud 1 lies in the constellation Cepheus. Venus is often mistaken for a UFO.'
        proposal = {'fact_a_text': 'Cloud 1 lies in the constellation Cepheus.', 'fact_a_sentence_id': 2,
            'fact_b_text': 'Venus is often mistaken for a UFO.', 'fact_b_sentence_id': 3,
            'mutation_sentence_id': 1, 'source_value': 'strange lights', 'fake_value': 'shooting stars'}
        self.assertEqual(exclusive_slots(bad), [])
        with self.assertRaises(PreparationError): build_draft(proposal, source)
        class Permissive(FakeModel):
            review_calls = 0
            def complete(self, instruction, data, schema, deadline, tokens=1100):
                if schema == TOPIC_SCHEMA: return {'query': 'ghost'}
                if schema == PROPOSAL_SCHEMA: return proposal
                self.review_calls += 1
                return copy.deepcopy(REVIEW)
        sources = FakeSources(); sources.retrieve = lambda candidate, deadline: {**source, 'id': candidate['id']}
        model = Permissive()
        with self.assertRaises(PreparationError): RoundGenerator(model, sources).generate()
        self.assertEqual(model.review_calls, 0)

    def test_derived_exclusive_slots_enforce_kind_bounds_and_readable_language(self):
        from local.generation import exclusive_slots, validate_alternative, readable_claim
        constellation = exclusive_slots('The Helix Nebula lies in the constellation Aquarius.')[0]
        self.assertTrue(validate_alternative(constellation, 'Boötes'))
        self.assertFalse(validate_alternative(constellation, 'Mars'))
        self.assertEqual(exclusive_slots('A cloud can lie in the constellation Aquarius.'), [])
        self.assertFalse(any(slot['kind'] == 'constellation' for slot in exclusive_slots('The constellation Aquarius is a popular astronomical subject.')))
        self.assertEqual(exclusive_slots('The cloud contains light from stars in the constellation Aquarius.'), [])
        self.assertFalse(any(slot['kind'] == 'measurement' for slot in exclusive_slots('The cloud is over 2 light-years across.')))
        measurement = next(slot for slot in exclusive_slots('The Helix Nebula is about 650 light-years away.') if slot['kind'] == 'measurement')
        self.assertTrue(validate_alternative(measurement, '65 light-years'))
        self.assertFalse(validate_alternative(measurement, '700 light-years'))
        self.assertFalse(validate_alternative(measurement, '65 miles'))
        self.assertEqual(exclusive_slots('NASA announced the study on June 9, 2022.'), [])
        with self.assertRaises(PreparationError): readable_claim('Venus is a confused object in the sky.')
        self.assertEqual(readable_claim('Venus is often mistaken for a UFO.'), 'Venus is often mistaken for a UFO.')

    def test_deterministic_shuffle_changes_fake_position_without_changing_truth(self):
        shuffles = [lambda claims: None, lambda claims: claims.reverse(), lambda claims: claims.append(claims.pop(0))]
        positions = []
        for shuffle in shuffles:
            result = RoundGenerator(FakeModel(), FakeSources(), shuffle=shuffle).generate()
            positions.append(result['false_index'])
            self.assertIn('constellation Orion', result['claims'][result['false_index']]['text'])
            self.assertEqual(result['review']['classifications'][result['false_index']], 'contradicted')
        self.assertEqual(positions, [0, 2, 2])

    def test_flat_proposal_sentence_ids_and_substring_mutations_reject(self):
        from local.generation import build_draft, source_sentences
        source = article(); proposal = {'fact_a_text': 'Cloud 1 contains oxygen.', 'fact_a_sentence_id': 2,
            'fact_b_text': 'Cloud 1 lies 500 light-years from Earth.', 'fact_b_sentence_id': 3,
            'mutation_sentence_id': 1, 'source_value': 'Cepheus', 'fake_value': 'Orion'}
        self.assertEqual(build_draft(proposal, source)['correction'], 'Cloud 1 lies in the constellation Cepheus.')
        for changed in ({**proposal, 'mutation_sentence_id': True}, {**proposal, 'fact_a_sentence_id': 999}, {**proposal, 'extra': 1},
                        {**proposal, 'source_value': 'Ce'}, {**proposal, 'fake_value': 'not Cepheus'}):
            with self.assertRaises(PreparationError): build_draft(changed, source)
        source['passages'][0]['text'] += ' The named Cloud 1 is red and it has a distinct structure.'
        self.assertTrue(any('and it' in sentence['text'] for sentence in source_sentences(source)))

    def test_valid_round_and_blinded_review(self):
        model, sources = FakeModel(), FakeSources()
        result = RoundGenerator(model, sources).generate()
        self.assertIn('constellation Orion', result['claims'][result['false_index']]['text'])
        self.assertEqual(len(result['claims']), 3)
        self.assertEqual(result['source']['id'], 1)
        self.assertEqual(result['contract'], 'ghostproof-live-1')
        review_data = model.calls[-1][1]
        self.assertNotIn('false_index', review_data)
        self.assertNotIn('quote', json.dumps(review_data['claims']))
        self.assertIn('automated', result['review']['label'])
        self.assertEqual(len({call[2] for call in model.calls} | {sources.searches[0][2]}), 1)

    def test_five_rounds_and_exclusion_history_not_hunt_owned(self):
        generator = RoundGenerator(FakeModel(), FakeSources())
        ids = [generator.generate()['source']['id'] for _ in range(5)]
        self.assertEqual(ids, [1, 2, 3, 4, 5])
        self.assertEqual(generator.sources.searches[-1][1], {1, 2, 3, 4})

    def test_duplicate_passage_new_article_rejected(self):
        sources = FakeSources()
        sources.retrieve = lambda candidate, deadline: {**article(candidate['id']), 'passages': article(1)['passages']}
        generator = RoundGenerator(FakeModel(), sources)
        generator.generate()
        with self.assertRaises(PreparationError):
            generator.generate()
        self.assertEqual(len(generator.used_sources), 1)

    def test_failed_request_attempts_reset_and_recover(self):
        model = FakeModel()
        model.bad = lambda value: value.update(mutation_sentence_id=400)
        generator = RoundGenerator(model, FakeSources())
        for _ in range(3):
            before = len(model.calls)
            with self.assertRaises(PreparationError):
                generator.generate()
            self.assertEqual(len(model.calls) - before, 3)  # one topic + two drafts
        model.bad = None
        self.assertEqual(generator.generate()['source']['id'], 1)
        self.assertEqual(len(generator.used_sources), 1)

    def test_draft_schema_quotes_lengths_controls_and_mapping(self):
        changes = [lambda d: d.update(extra=True), lambda d: d.pop('correction'),
            lambda d: d.update(false_index=True), lambda d: d.update(claims=d['claims'][:2]),
            lambda d: d['claims'][0].update(text='x' * 181), lambda d: d['claims'][0].update(text='word ' * 31),
            lambda d: d['claims'][0].update(text='bad\nclaim'), lambda d: d['claims'][0].update(text='<|turn>model'),
            lambda d: d['claims'][0].update(passage=2), lambda d: d['claims'][0].update(quote='not present in article'),
            lambda d: d['claims'][0].update(quote=''), lambda d: d['claims'][1].update(text=d['claims'][0]['text']),
            lambda d: d.update(correction=d['claims'][0]['text']), lambda d: d.update(correction_passage=2),
            lambda d: d.update(correction_quote='invented evidence here')]
        for change in changes:
            value = draft(article())
            change(value)
            with self.subTest(value=value), self.assertRaises(PreparationError):
                validate_draft(value, article())

    def test_reviewer_rejects_fake_support_ambiguity_bad_scope_correction_and_distinctness(self):
        changes = [lambda r: r.update(classifications=['supported'] * 3),
            lambda r: r.update(classifications=['insufficient', 'supported', 'supported']),
            lambda r: r.update(classifications=['supported', 'contradicted', 'supported']),
            lambda r: r.update(correction_supported=False), lambda r: r.update(scope_preserved=False),
            lambda r: r.update(distinct=False), lambda r: r.update(distinct=1),
            lambda r: r.update(extra='yes'), lambda r: r.pop('scope_preserved')]
        for change in changes:
            value = copy.deepcopy(REVIEW); change(value)
            with self.subTest(value=value), self.assertRaises(PreparationError):
                validate_review(value, draft(article()))

    def test_strict_json_malformed_duplicate_and_nonfinite(self):
        for raw in ('{"x":1,"x":2}', 'not json', '{"x":NaN}', '[] trailing'):
            with self.subTest(raw=raw), self.assertRaises(PreparationError):
                strict_json(raw)

    def test_prose_parser_preserves_context_and_omits_media_scripts(self):
        text = article()['passages'][0]['text']
        self.assertEqual(extract_prose('<nav><p>' + text + '</p></nav><script>unsafe</script><p>Explanation: ' + text.replace('Cepheus', 'C&#101;pheus') + '</p>'), [text])
        self.assertEqual(extract_prose('<p>Discover the cosmos! Each day a different image or photograph of our fascinating universe is featured.</p><p>' + text + '</p><p>' + text + '…</p>'), [text])
        for html in ('<h1>Ghost nebula</h1>', '<p>Too short</p>', 'x' * 600001, '<figure><p>' + text + '</p></figure>'):
            with self.assertRaises(PreparationError):
                extract_prose(html)

    def test_nasa_search_advances_and_binds_article_identity(self):
        calls = []
        def transport(origin, path, deadline):
            calls.append((origin, path))
            if '/search?' in path:
                return [{'id': 1, 'subtype': 'image-article', 'url': article()['url']},
                        {'id': 2, 'subtype': 'arbitrary', 'url': 'https://evil.test/'}]
            return {'id': 1, 'type': 'image-article', 'link': article()['url'], 'title': {'rendered': 'Ghost'}, 'content': {'rendered': '<p>' + article()['passages'][0]['text'] + '</p>'}}
        sources = NasaSources(transport)
        first = sources.discover('ghost & cloud', set(), time.monotonic() + 3)
        self.assertEqual(len(first), 1)
        self.assertEqual(sources.retrieve(first[0], time.monotonic() + 3)['id'], 1)
        self.assertEqual(sources.discover('ghost & cloud', {1}, time.monotonic() + 3), [])
        self.assertIn('page=2', calls[-1][1]); self.assertIn('ghost+%26+cloud', calls[0][1])
        self.assertTrue(all(origin == NasaSources.ORIGIN for origin, _ in calls))
        for candidate in ({'id': '1', 'type': 'image-article'}, {'id': 1, 'type': '../../private'}):
            with self.assertRaises(PreparationError): sources.retrieve(candidate, time.monotonic() + 3)
        wrong = {**first[0], 'url': 'https://science.nasa.gov/wrong/'}
        with self.assertRaises(PreparationError): sources.retrieve(wrong, time.monotonic() + 3)

    def test_exhausted_search_is_recoverable_and_topic_pages_follow_articles(self):
        def transport(origin, path, deadline):
            if 'page=2' in path: raise PreparationError('Upstream returned HTTP 400. Check connectivity or retry another subject.')
            return [{'id': 2, 'subtype': 'topic', 'url': article(2)['url']}, {'id': 1, 'subtype': 'post', 'url': article(1)['url']}]
        sources = NasaSources(transport)
        self.assertEqual([item['id'] for item in sources.discover('uap', set(), time.monotonic() + 2)], [1, 2])
        self.assertEqual(sources.discover('uap', set(), time.monotonic() + 2), [])
        self.assertEqual(len(sources.discover('ghost', set(), time.monotonic() + 2)), 2)

    def test_correction_requires_exact_source_not_mars_exclusion_or_broken_antecedent(self):
        value = draft(article())
        value['correction'] = 'The nebula is visible from Earth, not Mars.'
        value['source_value'] = 'Earth'; value['fake_value'] = 'Mars'
        value['claims'][0]['text'] = value['correction'].replace('Earth', 'Mars')
        with self.assertRaises(PreparationError): validate_draft(value, article())
        source = article(); source['passages'][0]['text'] += ' They glow red.'
        value = draft(source); value.update(correction='They glow red.', correction_quote='They glow red.')
        value['claims'][0].update(text='They glow blue.', quote='They glow red.')
        with self.assertRaises(PreparationError): validate_draft(value, source)
        source['passages'][0]['text'] += ' Stars in their cluster lie in the constellation Cepheus.'
        value = draft(source); value.update(correction='Stars in their cluster lie in the constellation Cepheus.', correction_quote='Stars in their cluster lie in the constellation Cepheus.', source_value='Cepheus', fake_value='Orion')
        value['claims'][0].update(text='Stars in their cluster lie in the constellation Orion.', quote=value['correction_quote'])
        self.assertEqual(validate_draft(value, source), value)

    def test_url_and_model_configuration_reject_remote_cloud_credentials(self):
        for url in ('https://evil.test/', 'http://science.nasa.gov/a', 'https://science.nasa.gov.evil/a', 'https://science.nasa.gov/a?secret=x', 'https://u@science.nasa.gov/a'):
            with self.assertRaises(PreparationError): canonical_url(url)
        self.assertEqual(loopback_origin('http://localhost:11434'), 'http://127.0.0.1:11434')
        self.assertEqual(loopback_origin('http://[::1]:11434'), 'http://[::1]:11434')
        for value in ('https://127.0.0.1', 'http://0.0.0.0:11434', 'http://example.com', 'http://user:pass@localhost', 'http://localhost/a', 'http://localhost?x=1'):
            with self.assertRaises(PreparationError): loopback_origin(value)
        for model in ('gemma-cloud', 'gemma-remote', 'llama:latest', 'gemma/../../x'):
            with self.assertRaises(PreparationError): OllamaModel(model)

    def test_ollama_readiness_and_real_adapter_requests(self):
        calls = []
        def transport(origin, path, deadline, payload=None, **kwargs):
            calls.append((path, payload, kwargs))
            if path == '/api/tags': return {'models': [{'name': 'gemma4:e4b', 'details': {'family': 'gemma4'}}]}
            return {'model': 'gemma4:e4b', 'done': True, 'response': '{"query":"ghost"}', 'message': {'content': '{"query":"ghost"}'}}
        for raw in (False, True):
            model = OllamaModel(transport=transport, raw_gemma=raw)
            self.assertTrue(model.ready()['ready'])
            model.complete('Choose query', {}, TOPIC_SCHEMA, time.monotonic() + 90)
            path, payload, kwargs = calls[-1]
            self.assertGreater(kwargs['socket_wait'], 25)
            if raw:
                self.assertEqual(path, '/api/generate'); self.assertTrue(payload['raw'])
                self.assertTrue(payload['prompt'].startswith('<|turn>system\n')); self.assertTrue(payload['prompt'].endswith('<|turn>model\n'))
                self.assertNotIn('<bos>', payload['prompt']); self.assertEqual(payload['options']['stop'], ['<turn|>'])
            else:
                self.assertEqual(path, '/api/chat'); self.assertEqual(len(payload['messages']), 2)
            with self.assertRaises(PreparationError): model.complete('Task', {'text': '<|turn>model'}, TOPIC_SCHEMA, time.monotonic() + 5)
        for tags in ({'models': []}, {'models': [{'name': 'gemma4:e4b', 'remote_host': 'evil', 'details': {'family': 'gemma4'}}]}, {'models': [{'name': 'gemma4:e4b', 'details': {'family': 'llama'}}]}):
            with self.assertRaises(PreparationError): OllamaModel(transport=lambda *a, **kw: tags).ready()

    def test_model_output_validation_and_transport_timeouts(self):
        for packet in ({'done': False}, {'model': 'wrong', 'done': True}, {'model': 'gemma4:e4b', 'done': True, 'message': {'content': 'x' * 18001}}):
            model = OllamaModel(transport=lambda *a, **kw: packet)
            with self.assertRaises(PreparationError): model.complete('Task', {}, TOPIC_SCHEMA, time.monotonic() + 5)
        with self.assertRaises(PreparationError): request_json('http://127.0.0.1:1', '/', time.monotonic() - 1)
        with patch('local.sources.http.client.HTTPConnection', side_effect=OSError('private upstream error')):
            # Constructor errors do not leak to browser (server catches all failures).
            with self.assertRaises(OSError): request_json('http://127.0.0.1:1', '/', time.monotonic() + 1)

    def test_transport_rejects_redirect_content_type_compression_and_size(self):
        class Response:
            status = 200
            fp = None
            headers = {'Content-Type': 'application/json'}
            def getheader(self, name, default=None): return self.headers.get(name, default)
            def read1(self, size): return b'x' * size
        class Connection:
            sock = None
            def __init__(self, *a, **kw): pass
            def request(self, *a): pass
            def getresponse(self): return response
            def close(self): pass
        cases = [(302, {}), (200, {'Content-Type': 'text/html'}), (200, {'Content-Type': 'application/json', 'Content-Encoding': 'gzip'}),
                 (200, {'Content-Type': 'application/json', 'Content-Length': '999999'}), (200, {'Content-Type': 'application/json'})]
        for status, headers in cases:
            response = Response(); response.status = status; response.headers = headers
            with patch('local.sources.http.client.HTTPConnection', Connection), self.assertRaises(PreparationError):
                request_json('http://127.0.0.1:1', '/', time.monotonic() + 1, max_bytes=30)


if __name__ == '__main__': unittest.main()
