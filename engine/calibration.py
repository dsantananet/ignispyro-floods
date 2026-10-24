"""Fit a local discharge-stage relation only from independent, qualified events.
This is a rating fit, not validation of hydraulic extent or reservoir routing.
"""
import math
import numpy as np

def fit_rating(rows,station_id,datum):
    accepted=[r for r in rows if r.get('station_id')==station_id and r.get('vertical_datum')==datum and r.get('qc')=='accepted' and r.get('event_id') and all(isinstance(r.get(k),(int,float)) and math.isfinite(r[k]) for k in ('stage_m','flow_m3s')) and r['flow_m3s']>0]
    events=sorted(set(r['event_id'] for r in accepted))
    if len(events)<3:raise ValueError('At least three independent qualified events required')
    train=[r for r in accepted if r['event_id']!=events[-1]];test=[r for r in accepted if r['event_id']==events[-1]]
    if len(train)<20 or len(test)<10:raise ValueError('Insufficient training or held-out observations')
    stage=np.array([r['stage_m'] for r in train]);q=np.array([r['flow_m3s'] for r in train]);best=None
    if np.ptp(stage)<.5:raise ValueError('Insufficient stage variation to identify a flood rating')
    for zero in np.linspace(min(stage)-5,min(stage)-.01,300):
        b,loga=np.polyfit(np.log(stage-zero),np.log(q),1)
        if not .5<=b<=5:continue
        a=float(np.exp(loga));rmse=float(np.sqrt(np.mean((a*(stage-zero)**b-q)**2)))
        if best is None or rmse<best[0]:best=(rmse,a,float(b),float(zero))
    if best is None:raise ValueError('No physically monotonic fit')
    _,a,b,zero=best;valid=[r for r in test if min(stage)<=r['stage_m']<=max(stage)]
    if len(valid)<10:raise ValueError('Held-out event outside training range; extrapolation forbidden')
    obs=np.array([r['flow_m3s'] for r in valid]);pred=np.array([a*(r['stage_m']-zero)**b for r in valid]);den=float(np.sum((obs-obs.mean())**2))
    return {'a':a,'b':b,'h0':zero,'stage_min_m':float(min(stage)),'stage_max_m':float(max(stage)),'training_events':events[:-1],'held_out_event':events[-1],'training_rmse_m3s':best[0],'validation_rmse_m3s':float(np.sqrt(np.mean((pred-obs)**2))),'validation_bias_m3s':float(np.mean(pred-obs)),'validation_nse':None if den==0 else 1-float(np.sum((pred-obs)**2))/den,'independent_validation_n':len(valid),'hydraulic_extent_validated':False,'operational_accepted':False,'station_id':station_id,'vertical_datum':datum}

def predict_rating(fit,stage):
    if not fit['stage_min_m']<=stage<=fit['stage_max_m']:raise ValueError('Extrapolation forbidden')
    return fit['a']*(stage-fit['h0'])**fit['b']
