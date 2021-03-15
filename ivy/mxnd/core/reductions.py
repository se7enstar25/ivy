"""
Collection of MXNet reduction functions, wrapped to fit Ivy syntax and signature.
"""

# global
import mxnet as _mx
from numbers import Number


def reduce_sum(x, axis=None, keepdims=False):
    axis_specified = True
    if axis is None:
        axis_specified = False
        num_dims = len(x.shape)
        axis = tuple(range(num_dims))
    elif isinstance(axis, Number):
        axis = (axis,)
    elif isinstance(axis, list):
        axis = tuple(axis)
    return _mx.nd.sum(x, axis=axis, keepdims=keepdims)


def reduce_prod(x, axis=None, keepdims=False):
    axis_specified = True
    if axis is None:
        axis_specified = False
        num_dims = len(x.shape)
        axis = tuple(range(num_dims))
    elif isinstance(axis, Number):
        axis = (axis,)
    elif isinstance(axis, list):
        axis = tuple(axis)
    return _mx.nd.prod(x, axis=axis, keepdims=keepdims)


def reduce_mean(x, axis=None, keepdims=False):
    axis_specified = True
    if axis is None:
        axis_specified = False
        num_dims = len(x.shape)
        axis = tuple(range(num_dims))
    elif isinstance(axis, Number):
        axis = (axis,)
    elif isinstance(axis, list):
        axis = tuple(axis)
    return _mx.nd.mean(x, axis=axis, keepdims=keepdims)


def reduce_min(x, axis=None, keepdims=False):
    axis_specified = True
    if axis is None:
        axis_specified = False
        num_dims = len(x.shape)
        axis = tuple(range(num_dims))
    elif isinstance(axis, Number):
        axis = (axis,)
    elif isinstance(axis, list):
        axis = tuple(axis)
    return _mx.nd.min(x, axis=axis, keepdims=keepdims)


def reduce_max(x, axis=None, keepdims=False):
    axis_specified = True
    if axis is None:
        axis_specified = False
        num_dims = len(x.shape)
        axis = tuple(range(num_dims))
    elif isinstance(axis, Number):
        axis = (axis,)
    elif isinstance(axis, list):
        axis = tuple(axis)
    return _mx.nd.max(x, axis=axis, keepdims=keepdims)
