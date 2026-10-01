"""Prints manifests produced by the real helper against a stand-in model API, for the bridge tests."""
import importlib.util
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('suite', Path(__file__).parent / 'test-cloud.py')
suite = importlib.util.module_from_spec(spec)
spec.loader.exec_module(suite)
c = suite.c
os.environ['ARK_API_KEY'] = 'test-key-not-a-real-credential'


def until(*statuses):
    for _ in range(200):
        result = c.execute('step')
        if result['status'] in statuses:
            return result
    raise RuntimeError('never reached ' + '/'.join(statuses))


with tempfile.TemporaryDirectory() as tmp, patch.object(c, 'ROOT', Path(tmp)), patch.object(suite.media, 'probe', lambda url: dict(suite.SOUND)):
    cloud = suite.Cloud()
    disputed = suite.report()
    disputed['checks'][0]['evidence'] = 'Required deliverable is missing'
    settled = suite.report('fail')
    settled['resolutions'] = [{'id': 'delivery', 'resolved': True, 'reason': 'Actual asset lacks the deliverable'}]
    cloud.answers.update(evaluation=[disputed, suite.report(), suite.report('fail'), suite.report(score=4.9), suite.report('fail', 3.9)],
                         audit=[suite.audit(True)], adjudication=[settled])
    with patch.object(c, 'api', cloud):
        started = c.execute('init', suite.plan())
        waiting = until('awaiting_selection')
        explore = c.execute('export')
        index = c.execute('export', chunk=1000)
        parts = [c.execute('export', part=i + 1, chunk=1000) for i in range(index['parts'])]
        c.execute('select', {'selected': ['v2', 'v4', 'v1']})
        revising = until('needs_revision')
        c.execute('revise', {'v2': {'mockup': 'better mockup', 'video': 'better video', 'changes': 'Làm rõ chữ in'},
                             'v1': {'design': 'corrected artwork', 'mockup': 'better mockup', 'video': 'better video'}})
        done = until(*c.TERMINAL)
        final = c.execute('export')
print(json.dumps({'brief': suite.plan()['brief'], 'explore': explore, 'final': final, 'index': index, 'parts': parts,
                  'progress': [started, waiting, revising, done]}, ensure_ascii=False))
