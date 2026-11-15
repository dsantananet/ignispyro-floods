import unittest

import numpy as np

from shallow_water import simulate


class ShallowWaterTest(unittest.TestCase):
    def test_lake_at_rest_across_dry_shoreline_and_slopes(self):
        bed = np.array([[0, 0.4, 1.5], [0.2, 0.8, 2], [0, 0.3, 1.1]])
        depth = np.maximum(1 - bed, 0)
        _, (last, stats) = simulate(bed, depth, 10, [0, 120], np.zeros((1, *bed.shape)))
        np.testing.assert_allclose(last, depth, atol=1e-12)
        self.assertAlmostEqual(stats["mass_error_m3"], 0, places=9)

    def test_dam_break_spreads_in_two_dimensions_and_conserves_mass(self):
        bed = np.zeros((21, 21))
        depth = bed.copy()
        depth[10, 10] = 2
        _, (last, stats) = simulate(bed, depth, 5, [0, 10], np.zeros((1, *bed.shape)))
        self.assertGreater(last[10, 12], 0)
        self.assertGreater(last[12, 10], 0)
        self.assertGreaterEqual(last.min(), 0)
        np.testing.assert_allclose(last, last.T, atol=1e-12)
        self.assertAlmostEqual(stats["mass_error_m3"], 0, places=9)

    def test_forcing_and_unavailable_withdrawal(self):
        bed = np.zeros((1, 1))
        frames = list(simulate(bed, bed, 10, [0, 15, 30], [[[2]], [[-3]]]))
        self.assertAlmostEqual(frames[1][1]["water_volume_m3"], 30)
        self.assertAlmostEqual(frames[2][1]["water_volume_m3"], 0)
        self.assertAlmostEqual(frames[2][1]["unmet_withdrawal_m3"], 15)
        self.assertAlmostEqual(frames[2][1]["mass_error_m3"], 0)

    def test_invalid_forcing_has_no_frames(self):
        with self.assertRaises(ValueError):
            list(simulate([[0]], [[0]], 10, [0, 15], [[[np.nan]]]))
