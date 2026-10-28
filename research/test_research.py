import unittest
import numpy as np
from contrastive import generate
from evaluation import metrics
from schema import LABELS

class ResearchTests(unittest.TestCase):
    def test_no_false_positive_span_targets_on_correct_pairs(self):
        for row in generate():
            if not row['altered']:
                self.assertEqual(row['english_spans'],[]);self.assertEqual(row['japanese_spans'],[])
    def test_template_groups_do_not_leak(self):
        groups={}
        for row in generate():
            if row['group'] in groups:self.assertEqual(groups[row['group']],row['split'])
            groups[row['group']]=row['split']
    def test_abstention_is_not_success(self):
        labels=np.array([[0]+[0]*len(LABELS),[1]+[1]*len(LABELS)])
        logits=np.zeros(labels.shape)
        result=metrics(labels,logits,thresholds={'altered':.9,'preserved':.1})
        self.assertEqual(result['selective']['coverage'],0)
        self.assertEqual(result['selective']['resolved_correct_fraction'],0)
        self.assertIsNone(result['selective']['selective_accuracy'])
    def test_unknown_labels_are_masked(self):
        labels=np.array([[0]+[-1]*len(LABELS),[1]+[1]*len(LABELS)])
        logits=np.ones(labels.shape)
        for value in metrics(labels,logits)['categories'].values():self.assertEqual(value['known'],1)

if __name__=='__main__':unittest.main()
