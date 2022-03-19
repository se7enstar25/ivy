# global
import mxnet as mx
from typing import Union, Tuple, Optional, List

# local
from ivy.functional.backends.mxnet.statistical import prod
from ivy.functional.backends.mxnet import _flat_array_to_1_dim_array, _1_dim_array_to_flat_array


# noinspection PyShadowingBuiltins
def all(x: mx.ndarray.ndarray.NDArray,
        axis: Optional[Union[int, Tuple[int], List[int]]] = None,
        keepdims: bool = False)\
        -> mx.ndarray.ndarray.NDArray:
    red_prod = prod(x, axis, keepdims)
    is_flat = red_prod.shape == ()
    if is_flat:
        red_prod = _flat_array_to_1_dim_array(red_prod)
    red_prod = red_prod.astype(mx.np.bool_)
    if is_flat:
        return _1_dim_array_to_flat_array(red_prod)
    return red_prod


# noinspection PyShadowingBuiltins
def any(x: mx.ndarray.ndarray.NDArray,
        axis: Optional[Union[int, Tuple[int], List[int]]] = None,
        keepdims: bool = False)\
        -> mx.ndarray.ndarray.NDArray:
    return mx.nd.array(mx.nd.array(x).asnumpy().any(axis=axis, keepdims=keepdims))
