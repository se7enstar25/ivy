"""Collection of PyTorch general functions, wrapped to fit Ivy syntax and signature."""

# global
import os
import importlib
import torch
from typing import Optional
from torch.profiler import ProfilerActivity
from torch.profiler import profile as _profile

# local
import ivy
from ivy.functional.ivy.device import Profiler as BaseProfiler

torch_scatter = None

# API #
# ----#


def dev(x: torch.Tensor, as_str: bool = False) -> str:
    dv = x.device
    if as_str:
        return dev_to_str(dv)
    return dv


def to_dev(
    x, device: Optional[str] = None, out: Optional[torch.Tensor] = None
) -> torch.Tensor:
    ret = x.to(dev_from_str(device))
    if isinstance(x, torch.nn.Parameter):
        if ivy.exists(out):
            return ivy.inplace_update(out, torch.nn.Parameter(ret))
        return torch.nn.Parameter(ret)

    if ivy.exists(out):
        return ivy.inplace_update(out, ret)
    return ret


def dev_to_str(device: torch.device):
    if isinstance(device, str):
        return device
    dev_type, dev_idx = (device.type, device.index)
    if dev_type == "cpu":
        return dev_type
    return dev_type.replace("cuda", "gpu") + (
        ":" + (str(dev_idx) if dev_idx is not None else "0")
    )


def dev_from_str(device: Optional[str] = None) -> Optional[torch.device]:
    if not isinstance(device, str):
        return device
    return torch.device(device.replace("gpu", "cuda"))


def clear_mem_on_dev(device):
    if "gpu" in device:
        torch.cuda.empty_cache()


_callable_dev = dev


def num_gpus() -> int:
    return torch.cuda.device_count()


def gpu_is_available() -> bool:
    return torch.cuda.is_available()


# noinspection PyUnresolvedReferences
def tpu_is_available() -> bool:
    if importlib.util.find_spec("torch_xla") is not None:
        return True
    return False


class Profiler(BaseProfiler):
    def __init__(self, save_dir):
        super(Profiler, self).__init__(save_dir)
        self._prof = _profile(
            activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA], with_stack=True
        )

    def start(self):
        self._prof.__enter__()

    def stop(self):
        self._prof.__exit__(None, None, None)
        self._prof.export_chrome_trace(os.path.join(self._save_dir, "trace.json"))

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
