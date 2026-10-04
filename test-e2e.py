"""Drives the helper exactly as the agent does: real command line, real HTTP and SSE, against a stand-in model API."""
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest

here = Path(__file__).parent
spec = importlib.util.spec_from_file_location('suite', here / 'test-cloud.py')
suite = importlib.util.module_from_spec(spec)
spec.loader.exec_module(suite)
KEY = 'test-key-not-a-real-credential'


class Api(BaseHTTPRequestHandler):
    cloud = None
    seen = []

    def log_message(self, *args):
        pass

    def answer(self, body):
        path = self.path.replace('/api/v3', '', 1)
        Api.seen.append((self.command, path, self.headers.get('Authorization')))
        try:
            result = Api.cloud(path, body)
        except suite.c.ApiError as error:
            payload = json.dumps({'error': {'code': error.code, 'message': 'refused'}}).encode()
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if path == '/responses':
            events = [{'type': 'response.created'}, {'type': 'response.completed', 'response': dict(result, status='completed')}]
            payload = ''.join('data: %s\n\n' % json.dumps(e) for e in events).encode() + b'data: [DONE]\n\n'
            kind = 'text/event-stream'
        else:
            payload, kind = json.dumps(result).encode(), 'application/json'
        self.send_response(200)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        self.answer(None)

    def do_POST(self):
        self.answer(json.loads(self.rfile.read(int(self.headers['Content-Length']))))


class CommandLine(unittest.TestCase):
    def setUp(self):
        Api.cloud, Api.seen = suite.Cloud(), []
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Api)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.tmp = tempfile.TemporaryDirectory()
        self.env = dict(os.environ, ARK_API_KEY=KEY, ARK_BASE_URL='http://127.0.0.1:%d/api/v3' % self.server.server_address[1],
                        CREATIVE_WORKDIR=self.tmp.name + '/loop', STEP_BUDGET_SECONDS='30', POLL_SECONDS='0', POLL_INTERVAL='0')

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.tmp.cleanup()

    def run_helper(self, *args, value=None, code=0, script='creative.py'):
        if value is not None:
            path = Path(self.tmp.name) / 'input.json'
            path.write_text(json.dumps(value, ensure_ascii=False))
            args += ('--input', str(path))
        done = subprocess.run([sys.executable, str(here / 'skills/pod-creative-loop/scripts' / script), *args], env=self.env, capture_output=True, text=True, timeout=120)
        self.assertEqual(done.returncode, code, done.stdout + done.stderr)
        self.assertEqual(done.stdout.count('\n'), 1, 'the helper prints exactly one JSON line')
        self.assertNotIn(KEY, done.stdout + done.stderr)
        return json.loads(done.stdout)

    def until(self, *statuses):
        for _ in range(40):
            result = self.run_helper('step')
            if result['status'] in statuses:
                return result
        self.fail('never reached ' + '/'.join(statuses))

    def test_a_whole_campaign(self):
        Api.cloud.answers['contract'] = [{'summary': 'Thiếu', 'gaps': [{'requirement': 'Không có nhạc', 'suggestion': 'Thêm tiêu chí'}], 'unsupported': []}]
        Api.cloud.answers['evaluation'] = [suite.report('fail')]
        self.assertEqual(self.run_helper('init', value=suite.plan())['status'], 'contract_gaps')
        self.assertEqual(self.run_helper('init', value=suite.plan())['status'], 'running')
        self.assertIn('Existing loop', self.run_helper('init', value=suite.plan(), code=1)['error'])
        self.assertIn('not finished', self.run_helper('export', code=1)['error'])

        waiting = self.until('awaiting_selection')
        self.assertEqual([x['unit'] for x in waiting['log']], ['design'] * 5 + ['screening'])
        index = self.run_helper('export', '--chunk', '2000')
        text = ''.join(self.run_helper('export', '--chunk', '2000', '--part', str(i + 1))['data'] for i in range(index['parts']))
        self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), index['sha256'])
        designs = json.loads(text)
        self.assertEqual((designs['stage'], designs['language'], len(designs['variants'])), ('designs', 'vi', 5))
        self.assertTrue(designs['research']['seasonal_calendar'])

        self.assertIn('Manual review', self.run_helper('review', code=1)['error'])
        self.assertEqual(self.run_helper('select', value={'selected': ['v3', 'v1']})['status'], 'running')
        revising = self.until('needs_revision')
        self.assertEqual([v['id'] for v in revising['revise']], ['v3'])
        self.assertEqual(self.run_helper('status')['status'], 'needs_revision')
        self.assertEqual(self.run_helper('revise', value={'v3': {'video': 'slower move', 'changes': 'Quay chậm hơn'}})['status'], 'running')
        self.assertEqual(self.until(*suite.c.TERMINAL)['status'], 'completed')

        final = self.run_helper('export')
        self.assertEqual((final['stage'], final['selected'], final['result_summary']['winner']), ('final', ['v3', 'v1'], 'v3'))
        self.assertEqual([len(v['rounds']) for v in final['variants']], [2, 1])
        # The stand-in serves media from a host that does not exist, so inspection is honestly reported as unverified.
        self.assertEqual(final['variants'][0]['rounds'][0]['technical'][0]['status'], 'unverified')
        self.assertEqual(len([1 for method, path, _ in Api.seen if method == 'POST' and path == '/contents/generations/tasks']), 3)
        self.assertTrue(all(auth == 'Bearer ' + KEY for _, _, auth in Api.seen))
        self.assertIs(Api.cloud.posts('/contents/generations/tasks')[0]['generate_audio'], True)

    def test_a_refused_request_is_reported_with_the_provider_code(self):
        Api.cloud.refuse = {1}
        self.run_helper('init', value=suite.plan())
        self.until('awaiting_selection')
        first = self.run_helper('export', '--chunk', '60000', '--part', '1')
        self.assertIn('InputTextSensitiveContentDetected', json.loads(first['data'])['variants'][0]['error'])

    def test_calendar_and_research_validation_commands(self):
        calendar = self.run_helper('calendar', '--today', '2026-09-30', '--days', '90', script='research.py')
        self.assertEqual(calendar['occasions'][-1]['id'], 'kwanzaa')
        self.assertEqual(self.run_helper('validate', value=suite.research(), script='research.py'), {'valid': True, 'sources': 8, 'channels': 8, 'by_channel': {k: 1 for k in ('amazon', 'etsy', 'competitor_store', 'tiktok', 'trends', 'industry', 'pinterest', 'meta_ads')}, 'status': 'complete'})
        self.assertIn('limited', self.run_helper('validate', value=dict(suite.research(2), competitor_designs=[]), code=1, script='research.py')['error'])
        self.assertIn('public storefront', self.run_helper('storefront', '--store', '127.0.0.1', code=1, script='research.py')['error'])


if __name__ == '__main__':
    unittest.main()
