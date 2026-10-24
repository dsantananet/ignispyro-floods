import unittest
import numpy as np
from validation import overlap_metrics

class SpatialValidationTests(unittest.TestCase):
    def test_domain_excludes_unknown_and_permanent_water(self):
        p=np.array([[1,1],[0,1]],bool);o=np.array([[1,0],[1,0]],bool)
        d=np.array([[1,1],[1,0]],bool);m=overlap_metrics(p,o,d,900)
        self.assertEqual(m['intersection_m2'],900)
        self.assertAlmostEqual(m['iou_diagnostic'],1/3)
        self.assertFalse(m['operationally_accepted'])
    def test_empty_observations_do_not_mean_perfect_validation(self):
        z=np.zeros((2,2),bool);m=overlap_metrics(z,z,~z,900)
        self.assertIsNone(m['iou_diagnostic']);self.assertIsNone(m['observed_recall_diagnostic'])
    def test_empty_domain_rejected(self):
        z=np.zeros((2,2),bool)
        with self.assertRaises(ValueError):overlap_metrics(z,z,z,900)
