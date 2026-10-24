import unittest
from coimbra_weir import integrate_boundary_volume,discharge_from_fitted_weir,terminal_release_sum
class WeirTests(unittest.TestCase):
 def test_observed_flow_is_integrated_without_duplicating_cascade(self):
  self.assertEqual(terminal_release_sum(20,3,7),30);self.assertIsNone(terminal_release_sum(20,None,7))
 def test_volume_and_missing_interval(self):
  b=integrate_boundary_volume({0:10,3600:20,20000:15},{0:5,3600:5,20000:5});self.assertEqual(b['inflow_volume_estimate_m3'],54000);self.assertEqual(b['net_storage_change_estimate_m3'],36000);self.assertEqual(b['rejected_gaps'],1)
 def test_unknown_gates_and_extrapolation_are_rejected(self):
  f={'crest_m':14.3,'head_min_m':3.5,'head_max_m':4.2,'coefficient_m05_s':1.5,'width_m':138.6}
  with self.assertRaises(ValueError):discharge_from_fitted_weir(18,f,'unknown')
  with self.assertRaises(ValueError):discharge_from_fitted_weir(20,f,'all_gates_open_verified')
  self.assertGreater(discharge_from_fitted_weir(18,f,'all_gates_open_verified'),0)
