import unittest
from calibration import fit_rating,predict_rating
class CalibrationTests(unittest.TestCase):
 def test_no_calibration_without_real_pairs(self):
  with self.assertRaises(ValueError):fit_rating([], '12G/04H','SNIRH')
 def test_events_held_out_and_no_extrapolation(self):
  rows=[{'station_id':'test','vertical_datum':'test','qc':'accepted','event_id':str(e),'stage_m':1+i/10,'flow_m3s':10*(1+i/10+.4)**1.7} for e in range(3) for i in range(30)]
  fit=fit_rating(rows,'test','test');self.assertEqual(fit['held_out_event'],'2');self.assertLess(fit['validation_rmse_m3s'],1);self.assertFalse(fit['operational_accepted'])
  with self.assertRaises(ValueError):predict_rating(fit,20)
 def test_different_datum_or_station_not_merged(self):
  with self.assertRaises(ValueError):fit_rating([{'station_id':'wrong','vertical_datum':'wrong'}]*100,'Santa Clara','EGM2008')
