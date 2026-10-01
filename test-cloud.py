import copy
from datetime import date
import hashlib
import importlib.util
import json
import os
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.update(STEP_BUDGET_SECONDS='0', POLL_SECONDS='0', POLL_INTERVAL='0')
scripts = Path(__file__).parent / 'skills/pod-creative-loop/scripts'
sys.path.insert(0, str(scripts))
spec = importlib.util.spec_from_file_location('creative', scripts / 'creative.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
ev, rs, media = c.ev, c.rs, c.media
SOUND = {'container': 'mp4', 'duration_seconds': 5.04, 'width': 720, 'height': 1280, 'has_audio': True, 'audio_codec': 'mp4a', 'video_codec': 'avc1'}


def rubric():
    return [
        {'id': 'delivery', 'description': 'Deliver the requested standalone asset', 'label': 'Giao đúng sản phẩm yêu cầu', 'source_requirement': 'Provide this asset', 'required': True, 'priority': 1, 'weight': 1, 'asset_refs': ['design']},
        {'id': 'style', 'description': 'Preferred visual style', 'source_requirement': 'Prefer this style', 'required': False, 'priority': 2, 'weight': 1, 'asset_refs': ['mockup', 'video']}
    ]


def report(status='pass', score=4.7):
    return {'summary': 'Actual media inspection', 'checks': [
        {'id': 'delivery', 'status': status, 'score': score, 'evidence': 'Observed deliverable', 'improvement': 'Correct the requested asset'},
        {'id': 'style', 'status': 'pass', 'score': score, 'evidence': 'Observed style', 'improvement': 'Refine style'}
    ], 'uncovered_requirements': [], 'release_checks': []}


def audit(conflict=False):
    return {'conflicts': [{'id': 'delivery', 'reason': 'The evidence says missing but the verdict says pass'}] if conflict else [], 'uncovered_requirements': []}


def research(sources=8):
    channels = ['amazon', 'etsy', 'competitor_store', 'tiktok', 'trends', 'industry', 'pinterest', 'meta_ads']
    rows = [{'id': 's%d' % (i + 1), 'channel': channels[i % len(channels)], 'title': 'Source %d' % (i + 1), 'url': 'https://example.com/%d' % i,
             'finding': 'Observed signal', 'retrieved': '2026-09-30', 'access': 'fetched'} for i in range(sources)]
    used = {r['channel'] for r in rows}
    return {'summary': 'Market summary', 'status': 'complete', 'sources': rows,
            'coverage': [{'channel': k, 'status': 'covered' if k in used else 'unavailable', 'note': 'Checked'} for k in rs.REQUIRED_COVERAGE],
            'keywords': [{'term': 'best friend', 'note': 'In a ranked listing title', 'source_ids': ['s1']}],
            'competitor_designs': [{'brand': 'Example store', 'why_it_works': 'Clear name placement', 'url': 'https://example.com/products/mug', 'source_ids': ['s3']}],
            'seasonal_focus': [],
            'opportunities': [{'title': 'Line art', 'design_direction': 'Minimal botanical', 'source_ids': [], 'basis': 'hypothesis'}]}


def plan(**changes):
    styles = ['Botanical line art', 'Retro badge', 'Watercolour', 'Bold typography', 'Minimal monogram', 'Hand lettering']
    count = changes.get('design_count', 5)
    value = {'brief': 'Provide this asset. Prefer this style.', 'language': 'vi', 'insights': {'market': 'US', 'audience': 'Gift shoppers'},
             'research': research(), 'criteria': rubric(), 'max_rounds': 2, 'target_score': 4.5,
             'variants': [{'title': 'Concept %d' % (i + 1), 'style': styles[i], 'rationale': 'Why it fits', 'palette': ['#1A2B3C'], 'inspired_by': ['s1'],
                           'prompts': {'design': 'CREATOR_PRIVATE_REASONING design %d' % i, 'mockup': 'mockup %d' % i, 'video': 'video %d' % i}} for i in range(count)]}
    value.update(changes)
    return value


class Cloud:
    """Stands in for the model APIs. Reviewer answers are chosen by role, then by call order."""

    def __init__(self):
        self.calls, self.images, self.tasks = [], 0, {}
        self.answers = {'contract': [], 'screening': [], 'evaluation': [], 'audit': [], 'adjudication': []}
        self.refuse = set()

    def role(self, text):
        if text.startswith('You are an independent requirements auditor'):
            return 'contract'
        if text.startswith('You are an independent creative reviewer'):
            return 'screening'
        return 'audit' if 'Evaluation to audit' in text else 'adjudication' if 'Disputed reports' in text else 'evaluation'

    def default(self, role, body):
        if role == 'contract':
            return {'summary': 'Complete', 'gaps': [], 'unsupported': []}
        if role == 'screening':
            ids = ['v%d' % (i + 1) for i in range(len(body['input'][0]['content']) - 1)]
            return {'summary': 'Ranked', 'recommended': ids[:3], 'ranking': [
                {'id': x, 'score': 4, 'text_check': 'pass', 'strengths': 'Clear', 'risks': 'None seen', 'best_for': 'Friends'} for x in ids]}
        return audit() if role == 'audit' else report()

    def __call__(self, path, body=None, stream=False):
        self.calls.append((path, body))
        if path == '/images/generations':
            self.images += 1
            if self.images in self.refuse:
                raise c.ApiError('Model API HTTP 400: InputTextSensitiveContentDetected', True, 'InputTextSensitiveContentDetected')
            return {'data': [{'url': 'https://example.com/image-%d' % self.images}]}
        if path == '/contents/generations/tasks':
            task = 'task-%d' % (len(self.tasks) + 1)
            self.tasks[task] = {'status': 'succeeded', 'content': {'video_url': 'https://example.com/%s.mp4' % task}}
            return {'id': task}
        if path.startswith('/contents/generations/tasks/'):
            return self.tasks[path.rsplit('/', 1)[1]]
        role = self.role(body['input'][0]['content'][0]['text'])
        value = self.answers[role].pop(0) if self.answers[role] else self.default(role, body)
        if isinstance(value, Exception):
            raise value
        return {'id': 'response-%d' % len(self.calls), 'output': [{'content': [{'type': 'output_text', 'text': json.dumps(value)}]}]}

    def posts(self, path):
        return [body for p, body in self.calls if p == path]


class CloudTests(unittest.TestCase):
    def setUp(self):
        self.old_key = os.environ.get('ARK_API_KEY')
        os.environ['ARK_API_KEY'] = 'test-key-not-a-real-credential'
        self.tmp = tempfile.TemporaryDirectory()
        self.old_root = c.ROOT
        c.ROOT = Path(self.tmp.name)
        self.cloud = Cloud()
        for target, value in ((c, 'api'), (media, 'probe')):
            patcher = patch.object(target, value, self.cloud if value == 'api' else lambda url: dict(SOUND))
            patcher.start()
            self.addCleanup(patcher.stop)

    def tearDown(self):
        c.ROOT = self.old_root
        self.tmp.cleanup()
        if self.old_key is None:
            os.environ.pop('ARK_API_KEY', None)
        else:
            os.environ['ARK_API_KEY'] = self.old_key

    def until(self, *statuses, limit=80):
        for _ in range(limit):
            result = c.execute('step')
            if result['status'] in statuses:
                return result
        self.fail('never reached ' + '/'.join(statuses) + '; last was ' + result['status'])

    def explored(self, **changes):
        c.execute('init', plan(**changes))
        return self.until('awaiting_selection')

    def producing(self, ids=('v1', 'v2'), **changes):
        self.explored(**changes)
        c.execute('select', {'selected': list(ids)})

    # --- campaign settings -------------------------------------------------

    def test_settings_reject_non_boolean_values(self):
        for key in ('watermark', 'generate_audio'):
            for value in ('false', 0, None):
                with self.subTest(key=key, value=value), self.assertRaisesRegex(ValueError, key):
                    c.execute('init', plan(**{key: value}))

    def test_sound_is_on_by_default_and_reaches_the_video_request(self):
        self.producing(['v1'])
        self.until('completed')
        video = self.cloud.posts('/contents/generations/tasks')[0]
        self.assertIs(video['generate_audio'], True)
        self.assertEqual((video['duration'], video['ratio']), (5, '9:16'))

    def test_watermark_false_reaches_images_and_video(self):
        self.producing(['v1'], watermark=False)
        self.until('completed')
        for body in self.cloud.posts('/images/generations') + self.cloud.posts('/contents/generations/tasks'):
            self.assertIs(body['watermark'], False)

    def test_settings_are_frozen(self):
        for key in ('watermark', 'generate_audio'):
            with self.subTest(key=key):
                c.ROOT = Path(tempfile.mkdtemp(dir=self.tmp.name))
                c.execute('init', plan())
                s = c.load()
                s[key] = not s[key]
                c.save(s)
                with self.assertRaisesRegex(ValueError, 'Frozen'):
                    c.execute('step')

    def test_frozen_contract_cannot_change_during_revision(self):
        c.execute('init', plan())
        s = c.load()
        s['criteria'][0]['description'] = 'Relaxed requirement'
        c.save(s)
        with self.assertRaisesRegex(ValueError, 'Frozen'):
            c.execute('step')

    def test_state_edit_detected(self):
        c.execute('init', plan())
        (c.ROOT / 'state.json').write_text('{"status":"completed"}')
        with self.assertRaises(RuntimeError):
            c.load()

    # --- plan, research and contract ---------------------------------------

    def test_variants_must_match_count_and_differ_in_style(self):
        short = plan()
        short['variants'].pop()
        same = plan()
        same['variants'][1]['style'] = same['variants'][0]['style'].upper()
        for value in (short, same):
            with self.assertRaises(ValueError):
                c.execute('init', value)

    def test_variant_inspiration_must_cite_recorded_sources(self):
        value = plan()
        value['variants'][0]['inspired_by'] = ['invented']
        with self.assertRaisesRegex(ValueError, 'inspired_by'):
            c.execute('init', value)

    def test_insights_must_name_market_and_audience(self):
        with self.assertRaisesRegex(ValueError, 'insights'):
            c.execute('init', plan(insights={'market': 'US'}))

    def test_research_claims_must_cite_sources_or_be_hypotheses(self):
        value = research()
        value['keywords'][0]['source_ids'] = []
        with self.assertRaisesRegex(ValueError, 'hypothesis'):
            rs.validate(value)
        value['keywords'][0]['source_ids'] = ['unknown']
        with self.assertRaisesRegex(ValueError, 'unknown source'):
            rs.validate(value)

    def test_thin_research_must_be_labelled_limited(self):
        value = research(sources=2)
        value.update(competitor_designs=[], keywords=[], coverage=[{'channel': k, 'status': 'limited', 'note': 'Checked'} for k in rs.REQUIRED_COVERAGE])
        with self.assertRaisesRegex(ValueError, 'limited'):
            rs.validate(value)
        value.update(status='limited', limitations='Search was unavailable')
        self.assertEqual(rs.validate(value)['status'], 'limited')

    def test_channel_cannot_claim_coverage_without_a_source(self):
        value = research()
        value['sources'] = [s for s in value['sources'] if s['channel'] != 'amazon']
        value['keywords'] = []
        with self.assertRaisesRegex(ValueError, 'amazon'):
            rs.validate(value)

    def test_sources_link_to_pages_people_can_open(self):
        for url in ('https://shop.example.com/products.json?limit=60', 'https://shop.example.com/collections/best-sellers/products.json'):
            value = research()
            value['sources'][0]['url'] = url
            with self.subTest(url=url), self.assertRaisesRegex(ValueError, 'data feed'):
                rs.validate(value)

    def test_the_customers_own_store_is_never_a_competitor(self):
        value = research()
        self.assertEqual(rs.validate(value, 'shop.test.com')['status'], 'complete')
        own = research()
        own['sources'][2]['url'] = 'https://www.example.com/collections/all'
        with self.assertRaisesRegex(ValueError, "own store"):
            rs.validate(own, 'example.com')
        named = research()
        named['competitor_designs'][0].update(brand='Macorner', url='https://amazon.com/dp/1')
        with self.assertRaisesRegex(ValueError, "own store"):
            rs.validate(named, 'macorner.co')
        studied = research()
        studied['sources'][0].update(channel='other', url='https://macorner.co/collections/all')
        studied['coverage'][0]['status'] = 'unavailable'
        self.assertEqual(rs.validate(studied, 'macorner.co')['status'], 'complete')
        with self.assertRaisesRegex(ValueError, "own store"):
            c.execute('init', plan(own_store='example.com', research=own))

    def test_sources_need_https_and_known_channel(self):
        for key, bad in (('url', 'http://example.com'), ('channel', 'rumour'), ('retrieved', 'today'), ('access', 'guessed')):
            value = research()
            value['sources'][0][key] = bad
            with self.subTest(key=key), self.assertRaises(ValueError):
                rs.validate(value)

    def test_contract_gaps_are_returned_before_anything_is_frozen(self):
        gaps = {'summary': 'Missing', 'gaps': [{'requirement': 'No music', 'suggestion': 'Add a criterion'}], 'unsupported': []}
        self.cloud.answers['contract'] = [gaps, gaps, gaps]
        for left in (2, 1):
            result = c.execute('init', plan())
            self.assertEqual((result['status'], result['audits_left']), ('contract_gaps', left))
            self.assertFalse((c.ROOT / 'state.json').exists())
        self.assertEqual(c.execute('init', plan())['status'], 'running')
        self.assertEqual(c.load()['contract_audit']['report']['gaps'][0]['requirement'], 'No music')
        self.assertEqual(self.cloud.posts('/images/generations'), [])

    def test_unavailable_contract_audit_does_not_block_the_campaign(self):
        self.cloud.answers['contract'] = [c.ApiError('Model API transport failure', False)]
        self.assertEqual(c.execute('init', plan())['status'], 'running')
        self.assertEqual(c.load()['contract_audit']['status'], 'unavailable')

    def test_seasonal_calendar_is_attached_by_the_helper(self):
        c.execute('init', plan())
        self.assertTrue(all('days_until' in o for o in c.load()['research']['seasonal_calendar']))

    # --- design exploration ------------------------------------------------

    def test_exploration_generates_every_style_then_screens_then_waits(self):
        result = self.explored()
        self.assertEqual(result['phase'], 'designs')
        self.assertEqual(len(self.cloud.posts('/images/generations')), 5)
        self.assertEqual(self.cloud.posts('/contents/generations/tasks'), [])
        screening = self.cloud.posts('/responses')[-1]['input'][0]['content']
        self.assertEqual(len(screening), 6)
        exported = c.execute('export')
        self.assertEqual((exported['stage'], exported['status'], len(exported['variants'])), ('designs', 'awaiting_selection', 5))
        self.assertEqual(exported['screening']['report']['recommended'], ['v1', 'v2', 'v3'])
        self.assertEqual(c.execute('step')['status'], 'awaiting_selection')
        self.assertEqual(len(self.cloud.posts('/images/generations')), 5)

    def test_one_step_can_cover_several_units_inside_its_budget(self):
        c.execute('init', plan())
        with patch.dict(os.environ, {'STEP_BUDGET_SECONDS': '60'}):
            result = c.execute('step')
        self.assertEqual(result['status'], 'awaiting_selection')
        self.assertEqual([x['unit'] for x in result['log']], ['design'] * 5 + ['screening'])

    def test_refused_design_is_isolated(self):
        self.cloud.refuse = {2}
        self.explored()
        exported = c.execute('export')
        self.assertIn('refused', exported['variants'][1]['error'])
        self.assertEqual(sum('design' in v for v in exported['variants']), 4)
        with self.assertRaises(ValueError):
            c.execute('select', {'selected': ['v2']})

    def test_unconfirmed_design_submission_is_never_repeated(self):
        c.execute('init', plan())
        with patch.object(c, 'api', side_effect=c.ApiError('Model API transport failure', False)) as api:
            with self.assertRaises(c.ApiError):
                c.execute('step')
            self.assertEqual(api.call_count, 1)
        self.until('awaiting_selection')
        state = c.load()
        self.assertIn('not confirmed', state['variants'][0]['error'])
        self.assertEqual(len(self.cloud.posts('/images/generations')), 4)

    def test_no_design_at_all_is_a_failure(self):
        self.cloud.refuse = {1, 2, 3, 4, 5}
        c.execute('init', plan())
        self.assertEqual(self.until('failed')['status'], 'failed')
        self.assertEqual(c.execute('export')['status'], 'failed')

    def test_screening_failure_degrades_without_blocking(self):
        self.cloud.answers['screening'] = [{'summary': 'looks good'}, {'summary': 'still bad'}]
        self.explored()
        self.assertEqual(c.execute('export')['screening'], {'status': 'unavailable'})

    def test_screening_sees_images_not_creator_reasoning(self):
        self.explored()
        body = json.dumps(self.cloud.posts('/responses')[-1])
        self.assertNotIn('CREATOR_PRIVATE_REASONING', body)
        self.assertNotIn('Why it fits', body)

    def test_selection_is_bounded(self):
        self.explored()
        for value in ({'selected': []}, {'selected': ['v1', 'v2', 'v3', 'v4']}, {'selected': ['v1', 'v1']}, {'selected': ['v9']}, None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                c.execute('select', value)
        c.execute('select', {'selected': ['v5', 'v2', 'v1']})
        self.assertEqual(c.load()['selected'], ['v5', 'v2', 'v1'])
        with self.assertRaises(ValueError):
            c.execute('select', {'selected': ['v3']})

    def test_selection_is_refused_before_designs_exist(self):
        c.execute('init', plan())
        with self.assertRaises(ValueError):
            c.execute('select', {'selected': ['v1']})

    # --- production and review ---------------------------------------------

    def test_chosen_design_is_reused_not_regenerated(self):
        self.producing(['v2', 'v4'])
        self.until('completed')
        images = self.cloud.posts('/images/generations')
        self.assertEqual(len(images), 7)
        self.assertEqual([b['image'] for b in images[5:]], ['https://example.com/image-2', 'https://example.com/image-4'])

    def test_revision_then_pass_selects_the_passing_round(self):
        self.producing(['v1', 'v2'])
        first = report()
        first['checks'][0]['evidence'] = 'Required deliverable is missing'
        resolution = report('fail')
        resolution['resolutions'] = [{'id': 'delivery', 'resolved': True, 'reason': 'Actual asset lacks the deliverable'}]
        self.cloud.answers.update(evaluation=[first], audit=[audit(True)], adjudication=[resolution])
        result = self.until('needs_revision')
        self.assertEqual([v['id'] for v in result['revise']], ['v1'])
        self.assertEqual(result['revise'][0]['blocking_checks'], ['delivery'])
        self.assertEqual(result['revise'][0]['rounds_left'], 1)
        self.assertEqual({v['id']: v['status'] for v in result['variants']}, {'v1': 'needs_revision', 'v2': 'completed'})
        contract = c.load()['contract_hash']
        c.execute('revise', {'v1': {'mockup': 'improved mockup', 'video': 'improved video', 'changes': 'Sửa bản in'}})
        self.assertEqual(self.until('completed')['status'], 'completed')
        exported = c.execute('export')
        one = exported['variants'][0]
        self.assertEqual((one['best_round'], one['status'], len(one['rounds'])), (2, 'completed', 2))
        self.assertEqual([r['review']['quality_gate'] for r in one['rounds']], ['blocked', 'passed'])
        self.assertEqual(one['rounds'][1]['changes'], 'Sửa bản in')
        self.assertEqual(one['rounds'][0]['evidence']['source'], 'adjudication')
        self.assertTrue(one['rounds'][1]['design']['reused'])
        self.assertEqual(exported['contract_hash'], contract)
        self.assertEqual(exported['result_summary']['winner'], 'v1')
        self.assertNotIn('checks', one['rounds'][0]['review'])

    def test_revision_covers_exactly_the_variants_that_need_it(self):
        self.producing(['v1', 'v2'])
        self.cloud.answers['evaluation'] = [report('fail'), report('fail')]
        self.until('needs_revision')
        fix = {'mockup': 'better', 'video': 'better'}
        for value in ({'v1': fix}, {'v1': fix, 'v2': fix, 'v3': fix}, {'v1': fix, 'v2': {}}, None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                c.execute('revise', value)
        c.execute('revise', {'v1': fix, 'v2': fix})
        self.assertEqual(c.load()['status'], 'running')

    def test_rewriting_the_design_prompt_regenerates_the_artwork(self):
        self.producing(['v1'])
        self.cloud.answers['evaluation'] = [report('fail')]
        self.until('needs_revision')
        c.execute('revise', {'v1': {'design': 'corrected artwork', 'mockup': 'm', 'video': 'v'}})
        self.until('completed')
        images = self.cloud.posts('/images/generations')
        self.assertTrue(images[-2]['prompt'].startswith('corrected artwork'))
        self.assertEqual(images[-1]['image'], 'https://example.com/image-7')

    def test_unchanged_mockup_is_kept_when_only_the_video_changes(self):
        self.producing(['v1'])
        self.cloud.answers['evaluation'] = [report('fail')]
        self.until('needs_revision')
        before = len(self.cloud.posts('/images/generations'))
        c.execute('revise', {'v1': {'video': 'slower camera move'}})
        self.until('completed')
        self.assertEqual(len(self.cloud.posts('/images/generations')), before)
        self.assertEqual(len(self.cloud.posts('/contents/generations/tasks')), 2)

    def test_round_limit_returns_best_available_without_approval(self):
        self.producing(['v1'], max_rounds=1)
        self.cloud.answers['evaluation'] = [report('fail')]
        self.assertEqual(self.until('max_rounds')['status'], 'max_rounds')
        exported = c.execute('export')
        self.assertFalse(exported['result_summary']['met_target'])
        self.assertEqual(exported['result_summary']['variants'][0]['failed_checks'], ['delivery'])
        with self.assertRaises(ValueError):
            c.execute('revise', {'v1': {'mockup': 'new', 'video': 'new'}})

    def test_missing_sound_blocks_acceptance_even_with_a_perfect_score(self):
        self.producing(['v1'], max_rounds=1)
        with patch.object(media, 'probe', lambda url: dict(SOUND, has_audio=False, audio_codec=None)):
            self.until('max_rounds')
        review = c.load()['variants'][0]['rounds'][0]['review']
        self.assertEqual((review['quality_gate'], review['blocking_checks']), ('blocked', ['tech_audio']))
        self.assertIn('âm thanh', review['priority_fix'])

    def test_uninspectable_video_is_unverified_not_failed(self):
        self.producing(['v1'])
        with patch.object(media, 'probe', lambda url: {'error': 'HTTPError: expired'}):
            self.until('completed')
        technical = c.load()['variants'][0]['rounds'][0]['review']['technical_checks']
        self.assertEqual([t['status'] for t in technical], ['unverified'])

    def test_reviewers_answer_in_the_campaign_language_with_measured_facts(self):
        self.producing(['v1'])
        self.until('completed')
        text = self.cloud.posts('/responses')[-1]['input'][0]['content'][0]['text']
        self.assertIn('in Vietnamese', text)
        self.assertIn('"has_audio": true', text)
        c.ROOT = Path(tempfile.mkdtemp(dir=self.tmp.name))
        c.execute('init', plan(language='en'))
        self.assertIn('in English', self.cloud.posts('/responses')[-1]['input'][0]['content'][0]['text'])

    def test_evaluator_context_excludes_creator_prompts_and_history(self):
        self.producing(['v1'])
        self.until('completed')
        body = next(b for b in self.cloud.posts('/responses') if self.cloud.role(b['input'][0]['content'][0]['text']) == 'evaluation')
        self.assertNotIn('CREATOR_PRIVATE_REASONING', json.dumps(body))
        self.assertNotIn('previous_response_id', body)
        self.assertEqual(len(body['input']), 1)
        self.assertEqual([x['type'] for x in body['input'][0]['content']], ['input_text', 'input_image', 'input_image', 'input_video'])

    def test_creator_cannot_submit_own_score(self):
        c.execute('init', plan())
        with self.assertRaisesRegex(ValueError, 'Manual review'):
            c.execute('review', report())

    def test_bad_evaluation_is_bounded_and_fails_only_that_variant(self):
        self.producing(['v1', 'v2'])
        self.cloud.answers['evaluation'] = [{'summary': 'looks good'}, {'summary': 'looks good'}]
        self.assertEqual(self.until('completed')['status'], 'completed')
        exported = c.execute('export')
        self.assertEqual([v['status'] for v in exported['variants']], ['failed', 'completed'])
        self.assertIn('exhausted', exported['variants'][0]['error'])
        self.assertEqual(exported['result_summary']['winner'], 'v2')

    def test_omitted_requirements_block_instead_of_mutating_contract(self):
        self.producing(['v1'])
        gap = audit()
        gap['uncovered_requirements'] = ['Another explicit user deliverable']
        self.cloud.answers['audit'] = [gap]
        self.assertEqual(self.until('blocked')['status'], 'blocked')
        self.assertEqual(c.execute('export')['variants'][0]['status'], 'blocked')

    def test_export_rejects_fabricated_review(self):
        self.producing(['v1'])
        self.until('completed')
        s = c.load()
        s['variants'][0]['rounds'][0]['review']['score'] = 5
        c.save(s)
        with self.assertRaisesRegex(ValueError, 'differs'):
            c.execute('export')

    def test_export_is_refused_mid_run(self):
        self.producing(['v1'])
        with self.assertRaises(ValueError):
            c.execute('export')

    def test_large_manifest_is_delivered_in_verified_parts(self):
        self.explored()
        with patch.object(c, 'EXPORT_CHUNK', 900):
            index = c.execute('export')
            self.assertEqual((index['export'], index['stage']), ('chunked', 'designs'))
            parts = [c.execute('export', part=i + 1) for i in range(index['parts'])]
            with self.assertRaises(ValueError):
                c.execute('export', part=index['parts'] + 1)
        text = ''.join(p['data'] for p in parts)
        self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), index['sha256'])
        self.assertEqual(json.loads(text), c.execute('export'))
        smaller = c.execute('export', chunk=1000)
        self.assertEqual((smaller['sha256'], smaller['parts'] > 1), (index['sha256'], True))
        self.assertIn('--chunk 1000 --part N', smaller['next_action'])
        self.assertEqual(''.join(c.execute('export', part=i + 1, chunk=1000)['data'] for i in range(smaller['parts'])), text)
        with self.assertRaises(ValueError):
            c.execute('export', chunk=10)

    # --- video failures ----------------------------------------------------

    def fail_next_video(self, code, times=1):
        create = self.cloud.__call__
        left = [times]

        def call(path, body=None, stream=False):
            result = create(path, body, stream)
            if path == '/contents/generations/tasks' and left[0]:
                left[0] -= 1
                self.cloud.tasks[result['id']] = {'status': 'failed', 'error': {'code': code}}
            return result
        patcher = patch.object(c, 'api', call)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_transient_video_retries_are_bounded_and_persisted(self):
        self.producing(['v1'])
        self.fail_next_video('InternalError', times=3)
        with patch.object(c.time, 'sleep'):
            self.assertEqual(self.until('failed')['status'], 'failed')
        r = c.load()['variants'][0]['rounds'][0]
        self.assertEqual((r['video_retries'], len(r['failed_tasks'])), (2, 3))
        self.assertEqual(len(self.cloud.posts('/contents/generations/tasks')), 3)
        self.assertEqual(len(self.cloud.posts('/images/generations')), 6)

    def test_transient_video_failure_recovers(self):
        self.producing(['v1'])
        self.fail_next_video('ServiceUnavailable')
        with patch.object(c.time, 'sleep'):
            self.assertEqual(self.until('completed')['status'], 'completed')

    def test_policy_failure_is_not_retried_and_spares_other_variants(self):
        self.producing(['v1', 'v2'])
        self.fail_next_video(c.AUDIO_REJECTION)
        self.assertEqual(self.until('completed')['status'], 'completed')
        one, two = c.load()['variants'][:2]
        self.assertEqual((one['status'], one['error_code'], two['status']), ('failed', c.AUDIO_REJECTION, 'completed'))
        self.assertNotIn('video_retries', one['rounds'][0])

    def test_silent_replacement_needs_the_specific_audio_rejection(self):
        self.producing(['v1', 'v2'])
        self.fail_next_video(c.AUDIO_REJECTION)
        self.until('completed')
        with self.assertRaises(ValueError):
            c.execute('retry-silent-video', variant='v2')
        c.execute('retry-silent-video', variant='v1')
        with patch.object(media, 'probe', lambda url: dict(SOUND, has_audio=False, audio_codec=None)):
            self.until('completed')
        self.assertIs(self.cloud.posts('/contents/generations/tasks')[-1]['generate_audio'], False)
        one = c.load()['variants'][0]
        self.assertEqual((one['status'], one['rounds'][0]['review']['quality_gate']), ('completed', 'passed'))
        with self.assertRaises(ValueError):
            c.execute('retry-silent-video', variant='v1')

    def test_unconfirmed_video_submission_is_never_repeated(self):
        self.producing(['v1', 'v2'])
        self.until('mockup_completed')
        self.until('mockup_completed')
        with patch.object(c, 'api', side_effect=c.ApiError('Model API transport failure', False)) as api:
            with self.assertRaises(c.ApiError):
                c.execute('step')
            self.assertEqual(api.call_count, 1)
        self.until('completed')
        one, two = c.load()['variants'][:2]
        self.assertEqual((one['status'], two['status']), ('failed', 'completed'))
        self.assertEqual(len(self.cloud.posts('/contents/generations/tasks')), 1)

    def test_videos_are_submitted_together_before_polling(self):
        self.producing(['v1', 'v2', 'v3'])
        with patch.dict(os.environ, {'STEP_BUDGET_SECONDS': '60'}):
            c.execute('step')
        order = [p for p, _ in self.cloud.calls if p.startswith('/contents')]
        self.assertEqual(order[:3], ['/contents/generations/tasks'] * 3)


class RuleTests(unittest.TestCase):
    def test_limit_prefers_highest_passing_gate_over_failed_higher_score(self):
        v = {'status': 'max_rounds', 'rounds': [
            {'number': 1, 'review': {'score': 4.8, 'quality_gate': 'blocked'}},
            {'number': 2, 'review': {'score': 4.7, 'quality_gate': 'passed'}}]}
        self.assertEqual(c.selected_round(v)['number'], 2)

    def test_limit_falls_back_to_highest_score_and_ties_keep_earliest(self):
        rounds = lambda a, b: {'status': 'max_rounds', 'rounds': [{'number': 1, 'review': {'score': a, 'quality_gate': 'blocked'}}, {'number': 2, 'review': {'score': b, 'quality_gate': 'blocked'}}]}
        self.assertEqual(c.selected_round(rounds(4.8, 4.4))['number'], 1)
        self.assertEqual(c.selected_round(rounds(4, 4))['number'], 1)

    def test_early_pass_returns_current_passing_round(self):
        v = {'status': 'completed', 'rounds': [{'number': 1, 'review': {'score': 4.9}}, {'number': 2, 'review': {'score': 4.6}}]}
        self.assertEqual(c.selected_round(v)['number'], 2)

    def test_winner_prefers_an_accepted_variant_over_a_higher_score(self):
        review = lambda score, gate: {'score': score, 'quality_gate': gate}
        state = {'selected': ['v1', 'v2', 'v3'], 'variants': [
            {'id': 'v1', 'selected': True, 'status': 'max_rounds', 'rounds': [{'number': 1, 'review': review(4.9, 'blocked')}]},
            {'id': 'v2', 'selected': True, 'status': 'completed', 'rounds': [{'number': 1, 'review': review(4.6, 'passed')}]},
            {'id': 'v3', 'selected': True, 'status': 'failed', 'rounds': [{'number': 1}]}]}
        self.assertEqual(c.winner(state)['id'], 'v2')

    def test_dynamic_contract_accepts_different_criteria_counts(self):
        value = rubric()
        value.append({'id': 'something-else', 'description': 'Another requirement', 'source_requirement': 'Another request', 'required': True, 'priority': 3, 'weight': 2, 'asset_refs': ['video']})
        self.assertEqual(len(ev.criteria(value)), 3)
        with self.assertRaises(ValueError):
            ev.criteria(value + [value[0]])
        value[0]['label'] = ' '
        with self.assertRaises(ValueError):
            ev.criteria(value)

    def test_optional_failure_affects_score_not_required_gate(self):
        r = report()
        r['checks'][1].update(status='fail', score=4.5)
        review = ev.effective_review(rubric(), r, audit())
        self.assertEqual((review['quality_gate'], review['score']), ('passed', 4.6))

    def test_review_carries_display_labels(self):
        checks = ev.effective_review(rubric(), report(), audit())['checks']
        self.assertEqual([x['label'] for x in checks], ['Giao đúng sản phẩm yêu cầu', 'Preferred visual style'])

    def test_required_unverified_blocks_even_high_score(self):
        self.assertEqual(ev.effective_review(rubric(), report('unverified'), audit())['quality_gate'], 'blocked')

    def test_unresolved_conflict_cannot_pass(self):
        r = report()
        r['resolutions'] = [{'id': 'delivery', 'resolved': False, 'reason': 'Not enough evidence'}]
        result = ev.effective_review(rubric(), report(), audit(True), r)
        self.assertEqual((result['checks'][0]['status'], result['quality_gate']), ('unverified', 'blocked'))

    def test_conflict_requires_complete_adjudication(self):
        with self.assertRaises(ValueError):
            ev.effective_review(rubric(), report(), audit(True))
        r = report()
        r['resolutions'] = []
        with self.assertRaises(ValueError):
            ev.effective_review(rubric(), report(), audit(True), r)

    def test_report_rejects_missing_duplicate_unknown_ids_and_scores(self):
        for mutation in ('missing', 'duplicate', 'unknown', 'score'):
            r = report()
            if mutation == 'missing': r['checks'].pop()
            elif mutation == 'duplicate': r['checks'][1]['id'] = 'delivery'
            elif mutation == 'unknown': r['checks'][1]['id'] = 'other'
            else: r['checks'][0]['score'] = float('nan')
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                ev.validate_report(r, rubric())

    def test_weighted_score_uses_contract_not_reviewer_weights(self):
        value = rubric()
        value[0]['weight'] = 3
        r = report()
        r['checks'][0]['score'] = 4
        r['checks'][1]['score'] = 5
        self.assertEqual(ev.effective_review(value, r, audit())['score'], 4.25)

    def test_screening_must_rank_every_candidate_once(self):
        good = Cloud().default('screening', {'input': [{'content': [0, 1, 2, 3]}]})
        self.assertEqual(ev.validate_screening(copy.deepcopy(good), ['v1', 'v2', 'v3'], 3), good)
        for mutation in ('missing', 'score', 'too_many', 'stranger'):
            value = copy.deepcopy(good)
            if mutation == 'missing': value['ranking'].pop()
            elif mutation == 'score': value['ranking'][0]['score'] = 9
            elif mutation == 'too_many': value['recommended'] = ['v1', 'v2', 'v3']
            else: value['recommended'] = ['v7']
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                ev.validate_screening(value, ['v1', 'v2', 'v3'], 2 if mutation == 'too_many' else 3)

    def test_fenced_reviewer_json_is_accepted_but_prose_is_not(self):
        self.assertEqual(ev.parse('```json\n{"a":1}\n```'), {'a': 1})
        self.assertEqual(ev.parse('```\n{"a":1}\n```'), {'a': 1})
        for text in ('Here you go: {"a":1}', '[1]'):
            with self.assertRaises(ValueError):
                ev.parse(text)

    def test_stream_requires_completed(self):
        with self.assertRaises(RuntimeError):
            c.response_stream([b'data: [DONE]\n', b'\n'])
        with self.assertRaises(RuntimeError):
            c.response_stream([b'data: {"type":"response.incomplete"}\n', b'\n'])
        event = {'type': 'response.completed', 'response': {'status': 'completed', 'id': 'r'}}
        self.assertEqual(c.response_stream([('data: ' + json.dumps(event) + '\n').encode(), b'\n'])['id'], 'r')

    def test_only_safe_requests_are_repeated(self):
        os.environ['ARK_API_KEY'] = 'test-key-not-a-real-credential'
        for code, body, count, certain in ((503, None, 3, False), (503, {'prompt': 'test'}, 1, False), (429, {'prompt': 'test'}, 3, True), (400, {'prompt': 'test'}, 1, True)):
            error = c.urllib.error.HTTPError('https://example.com', code, 'refused', {}, None)
            with self.subTest(code=code, body=body), patch.object(c.urllib.request, 'urlopen', side_effect=error) as request, patch.object(c.time, 'sleep'):
                with self.assertRaises(c.ApiError) as raised:
                    c.api('/test', body)
                self.assertEqual((request.call_count, raised.exception.certain), (count, certain))

    def test_errors_never_echo_the_credential(self):
        os.environ['ARK_API_KEY'] = 'test-key-not-a-real-credential'
        with patch.object(c.urllib.request, 'urlopen', side_effect=c.urllib.error.URLError('test-key-not-a-real-credential')):
            with self.assertRaises(c.ApiError) as raised:
                c.api('/test', {'prompt': 'x'})
        self.assertNotIn('test-key', str(raised.exception))


class MediaTests(unittest.TestCase):
    def movie(self, audio):
        box = lambda kind, payload: struct.pack('>I4s', 8 + len(payload), kind) + payload
        def trak(handler, codec, width=0, height=0):
            sample = box(b'stsd', bytes(8) + struct.pack('>I4s', 16, codec) + bytes(8))
            return box(b'trak', box(b'tkhd', bytes(76) + struct.pack('>II', width << 16, height << 16))
                       + box(b'mdia', box(b'hdlr', bytes(8) + handler + bytes(12)) + box(b'minf', box(b'stbl', sample))))
        tracks = trak(b'vide', b'avc1', 720, 1280) + (trak(b'soun', b'mp4a') if audio else b'')
        header = box(b'mvhd', bytes(12) + struct.pack('>II', 1000, 5042) + bytes(80))
        return box(b'ftyp', b'isom' + bytes(4)) + box(b'mdat', bytes(64)) + box(b'moov', header + tracks)

    def test_audio_track_is_detected(self):
        facts = media.inspect(self.movie(True))
        self.assertEqual((facts['has_audio'], facts['audio_codec'], facts['width'], facts['height'], facts['duration_seconds']), (True, 'mp4a', 720, 1280, 5.042))
        self.assertEqual([t['status'] for t in ev.technical_checks(facts, True)], ['pass', 'pass', 'pass'])

    def test_silent_file_fails_the_sound_check_only_when_sound_was_requested(self):
        facts = media.inspect(self.movie(False))
        self.assertIs(facts['has_audio'], False)
        self.assertEqual(ev.technical_checks(facts, True)[0]['status'], 'fail')
        self.assertEqual(ev.technical_checks(facts, False)[0]['status'], 'pass')

    def test_archived_generated_video_is_readable(self):
        path = Path(__file__).parent / 'docs/assets/retest-20260928/round-2-video.mp4'
        facts = media.inspect(path.read_bytes())
        self.assertEqual((facts['width'], facts['height'], facts['has_audio'], facts['video_codec']), (720, 1280, False, 'avc1'))

    def test_unreadable_media_is_reported_not_raised(self):
        self.assertIn('error', media.probe('http://example.com/video.mp4'))
        with self.assertRaises(ValueError):
            media.inspect(b'not a video')


class ResearchTests(unittest.TestCase):
    def test_calendar_computes_movable_dates(self):
        found = {o['id']: o for o in rs.calendar(date(2026, 9, 30), 250)}
        self.assertEqual([found[k]['date'] for k in ('halloween', 'thanksgiving', 'black_friday', 'cyber_monday', 'hanukkah', 'christmas', 'valentines', 'easter', 'mothers_day')],
                         ['2026-10-31', '2026-11-26', '2026-11-27', '2026-11-30', '2026-12-04', '2026-12-25', '2027-02-14', '2027-03-28', '2027-05-09'])
        self.assertEqual(found['christmas']['days_until'], 86)
        self.assertEqual((found['christmas']['listing_live_by'], found['christmas']['order_cutoff_estimate']), ('2026-10-30', '2026-12-11'))
        self.assertEqual((found['black_friday']['kind'], found['black_friday']['order_cutoff_estimate']), ('sale_event', None))

    def test_calendar_is_sorted_and_bounded(self):
        found = rs.calendar(date(2026, 12, 20), 30)
        self.assertEqual([o['id'] for o in found], ['christmas', 'kwanzaa', 'new_year'])
        self.assertEqual(found[0]['window'], 'last_call')

    def test_storefront_refuses_private_or_malformed_hosts(self):
        for host in ('localhost', '127.0.0.1', '10.0.0.8', 'intranet.local', 'bad host', ''):
            with self.subTest(host=host), self.assertRaises(ValueError):
                rs.public_host(host)
        self.assertEqual(rs.public_host('https://Shop.Example.com/collections/all'), 'shop.example.com')

    def test_storefront_summary_reads_only_public_catalog_fields(self):
        product = lambda i: {'title': 'Personalized Dog Mom Mug %d' % i, 'handle': 'mug-%d' % i, 'product_type': 'Mug', 'tags': ['dog', 'mom'],
                             'published_at': '2026-09-%02dT10:00:00-04:00' % (i + 1), 'variants': [{'price': '19.95'}, {'price': '24.95'}], 'images': [{'src': 'https://cdn.example.com/%d.jpg' % i}]}
        feeds = {'/products.json?limit=60': [product(i) for i in range(4)], '/collections/best-sellers/products.json?limit=20': [product(9)]}
        rules = type('Rules', (), {'read': lambda self: None, 'can_fetch': lambda self, agent, url: 'sort_by' not in url})
        with patch.object(rs.urllib.robotparser, 'RobotFileParser', lambda url: rules()), patch.object(rs.time, 'sleep'), \
                patch.object(rs, 'fetch', lambda url: {'products': feeds[url.split('example.com', 1)[1]]}):
            summary = rs.storefront('shop.example.com')
        self.assertEqual((summary['status'], summary['products_read'], summary['personalized_share']), ('ok', 4, 1.0))
        self.assertNotIn('price', summary)
        self.assertNotIn('price_from', summary['newest'][0])
        self.assertEqual((summary['store_url'], summary['best_sellers_url']), ('https://shop.example.com/collections/all', 'https://shop.example.com/collections/best-sellers'))
        self.assertEqual(summary['newest'][0]['published'], '2026-09-04')
        self.assertEqual(summary['merchant_best_sellers'][0]['url'], 'https://shop.example.com/products/mug-9')
        self.assertEqual(summary['title_keywords'][0], ('dog', 4))

    def test_storefront_respects_robots_and_does_not_work_around_blocks(self):
        rules = type('Rules', (), {'read': lambda self: None, 'can_fetch': lambda self, agent, url: False})
        with patch.object(rs.urllib.robotparser, 'RobotFileParser', lambda url: rules()), patch.object(rs, 'fetch') as fetch:
            summary = rs.storefront('shop.example.com')
        self.assertEqual(summary['status'], 'unavailable')
        fetch.assert_not_called()


if __name__ == '__main__':
    unittest.main()
