"""Run a frozen 2D input package and save explicitly experimental results."""
import argparse
import json

import numpy as np

from shallow_water import simulate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", help="NPZ with bed_m, depth_m, cell_m, seconds and net_m3s")
    parser.add_argument("output", help="Output NPZ path")
    parser.add_argument("--manning", type=float, default=0.035)
    args = parser.parse_args()
    with np.load(args.inputs, allow_pickle=False) as source:
        frames = list(simulate(source["bed_m"], source["depth_m"], float(source["cell_m"]),
                               source["seconds"], source["net_m3s"], args.manning))
    metadata = {"schema": "ignispyro-floods-2d/1", "status": "experimental",
                "operationally_accepted": False, "diagnostics": [stats for _, stats in frames]}
    np.savez_compressed(args.output, depth_m=np.stack([depth for depth, _ in frames]),
                        metadata_json=json.dumps(metadata))


if __name__ == "__main__":
    main()
