"""
Collection of MXNet random functions, wrapped to fit Ivy syntax and signature.
"""

# global
import mxnet as mx
from typing import Optional, Union, Tuple

# local
import ivy
from ivy.functional.ivy.device import default_device

# noinspection PyProtectedMember
from ivy.functional.backends.mxnet import _mxnet_init_context

# noinspection PyProtectedMember
from ivy.functional.backends.mxnet import _1_dim_array_to_flat_array


# Extra #
# ------#


def random_uniform(
    low: float = 0.0,
    high: float = 1.0,
    shape: Optional[Union[int, Tuple[int, ...]]] = None,
    device: Optional[ivy.Device] = None,
) -> mx.ndarray.ndarray.NDArray:
    if isinstance(low, mx.nd.NDArray):
        low = low.asscalar()
    if isinstance(high, mx.nd.NDArray):
        high = high.asscalar()
    ctx = _mxnet_init_context(default_device(device))
    if shape is None or len(shape) == 0:
        return _1_dim_array_to_flat_array(
            mx.nd.random.uniform(low, high, (1,), ctx=ctx)
        )
    return mx.nd.random.uniform(low, high, shape, ctx=ctx)


def random_normal(mean=0.0, std=1.0, shape=None, device=None):
    if isinstance(mean, mx.nd.NDArray):
        mean = mean.asscalar()
    if isinstance(std, mx.nd.NDArray):
        std = std.asscalar()
    ctx = _mxnet_init_context(default_device(device))
    if shape is None or len(shape) == 0:
        return _1_dim_array_to_flat_array(mx.nd.random.normal(mean, std, (1,), ctx=ctx))
    return mx.nd.random.uniform(mean, std, shape, ctx=ctx)


def multinomial(
    population_size, num_samples, batch_size, probs=None, replace=True, device=None
):
    if not replace:
        raise Exception("MXNet does not support multinomial without replacement")
    ctx = _mxnet_init_context(default_device(device))
    if probs is None:
        probs = (
            mx.nd.ones(
                (
                    batch_size,
                    population_size,
                ),
                ctx=ctx,
            )
            / population_size
        )
    probs = probs / mx.nd.sum(probs, -1, True)
    return mx.nd.sample_multinomial(probs, (num_samples,))


def randint(low, high, shape, device=None):
    if isinstance(low, mx.nd.NDArray):
        low = int(low.asscalar())
    if isinstance(high, mx.nd.NDArray):
        high = int(high.asscalar())
    ctx = _mxnet_init_context(default_device(device))
    if len(shape) == 0:
        return _1_dim_array_to_flat_array(
            mx.nd.random.randint(low, high, (1,), ctx=ctx)
        )
    return mx.nd.random.randint(low, high, shape, ctx=ctx)


seed = lambda seed_value=0: mx.random.seed(seed_value)
shuffle = lambda x: mx.nd.random.shuffle(x)
