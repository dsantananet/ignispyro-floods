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


class StandardStepTests(unittest.TestCase):
 def setUp(self):
  from hydraulics import standard_step,section_hydraulics
  self.ss=standard_step;self.sh=section_hydraulics
  self.x=np.arange(-300,301,2.,dtype=float);self.z=np.where(abs(self.x)<=25,0.,np.where(abs(self.x)<=40,(abs(self.x)-25)*.2,3.+(abs(self.x)-40)*.01))
 def test_alpha_is_one_in_uniform_section_and_larger_with_overbanks(self):
  rect=np.where(abs(self.x)<=25,0.,50.);self.assertAlmostEqual(self.sh(self.x,rect,2,50,.035,.035)['alpha'],1,places=6)
  self.assertGreater(self.sh(self.x,self.z,5,50,.035,.08)['alpha'],1.01)
 def test_uniform_reach_with_normal_depth_boundary_stays_uniform(self):
  q=250;slope=.0005;stage,_,_=solve_stage(self.x,self.z,q,slope,50,.035,.08);profiles=[self.z+i*0 for i in range(6)]
  # bed drops with the slope so geometry is prismatic along the reach
  profiles=[self.z+(5-i)*slope*500 for i in range(6)];res=self.ss(profiles,self.x,[500]*5,q,50,.035,.08,stage)
  depths=[r['depth'] for r in res];self.assertLess(max(depths)-min(depths),0.02)
 def test_backwater_raises_upstream_levels_and_closes_energy_balance(self):
  q=250;slope=.0005;normal,_,_=solve_stage(self.x,self.z,q,slope,50,.035,.08);profiles=[self.z+(5-i)*slope*500 for i in range(6)]
  low=self.ss(profiles,self.x,[500]*5,q,50,.035,.08,normal);high=self.ss(profiles,self.x,[500]*5,q,50,.035,.08,normal+1.5)
  self.assertTrue(all(h['wse']>=l['wse']-1e-6 for h,l in zip(high,low)));self.assertGreater(high[0]['depth'],low[0]['depth'])
  for i in range(5):  # E_up = E_down + hf + hc
   self.assertAlmostEqual(high[i]['energy_m'],high[i+1]['energy_m']+high[i]['friction_loss_m']+high[i]['eddy_loss_m'],places=5)
  self.assertTrue(all(not r['supercritical_or_critical'] for r in high))
 def test_invalid_inputs_rejected(self):
  with self.assertRaises(ValueError):self.ss([self.z,self.z],self.x,[100],0,50,.035,.08,2)
  with self.assertRaises(ValueError):self.ss([self.z,self.z],self.x,[100,100],10,50,.035,.08,2)
if __name__=='__main__':unittest.main()
