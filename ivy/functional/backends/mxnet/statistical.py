from numbers import Number
from typing import Optional, Tuple, Union
import mxnet as mx

# Local
import ivy
from ivy.functional.backends.mxnet import (
    _flat_array_to_1_dim_array,
    _1_dim_array_to_flat_array,
    _handle_output,
)


# Array API Standard #
# -------------------#


def sum(
    x: mx.ndarray.ndarray.NDArray,
    axis: Optional[Union[int, Tuple[int, ...]]] = None,
    keepdims: bool = False,
    out: Optional[mx.ndarray.ndarray.NDArray] = None,
) -> mx.ndarray.ndarray.NDArray:

    if axis is None:
        num_dims = len(x.shape)
        axis = tuple(range(num_dims))
    elif isinstance(axis, Number):
        axis = (axis,)
    elif isinstance(axis, list):
        axis = tuple(axis)
    if x.shape == ():
        x = _flat_array_to_1_dim_array(x)
    ret = mx.nd.sum(x, axis=axis, keepdims=keepdims)
    if ivy.exists(out):
        return ivy.inplace_update(out, _handle_output(x, axis, keepdims, ret))
    else:
        return _handle_output(x, axis, keepdims, ret)


def prod(
    x: mx.ndarray.ndarray.NDArray,
    axis: Optional[Union[int, Tuple[int, ...]]] = None,
    keepdims: bool = False,
    out: Optional[mx.ndarray.ndarray.NDArray] = None,
) -> mx.ndarray.ndarray.NDArray:
    if axis is None:
        num_dims = len(x.shape)
        axis = tuple(range(num_dims))
    elif isinstance(axis, Number):
        axis = (axis,)
    elif isinstance(axis, list):
        axis = tuple(axis)
    if x.shape == ():
        x = _flat_array_to_1_dim_array(x)
    ret = mx.nd.prod(x, axis=axis, keepdims=keepdims)
    if ivy.exists(out):
        return ivy.inplace_update(out, _handle_output(x, axis, keepdims, ret))
    else:
        return _handle_output(x, axis, keepdims, ret)


def mean(
    x: mx.ndarray.ndarray.NDArray,
    axis: Optional[Union[int, Tuple[int, ...]]] = None,
    keepdims: bool = False,
    out: Optional[mx.ndarray.ndarray.NDArray] = None,
) -> mx.ndarray.ndarray.NDArray:
    if axis is None:
        num_dims = len(x.shape)
        axis = tuple(range(num_dims))
    elif isinstance(axis, Number):
        axis = (axis,)
    elif isinstance(axis, list):
        axis = tuple(axis)
    if x.shape == ():
        x = _flat_array_to_1_dim_array(x)
    ret = mx.nd.mean(x, axis=axis, keepdims=keepdims)
    if ivy.exists(out):
        return ivy.inplace_update(out, _handle_output(x, axis, keepdims, ret))
    else:
        return _handle_output(x, axis, keepdims, ret)


def var(
    x: mx.ndarray.ndarray,
    axis: Union[int, Tuple[int, ...]] = None,
    keepdims: bool = False,
    out: Optional[mx.ndarray.ndarray.NDArray] = None,
) -> mx.ndarray.ndarray.NDArray:
    mean_of_x_sqrd = mean(x**2, axis, keepdims)
    mean_of_x = mean(x, axis, keepdims)
    is_flat = mean_of_x.shape == ()
    if is_flat:
        mean_of_x_sqrd = _flat_array_to_1_dim_array(mean_of_x_sqrd)
        mean_of_x = _flat_array_to_1_dim_array(mean_of_x)
    ret = mean_of_x_sqrd - mean_of_x**2
    if is_flat:
        if ivy.exists(out):
            return ivy.inplace_update(out, _1_dim_array_to_flat_array(ret))
        else:
            return _1_dim_array_to_flat_array(ret)
    if ivy.exists(out):
        return ivy.inplace_update(out, ret)
    else:
        return ret


def std(
    x: mx.ndarray.ndarray.NDArray,
    axis: Optional[Union[int, Tuple[int, ...]]] = None,
    keepdims: bool = False,
    out: Optional[mx.ndarray.ndarray.NDArray] = None,
) -> mx.ndarray.ndarray.NDArray:
    red_var = var(x, axis, keepdims)
    is_flat = red_var.shape == ()
    if is_flat:
        red_var = _flat_array_to_1_dim_array(red_var)
    red_std = red_var**0.5
    if is_flat:
        if ivy.exists(out):
            return ivy.inplace_update(out, _1_dim_array_to_flat_array(red_std))
        else:
            return _1_dim_array_to_flat_array(red_std)
    if ivy.exists(out):
        return ivy.inplace_update(out, red_std)
    else:
        return red_std


def min(
    x: mx.ndarray.ndarray.NDArray,
    axis: Union[int, Tuple[int, ...]] = None,
    keepdims: bool = False,
    out: Optional[mx.ndarray.ndarray.NDArray] = None,
) -> mx.ndarray.ndarray.NDArray:
    if axis is None:
        num_dims = len(x.shape)
        axis = tuple(range(num_dims))
    elif isinstance(axis, Number):
        axis = (axis,)
    elif isinstance(axis, list):
        axis = tuple(axis)
    if x.shape == ():
        x = _flat_array_to_1_dim_array(x)
    ret = mx.nd.min(x, axis=axis, keepdims=keepdims)
    if ivy.exists(out):
        return ivy.inplace_update(out, _handle_output(x, axis, keepdims, ret))
    else:
        return _handle_output(x, axis, keepdims, ret)


def max(
    x: mx.ndarray.ndarray.NDArray,
    axis: Union[int, Tuple[int, ...]] = None,
    keepdims: bool = False,
    out: Optional[mx.ndarray.ndarray.NDArray] = None,
) -> mx.ndarray.ndarray.NDArray:
    if axis is None:
        num_dims = len(x.shape)
        axis = tuple(range(num_dims))
    elif isinstance(axis, Number):
        axis = (axis,)
    elif isinstance(axis, list):
        axis = tuple(axis)
    if x.shape == ():
        x = _flat_array_to_1_dim_array(x)
    ret = mx.nd.max(x, axis=axis, keepdims=keepdims)
    if ivy.exists(out):
        return ivy.inplace_update(out, _handle_output(x, axis, keepdims, ret))
    else:
        return _handle_output(x, axis, keepdims, ret)


# Extra #
# ------#


def einsum(
    equation: str,
    *operands: mx.ndarray.ndarray.NDArray,
    out: Optional[mx.ndarray.ndarray.NDArray] = None
) -> mx.ndarray.ndarray.NDArray:
    if ivy.exists(out):
        return ivy.inplace_update(
            out,
            mx.np.einsum(
                equation, *[op.as_np_ndarray() for op in operands]
            ).as_nd_ndarray(),
        )
    else:
        return mx.np.einsum(
            equation, *[op.as_np_ndarray() for op in operands]
        ).as_nd_ndarray()
