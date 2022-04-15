# global
import numpy as np
import pytest

# local
import ivy
import ivy_tests.test_ivy.helpers as helpers

# unique_values
@pytest.mark.parametrize(
    "arr_uniqarr", [([1., 1., 2., 2., 3., 4., 5.], [1., 2., 3., 4., 5.])])
@pytest.mark.parametrize(
    "dtype", ['float32'])
@pytest.mark.parametrize(
    "tensor_fn", [ivy.array, helpers.var_fn])
@pytest.mark.parametrize(
    "with_out", [False, True])
def test_unique_values(arr_uniqarr, dtype, tensor_fn, with_out, dev):

    if dtype in ivy.invalid_dtype_strs:
        pytest.skip("invalid dtype")

    arr, gt = arr_uniqarr
    arr = tensor_fn(arr, dtype, dev)
    gt = tensor_fn(gt, dtype, dev)
    
    # create dummy out so that it is broadcastable to gt
    out = ivy.zeros(ivy.shape(gt)) if with_out else None

    # do the operation
    res = ivy.unique_values(arr, out=out)

    assert np.allclose(ivy.to_numpy(res), ivy.to_numpy(gt))

    if with_out:
        # match the values of res and out
        assert np.allclose(ivy.to_numpy(res), ivy.to_numpy(out))

        if ivy.current_framework_str() in ["tensorflow", "jax"]:
            # these frameworks do not support native inplace updates
            return

        # native arrays should be the same object
        assert res.data is out.data