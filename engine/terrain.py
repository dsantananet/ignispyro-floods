"""Terrain screening from a DEM (MDT): height above nearest drainage (HAND-like) and slope.

HAND here is the *nearest-drainage* approximation (elevation minus elevation of the
Euclidean-nearest river cell), not flow-routed HAND. It is a susceptibility proxy,
never a flood depth."""
import numpy as np
from scipy import ndimage

def nearest_drainage_hand(dem,drainage,cell_y_m,cell_x_m,max_distance_m=3000.):
    """Return (hand_m, distance_m). Cells farther than max_distance_m from drainage get NaN HAND."""
    dem=np.asarray(dem,float);drainage=np.asarray(drainage,bool)
    if not drainage.any():raise ValueError('No drainage cells')
    dist,(ri,ci)=ndimage.distance_transform_edt(~drainage,sampling=(cell_y_m,cell_x_m),return_indices=True)
    hand=dem-dem[ri,ci];hand=np.where(np.isfinite(dem),hand,np.nan);hand[dist>max_distance_m]=np.nan
    return hand,dist

def slope_degrees(dem,cell_y_m,cell_x_m):
    dem=np.asarray(dem,float);gy,gx=np.gradient(dem,cell_y_m,cell_x_m);return np.degrees(np.arctan(np.hypot(gx,gy)))

def zonal_fraction(labels,mask,n_labels):
    """Fraction of cells per integer label (1..n_labels) where mask is True."""
    labels=np.asarray(labels).ravel();mask=np.asarray(mask).ravel().astype(float)
    total=np.bincount(labels,minlength=n_labels+1)[1:n_labels+1].astype(float);hit=np.bincount(labels,weights=mask,minlength=n_labels+1)[1:n_labels+1]
    return np.divide(hit,total,out=np.full(n_labels,np.nan),where=total>0)

def roc_auc(scores,positives):
    """Rank-based AUC (Mann–Whitney). Used for diagnostic checks against APA zones."""
    s=np.asarray(scores,float);y=np.asarray(positives,bool);ok=np.isfinite(s);s,y=s[ok],y[ok]
    n1,n0=int(y.sum()),int((~y).sum())
    if n1==0 or n0==0:return None
    order=np.argsort(s,kind='mergesort');ss=s[order];r=np.empty(len(s));i=0
    while i<len(ss):
        j=i
        while j+1<len(ss) and ss[j+1]==ss[i]:j+=1
        r[order[i:j+1]]=(i+j)/2+1;i=j+1
    return float((r[y].sum()-n1*(n1+1)/2)/(n1*n0))

def parish_terrain_stats(dem,drainage,labels,n_labels,res_deg,lat_deg,hand_threshold_m=5.,max_distance_m=3000.):
    """Per-label share of the label's cells with HAND < threshold (nearest-drainage HAND) and mean slope.
    dem/drainage/labels are on one regular EPSG:4326 grid; labels are 1..n (0 = outside)."""
    import math
    cell_y=res_deg*111320.;cell_x=cell_y*math.cos(math.radians(lat_deg))
    hand,_=nearest_drainage_hand(dem,drainage,cell_y,cell_x,max_distance_m)
    slope=slope_degrees(dem,cell_y,cell_x)
    low=np.isfinite(hand)&(hand<hand_threshold_m)
    valid=np.isfinite(np.asarray(dem,float))
    inside=np.asarray(labels)>0
    frac_low=zonal_fraction(np.where(inside,labels,0),low,n_labels)
    cover=zonal_fraction(np.where(inside,labels,0),valid,n_labels)
    mean_slope=np.full(n_labels,np.nan)
    flat=np.asarray(labels).ravel();w=np.where(valid,slope,0.).ravel();cnt=np.bincount(flat,weights=valid.ravel().astype(float),minlength=n_labels+1)[1:n_labels+1]
    tot=np.bincount(flat,weights=w,minlength=n_labels+1)[1:n_labels+1];np.divide(tot,cnt,out=mean_slope,where=cnt>0)
    return {'hand_lt_threshold_frac':frac_low,'dem_coverage_frac':cover,'mean_slope_deg':mean_slope}
