# global
import tensorflow as tf
from tensorflow.python.types.core import Tensor


# local
import ivy


def isfinite(x: Tensor)\
        -> Tensor:
    if ivy.is_int_dtype(x):
        return tf.ones_like(x, tf.bool)
    return tf.math.is_finite(x)


def cos(x: Tensor)\
        -> Tensor:
    return tf.cos(x)

  
def logical_not(x: Tensor) -> Tensor:
    return tf.logical_not(tf.cast(x, tf.bool))
