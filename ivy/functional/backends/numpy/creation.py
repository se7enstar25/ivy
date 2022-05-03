# global
import numpy as np
from typing import Union, Tuple, Optional, List

# local
from .data_type import dtype_from_str
from ivy.functional.ivy import default_dtype

# noinspection PyProtectedMember
from ivy.functional.backends.numpy.device import _to_dev


# Array API Standard #
# -------------------#


def asarray(object_in, dtype=None, device=None, copy=None):
    # If copy=none then try using existing memory buffer
    if isinstance(object_in, np.ndarray) and dtype is None:
        dtype = object_in.dtype
    elif (
        isinstance(object_in, (list, tuple, dict))
        and len(object_in) != 0
        and dtype is None
    ):
        # Temporary fix on type
        # Because default_type() didn't return correct type for normal python array
        if copy is True:
            return _to_dev(np.copy(np.asarray(object_in)), device)
        else:
            return _to_dev(np.asarray(object_in), device)
    else:
        dtype = default_dtype(dtype, object_in)
    if copy is True:
        return _to_dev(np.copy(np.asarray(object_in, dtype=dtype)), device)
    else:
        return _to_dev(np.asarray(object_in, dtype=dtype), device)


def zeros(
    shape: Union[int, Tuple[int], List[int]],
    dtype: Optional[np.dtype] = None,
    device: Optional[str] = None,
) -> np.ndarray:
    return _to_dev(np.zeros(shape, dtype_from_str(default_dtype(dtype))), device)


def ones(
    shape: Union[int, Tuple[int], List[int]],
    dtype: Optional[np.dtype] = None,
    device: Optional[str] = None,
) -> np.ndarray:
    dtype = dtype_from_str(default_dtype(dtype))
    return _to_dev(np.ones(shape, dtype), device)


def full_like(
    x: np.ndarray,
    fill_value: Union[int, float],
    dtype: Optional[Union[np.dtype, str]] = None,
    device: Optional[str] = None,
) -> np.ndarray:
    if dtype:
        dtype = "bool_" if dtype == "bool" else dtype
    else:
        dtype = x.dtype
    return _to_dev(np.full_like(x, fill_value, dtype=dtype), device)


def ones_like(
    x: np.ndarray,
    dtype: Optional[Union[np.dtype, str]] = None,
    device: Optional[str] = None,
) -> np.ndarray:

    if dtype:
        dtype = "bool_" if dtype == "bool" else dtype
        dtype = np.dtype(dtype)
    else:
        dtype = x.dtype

    return _to_dev(np.ones_like(x, dtype=dtype), device)


def zeros_like(
    x: np.ndarray, dtype: Optional[np.dtype] = None, device: Optional[str] = None
) -> np.ndarray:
    if dtype:
        dtype = "bool_" if dtype == "bool" else dtype
    else:
        dtype = x.dtype
    return _to_dev(np.zeros_like(x, dtype=dtype), device)


def tril(x: np.ndarray, k: int = 0) -> np.ndarray:
    return np.tril(x, k)


def triu(x: np.ndarray, k: int = 0) -> np.ndarray:
    return np.triu(x, k)


def empty(
    shape: Union[int, Tuple[int], List[int]],
    dtype: Optional[np.dtype] = None,
    device: Optional[str] = None,
) -> np.ndarray:
    return _to_dev(np.empty(shape, dtype_from_str(default_dtype(dtype))), device)


def empty_like(
    x: np.ndarray,
    dtype: Optional[Union[np.dtype, str]] = None,
    device: Optional[str] = None,
) -> np.ndarray:

    if dtype:
        dtype = "bool_" if dtype == "bool" else dtype
        dtype = np.dtype(dtype)
    else:
        dtype = x.dtype

    return _to_dev(np.empty_like(x, dtype=dtype), device)


def linspace(start, stop, num, axis=None, device=None):
    if axis is None:
        axis = -1
    return _to_dev(np.linspace(start, stop, num, axis=axis), device)


def meshgrid(*arrays: np.ndarray, indexing: str = "xy") -> List[np.ndarray]:
    return np.meshgrid(*arrays, indexing=indexing)


def eye(
    n_rows: int,
    n_cols: Optional[int] = None,
    k: Optional[int] = 0,
    dtype: Optional[np.dtype] = None,
    device: Optional[str] = None,
) -> np.ndarray:
    dtype = dtype_from_str(default_dtype(dtype))
    return _to_dev(np.eye(n_rows, n_cols, k, dtype), device)


# noinspection PyShadowingNames
def arange(start, stop=None, step=1, dtype=None, device=None):
    if dtype:
        dtype = dtype_from_str(dtype)
    res = _to_dev(np.arange(start, stop, step=step, dtype=dtype), device)
    if not dtype:
        if res.dtype == np.float64:
            return res.astype(np.float32)
        elif res.dtype == np.int64:
            return res.astype(np.int32)
    return res


def full(
    shape: Union[int, Tuple[int, ...]],
    fill_value: Union[int, float],
    dtype: Optional[np.dtype] = None,
    device: Optional[str] = None,
) -> np.ndarray:
    return _to_dev(
        np.full(shape, fill_value, dtype_from_str(default_dtype(dtype, fill_value))),
        device,
    )


def from_dlpack(x):
    return np.from_dlpack(x)


# Extra #
# ------#

array = asarray


def logspace(start, stop, num, base=10.0, axis=None, device=None):
    if axis is None:
        axis = -1
    return _to_dev(np.logspace(start, stop, num, base=base, axis=axis), device)
