"""Spatial diagnostics; absent satellite detections are not confirmed dry ground."""
import numpy as np

def overlap_metrics(predicted, observed, domain, cell_area):
    if predicted.shape != observed.shape or domain.shape != observed.shape:
        raise ValueError('Grid shapes differ')
    if cell_area <= 0 or not domain.any():
        raise ValueError('Empty or invalid comparison domain')
    p = predicted & domain; o = observed & domain
    hit = int((p & o).sum()); extra = int((p & ~o).sum()); missed = int((o & ~p).sum())
    union = hit + extra + missed
    return {'intersection_m2': hit*cell_area, 'simulation_only_m2': extra*cell_area,
            'observation_only_m2': missed*cell_area,
            'iou_diagnostic': hit/union if union else None,
            'observed_recall_diagnostic': hit/(hit+missed) if hit+missed else None,
            'simulation_precision_diagnostic': hit/(hit+extra) if hit+extra else None,
            'observed_area_m2': (hit+missed)*cell_area, 'simulated_area_m2': (hit+extra)*cell_area,
            'domain_area_m2': int(domain.sum())*cell_area,
            'operationally_accepted': False}
