"""Local CPU integration checks; development cases, not a benchmark."""
import json,socket,time,unittest
from pathlib import Path
from infer import Inference

class OfflineInferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def prohibited(*args,**kwargs):raise AssertionError('Inference attempted network access')
        socket.create_connection=prohibited;socket.socket.connect=prohibited
        cls.engine=Inference(Path(__file__).resolve().parent.parent/'model/neural')
    def test_repeatability_and_spans(self):
        jp='全員が試験に合格したわけではない。';en='Nobody passed the exam.'
        one=self.engine.analyze(jp,en);two=self.engine.analyze(jp,en)
        self.assertEqual(one['probabilityAltered'],two['probabilityAltered'])
        for name,text in [('japanese',jp),('english',en)]:
            for span in one['neuralSpans'][name]:self.assertEqual(text.encode('utf-16-le')[span['start']*2:span['end']*2].decode('utf-16-le'),span['text'])
    def test_long_inputs_abstain(self):
        result=self.engine.analyze('これは長い文章です。'*100,'This is a long sentence. '*100)
        self.assertEqual(result['verdict'],'uncertain');self.assertIsNone(result['probabilityAltered'])
    def test_multi_head_output(self):
        result=self.engine.analyze('彼は犯人ではない可能性が高い。','He is probably the culprit.')
        self.assertEqual(len(result['categoryScores']),10);self.assertGreaterEqual(result['probabilityAltered'],0);self.assertLessEqual(result['probabilityAltered'],1)

if __name__=='__main__':unittest.main()
