"""Collection of Numpy general functions, wrapped to fit Ivy syntax and signature."""

# global
import os
import time

import numpy as np
from typing import Optional

# local
import ivy
from ivy.functional.ivy.device import Profiler as BaseProfiler

dev = lambda x, as_str=False: "cpu"
dev.__name__ = "dev"
_dev_callable = dev
dev_to_str = lambda dev: "cpu"
dev_from_str = lambda dev: "cpu"
clear_mem_on_dev = lambda dev: None


def tpu_is_available() -> bool:
    return False


def num_gpus() -> int:
    return 0


def gpu_is_available() -> bool:
    return False


def _to_dev(x: np.ndarray, device=None, out: Optional[np.ndarray] = None) -> np.ndarray:
    if device is not None:
        if "gpu" in device:
            raise Exception(
                "Native Numpy does not support GPU placement, "
                "consider using Jax instead"
            )
        elif "cpu" in device:
            pass
        else:
            raise Exception(
                "Invalid device specified, must be in the form "
                "[ 'cpu:idx' | 'gpu:idx' ], but found {}".format(device)
            )
    if ivy.exists(out):
        return ivy.inplace_update(out, x)
    return x


# bind to_dev to _to_dev
# _to_dev is imported in creation, so to minimize
# changes, we bind it to to_dev
to_dev = _to_dev


class Profiler(BaseProfiler):
    def __init__(self, save_dir):
        # ToDO: add proper numpy profiler
        super(Profiler, self).__init__(save_dir)
        os.makedirs(save_dir, exist_ok=True)
        self._start_time = None

    def start(self):
        self._start_time = time.perf_counter()

    def stop(self):
        time_taken = time.perf_counter() - self._start_time
        with open(os.path.join(self._save_dir, "profile.log"), "w+") as f:
            f.write("took {} seconds to complete".format(time_taken))

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
