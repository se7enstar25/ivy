"""
Collection of PyTorch general functions, wrapped to fit Ivy syntax and signature.
"""

# global
import torch
import importlib
import numpy as np
torch_scatter = None
from operator import mul
from torch.types import Number
from functools import reduce as _reduce
from typing import List, Dict, Optional, Union

# API #
# ----#


# noinspection PyShadowingNames
def array(object_in, dtype_str: Optional[str] = None, dev_str: Optional[str] = None):
    if dtype_str is not None:
        return torch.tensor(object_in, dtype=dtype_from_str(dtype_str)).to(str_to_dev(dev_str))
    else:
        return torch.tensor(object_in).to(str_to_dev(dev_str))


def is_array(x):
    if isinstance(x, torch.Tensor):
        return True
    return False


def dtype_from_str(dtype_str_in: str) -> torch.dtype:
    return {'bool': torch.bool,
            'int8': torch.int8,
            'int16': torch.int16,
            'int32': torch.int32,
            'int64': torch.int64,
            'float16': torch.float16,
            'float32': torch.float32,
            'float64': torch.float64}[dtype_str_in]


def to_numpy(x) -> np.ndarray:
    if isinstance(x, np.ndarray):
        return x
    elif torch.is_tensor(x):
        return x.detach().cpu().numpy()
    raise ValueError('Expected a pytroch tensor.')


def to_list(x):
    if isinstance(x, np.ndarray):
        return x.tolist()
    elif torch.is_tensor(x):
        return x.detach().cpu().tolist()
    raise ValueError('Expected a pytroch tensor.')


def shape(x, as_tensor=False) -> Union[torch.Tensor, List[int]]:
    return torch.tensor(x.shape) if as_tensor else x.shape


def get_num_dims(x, as_tensor=False) -> Union[torch.Tensor, int]:
    return torch.tensor(len(x.shape)) if as_tensor else len(x.shape)


def minimum(x, y):
    x_val = torch.tensor(x) if (isinstance(x, int) or isinstance(x, float)) else x
    y_val = torch.tensor(y) if (isinstance(y, int) or isinstance(y, float)) else y
    return torch.min(x_val, y_val)


def maximum(x, y):
    x_val = torch.tensor(x) if (isinstance(x, int) or isinstance(x, float)) else x
    y_val = torch.tensor(y) if (isinstance(y, int) or isinstance(y, float)) else y
    return torch.max(x_val, y_val)


def clip(x, x_min, x_max):
    if isinstance(x_min, torch.Tensor):
        x_min = x_min.item()
    if isinstance(x_max, torch.Tensor):
        x_max = x_max.item()
    return torch.clamp(x, x_min, x_max)


# noinspection PyShadowingBuiltins
def round(x):
    return torch.round(x)


def floormod(x, y):
    return x % y


def floor(x):
    return torch.floor(x)


def ceil(x):
    return torch.ceil(x)


# noinspection PyShadowingBuiltins
def abs(x):
    return torch.abs(x)


def argmax(x, axis: int = 0):
    return torch.argmax(x, axis).reshape(-1)


def argmin(x, axis: int = 0):
    return torch.argmin(x, axis).reshape(-1)


def cast(x, dtype_str_in: str):
    dtype_val = dtype_from_str(dtype_str_in)
    return x.type(dtype_val)


# noinspection PyShadowingNames
def arange(stop: Number, start: Number = 0, step: Number = 1, dtype_str: Optional[str] = None,
           dev_str: Optional[str] = None):
    if dtype_str is not None:
        return torch.arange(start, stop, step=step, dtype=dtype_from_str(dtype_str)).to(str_to_dev(dev_str))
    else:
        return torch.arange(start, stop, step=step).to(str_to_dev(dev_str))


def _differentiable_linspace(start, stop, num, device):
    if num == 1:
        return torch.unsqueeze(start, 0)
    n_m_1 = num - 1
    increment = (stop - start) / n_m_1
    increment_tiled = increment.repeat(n_m_1)
    increments = increment_tiled * torch.linspace(1, n_m_1, n_m_1, device=device)
    res = torch.cat((torch.unsqueeze(start, 0), start + increments), 0)
    return res


# noinspection PyUnboundLocalVariable,PyShadowingNames
def linspace(start, stop, num, axis=None, dev_str=None):
    num = num.detach().numpy().item() if isinstance(num, torch.Tensor) else num
    start_is_array = isinstance(start, torch.Tensor)
    stop_is_array = isinstance(stop, torch.Tensor)
    linspace_method = torch.linspace
    if start_is_array:
        start_shape = list(start.shape)
        start = start.reshape((-1,))
        linspace_method = _differentiable_linspace if start.requires_grad else torch.linspace
        dev_str = _callable_dev_str(start)
    if stop_is_array:
        start_shape = list(stop.shape)
        stop = stop.reshape((-1,))
        linspace_method = _differentiable_linspace if stop.requires_grad else torch.linspace
        dev_str = _callable_dev_str(stop)
    if start_is_array and stop_is_array:
        res = [linspace_method(strt, stp, num, device=str_to_dev(dev_str)) for strt, stp in zip(start, stop)]
    elif start_is_array and not stop_is_array:
        res = [linspace_method(strt, stop, num, device=str_to_dev(dev_str)) for strt in start]
    elif not start_is_array and stop_is_array:
        res = [linspace_method(start, stp, num, device=str_to_dev(dev_str)) for stp in stop]
    else:
        return linspace_method(start, stop, num, device=str_to_dev(dev_str))
    res = torch.cat(res, -1).reshape(start_shape + [num])
    if axis is not None:
        res = torch.transpose(res, axis, -1)
    return res.to(str_to_dev(dev_str))


def concatenate(xs: List[torch.Tensor], axis: int = -1):
    if xs[0].shape == ():
        return torch.cat([x.unsqueeze(0) for x in xs], axis)
    return torch.cat(xs, axis)


def flip(x, axis: Optional[List[int]] = None, batch_shape: Optional[List[int]] = None):
    num_dims: int = len(batch_shape) if batch_shape is not None else len(x.shape)
    if not num_dims:
        return x
    if axis is None:
        new_axis: List[int] = list(range(num_dims))
    else:
        new_axis: List[int] = axis
    if isinstance(new_axis, int):
        new_axis = [new_axis]
    else:
        new_axis = new_axis
    new_axis = [item + num_dims if item < 0 else item for item in new_axis]
    return torch.flip(x, new_axis)


def stack(xs: List[torch.Tensor], axis: int = 0):
    return torch.stack(xs, axis)


def unstack(x, axis: int) -> List[torch.Tensor]:
    if x.shape == ():
        return [x]
    return list(torch.unbind(x, axis))


def split(x, num_sections: Optional[int] = None, axis: int = 0) -> List[torch.Tensor]:
    if x.shape == ():
        if num_sections is not None and num_sections != 1:
            raise Exception('input array had no shape, but num_sections specified was {}'.format(num_sections))
        return [x]
    dim_size: int = x.shape[axis]
    if num_sections is None:
        # noinspection PyUnboundLocalVariable
        num_sections = dim_size
    chunk_size = round(torch.tensor(dim_size) / torch.tensor(num_sections))
    return list(torch.split(x, chunk_size, axis))


def tile(x, reps):
    if isinstance(reps, torch.Tensor):
        reps = reps.detach().cpu().numpy().tolist()
    return x.repeat(reps)


# noinspection PyUnresolvedReferences
def constant_pad(x, pad_width: List[List[int]], value: Number = 0.):
    if x.shape == ():
        x = x.unsqueeze(0)
    if isinstance(pad_width, torch.Tensor):
        pad_width = pad_width.detach().cpu().numpy().tolist()
    pad_width.reverse()
    pad_width_flat: List[int] = list()
    for pad_width_sec in pad_width:
        for item in pad_width_sec:
            pad_width_flat.append(item)
    return torch.nn.functional.pad(x, pad_width_flat, mode='constant', value=value)


def zero_pad(x, pad_width: List[List[int]]):
    return constant_pad(x, pad_width, 0.)


def swapaxes(x, axis0, axis1):
    return torch.transpose(x, axis0, axis1)


def transpose(x, axes: List[int]):
    if axes is None:
        num_dims = len(x.shape)
        axes = list(range(num_dims))
        axes.reverse()
    return x.permute(axes)


def expand_dims(x, axis: int):
    return torch.unsqueeze(x, axis)


def where(condition, x1, x2):
    return torch.where(condition.type(torch.bool), x1, x2)


def indices_where(x):
    where_x = torch.where(x)
    res = torch.cat([torch.unsqueeze(item, -1) for item in where_x], -1)
    return res


def reshape(x, newshape: List[int]):
    return torch.reshape(x, newshape)


def broadcast_to(x, new_shape):
    return torch.broadcast_to(x, new_shape)


def squeeze(x, axis: Optional[int] = None):
    if axis is None:
        return torch.squeeze(x)
    return torch.squeeze(x, axis)


# noinspection PyShadowingNames
def zeros(shape: List[int], dtype_str: str = 'float32', dev_str: Optional[str] = None):
    type_dict: Dict[str, torch.dtype] = {'bool': torch.bool,
                                         'int8': torch.int8,
                                         'int16': torch.int16,
                                         'int32': torch.int32,
                                         'int64': torch.int64,
                                         'float16': torch.float16,
                                         'float32': torch.float32,
                                         'float64': torch.float64}
    dtype_val: torch.dtype = type_dict[dtype_str]
    return torch.zeros(shape, dtype=dtype_val).to(str_to_dev(dev_str))


# noinspection PyShadowingNames
def zeros_like(x, dtype_str: Optional[str] = None, dev_str: Optional[str] = None):
    if dev_str is None:
        dev_str = _callable_dev_str(x)
    if dtype_str is not None:
        type_dict: Dict[str, torch.dtype] = {'bool': torch.bool,
                                             'int8': torch.int8,
                                             'int16': torch.int16,
                                             'int32': torch.int32,
                                             'int64': torch.int64,
                                             'float16': torch.float16,
                                             'float32': torch.float32,
                                             'float64': torch.float64}
        return torch.zeros_like(x, dtype=type_dict[dtype_str]).to(str_to_dev(dev_str))
    return torch.zeros_like(x).to(str_to_dev(dev_str))


# noinspection PyShadowingNames
def ones(shape: List[int], dtype_str: str = 'float32', dev_str: Optional[str] = None):
    type_dict: Dict[str, torch.dtype] = {'bool': torch.bool,
                                         'int8': torch.int8,
                                         'int16': torch.int16,
                                         'int32': torch.int32,
                                         'int64': torch.int64,
                                         'float16': torch.float16,
                                         'float32': torch.float32,
                                         'float64': torch.float64}
    dtype_val: torch.dtype = type_dict[dtype_str]
    return torch.ones(shape, dtype=dtype_val).to(str_to_dev(dev_str))


# noinspection PyShadowingNames
def ones_like(x, dtype_str: Optional[str] = None, dev_str: Optional[str] = None):
    if dev_str is None:
        dev_str = _callable_dev_str(x)
    if dtype_str is not None:
        type_dict: Dict[str, torch.dtype] = {'bool': torch.bool,
                                             'int8': torch.int8,
                                             'int16': torch.int16,
                                             'int32': torch.int32,
                                             'int64': torch.int64,
                                             'float16': torch.float16,
                                             'float32': torch.float32,
                                             'float64': torch.float64}
        return torch.ones_like(x, dtype=type_dict[dtype_str]).to(str_to_dev(dev_str))
    return torch.ones_like(x).to(str_to_dev(dev_str))


# noinspection PyUnresolvedReferences,PyShadowingNames
def one_hot(indices, depth: int, dev_str: Optional[str] = None):
    if dev_str is None:
        dev_str = _callable_dev_str(indices)
    return torch.nn.functional.one_hot(indices.type(torch.int64), depth).to(str_to_dev(dev_str))


def cross(x1, x2):
    return torch.cross(x1, x2)


def matmul(x1, x2):
    return torch.matmul(x1, x2)


def cumsum(x, axis: int = 0):
    return torch.cumsum(x, axis)


def cumprod(x, axis: int = 0, exclusive: bool = False):
    if exclusive:
        x = torch.swapaxes(x, axis, -1)
        x = torch.cat((torch.ones_like(x[..., -1:]), x[..., :-1]), -1)
        res = torch.cumprod(x, -1)
        return torch.swapaxes(res, axis, -1)
    return torch.cumprod(x, axis)


# noinspection PyShadowingNames
def identity(n: int, dtype_str: str = 'float32', batch_shape: Optional[List[int]] = None,
             dev_str: Optional[str] = None):
    type_dict: Dict[str, torch.dtype] = {'bool': torch.bool,
                                         'int8': torch.int8,
                                         'int16': torch.int16,
                                         'int32': torch.int32,
                                         'int64': torch.int64,
                                         'float16': torch.float16,
                                         'float32': torch.float32,
                                         'float64': torch.float64}
    dtype_val: torch.dtype = type_dict[dtype_str]
    mat = torch.eye(n, n, dtype=dtype_val).to(str_to_dev(dev_str))
    if batch_shape is None:
        return mat
    else:
        reshape_dims = [1] * len(batch_shape) + [n, n]
        tile_dims = list(batch_shape) + [1, 1]
        res = torch.reshape(mat, reshape_dims).repeat(tile_dims)
        return res


def meshgrid(*xs, indexing='ij'):
    ret = torch.meshgrid(*xs)
    if indexing == 'xy':
        # ToDo: verify if this is correct
        return tuple([torch.swapaxes(x, 1, 0) for x in ret])
    return ret


# noinspection PyShadowingNames
def scatter_flat(indices, updates, size: int, reduction: str = 'sum', dev_str: Optional[str] = None):
    if dev_str is None:
        dev_str = _callable_dev_str(updates)
    dtype = updates.dtype
    if reduction == 'sum':
        initial_val = torch.tensor(0).type(dtype).to(str_to_dev(dev_str))
    elif reduction == 'min':
        initial_val = torch.tensor(1e12).type(dtype).to(str_to_dev(dev_str))
    elif reduction == 'max':
        initial_val = torch.tensor(-1e12).type(dtype).to(str_to_dev(dev_str))
    else:
        raise Exception('reduction is {}, but it must be one of "sum", "min" or "max"'.format(reduction))
    output = torch.ones([size], dtype=dtype).to(str_to_dev(dev_str)) * initial_val
    global torch_scatter
    if torch_scatter is None:
        try:
            import torch_scatter as torch_scatter
        except:
            raise Exception('Unable to import torch_scatter, verify this is correctly installed.')
    res = torch_scatter.scatter(updates, indices.type(torch.int64), out=output, reduce=reduction)
    res = torch.where(res == initial_val, torch.zeros([size], dtype=updates.dtype).to(str_to_dev(dev_str)), res)
    return res


# noinspection PyShadowingNames
def scatter_nd(indices, updates, shape, reduction='sum', dev_str=None):
    if dev_str is None:
        dev_str = _callable_dev_str(updates)
    shape = list(shape)
    dtype = updates.dtype
    indices_shape = indices.shape
    num_index_dims = indices_shape[-1]
    result_dim_sizes_list = [_reduce(mul, shape[i + 1:], 1) for i in range(len(shape) - 1)] + [1]
    result_dim_sizes = torch.tensor(result_dim_sizes_list).to(str_to_dev(dev_str))
    implicit_indices_factor = int(result_dim_sizes[num_index_dims - 1].item())
    flat_result_size = _reduce(mul, shape, 1)
    if reduction == 'sum':
        initial_val = torch.tensor(0).type(dtype).to(str_to_dev(dev_str))
    elif reduction == 'min':
        initial_val = torch.tensor(1e12).type(dtype).to(str_to_dev(dev_str))
    elif reduction == 'max':
        initial_val = torch.tensor(-1e12).type(dtype).to(str_to_dev(dev_str))
    else:
        raise Exception('reduction is {}, but it must be one of "sum", "min" or "max"'.format(reduction))
    flat_output = torch.ones(flat_result_size, dtype=dtype).to(str_to_dev(dev_str)) * initial_val
    flat_updates = torch.reshape(updates, (-1,))
    new_shape = [1] * (len(indices_shape) - 1) + [num_index_dims]
    indices_scales = torch.reshape(result_dim_sizes[0:num_index_dims], new_shape)
    indices_for_flat_tiled = torch.reshape(torch.sum(indices * indices_scales, -1, keepdim=True), (-1, 1)).repeat(
        *[1, implicit_indices_factor])
    implicit_indices = torch.unsqueeze(torch.arange(implicit_indices_factor).to(str_to_dev(dev_str)), 0).repeat(
        *[indices_for_flat_tiled.shape[0], 1])
    indices_for_flat = indices_for_flat_tiled + implicit_indices
    flat_indices_for_flat = torch.reshape(indices_for_flat, (-1,)).type(torch.long)
    global torch_scatter
    if torch_scatter is None:
        try:
            import torch_scatter as torch_scatter
        except:
            raise Exception('Unable to import torch_scatter, verify this is correctly installed.')
    flat_scatter = torch_scatter.scatter(flat_updates, flat_indices_for_flat, out=flat_output, reduce=reduction)
    # noinspection PyTypeChecker
    flat_scatter = torch.where(flat_scatter == initial_val, torch.zeros(flat_result_size, dtype=updates.dtype)
                               .to(str_to_dev(dev_str)), flat_scatter)
    res = torch.reshape(flat_scatter, list(shape))
    return res


# noinspection PyShadowingNames
def gather(params, indices, axis=-1, dev_str: Optional[str] = None):
    if dev_str is None:
        dev_str = _callable_dev_str(params)
    return torch.gather(params, axis, indices.type(torch.int64)).to(str_to_dev(dev_str))


# noinspection PyShadowingNames
def gather_nd(params, indices, dev_str: Optional[str] = None):
    if dev_str is None:
        dev_str = _callable_dev_str(params)
    indices_shape = indices.shape
    params_shape = params.shape
    num_index_dims = indices_shape[-1]
    result_dim_sizes_list = [_reduce(mul, params_shape[i + 1:], 1) for i in range(len(params_shape) - 1)] + [1]
    result_dim_sizes = torch.tensor(result_dim_sizes_list).to(str_to_dev(dev_str))
    implicit_indices_factor = int(result_dim_sizes[num_index_dims - 1].item())
    flat_params = torch.reshape(params, (-1,))
    new_shape = [1] * (len(indices_shape) - 1) + [num_index_dims]
    indices_scales = torch.reshape(result_dim_sizes[0:num_index_dims], new_shape)
    indices_for_flat_tiled = torch.reshape(torch.sum(indices * indices_scales, -1, keepdim=True), (-1, 1)).repeat(
        *[1, implicit_indices_factor])
    implicit_indices = torch.unsqueeze(torch.arange(implicit_indices_factor).to(str_to_dev(dev_str)), 0).repeat(
        *[indices_for_flat_tiled.shape[0], 1])
    indices_for_flat = indices_for_flat_tiled + implicit_indices
    flat_indices_for_flat = torch.reshape(indices_for_flat, (-1,)).type(torch.long)
    flat_gather = torch.gather(flat_params, 0, flat_indices_for_flat)
    res = torch.reshape(flat_gather, list(indices_shape[:-1]) + list(params_shape[num_index_dims:]))
    return res


def dev(x):
    return x.device


def to_dev(x, dev_str: Optional[str] = None):
    return x.to(str_to_dev(dev_str))


def dev_to_str(dev_in: torch.device):
    dev_type, dev_idx = (dev_in.type, dev_in.index)
    return dev_type + (':' + (str(dev_idx) if dev_idx is not None else '0'))


def str_to_dev(dev_str: Optional[str] = None) -> Optional[torch.device]:
    if dev_str is None:
        return dev_str
    return torch.device(dev_str.replace('gpu', 'cuda'))


def dev_str(x):
    return dev_to_str(dev(x))


_callable_dev_str = dev_str
gpu_is_available = torch.cuda.is_available


# noinspection PyUnresolvedReferences
def tpu_is_available():
    if importlib.util.find_spec("torch_xla") is not None:
        return True
    return False


def dtype(x):
    return x.dtype


def dtype_str(x):
    return {torch.bool: 'bool',
            torch.int8: 'int8',
            torch.int16: 'int16',
            torch.int32: 'int32',
            torch.int64: 'int64',
            torch.float16: 'float16',
            torch.float32: 'float32',
            torch.float64: 'float64'}[x.dtype]


def dtype_to_str(dtype_in):
    return {torch.bool: 'bool',
            torch.int8: 'int8',
            torch.int16: 'int16',
            torch.int32: 'int32',
            torch.int64: 'int64',
            torch.float16: 'float16',
            torch.float32: 'float32',
            torch.float64: 'float64'}[dtype_in]


def compile_fn(fn, dynamic=True, example_inputs=None):
    if dynamic:
        return torch.jit.script(fn)
    return torch.jit.trace(fn, example_inputs)
