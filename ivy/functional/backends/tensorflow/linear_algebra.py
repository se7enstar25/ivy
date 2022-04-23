# global
import tensorflow as tf
from tensorflow.python.types.core import Tensor
from typing import Union, Optional, Tuple, Literal, List
from collections import namedtuple

# local
from ivy import inf
import ivy


# Array API Standard #
# -------------------#


def eigh(x: Tensor,
         out: Optional[Tensor] = None)\
        -> Tensor:
        ret = tf.linalg.eigh(x)
        if ivy.exists(out):
            return ivy.inplace_update(out, ret)
        return ret

def inv(x: Tensor,
        out: Optional[Tensor] = None) \
        -> Tensor:
    if tf.math.reduce_any(tf.linalg.det(x) == 0 ):
        ret = x
    else:
        ret = tf.linalg.inv(x)
    if ivy.exists(out):
        return ivy.inplace_update(out, ret)
    return ret


def tensordot(x1: Tensor,
              x2: Tensor,
              axes: Union[int, Tuple[List[int], List[int]]] = 2,
              out: Optional[Tensor] = None) \
        -> Tensor:

    # find type to promote to
    dtype = tf.experimental.numpy.promote_types(x1.dtype, x2.dtype)

    # type casting to float32 which is acceptable for tf.tensordot
    x1, x2 = tf.cast(x1, tf.float32), tf.cast(x2, tf.float32)

    ret = tf.cast(tf.tensordot(x1, x2, axes), dtype)
    if ivy.exists(out):
        return ivy.inplace_update(out, ret)
    return ret


def vecdot(x1: Tensor,
           x2: Tensor,
           axis: int = -1,
           out: Optional[Tensor] = None)\
        -> Tensor:
    dtype = tf.experimental.numpy.promote_types(x1.dtype, x2.dtype)
    x1, x2 = tf.cast(x1, tf.float32), tf.cast(x2, tf.float32)
    ret = tf.cast(tf.tensordot(x1, x2, (axis, axis)), dtype)
    if ivy.exists(out):
        return ivy.inplace_update(out, ret)
    return ret


def pinv(x: Tensor,
         rtol: Optional[Union[float, Tuple[float]]] = None,
         out: Optional[Tensor] = None) \
        -> Tensor:
    if rtol is None:
        ret = tf.linalg.pinv(x)
    else:
        ret = tf.linalg.pinv(tf.cast(x != 0, 'float32'), tf.cast(rtol != 0, 'float32'))
    if ivy.exists(out):
        return ivy.inplace_update(out, ret)
    return ret


def matrix_transpose(x: Tensor,
                     out: Optional[Tensor] = None)\
        -> Tensor:
    ret = tf.experimental.numpy.swapaxes(x, -1, -2)
    if ivy.exists(out):
        return ivy.inplace_update(out, ret)
    return ret


# noinspection PyUnusedLocal,PyShadowingBuiltins
def vector_norm(x: Tensor,
                axis: Optional[Union[int, Tuple[int]]] = None,
                keepdims: bool = False,
                ord: Union[int, float, Literal[inf, - inf]] = 2,
                out: Optional[Tensor] = None)\
                 -> Tensor:

    if ord == -float('inf'):
        tn_normalized_vector = tf.reduce_min(tf.abs(x), axis, keepdims)
    elif ord == -1:
        tn_normalized_vector = tf.reduce_sum(tf.abs(x)**ord, axis, keepdims)**(1./ord)

    elif ord == 0:
        tn_normalized_vector = tf.reduce_sum(tf.cast(x != 0, 'float32'), axis, keepdims).numpy()

    else:
        tn_normalized_vector = tf.linalg.norm(x, ord, axis, keepdims)

    if tn_normalized_vector.shape == tuple():
        ret =  tf.expand_dims(tn_normalized_vector, 0)
    else:
        ret = tn_normalized_vector
    if ivy.exists(out):
        return ivy.inplace_update(out, ret)
    return ret


def matrix_norm(x: Tensor,
                ord: Optional[Union[int, float, Literal[inf, - inf, 'fro', 'nuc']]] = 'fro',
                keepdims: bool = False,
                out: Optional[Tensor] = None)\
        -> Tensor:
    axes = (-2, -1)
    if ord == -float('inf'):
        ret = tf.reduce_min(tf.reduce_sum(tf.abs(x), axis=axes[1], keepdims=True), axis=axes)
    elif ord == -1:
        ret = tf.reduce_min(tf.reduce_sum(tf.abs(x), axis=axes[0], keepdims=True), axis=axes)
    elif ord == -2:
        ret = tf.reduce_min(x, axis=(-2, -1), keepdims=keepdims)
    elif ord == 'nuc':
        if tf.size(x).numpy() == 0:
            ret = x
        else:
            ret = tf.reduce_sum(tf.linalg.svd(x, compute_uv=False), axis=-1)
    elif ord == 'fro':
        ret = tf.linalg.norm(x, 2, axes, keepdims)
    else:
        ret = tf.linalg.norm(x, ord, axes, keepdims)

    if keepdims:
        ret =  tf.reshape(ret, x.shape[:-2] + (1, 1))
    else:
        ret = tf.reshape(ret, x.shape[:-2])
    if ivy.exists(out):
        return ivy.inplace_update(out, ret)
    return ret


# noinspection PyPep8Naming
def svd(x:Tensor,
        full_matrices: bool = True,
        out: Optional[Union[Tensor, Tuple[Tensor,...]]] = None) \
        -> Union[Tensor, Tuple[Tensor,...]]:
    results=namedtuple("svd", "U S Vh")

    batch_shape = tf.shape(x)[:-2]
    num_batch_dims = len(batch_shape)
    transpose_dims = list(range(num_batch_dims)) + [num_batch_dims + 1, num_batch_dims]
    D, U, V = tf.linalg.svd(x,full_matrices=full_matrices)
    VT = tf.transpose(V, transpose_dims)
    ret=results(U, D, VT)
    if ivy.exists(out):
        return ivy.inplace_update(out, ret)
    return ret


def outer(x1: Tensor,
          x2: Tensor,
          out: Optional[Tensor] = None) \
        -> Tensor:
    ret =  tf.experimental.numpy.outer(x1, x2)
    if ivy.exists(out):
        return ivy.inplace_update(out, ret)
    return ret


def diagonal(x: tf.Tensor,
             offset: int = 0,
             axis1: int = -2,
             axis2: int = -1,
             out: Optional[Tensor] = None)\
        -> tf.Tensor:
    ret = tf.experimental.numpy.diagonal(x, offset, axis1=axis1, axis2=axis2)
    if ivy.exists(out):
        return ivy.inplace_update(out, ret)
    return ret


def qr(x: tf.Tensor,
       mode: str = 'reduced',
       out: Optional[Tuple[Tensor, Tensor]] = None) -> namedtuple('qr', ['Q', 'R']):
    res = namedtuple('qr', ['Q', 'R'])
    if mode == 'reduced':
        q, r = tf.linalg.qr(x, full_matrices=False)
        ret = res(q, r)
    elif mode == 'complete':
        q, r = tf.linalg.qr(x, full_matrices=True)
        ret =  res(q, r)
    else:
        raise Exception("Only 'reduced' and 'complete' qr modes are allowed for the tensorflow backend.")
    if ivy.exists(out):
        return ivy.inplace_update(out, ret)
    return ret


def matmul(x1: tf.Tensor,
           x2: tf.Tensor,
           out: Optional[Tensor] = None)\
        -> tf.Tensor:
    dtype_from = tf.experimental.numpy.promote_types(x1.dtype.as_numpy_dtype, x2.dtype.as_numpy_dtype)
    dtype_from = tf.as_dtype(dtype_from)
    if dtype_from.is_unsigned or dtype_from==tf.int8 or dtype_from==tf.int16:
        x1 = tf.cast(x1, tf.int64)
        x2 = tf.cast(x2, tf.int64)
    if x1.dtype != x2.dtype:
        x1 = tf.cast(x1, dtype_from)
        x2 = tf.cast(x2, dtype_from)

    if (x1.shape == () or x2.shape == ()
            or (len(x1.shape) == len(x2.shape) == 1 and x1.shape != x2.shape)
            or (len(x1.shape) == len(x2.shape) == 1 and x1.shape != x2.shape)
            or (len(x1.shape) == 1 and len(x2.shape) >= 2 and x1.shape[0] != x2.shape[-2])
            or (len(x2.shape) == 1 and len(x1.shape) >= 2 and x2.shape[0] != x1.shape[-1])
            or (len(x1.shape) >= 2 and len(x2.shape) >= 2 and x1.shape[-1] != x2.shape[-2])):
        raise Exception('Error,shapes not compatible')

    x1_padded = False
    x1_padded_2 = False
    x2_padded = False

    if len(x1.shape) == len(x2.shape) == 1:
        if x1.shape == 0:
            ret = tf.constant(0)
        else:

            ret = tf.math.multiply(x1, x2)[0]
        ret = tf.cast(ret, dtype=dtype_from)
        #return ret

    else:
        if len(x1.shape) == 1:
            if len(x2.shape) == 2:
                x1_padded_2 = True
            elif len(x2.shape) > 2:
                x1_padded = True
            x1 = tf.expand_dims(x1, axis=0)

        elif len(x2.shape) == 1 and len(x1.shape) >= 2:
            x2 = tf.expand_dims(x2, axis=1)
            x2_padded = True

        ret = tf.matmul(x1, x2)

    ret = tf.cast(ret, dtype=dtype_from)
    if x1_padded_2:
        ret = ret[0]
    elif x1_padded:
        ret = tf.squeeze(ret, axis=-2)
    elif x2_padded:
        ret = tf.squeeze(ret, axis=-1)
    if ivy.exists(out):
        return ivy.inplace_update(out, ret)
    return ret


def svdvals(x: tf.Tensor,
            out: Optional[Tensor] = None)\
        -> tf.Tensor:
    ret =  tf.linalg.svd(x, compute_uv=False)
    if ivy.exists(out):
        return ivy.inplace_update(out, ret)
    return ret


def slogdet(x:Union[ivy.Array,ivy.NativeArray],
            out: Optional[Tensor] = None) \
        -> Union[Tensor, Tuple[Tensor,...]]:
    results = namedtuple("slogdet", "sign logabsdet")
    sign, logabsdet = tf.linalg.slogdet(x)
    ret = results(sign, logabsdet)
    if ivy.exists(out):
        return ivy.inplace_update(out, ret)
    return ret


def trace(x: tf.Tensor,
          offset: int = 0,
          out: Optional[Tensor] = None)\
              -> tf.Tensor:
    ret = tf.linalg.trace(x, offset)
    if ivy.exists(out):
        return ivy.inplace_update(out, ret)
    return ret


def det(x: Tensor,
        out: Optional[Tensor] = None) \
    -> Tensor:
    ret = tf.linalg.det(x)
    if ivy.exists(out):
        return ivy.inplace_update(out, ret)
    return ret


def cholesky(x: tf.Tensor,
            upper: bool = False,
            out: Optional[Tensor] = None)\
        -> tf.Tensor:
    if not upper:
        ret = tf.linalg.cholesky(x)
    else:
        axes = list(range(len(x.shape) - 2)) + [len(x.shape) - 1, len(x.shape) - 2]
        ret = tf.transpose(tf.linalg.cholesky(tf.transpose(x, perm=axes)),
                            perm=axes)
    if ivy.exists(out):
        return ivy.inplace_update(out, ret)
    return ret



def eigvalsh(x: Tensor,
             out: Optional[Tensor] = None)\
        -> Tensor:
    ret = tf.linalg.eigvalsh(x)
    if ivy.exists(out):
        return ivy.inplace_update(out, ret)
    return ret


def matrix_rank(x: Tensor,
                rtol: Optional[Union[float, Tuple[float]]] = None,
                out: Optional[Tensor] = None)\
        -> Tensor:
    if rtol is None:
        ret = tf.linalg.matrix_rank(x)
    elif tf.size(x) == 0:
        ret = 0
    elif tf.size(x) == 1:
        ret = tf.math.count_nonzero(x)
    else:
        x = tf.reshape(x, [-1])
        x = tf.expand_dims(x, 0)
        if hasattr(rtol, 'dtype'):
            if rtol.dtype != x.dtype:
                promoted_dtype = tf.experimental.numpy.promote_types(rtol.dtype, x.dtype)
                x = tf.cast(x, promoted_dtype)
                rtol = tf.cast(rtol, promoted_dtype)
        ret = tf.linalg.matrix_rank(x, rtol)
    if ivy.exists(out):
        return ivy.inplace_update(out, ret)
    return ret


def cross (x1: tf.Tensor,
           x2: tf.Tensor,
           axis:int = -1,
           out: Optional[Tensor] = None)\
        -> tf.Tensor:
    ret = tf.experimental.numpy.cross(x1, x2,axis=axis)
    if ivy.exists(out):
        return ivy.inplace_update(out, ret)
    return ret

# Extra #
# ------#

def vector_to_skew_symmetric_matrix(vector: Tensor,
                                    out: Optional[Tensor] = None)\
        -> Tensor:
    batch_shape = list(vector.shape[:-1])
    # BS x 3 x 1
    vector_expanded = tf.expand_dims(vector, -1)
    # BS x 1 x 1
    a1s = vector_expanded[..., 0:1, :]
    a2s = vector_expanded[..., 1:2, :]
    a3s = vector_expanded[..., 2:3, :]
    # BS x 1 x 1
    zs = tf.zeros(batch_shape + [1, 1])
    # BS x 1 x 3
    row1 = tf.concat((zs, -a3s, a2s), -1)
    row2 = tf.concat((a3s, zs, -a1s), -1)
    row3 = tf.concat((-a2s, a1s, zs), -1)
    # BS x 3 x 3
    ret = tf.concat((row1, row2, row3), -2)
    if ivy.exists(out):
        return ivy.inplace_update(out, ret)
    return ret
