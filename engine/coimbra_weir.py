"""Research boundary components. No gate state or current bathymetry is inferred."""
import math

def integrate_boundary_volume(inflow,outflow,max_gap_seconds=7200):
    """Trapezoidal volume between simultaneous samples, never fill long gaps."""
    paired=sorted(set(inflow)&set(outflow));vin=vout=duration=0.;gaps=0
    for t0,t1 in zip(paired,paired[1:]):
        dt=t1-t0
        if dt<=0 or dt>max_gap_seconds:gaps+=1;continue
        rates=[inflow[t0],inflow[t1],outflow[t0],outflow[t1]]
        if not all(math.isfinite(v) and v>=0 for v in rates):gaps+=1;continue
        vin+=(inflow[t0]+inflow[t1])*.5*dt;vout+=(outflow[t0]+outflow[t1])*.5*dt;duration+=dt
    return {'inflow_volume_estimate_m3':vin,'outflow_volume_estimate_m3':vout,'net_storage_change_estimate_m3':vin-vout,'integrated_seconds':duration,'rejected_gaps':gaps,'method':'trapezoidal integration of published rates, not measured interval volumes; abstractions and other terms unresolved'}

def discharge_from_fitted_weir(elevation,fit,regime):
    if regime!='all_gates_open_verified':raise ValueError('Gate regime must be verified; level alone is insufficient')
    low=fit['crest_m']+fit['head_min_m'];high=fit['crest_m']+fit['head_max_m']
    if not math.isfinite(elevation) or not low<=elevation<=high:raise ValueError('Outside training range; no extrapolation')
    return fit['coefficient_m05_s']*fit['width_m']*(elevation-fit['crest_m'])**1.5

def terminal_release_sum(raiva,fronhas,ceira):
    # Aguieira is upstream of Raiva and is intentionally not another summand.
    if any(q is None for q in [raiva,fronhas,ceira]):return None
    if any(not math.isfinite(q) or q<0 for q in [raiva,fronhas,ceira]):raise ValueError('Invalid release')
    return raiva+fronhas+ceira
