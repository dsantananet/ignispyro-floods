import unittest,numpy as np
from hydraulics import section_properties,solve_stage,linear_reservoir,connected_wet,terrain_footprint
class HydraulicTests(unittest.TestCase):
 def test_rectangular_manning_solution(self):
  x=np.arange(-100,101,1,dtype=float);z=np.where(abs(x)<=20,0,30).astype(float);q,a,v=section_properties(x,z,2,.001,40,.035,.08);stage,_,_=solve_stage(x,z,q,.001,40,.035,.08);self.assertAlmostEqual(stage,2,places=8);self.assertGreater(q,0)
 def test_rating_monotonic(self):
  x=np.linspace(-100,100,201);z=.001*x*x;q=[section_properties(x,z,h,.001,30,.04,.08)[0] for h in [1,2,3,4]];self.assertEqual(q,sorted(q))
 def test_routing_conserves_water(self):
  q,b=linear_reservoir([2,4,30,70,10,0]*10,3600,10800);self.assertLess(abs(b['mass_balance_error_m3']),1e-6);self.assertTrue(all(x>=0 for x in q))
 def test_unconnected_depression_not_inundated(self):
  terrain=np.ones((5,7))*10;terrain[2,0:2]=0;terrain[2,4:7]=0;seed=np.zeros((5,7),bool);seed[2,0]=True;wet=connected_wet(terrain,np.ones((5,7))*2,seed,np.ones((5,7),bool));self.assertTrue(wet[2,1]);self.assertFalse(wet[2,5])
 def test_no_overbank_water_without_available_volume(self):
  dem=np.zeros((4,4));channel=np.zeros((4,4),bool);channel[:,0]=True;d,m,b=terrain_footprint(dem,np.ones((4,4)),channel,channel,np.ones((4,4),bool),900,.15,0);self.assertEqual(m.sum(),0);self.assertLessEqual(b['mapped_overbank_storage_m3'],1e-6)
 def test_volume_constraint(self):
  dem=np.zeros((4,4));channel=np.zeros((4,4),bool);channel[:,0]=True;d,m,b=terrain_footprint(dem,np.ones((4,4))*2,channel,channel,np.ones((4,4),bool),900,.15,8000);self.assertLessEqual(b['mapped_overbank_storage_m3'],8000+1e-5)
if __name__=='__main__':unittest.main()
