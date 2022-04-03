# global
import jax.numpy as jnp

from typing import Tuple, Union, Optional , List
from ivy.functional.backends.jax import JaxArray


# local
from ivy.functional.backends.jax import JaxArray

# Array API Standard #
# -------------------#
import ivy


def min(x: JaxArray,
        axis: Union[int, Tuple[int]] = None,
        keepdims = False, device = None) \
        -> JaxArray:
    return jnp.min(a = jnp.asarray(x), axis = axis, keepdims = keepdims)


def sum(x: JaxArray,
        axis: Optional[Union[int,Tuple[int]]] = None,
        dtype: Optional[jnp.dtype] = None,
        keepdims: bool = False) -> JaxArray:

    if dtype == None and jnp.issubdtype(x.dtype, jnp.integer):
        if jnp.issubdtype(x.dtype, jnp.signedinteger) and x.dtype in [jnp.int8, jnp.int16, jnp.int32]:
            dtype = jnp.int32
        elif jnp.issubdtype(x.dtype, jnp.unsignedinteger) and x.dtype in [jnp.uint8, jnp.uint16, jnp.uint32]:
            dtype = jnp.uint32
        elif x.dtype == jnp.int64:
            dtype = jnp.int64
        else:
            dtype = jnp.uint64

    return jnp.sum(a=x, axis=axis, dtype=dtype, keepdims=keepdims)


def mean(x: JaxArray,
         axis: Optional[Union[int, Tuple[int, ...]]] = None,
         keepdims: bool = False)\
        -> JaxArray:
    if axis is None:
        num_dims = len(x.shape)
        axis = tuple(range(num_dims))
    elif isinstance(axis, list):
        axis = tuple(axis)
    return jnp.mean(x, axis=axis, keepdims=keepdims)


def prod(x: JaxArray,
         axis: Optional[Union[int, Tuple[int]]] = None,
         dtype: Optional[jnp.dtype] = None,
         keepdims: bool = False)\
        -> JaxArray:

    if dtype == None and jnp.issubdtype(x.dtype,jnp.integer):
        if jnp.issubdtype(x.dtype,jnp.signedinteger) and x.dtype in [jnp.int8,jnp.int16,jnp.int32]:
            dtype = jnp.int32
        elif jnp.issubdtype(x.dtype,jnp.unsignedinteger) and x.dtype in [jnp.uint8,jnp.uint16,jnp.uint32]:
            dtype = jnp.uint32
        elif x.dtype == jnp.int64: 
            dtype = jnp.int64
        else:
            dtype = jnp.uint64

    return jnp.prod(a=x,axis=axis,dtype=dtype,keepdims=keepdims)


def max(x: JaxArray,
        axis: Union[int, Tuple[int]] = None,
        keepdims = False, device = None) \
        -> JaxArray:
    return jnp.max(a = jnp.asarray(x), axis = axis, keepdims = keepdims)


def var(x: JaxArray,
        axis: Optional[Union[int, Tuple[int]]] = None,
        correction: Union[int, float] = 0.0,
        keepdims: bool = False) \
        -> JaxArray:
    return jnp.var(x, axis=axis, ddof=correction, keepdims=keepdims)


def std(x: JaxArray,
        axis: Optional[Union[int, Tuple[int]]] = None,
        correction: Union[int, float] = 0.0,
        keepdims: bool = False) \
        -> JaxArray:
    return jnp.std(x, axis=axis, ddof=correction, keepdims=keepdims)


# Extra #
# ------#

def einsum(equation, *operands):
    return jnp.einsum(equation, *operands)
