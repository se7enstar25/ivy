"""
Collection of Numpy general functions, wrapped to fit Ivy syntax and signature.
"""

# global
import logging
import numpy as _np
import math as _math
from operator import mul as _mul
from functools import reduce as _reduce
import multiprocessing as _multiprocessing

# local
import ivy
from ivy.functional.ivy.old import default_dtype
from ivy.functional.backends.numpy.device import _dev_callable

DTYPE_TO_STR = {_np.dtype('int8'): 'int8',
                _np.dtype('int16'): 'int16',
                _np.dtype('int32'): 'int32',
                _np.dtype('int64'): 'int64',
                _np.dtype('uint8'): 'uint8',
                _np.dtype('uint16'): 'uint16',
                _np.dtype('uint32'): 'uint32',
                _np.dtype('uint64'): 'uint64',
                'bfloat16': 'bfloat16',
                _np.dtype('float16'): 'float16',
                _np.dtype('float32'): 'float32',
                _np.dtype('float64'): 'float64',
                _np.dtype('bool'): 'bool',

                _np.int8: 'int8',
                _np.int16: 'int16',
                _np.int32: 'int32',
                _np.int64: 'int64',
                _np.uint8: 'uint8',
                _np.uint16: 'uint16',
                _np.uint32: 'uint32',
                _np.uint64: 'uint64',
                _np.float16: 'float16',
                _np.float32: 'float32',
                _np.float64: 'float64',
                _np.bool_: 'bool'}

DTYPE_FROM_STR = {'int8': _np.dtype('int8'),
                'int16': _np.dtype('int16'),
                'int32': _np.dtype('int32'),
                'int64': _np.dtype('int64'),
                'uint8': _np.dtype('uint8'),
                'uint16': _np.dtype('uint16'),
                'uint32': _np.dtype('uint32'),
                'uint64': _np.dtype('uint64'),
                'bfloat16': 'bfloat16',
                'float16': _np.dtype('float16'),
                'float32': _np.dtype('float32'),
                'float64': _np.dtype('float64'),
                'bool': _np.dtype('bool')}


# Helpers #
# --------#

def _to_dev(x, dev):
    if dev is not None:
        if 'gpu' in dev:
            raise Exception('Native Numpy does not support GPU placement, consider using Jax instead')
        elif 'cpu' in dev:
            pass
        else:
            raise Exception('Invalid device specified, must be in the form [ "cpu:idx" | "gpu:idx" ],'
                            'but found {}'.format(dev))
    return x


def _flat_array_to_1_dim_array(x):
    return x.reshape((1,)) if x.shape == () else x


# API #
# ----#







def dtype_bits(dtype_in):
    dtype_str = dtype_to_str(dtype_in)
    if 'bool' in dtype_str:
        return 1
    return int(dtype_str.replace('uint', '').replace('int', '').replace('bfloat', '').replace('float', ''))



to_numpy = lambda x: x
to_numpy.__name__ = 'to_numpy'
to_scalar = lambda x: x.item()
to_scalar.__name__ = 'to_scalar'
to_list = lambda x: x.tolist()
to_list.__name__ = 'to_list'
shape = lambda x, as_tensor=False: _np.asarray(_np.shape(x)) if as_tensor else x.shape
shape.__name__ = 'shape'
get_num_dims = lambda x, as_tensor=False: _np.asarray(len(_np.shape(x))) if as_tensor else len(x.shape)
minimum = _np.minimum
maximum = _np.maximum
clip = lambda x, x_min, x_max: _np.asarray(_np.clip(x, x_min, x_max))
round = lambda x: _np.asarray(_np.round(x))
floormod = lambda x, y: _np.asarray(x % y)
floor = lambda x: _np.asarray(_np.floor(x))
abs = lambda x: _np.asarray(_np.absolute(x))


def argmin(x, axis=0):
    ret = _np.asarray(_np.argmin(x, axis))
    if ret.shape == ():
        return ret.reshape(-1)
    return ret


def cast(x, dtype):
    return x.astype(dtype_from_str(dtype))


astype = cast


# noinspection PyShadowingNames
def arange(stop, start=0, step=1, dtype=None, dev=None):
    if dtype:
        dtype = dtype_from_str(dtype)
    res = _to_dev(_np.arange(start, stop, step=step, dtype=dtype), dev)
    if not dtype:
        if res.dtype == _np.float64:
            return res.astype(_np.float32)
        elif res.dtype == _np.int64:
            return res.astype(_np.int32)
    return res


def linspace(start, stop, num, axis=None, dev=None):
    if axis is None:
        axis = -1
    return _to_dev(_np.linspace(start, stop, num, axis=axis), dev)


def logspace(start, stop, num, base=10., axis=None, dev=None):
    if axis is None:
        axis = -1
    return _to_dev(_np.logspace(start, stop, num, base=base, axis=axis), dev)


def concatenate(xs, axis=-1):
    if xs[0].shape == ():
        return _np.concatenate([_np.expand_dims(x, 0) for x in xs], axis)
    return _np.concatenate(xs, axis)


stack = _np.stack


def unstack(x, axis, keepdims=False):
    if x.shape == ():
        return [x]
    x_split = _np.split(x, x.shape[axis], axis)
    if keepdims:
        return x_split
    return [_np.squeeze(item, axis) for item in x_split]


def split(x, num_or_size_splits=None, axis=0, with_remainder=False):
    if x.shape == ():
        if num_or_size_splits is not None and num_or_size_splits != 1:
            raise Exception('input array had no shape, but num_sections specified was {}'.format(num_or_size_splits))
        return [x]
    if num_or_size_splits is None:
        num_or_size_splits = x.shape[axis]
    elif isinstance(num_or_size_splits, int) and with_remainder:
        num_chunks = x.shape[axis] / num_or_size_splits
        num_chunks_int = _math.floor(num_chunks)
        remainder = num_chunks - num_chunks_int
        if remainder != 0:
            num_or_size_splits = [num_or_size_splits]*num_chunks_int + [int(remainder*num_or_size_splits)]
    if isinstance(num_or_size_splits, (list, tuple)):
        num_or_size_splits = _np.cumsum(num_or_size_splits[:-1])
    return _np.split(x, num_or_size_splits, axis)


repeat = _np.repeat
tile = _np.tile
constant_pad = lambda x, pad_width, value=0: _np.pad(_flat_array_to_1_dim_array(x), pad_width, constant_values=value)
zero_pad = lambda x, pad_width: _np.pad(_flat_array_to_1_dim_array(x), pad_width)
swapaxes = _np.swapaxes


def transpose(x, axes=None):
    if axes is None:
        num_dims = len(x.shape)
        axes = list(range(num_dims))
        axes.reverse()
    return _np.transpose(x, axes)


where = lambda condition, x1, x2: _np.where(condition, x1, x2)


def indices_where(x):
    where_x = _np.where(x)
    if len(where_x) == 1:
        return _np.expand_dims(where_x[0], -1)
    res = _np.concatenate([_np.expand_dims(item, -1) for item in where_x], -1)
    return res


reshape = _np.reshape
broadcast_to = _np.broadcast_to


def squeeze(x, axis=None):
    if x.shape == ():
        if axis is None or axis == 0 or axis == -1:
            return x
        raise Exception('tried to squeeze a zero-dimensional input by axis {}'.format(axis))
    return _np.squeeze(x, axis)




# noinspection PyShadowingNames
def zeros_like(x, dtype=None, dev=None):
    if dtype:
        dtype = 'bool_' if dtype == 'bool' else dtype
        dtype = _np.__dict__[dtype]
    else:
        dtype = x.dtype
    return _to_dev(_np.zeros_like(x, dtype=dtype), dev)


def full(shape, fill_value, dtype=None, device=None):
    return _to_dev(_np.full(shape, fill_value, dtype_from_str(default_dtype(dtype, fill_value))), device)


# noinspection PyUnusedLocal
def one_hot(indices, depth, dev=None):
    # from https://stackoverflow.com/questions/38592324/one-hot-encoding-using-numpy
    res = _np.eye(depth)[_np.array(indices).reshape(-1)]
    return res.reshape(list(indices.shape) + [depth])


cross = _np.cross
cumsum = _np.cumsum


def cumprod(x, axis=0, exclusive=False):
    if exclusive:
        x = _np.swapaxes(x, axis, -1)
        x = _np.concatenate((_np.ones_like(x[..., -1:]), x[..., :-1]), -1)
        res = _np.cumprod(x, -1)
        return _np.swapaxes(res, axis, -1)
    return _np.cumprod(x, axis)


# noinspection PyShadowingNames
def identity(n, dtype='float32', batch_shape=None, dev=None):
    dtype = 'bool_' if dtype == 'bool' else dtype
    dtype = _np.__dict__[dtype]
    mat = _np.identity(n, dtype=dtype)
    if batch_shape is None:
        return_mat = mat
    else:
        reshape_dims = [1] * len(batch_shape) + [n, n]
        tile_dims = list(batch_shape) + [1, 1]
        return_mat = _np.tile(_np.reshape(mat, reshape_dims), tile_dims)
    return _to_dev(return_mat, dev)


meshgrid = lambda *xs, indexing='ij': _np.meshgrid(*xs, indexing=indexing)


def scatter_flat(indices, updates, size=None, tensor=None, reduction='sum', dev=None):
    target = tensor
    target_given = ivy.exists(target)
    if ivy.exists(size) and ivy.exists(target):
        assert len(target.shape) == 1 and target.shape[0] == size
    if dev is None:
        dev = _dev_callable(updates)
    if reduction == 'sum':
        if not target_given:
            target = _np.zeros([size], dtype=updates.dtype)
        _np.add.at(target, indices, updates)
    elif reduction == 'replace':
        if not target_given:
            target = _np.zeros([size], dtype=updates.dtype)
        target = _np.asarray(target).copy()
        target.setflags(write=1)
        target[indices] = updates
    elif reduction == 'min':
        if not target_given:
            target = _np.ones([size], dtype=updates.dtype) * 1e12
        _np.minimum.at(target, indices, updates)
        if not target_given:
            target = _np.where(target == 1e12, 0., target)
    elif reduction == 'max':
        if not target_given:
            target = _np.ones([size], dtype=updates.dtype) * -1e12
        _np.maximum.at(target, indices, updates)
        if not target_given:
            target = _np.where(target == -1e12, 0., target)
    else:
        raise Exception('reduction is {}, but it must be one of "sum", "min" or "max"'.format(reduction))
    return _to_dev(target, dev)


# noinspection PyShadowingNames
def scatter_nd(indices, updates, shape=None, tensor=None, reduction='sum', dev=None):
    target = tensor
    target_given = ivy.exists(target)
    if ivy.exists(shape) and ivy.exists(target):
        assert ivy.shape_to_tuple(target.shape) == ivy.shape_to_tuple(shape)
    if dev is None:
        dev = _dev_callable(updates)
    shape = list(shape) if ivy.exists(shape) else list(tensor.shape)
    indices_flat = indices.reshape(-1, indices.shape[-1]).T
    indices_tuple = tuple(indices_flat) + (Ellipsis,)
    if reduction == 'sum':
        if not target_given:
            target = _np.zeros(shape, dtype=updates.dtype)
        _np.add.at(target, indices_tuple, updates)
    elif reduction == 'replace':
        if not target_given:
            target = _np.zeros(shape, dtype=updates.dtype)
        target = _np.asarray(target).copy()
        target.setflags(write=1)
        target[indices_tuple] = updates
    elif reduction == 'min':
        if not target_given:
            target = _np.ones(shape, dtype=updates.dtype) * 1e12
        _np.minimum.at(target, indices_tuple, updates)
        if not target_given:
            target = _np.where(target == 1e12, 0., target)
    elif reduction == 'max':
        if not target_given:
            target = _np.ones(shape, dtype=updates.dtype) * -1e12
        _np.maximum.at(target, indices_tuple, updates)
        if not target_given:
            target = _np.where(target == -1e12, 0., target)
    else:
        raise Exception('reduction is {}, but it must be one of "sum", "min" or "max"'.format(reduction))
    return _to_dev(target, dev)


def gather(params, indices, axis=-1, dev=None):
    if dev is None:
        dev = _dev_callable(params)
    return _to_dev(_np.take_along_axis(params, indices, axis), dev)


def gather_nd(params, indices, dev=None):
    if dev is None:
        dev = _dev_callable(params)
    indices_shape = indices.shape
    params_shape = params.shape
    num_index_dims = indices_shape[-1]
    result_dim_sizes_list = [_reduce(_mul, params_shape[i + 1:], 1) for i in range(len(params_shape) - 1)] + [1]
    result_dim_sizes = _np.array(result_dim_sizes_list)
    implicit_indices_factor = int(result_dim_sizes[num_index_dims - 1].item())
    flat_params = _np.reshape(params, (-1,))
    new_shape = [1] * (len(indices_shape) - 1) + [num_index_dims]
    indices_scales = _np.reshape(result_dim_sizes[0:num_index_dims], new_shape)
    indices_for_flat_tiled = _np.tile(_np.reshape(_np.sum(indices * indices_scales, -1, keepdims=True), (-1, 1)), (1, implicit_indices_factor))
    implicit_indices = _np.tile(_np.expand_dims(_np.arange(implicit_indices_factor), 0), (indices_for_flat_tiled.shape[0], 1))
    indices_for_flat = indices_for_flat_tiled + implicit_indices
    flat_indices_for_flat = _np.reshape(indices_for_flat, (-1,)).astype(_np.int32)
    flat_gather = _np.take(flat_params, flat_indices_for_flat, 0)
    new_shape = list(indices_shape[:-1]) + list(params_shape[num_index_dims:])
    res = _np.reshape(flat_gather, new_shape)
    return _to_dev(res, dev)


def linear_resample(x, num_samples, axis=-1):
    x_shape = list(x.shape)
    num_x_dims = len(x_shape)
    axis = axis % num_x_dims
    x_pre_shape = x_shape[0:axis]
    x_pre_size = _reduce(_mul, x_pre_shape) if x_pre_shape else 1
    num_pre_dims = len(x_pre_shape)
    num_vals = x.shape[axis]
    x_post_shape = x_shape[axis+1:]
    x_post_size = _reduce(_mul, x_post_shape) if x_post_shape else 1
    num_post_dims = len(x_post_shape)
    xp = _np.reshape(_np.arange(num_vals*x_pre_size*x_post_size), x_shape)
    x_coords = _np.arange(num_samples) * ((num_vals-1)/(num_samples-1)) * x_post_size
    x_coords = _np.reshape(x_coords, [1]*num_pre_dims + [num_samples] + [1]*num_post_dims)
    x_coords = _np.broadcast_to(x_coords, x_pre_shape + [num_samples] + x_post_shape)
    slc = [slice(None)] * num_x_dims
    slc[axis] = slice(0, 1, 1)
    x_coords = x_coords + xp[tuple(slc)]
    x = _np.reshape(x, (-1,))
    xp = _np.reshape(xp, (-1,))
    x_coords = _np.reshape(x_coords, (-1,))
    ret = _np.interp(x_coords, xp, x)
    return _np.reshape(ret, x_pre_shape + [num_samples] + x_post_shape)


def dtype(x, as_str=False):
    dt = x.dtype
    if as_str:
        return dtype_to_str(dt)
    return dt


def dtype_to_str(dtype_in):
    if isinstance(dtype_in, str):
        return dtype_in
    return DTYPE_TO_STR[dtype_in]


def dtype_from_str(dtype_in):
    if not isinstance(dtype_in, str):
        return dtype_in
    return DTYPE_FROM_STR[dtype_in]


# noinspection PyUnusedLocal
def compile(func, dynamic=True, example_inputs=None, static_argnums=None, static_argnames=None):
    logging.warning('Numpy does not support compiling functions.\n'
                    'Now returning the unmodified function.')
    return func


current_framework_str = lambda: 'numpy'
current_framework_str.__name__ = 'current_framework_str'
multiprocessing = lambda context=None: _multiprocessing if context is None else _multiprocessing.get_context(context)
container_types = lambda: []


def inplace_update(x, val):
    x.data = val
    return x


def inplace_decrement(x, val):
    x -= val
    return x


def inplace_increment(x, val):
    x += val
    return x

inplace_arrays_supported = lambda: True
inplace_variables_supported = lambda: True
