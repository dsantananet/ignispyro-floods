"""Experimental finite-volume shallow-water solver on a rectangular metric grid."""
import numpy as np

GRAVITY = 9.81
DRY = 1e-9


def velocity(discharge, depth):
    return np.divide(discharge, depth, out=np.zeros_like(depth), where=depth > DRY)


def face_flux(left, right, bed_left, bed_right, normal):
    """Hydrostatic reconstruction with separate bed corrections on each side."""
    crest = np.maximum(bed_left, bed_right)
    h_left = np.maximum(0, left[0] + bed_left - crest)
    h_right = np.maximum(0, right[0] + bed_right - crest)
    u_left = velocity(left[normal], left[0])
    u_right = velocity(right[normal], right[0])
    reconstructed_left = np.stack([h_left, *(velocity(q, left[0]) * h_left for q in left[1:])])
    reconstructed_right = np.stack([h_right, *(velocity(q, right[0]) * h_right for q in right[1:])])
    flux_left = reconstructed_left * u_left
    flux_right = reconstructed_right * u_right
    flux_left[normal] += 0.5 * GRAVITY * h_left**2
    flux_right[normal] += 0.5 * GRAVITY * h_right**2
    wave = np.maximum(abs(u_left) + np.sqrt(GRAVITY * h_left),
                      abs(u_right) + np.sqrt(GRAVITY * h_right))
    flux = 0.5 * (flux_left + flux_right - wave * (reconstructed_right - reconstructed_left))
    corrected_left, corrected_right = flux.copy(), flux.copy()
    corrected_left[normal] += 0.5 * GRAVITY * (left[0]**2 - h_left**2)
    corrected_right[normal] += 0.5 * GRAVITY * (right[0]**2 - h_right**2)
    return corrected_left, corrected_right


def divergence(state, bed, axis, normal):
    padding = [(0, 0)] * 3
    padding[axis] = (1, 1)
    ghost = np.moveaxis(np.pad(state, padding, mode="edge"), axis, -1)
    ghost[normal, ..., 0] *= -1
    ghost[normal, ..., -1] *= -1
    bed_padding = padding[1:]
    extended_bed = np.moveaxis(np.pad(bed, bed_padding, mode="edge"), axis - 1, -1)
    left, right = face_flux(ghost[..., :-1], ghost[..., 1:],
                            extended_bed[..., :-1], extended_bed[..., 1:], normal)
    return np.moveaxis(left[..., 1:] - right[..., :-1], -1, axis)


def simulate(bed, initial_depth, cell_m, frame_seconds, input_rates, manning=0.035):
    """Yield depth frames and mass diagnostics. Outer walls are reflecting.

    input_rates[i] is net inflow in m³/s per cell, held constant between frame
    i and i+1. Negative rates withdraw only available water. The operator
    supplies spatially distributed inflow, rainfall or withdrawals explicitly.
    """
    bed = np.asarray(bed, dtype=float)
    depth = np.asarray(initial_depth, dtype=float)
    times = np.asarray(frame_seconds, dtype=float)
    rates = np.asarray(input_rates, dtype=float)
    if (bed.ndim != 2 or not bed.size or depth.shape != bed.shape or times.ndim != 1
            or times.size < 2 or rates.shape != (times.size - 1, *bed.shape)):
        raise ValueError("Invalid grid, frame schedule or input-rate shape")
    if (not all(np.isfinite(a).all() for a in (bed, depth, times, rates))
            or np.any(depth < 0) or times[0] != 0 or np.any(np.diff(times) <= 0)
            or not np.isfinite(cell_m) or cell_m <= 0
            or not np.isfinite(manning) or manning < 0):
        raise ValueError("Invalid hydraulic parameters")
    area = cell_m**2
    state = np.stack((depth, np.zeros_like(depth), np.zeros_like(depth)))
    initial_volume = float(depth.sum() * area)
    net_input = 0.0
    unmet_withdrawal = 0.0

    def frame(time):
        volume = float(state[0].sum() * area)
        return state[0].copy(), {
            "seconds": float(time), "water_volume_m3": volume,
            "net_input_m3": net_input, "unmet_withdrawal_m3": unmet_withdrawal,
            "mass_error_m3": volume - initial_volume - net_input,
        }

    yield frame(0)
    for start, stop, rate in zip(times[:-1], times[1:], rates):
        remaining = stop - start
        while remaining > 0:
            h, qx, qy = state
            speed = np.max(abs(velocity(qx, h)) + abs(velocity(qy, h)) + 2 * np.sqrt(GRAVITY * h))
            # Bound the wave speed due to the source before choosing the step.
            added_depth = max(0.0, float(rate.max())) * min(remaining, 10) / area
            speed += 2 * np.sqrt(GRAVITY * added_depth)
            dt = min(remaining, 10.0, 0.4 * cell_m / max(speed, DRY))
            if dt <= 1e-9:
                raise FloatingPointError("Hydraulic time step collapsed")
            state -= dt / cell_m * (divergence(state, bed, 2, 1) + divergence(state, bed, 1, 2))
            if not np.isfinite(state).all() or state[0].min() < -1e-8:
                raise FloatingPointError("Non-finite state or negative depth")
            np.maximum(state[0], 0, out=state[0])
            requested = rate * (dt / area)
            actual = np.maximum(requested, -state[0])
            retained = np.divide(np.minimum(actual, 0), state[0], out=np.zeros_like(actual),
                                 where=state[0] > 0) + 1
            state[1:] *= retained
            state[0] += actual
            net_input += float(actual.sum() * area)
            unmet_withdrawal += float((actual - requested).sum() * area)
            depth_safe = np.maximum(state[0], DRY)
            magnitude = np.hypot(state[1], state[2])
            state[1:] /= 1 + dt * GRAVITY * manning**2 * magnitude / depth_safe**(7 / 3)
            state[1:, state[0] <= DRY] = 0
            remaining -= dt
        yield frame(stop)
