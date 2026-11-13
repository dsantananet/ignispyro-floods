import unittest,numpy as np
from terrain import nearest_drainage_hand,slope_degrees,zonal_fraction,roc_auc
class TerrainTests(unittest.TestCase):
 def test_hand_on_valley(self):
  x=np.arange(-50,51);dem=np.tile(np.abs(x)*.5,(11,1)).astype(float);drain=np.zeros(dem.shape,bool);drain[:,50]=True
  hand,dist=nearest_drainage_hand(dem,drain,30,30,max_distance_m=1e6)
  self.assertEqual(hand[5,50],0);self.assertAlmostEqual(hand[5,60],5.);self.assertAlmostEqual(dist[5,60],300.)
 def test_far_cells_are_unknown_not_zero(self):
  dem=np.zeros((3,100));drain=np.zeros(dem.shape,bool);drain[:,0]=True;hand,_=nearest_drainage_hand(dem,drain,30,30,max_distance_m=300)
  self.assertTrue(np.isnan(hand[1,99]));self.assertEqual(hand[1,5],0)
 def test_requires_drainage(self):
  with self.assertRaises(ValueError):nearest_drainage_hand(np.zeros((3,3)),np.zeros((3,3),bool),30,30)
 def test_slope_of_plane(self):
  dem=np.tile(np.arange(10)*30.,(10,1));self.assertAlmostEqual(float(slope_degrees(dem,30,30)[5,5]),45,places=6)
 def test_zonal_fraction(self):
  labels=np.array([[1,1],[2,2]]);mask=np.array([[True,False],[False,False]]);f=zonal_fraction(labels,mask,3);self.assertEqual(f[0],.5);self.assertEqual(f[1],0);self.assertTrue(np.isnan(f[2]))
 def test_auc(self):
  self.assertEqual(roc_auc([1,2,3,4],[0,0,1,1]),1.);self.assertEqual(roc_auc([4,3,2,1],[0,0,1,1]),0.);self.assertEqual(roc_auc([1,1,1,1],[0,0,1,1]),.5);self.assertIsNone(roc_auc([1,2],[1,1]))
if __name__=='__main__':unittest.main()

class ParishStatsTests(unittest.TestCase):
 def test_valley_parish_has_more_low_hand_than_upland_parish(self):
  from terrain import parish_terrain_stats
  x=np.arange(-60,61);dem=np.tile(np.abs(x)*1.5,(40,1)).astype(float);drain=np.zeros(dem.shape,bool);drain[:,60]=True
  labels=np.zeros(dem.shape,int);labels[:,55:66]=1;labels[:,100:120]=2
  r=parish_terrain_stats(dem,drain,labels,2,.0009,39.5,hand_threshold_m=5,max_distance_m=1e6)
  self.assertGreater(r['hand_lt_threshold_frac'][0],r['hand_lt_threshold_frac'][1]);self.assertEqual(r['dem_coverage_frac'][0],1.)
