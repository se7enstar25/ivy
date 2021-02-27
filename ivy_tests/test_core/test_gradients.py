"""
Collection of tests for templated gradient functions
"""

# global
import numpy as np

# local
import ivy
import ivy_tests.helpers as helpers
from ivy.core.container import Container


def test_variable():
    for lib, call in helpers.calls():
        if call is helpers.tf_graph_call:
            # cannot create variables as part of compiled tf graph
            continue
        call(ivy.variable, ivy.array([0.], f=lib))
        call(ivy.variable, ivy.array([0.], 'float32', f=lib))
        call(ivy.variable, ivy.array([[0.]], f=lib))
        if call in [helpers.torch_call]:
            # pytorch scripting does not support attribute setting
            continue
        helpers.assert_compilable('variable', lib)


def test_execute_with_gradients():
    for lib, call in helpers.calls():
        if call is helpers.mx_graph_call:
            # mxnet symbolic does not support ivy gradient functions
            continue

        # func with single return val
        func = lambda xs_in: (xs_in['w'] * xs_in['w'])[0]
        xs = Container({'w': ivy.variable(ivy.array([3.], f=lib))})
        y, dydxs = call(ivy.execute_with_gradients, func, xs, f=lib)
        assert np.allclose(y, np.array(9.))
        if call is helpers.np_call:
            # numpy doesn't support autodiff
            assert dydxs is None
        else:
            assert np.allclose(lib.to_numpy(dydxs['w']), np.array([6.]))

        # func with multi return vals
        func = lambda xs_in: ((xs_in['w'] * xs_in['w'])[0], xs_in['w'] * 1.5)
        xs = Container({'w': ivy.variable(ivy.array([3.], f=lib))})
        y, dydxs, extra_out = call(ivy.execute_with_gradients, func, xs, f=lib)
        assert np.allclose(y, np.array(9.))
        assert np.allclose(extra_out, np.array([4.5]))
        if call is helpers.np_call:
            # numpy doesn't support autodiff
            assert dydxs is None
        else:
            assert np.allclose(lib.to_numpy(dydxs['w']), np.array([6.]))

        # func with multi weights vals
        func = lambda xs_in: (xs_in['w1'] * xs_in['w2'])[0]
        xs = Container({'w1': ivy.variable(ivy.array([3.], f=lib)),
                        'w2': ivy.variable(ivy.array([5.], f=lib))})
        y, dydxs = call(ivy.execute_with_gradients, func, xs, f=lib)
        assert np.allclose(y, np.array(15.))
        if call is helpers.np_call:
            # numpy doesn't support autodiff
            assert dydxs is None
        else:
            assert np.allclose(lib.to_numpy(dydxs['w1']), np.array([5.]))
            assert np.allclose(lib.to_numpy(dydxs['w2']), np.array([3.]))

        # compile
        if call in [helpers.torch_call]:
            # pytorch scripting does not support internal function definitions
            continue
        helpers.assert_compilable('execute_with_gradients', lib)



def test_gradient_descent_update():
    for lib, call in helpers.calls():
        if call is helpers.mx_graph_call:
            # mxnet symbolic does not support ivy gradient functions
            continue
        ws = Container({'w': ivy.variable(ivy.array([3.], f=lib))})
        dcdws = Container({'w': ivy.array([6.], f=lib)})
        w_new = ivy.array(ivy.gradient_descent_update(ws, dcdws, 0.1, f=lib)['w'], f=lib)
        assert np.allclose(ivy.to_numpy(w_new), np.array([2.4]))
        if call in [helpers.torch_call]:
            # pytorch scripting does not support internal function definitions
            continue
        helpers.assert_compilable('gradient_descent_update', lib)


def test_adam_update():
    for lib, call in helpers.calls():
        if call is helpers.mx_graph_call:
            # mxnet symbolic does not support ivy gradient functions
            continue
        ws = Container({'w': ivy.variable(ivy.array([3.], f=lib))})
        dcdws = Container({'w': ivy.array([6.], f=lib)})
        mw = dcdws
        vw = dcdws.map(lambda x, _: x ** 2)
        w_new = ivy.array(ivy.adam_update(ws, dcdws, 0.1, mw, vw, lib.array(1), f=lib)[0]['w'], f=lib)
        assert np.allclose(ivy.to_numpy(w_new), np.array([2.96837726]))
        if call in [helpers.torch_call]:
            # pytorch scripting does not support internal function definitions
            continue
        helpers.assert_compilable('adam_update', lib)


def test_stop_gradient():
    for lib, call in helpers.calls():
        x_init = ivy.array([0.], f=lib)
        x_init_np = call(lambda x: x, x_init)
        x_new = call(ivy.stop_gradient, x_init, f=lib)
        assert np.array_equal(x_init_np, x_new)
        if call in [helpers.torch_call]:
            # pytorch scripting does not support attribute setting
            continue
        helpers.assert_compilable('stop_gradient', lib)
