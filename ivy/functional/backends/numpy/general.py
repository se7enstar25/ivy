"""
Collection of Numpy general functions, wrapped to fit Ivy syntax and signature.
"""

# global
import logging
from typing import Optional
import numpy as np
from operator import mul as _mul
from functools import reduce as _reduce
import multiprocessing as _multiprocessing
from numbers import Number

# local
import ivy
from ivy.functional.ivy import default_dtype
from ivy.functional.backends.numpy.device import _dev_callable, _to_dev

# Helpers #
# --------#


copy_array = lambda x: x.copy()
array_equal = np.array_equal


def to_numpy(x: np.ndarray) \
        -> np.ndarray:
    return x

def to_scalar(x: np.ndarray) \
        -> Number:
    return x.item()

def to_list(x: np.ndarray) \
        -> list:
    return x.tolist()

container_types = lambda: []
inplace_arrays_supported = lambda: True
inplace_variables_supported = lambda: True


def inplace_update(x, val):
    (x_native, val_native), _ = ivy.args_to_native(x, val)
    x_native.data = val_native
    if ivy.is_ivy_array(x):
        x.data = x_native
    else:
        x = ivy.Array(x_native)
    return x


def is_native_array(x, exclusive=False):
    if isinstance(x, np.ndarray):
        return True
    return False


def floormod(x: np.ndarray, y: np.ndarray, out: Optional[np.ndarray] = None)\
        -> np.ndarray:
    ret = np.asarray(x%y)
    if ivy.exists(out):
        return ivy.inplace_update(out,ret)
    return ret


def unstack(x, axis, keepdims=False):
    if x.shape == ():
        return [x]
    x_split = np.split(x, x.shape[axis], axis)
    if keepdims:
        return x_split
    return [np.squeeze(item, axis) for item in x_split]


def inplace_decrement(x, val):
    (x_native, val_native), _ = ivy.args_to_native(x, val)
    x_native -= val_native
    if ivy.is_ivy_array(x):
        x.data = x_native
    else:
        x = ivy.Array(x_native)
    return x


def inplace_increment(x, val):
    (x_native, val_native), _ = ivy.args_to_native(x, val)
    x_native+= val_native
    if ivy.is_ivy_array(x):
        x.data = x_native
    else:
        x = ivy.Array(x_native)
    return x


def cumsum(x:np.ndarray,axis:int=0,out: Optional[np.ndarray] = None)\
        -> np.ndarray:
        if ivy.exists(out):
            return ivy.inplace_update(out,np.cumsum(x,axis))
        else:
            return np.cumsum(x,axis)


def cumprod(x:np.ndarray, axis:int=0, exclusive:Optional[bool]=False,
    out:Optional[np.ndarray] = None)\
        -> np.ndarray:
    if exclusive:
        x = np.swapaxes(x, axis, -1)
        x = np.concatenate((np.ones_like(x[..., -1:]), x[..., :-1]), -1)
        res = np.cumprod(x, -1)
        if ivy.exists(out):
            return ivy.inplace_update(out,np.swapaxes(res, axis, -1).copy())
        else:
            return np.swapaxes(res, axis, -1)
    if ivy.exists(out):
        return ivy.inplace_update(out,np.cumprod(x, axis))  
    else:
        return np.cumprod(x, axis)



def scatter_flat(indices, updates, size=None, tensor=None, reduction='sum', dev=None):
    target = tensor
    target_given = ivy.exists(target)
    if ivy.exists(size) and ivy.exists(target):
        assert len(target.shape) == 1 and target.shape[0] == size
    if dev is None:
        dev = _dev_callable(updates)
    if reduction == 'sum':
        if not target_given:
            target = np.zeros([size], dtype=updates.dtype)
        np.add.at(target, indices, updates)
    elif reduction == 'replace':
        if not target_given:
            target = np.zeros([size], dtype=updates.dtype)
        target = np.asarray(target).copy()
        target.setflags(write=1)
        target[indices] = updates
    elif reduction == 'min':
        if not target_given:
            target = np.ones([size], dtype=updates.dtype) * 1e12
        np.minimum.at(target, indices, updates)
        if not target_given:
            target = np.where(target == 1e12, 0., target)
    elif reduction == 'max':
        if not target_given:
            target = np.ones([size], dtype=updates.dtype) * -1e12
        np.maximum.at(target, indices, updates)
        if not target_given:
            target = np.where(target == -1e12, 0., target)
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
            target = np.zeros(shape, dtype=updates.dtype)
        np.add.at(target, indices_tuple, updates)
    elif reduction == 'replace':
        if not target_given:
            target = np.zeros(shape, dtype=updates.dtype)
        target = np.asarray(target).copy()
        target.setflags(write=1)
        target[indices_tuple] = updates
    elif reduction == 'min':
        if not target_given:
            target = np.ones(shape, dtype=updates.dtype) * 1e12
        np.minimum.at(target, indices_tuple, updates)
        if not target_given:
            target = np.where(target == 1e12, 0., target)
    elif reduction == 'max':
        if not target_given:
            target = np.ones(shape, dtype=updates.dtype) * -1e12
        np.maximum.at(target, indices_tuple, updates)
        if not target_given:
            target = np.where(target == -1e12, 0., target)
    else:
        raise Exception('reduction is {}, but it must be one of "sum", "min" or "max"'.format(reduction))
    return _to_dev(target, dev)


def gather(params: np.ndarray, indices:np.ndarray, axis: Optional[int]=-1, dev:Optional[str]=None, out:Optional[np.ndarray] = None)\
        -> np.ndarray:
    if dev is None:
        dev = _dev_callable(params)
    ret = _to_dev(np.take_along_axis(params, indices, axis), dev)
    if ivy.exists(out):
        return ivy.inplace_update(out,ret)
    else :
        return ret

def gather_nd(params, indices, dev=None):
    if dev is None:
        dev = _dev_callable(params)
    indices_shape = indices.shape
    params_shape = params.shape
    num_index_dims = indices_shape[-1]
    result_dim_sizes_list = [_reduce(_mul, params_shape[i + 1:], 1) for i in range(len(params_shape) - 1)] + [1]
    result_dim_sizes = np.array(result_dim_sizes_list)
    implicit_indices_factor = int(result_dim_sizes[num_index_dims - 1].item())
    flat_params = np.reshape(params, (-1,))
    new_shape = [1] * (len(indices_shape) - 1) + [num_index_dims]
    indices_scales = np.reshape(result_dim_sizes[0:num_index_dims], new_shape)
    indices_for_flat_tiled = np.tile(np.reshape(np.sum(indices * indices_scales, -1, keepdims=True), (-1, 1)), (1, implicit_indices_factor))
    implicit_indices = np.tile(np.expand_dims(np.arange(implicit_indices_factor), 0), (indices_for_flat_tiled.shape[0], 1))
    indices_for_flat = indices_for_flat_tiled + implicit_indices
    flat_indices_for_flat = np.reshape(indices_for_flat, (-1,)).astype(np.int32)
    flat_gather = np.take(flat_params, flat_indices_for_flat, 0)
    new_shape = list(indices_shape[:-1]) + list(params_shape[num_index_dims:])
    res = np.reshape(flat_gather, new_shape)
    return _to_dev(res, dev)

multiprocessing = lambda context=None: _multiprocessing if context is None else _multiprocessing.get_context(context)


def indices_where(x):
    where_x = np.where(x)
    if len(where_x) == 1:
        return np.expand_dims(where_x[0], -1)
    res = np.concatenate([np.expand_dims(item, -1) for item in where_x], -1)
    return res


# noinspection PyUnusedLocal
def one_hot(indices, depth, dev=None):
    # from https://stackoverflow.com/questions/38592324/one-hot-encoding-using-numpy
    res = np.eye(depth)[np.array(indices).reshape(-1)]
    return res.reshape(list(indices.shape) + [depth])

shape = lambda x, as_tensor=False: np.asarray(np.shape(x)) if as_tensor else x.shape
shape.__name__ = 'shape'
get_num_dims = lambda x, as_tensor=False: np.asarray(len(np.shape(x))) if as_tensor else len(x.shape)


# noinspection PyUnusedLocal
def compile(func, dynamic=True, example_inputs=None, static_argnums=None, static_argnames=None):
    logging.warning('Numpy does not support compiling functions.\n'
                    'Now returning the unmodified function.')
    return func

current_framework_str = lambda: 'numpy'
current_framework_str.__name__ = 'current_framework_str'
