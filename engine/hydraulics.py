"""Experimental normal-flow sections + connected terrain inundation.

Not a Saint-Venant solver and not a substitute for surveyed bathymetry, weir
operations, downstream stage and calibrated unsteady 1D/2D hydraulic modelling.
"""
import math
from collections import deque
import numpy as np

def section_properties(x,z,stage,slope,width,n_channel,n_flood):
    depth=stage-z;mid=len(x)//2
    if depth[mid]<=0:return 0.,0.,0.
    left=mid
    while left>0 and depth[left-1]>0:left-=1
    right=mid
    while right<len(x)-1 and depth[right+1]>0:right+=1
    area=[0.,0.,0.];perimeter=[0.,0.,0.]
    for i in range(max(0,left-1),min(len(x)-1,right+1)):
        xa,xb=float(x[i]),float(x[i+1]);za,zb=float(z[i]),float(z[i+1]);da,db=stage-za,stage-zb
        if da<=0 and db<=0:continue
        if da<0:
            xa=xa+(xb-xa)*(-da)/(db-da);za=stage;da=0.
        elif db<0:
            xb=xa+(xb-xa)*da/(da-db);zb=stage;db=0.
        m=(xa+xb)/2;k=1 if abs(m)<=width/2 else 0 if m<0 else 2
        area[k]+=(da+db)*(xb-xa)/2;perimeter[k]+=math.hypot(xb-xa,zb-za)
    q=0.
    for i in range(3):
        if area[i]>0 and perimeter[i]>0:q+=(area[i]/(n_channel if i==1 else n_flood))*(area[i]/perimeter[i])**(2/3)*math.sqrt(slope)
    a=sum(area)
    return q,a,q/a if a else 0.

def solve_stage(x,z,q,slope,width,n_channel,n_flood):
    if not math.isfinite(q) or q<0:raise ValueError('Invalid discharge')
    low=float(z[len(z)//2]);high=low+40
    if section_properties(x,z,high,slope,width,n_channel,n_flood)[0]<q:raise ValueError('Flow exceeds represented cross-section')
    for _ in range(42):
        h=(low+high)/2
        if section_properties(x,z,h,slope,width,n_channel,n_flood)[0]<q:low=h
        else:high=h
    stage=(low+high)/2;_,a,v=section_properties(x,z,stage,slope,width,n_channel,n_flood)
    return stage,a,v

def linear_reservoir(inflows,dt_s,k_s):
    if k_s<=0 or dt_s<=0 or not inflows or min(inflows)<0:raise ValueError('Invalid routing inputs')
    storage=inflows[0]*k_s;initial=storage;outputs=[];vin=vout=0.;decay=math.exp(-dt_s/k_s)
    for q in inflows:
        nxt=storage*decay+q*k_s*(1-decay);out=storage+q*dt_s-nxt
        outputs.append(out/dt_s);vin+=q*dt_s;vout+=out;storage=nxt
    return outputs,{'initial_storage_m3':initial,'final_storage_m3':storage,'inflow_m3':vin,'outflow_m3':vout,'mass_balance_error_m3':initial+vin-vout-storage,'response_time_seconds':k_s}

def connected_wet(dem,stage,river_seed,corridor):
    wet=(stage>dem)&corridor;seen=np.zeros(wet.shape,dtype=bool);queue=deque()
    for row,col in np.argwhere(wet&river_seed):seen[row,col]=True;queue.append((int(row),int(col)))
    height,width=wet.shape
    while queue:
        r,c=queue.popleft()
        for rr,cc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
            if 0<=rr<height and 0<=cc<width and wet[rr,cc] and not seen[rr,cc]:seen[rr,cc]=True;queue.append((rr,cc))
    return seen

def terrain_footprint(dem,water,channel,seed,corridor,cell_area,min_depth,available_volume):
    connected=connected_wet(dem,water,seed,corridor);depth=np.maximum(0,water-dem);outside=connected&~channel&(depth>=min_depth);volume=float(np.sum(depth[outside])*cell_area);offset=0.
    if volume>available_volume+1e-6:
        lo,hi=0.,max(0.,float(np.max(water-dem)))+1
        for _ in range(24):
            delta=(lo+hi)/2;lev=water-delta;conn=connected_wet(dem,lev,seed,corridor);d=np.maximum(0,lev-dem);m=conn&~channel&(d>=min_depth);v=float(np.sum(d[m])*cell_area)
            if v>available_volume:lo=delta
            else:hi=delta
        offset=hi;water=water-offset;connected=connected_wet(dem,water,seed,corridor);depth=np.maximum(0,water-dem);outside=connected&~channel&(depth>=min_depth);volume=float(np.sum(depth[outside])*cell_area)
    return depth,outside,{'mapped_overbank_storage_m3':volume,'available_overbank_volume_upper_bound_m3':float(available_volume),'stage_reduction_for_volume_constraint_m':offset,'storage_not_mapped_m3':max(0.,available_volume-volume)}
