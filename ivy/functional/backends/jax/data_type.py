# global
import numpy as np
import jax
import jaxlib
import jax.numpy as jnp
from typing import Union, Tuple, List

# local
import ivy
from ivy.functional.backends.jax import JaxArray


def can_cast(from_: Union[jnp.dtype, JaxArray], to: jnp.dtype) -> bool:
    if type(from_) in [
        jax.interpreters.xla._DeviceArray,
        jaxlib.xla_extension.DeviceArray,
    ]:
        from_ = str(from_.dtype)
    from_ = str(from_)
    to = str(to)
    if "bool" in from_ and (("int" in to) or ("float" in to)):
        return False
    if "int" in from_ and "float" in to:
        return False
    return jnp.can_cast(from_, to)


DTYPE_TO_STR = {
    jnp.dtype("int8"): "int8",
    jnp.dtype("int16"): "int16",
    jnp.dtype("int32"): "int32",
    jnp.dtype("int64"): "int64",
    jnp.dtype("uint8"): "uint8",
    jnp.dtype("uint16"): "uint16",
    jnp.dtype("uint32"): "uint32",
    jnp.dtype("uint64"): "uint64",
    jnp.dtype("bfloat16"): "bfloat16",
    jnp.dtype("float16"): "float16",
    jnp.dtype("float32"): "float32",
    jnp.dtype("float64"): "float64",
    jnp.dtype("bool"): "bool",
    jnp.int8: "int8",
    jnp.int16: "int16",
    jnp.int32: "int32",
    jnp.int64: "int64",
    jnp.uint8: "uint8",
    jnp.uint16: "uint16",
    jnp.uint32: "uint32",
    jnp.uint64: "uint64",
    jnp.bfloat16: "bfloat16",
    jnp.float16: "float16",
    jnp.float32: "float32",
    jnp.float64: "float64",
    jnp.bool_: "bool",
}

DTYPE_FROM_STR = {
    "int8": jnp.dtype("int8"),
    "int16": jnp.dtype("int16"),
    "int32": jnp.dtype("int32"),
    "int64": jnp.dtype("int64"),
    "uint8": jnp.dtype("uint8"),
    "uint16": jnp.dtype("uint16"),
    "uint32": jnp.dtype("uint32"),
    "uint64": jnp.dtype("uint64"),
    "bfloat16": jnp.dtype("bfloat16"),
    "float16": jnp.dtype("float16"),
    "float32": jnp.dtype("float32"),
    "float64": jnp.dtype("float64"),
    "bool": jnp.dtype("bool"),
}


# noinspection PyShadowingBuiltins
def iinfo(type: Union[jnp.dtype, str, JaxArray]) -> np.iinfo:
    return jnp.iinfo(ivy.dtype_from_str(type))


class Finfo:
    def __init__(self, jnp_finfo):
        self._jnp_finfo = jnp_finfo

    @property
    def bits(self):
        return self._jnp_finfo.bits

    @property
    def eps(self):
        return float(self._jnp_finfo.eps)

    @property
    def max(self):
        return float(self._jnp_finfo.max)

    @property
    def min(self):
        return float(self._jnp_finfo.min)

    @property
    def smallest_normal(self):
        return float(self._jnp_finfo.tiny)


# noinspection PyShadowingBuiltins
def finfo(type: Union[jnp.dtype, str, JaxArray]) -> Finfo:
    return Finfo(jnp.finfo(ivy.dtype_from_str(type)))


def result_type(*arrays_and_dtypes: Union[JaxArray, jnp.dtype]) -> jnp.dtype:
    if len(arrays_and_dtypes) <= 1:
        return jnp.result_type(arrays_and_dtypes)

    result = jnp.result_type(arrays_and_dtypes[0], arrays_and_dtypes[1])
    for i in range(2, len(arrays_and_dtypes)):
        result = jnp.result_type(result, arrays_and_dtypes[i])
    return result


def broadcast_to(x: JaxArray, shape: Tuple[int, ...]) -> JaxArray:
    return jnp.broadcast_to(x, shape)


def broadcast_arrays(*arrays: JaxArray) -> List[JaxArray]:
    return jnp.broadcast_arrays(*arrays)


def astype(x: JaxArray, dtype: jnp.dtype, copy: bool = True) -> JaxArray:
    if copy:
        if x.dtype == dtype:
            new_tensor = jnp.array(x)
            return new_tensor
    else:
        if x.dtype == dtype:
            return x
        else:
            new_tensor = jnp.array(x)
            return new_tensor.astype(dtype)
    return x.astype(dtype)


def dtype_bits(dtype_in):
    dtype_str = dtype_to_str(dtype_in)
    if "bool" in dtype_str:
        return 1
    return int(
        dtype_str.replace("uint", "")
        .replace("int", "")
        .replace("bfloat", "")
        .replace("float", "")
    )


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
