"""
Collection of tests for Ivy distributed training
"""

# global
import pytest

# local
import ivy
import ivy_tests.test_ivy.helpers as helpers
from ivy_tests.test_ivy.test_stateful.test_converters import NATIVE_MODULES


class TrainableModule(ivy.Module):

    def __init__(self, in_size, out_size, dev=None, build_mode='explicit', hidden_size=64, store_vars=True):
        self._in_size = in_size
        self._out_size = out_size
        self._hidden_size = hidden_size
        ivy.Module.__init__(self, dev, build_mode=build_mode, store_vars=store_vars)

    def _build(self):
        self._linear0 = ivy.Linear(self._in_size, self._hidden_size, dev=self._dev)
        self._linear1 = ivy.Linear(self._hidden_size, self._hidden_size, dev=self._dev)
        self._linear2 = ivy.Linear(self._hidden_size, self._out_size, dev=self._dev)

    def _forward(self, x):
        x = ivy.expand_dims(x, 0)
        x = ivy.tanh(self._linear0(x))
        x = ivy.tanh(self._linear1(x))
        return ivy.tanh(self._linear2(x))[0]


class TrainableModuleWithSplit(ivy.Module):

    def __init__(self, in_size, out_size, dev=None, build_mode='explicit', hidden_size=64, store_vars=True):
        self._in_size = in_size
        self._out_size = out_size
        self._hidden_size = hidden_size
        ivy.Module.__init__(self, dev, build_mode=build_mode, store_vars=store_vars)

    def _build(self):
        self._linear0 = ivy.Linear(self._in_size, self._hidden_size, dev=self._dev)
        self._linear1 = ivy.Linear(self._hidden_size, self._hidden_size, dev=self._dev)
        self._linear2 = ivy.Linear(self._hidden_size, self._out_size, dev=self._dev)

    def _forward_unsplit(self, x):
        x = ivy.expand_dims(x, 0)
        x = ivy.tanh(self._linear0(x))
        x = ivy.tanh(self._linear1(x))
        return ivy.tanh(self._linear2(x))[0]

    def _forward(self, x):
        return ivy.split_func_call(self._forward_unsplit, [x], 'concat', x.shape[0])


def loss_fn(module, x_, v_):
    out = module(x_, v=v_)
    return ivy.reduce_mean(out)[0]


def map_fn(module, dev, xn, vc):
    return ivy.execute_with_gradients(lambda v: loss_fn(module, xn, v), vc)


# distributed training
@pytest.mark.parametrize(
    "bs_ic_oc", [([2, 1], 4, 5)])
def test_distributed_training(bs_ic_oc, dev, call):
    # smoke test
    if call is helpers.np_call:
        # NumPy does not support gradients
        pytest.skip()

    # devices and inputs
    devs = list()
    xs = dict()

    # first device
    dev0 = dev
    devs.append(dev0)

    # first input
    batch_shape, input_channels, output_channels = bs_ic_oc
    dev_batch_shape = [int(batch_shape[0]/2)] + batch_shape[1:]
    xs[dev0] = ivy.cast(ivy.linspace(ivy.zeros(dev_batch_shape), ivy.ones(dev_batch_shape),
                                         input_channels, dev=dev0), 'float32')

    # second device
    if 'gpu' in dev and ivy.num_gpus() > 1:
        idx = ivy.num_gpus() - 1
        dev1 = dev[:-1] + str(idx)
        devs.append(dev1)

        # second input
        xs[dev1] = ivy.cast(ivy.linspace(ivy.zeros(dev_batch_shape), ivy.ones(dev_batch_shape),
                                             input_channels, dev=dev1), 'float32')

    # combined inputs
    x = ivy.DevDistItem(xs)

    # module
    module = TrainableModule(input_channels, output_channels, dev=dev0)
    module.build()

    # optimizer
    optim = ivy.SGD(1e-4)

    # train
    loss_tm1 = 1e12
    loss = None
    grads = None
    for i in range(10):
        loss_n_grads = ivy.MultiDevIter(
            ivy.map(map_fn,
                    constant={'module': module, 'dev': dev0},
                    unique={'xn': x.values(), 'vc': module.v.dev_clone(devs).values()}), devs)
        loss, grads = ivy.dev_unify_iter(loss_n_grads, dev0, 'mean', transpose=True)
        module.v = optim.step(module.v, grads)
        assert loss < loss_tm1
        loss_tm1 = loss

    # type test
    assert ivy.is_array(loss)
    assert isinstance(grads, ivy.Container)
    # cardinality test
    if call is helpers.mx_call:
        # mxnet slicing cannot reduce dimension to zero
        assert loss.shape == (1,)
    else:
        assert loss.shape == ()
    # value test
    assert ivy.reduce_max(ivy.abs(grads.linear0.b)) > 0
    assert ivy.reduce_max(ivy.abs(grads.linear0.w)) > 0
    assert ivy.reduce_max(ivy.abs(grads.linear1.b)) > 0
    assert ivy.reduce_max(ivy.abs(grads.linear1.w)) > 0
    assert ivy.reduce_max(ivy.abs(grads.linear2.b)) > 0
    assert ivy.reduce_max(ivy.abs(grads.linear2.w)) > 0
    # compilation test
    if call is helpers.torch_call:
        # pytest scripting does not support **kwargs
        return
    if not ivy.array_mode():
        helpers.assert_compilable(loss_fn)


# distributed multiprocess training
@pytest.mark.parametrize(
    "bs_ic_oc", [([2, 1], 4, 5)])
def test_distributed_multiprocess_training(bs_ic_oc, dev, array_mode, call):
    if array_mode:
        # ToDo: get this test passing
        pytest.skip()
    # smoke test
    if call is helpers.np_call:
        # NumPy does not support gradients
        pytest.skip()

    if call is not helpers.torch_call:
        # ToDo: add support for other frameworks, currently only supported for torch
        pytest.skip()

    # devices and inputs
    devs = list()
    xs = dict()

    # first device
    dev0 = dev
    devs.append(dev0)

    # first input
    batch_shape, input_channels, output_channels = bs_ic_oc
    dev_batch_shape = [int(batch_shape[0]/2)] + batch_shape[1:]
    xs[dev0] = ivy.cast(ivy.linspace(ivy.zeros(dev_batch_shape), ivy.ones(dev_batch_shape),
                                         input_channels, dev=dev0), 'float32')

    # second device
    if 'gpu' in dev and ivy.num_gpus() > 1:
        idx = ivy.num_gpus() - 1
        dev1 = dev[:-1] + str(idx)
        devs.append(dev1)

        # second input
        xs[dev1] = ivy.cast(ivy.linspace(ivy.zeros(dev_batch_shape), ivy.ones(dev_batch_shape),
                                             input_channels, dev=dev1), 'float32')

    # combined inputs
    x = ivy.DevDistItem(xs)

    # module for processes
    module = TrainableModule(input_channels, output_channels, dev=dev0, store_vars=False)

    # optimizer
    optim = ivy.SGD(1e-4)

    # return fn
    ret_fn = lambda ret: ivy.dev_unify_iter(ret, dev0, 'mean', transpose=True)

    # device mapper
    orig_timeout = ivy.queue_timeout()
    ivy.set_queue_timeout(30.)
    dev_mapper = ivy.DevMapperMultiProc(map_fn, ret_fn, devs, constant={'module': module})

    # local module
    module = TrainableModule(input_channels, output_channels, dev=dev0, store_vars=True)
    module.build()

    # train
    loss_tm1 = 1e12
    loss = None
    grads = None
    for i in range(10):
        loss, grads = dev_mapper.map(xn=x, vc=module.v.dev_clone(devs))
        module.v = optim.step(module.v, grads)
        assert loss < loss_tm1
        loss_tm1 = loss
    ivy.set_queue_timeout(orig_timeout)

    # type test
    assert ivy.is_array(loss)
    assert isinstance(grads, ivy.Container)
    # cardinality test
    if call is helpers.mx_call:
        # mxnet slicing cannot reduce dimension to zero
        assert loss.shape == (1,)
    else:
        assert loss.shape == ()
    # value test
    assert ivy.reduce_max(ivy.abs(grads.linear0.b)) > 0
    assert ivy.reduce_max(ivy.abs(grads.linear0.w)) > 0
    assert ivy.reduce_max(ivy.abs(grads.linear1.b)) > 0
    assert ivy.reduce_max(ivy.abs(grads.linear1.w)) > 0
    assert ivy.reduce_max(ivy.abs(grads.linear2.b)) > 0
    assert ivy.reduce_max(ivy.abs(grads.linear2.w)) > 0
    # delete dev mapper
    dev_mapper.__del__()
    del dev_mapper
    # compilation test
    if call is helpers.torch_call:
        # pytest scripting does not support **kwargs
        return
    if not ivy.array_mode():
        helpers.assert_compilable(loss_fn)


# to_ivy_module_distributed
@pytest.mark.parametrize(
    "bs_ic_oc", [([2, 1], 4, 5)])
@pytest.mark.parametrize(
    "from_class_and_args", [True, False])
@pytest.mark.parametrize(
    "inplace_update", [True, False])
def test_to_ivy_module_distributed(bs_ic_oc, from_class_and_args, inplace_update, dev, array_mode, call):
    if array_mode:
        # ToDo: get this test passing
        pytest.skip()
    # smoke test
    if call is not helpers.torch_call:
        # Currently only implemented for PyTorch
        pytest.skip()

    # devices and inputs
    devs = list()
    xs = dict()

    # first device
    dev0 = dev
    devs.append(dev0)

    # first input
    batch_shape, input_channels, output_channels = bs_ic_oc
    dev_batch_shape = [int(batch_shape[0]/2)] + batch_shape[1:]
    xs[dev0] = ivy.cast(ivy.linspace(ivy.zeros(dev_batch_shape), ivy.ones(dev_batch_shape),
                                         input_channels, dev=dev0), 'float32')

    # second device
    if 'gpu' in dev and ivy.num_gpus() > 1:
        idx = ivy.num_gpus() - 1
        dev1 = dev[:-1] + str(idx)
        devs.append(dev1)

        # second input
        xs[dev1] = ivy.cast(ivy.linspace(ivy.zeros(dev_batch_shape), ivy.ones(dev_batch_shape),
                                             input_channels, dev=dev1), 'float32')

    # combined inputs
    x = ivy.DevDistItem(xs)

    # ivy module
    natvie_module_class = NATIVE_MODULES[ivy.current_framework_str()]
    if from_class_and_args:
        ivy_module = ivy.to_ivy_module(native_module_class=natvie_module_class,
                                       args=[input_channels, output_channels],
                                       devs=devs, inplace_update=inplace_update)
    else:
        native_module = natvie_module_class(input_channels, output_channels)
        ivy_module = ivy.to_ivy_module(native_module, devs=devs, inplace_update=inplace_update)

    # optimizer
    optim = ivy.SGD(1e-4)

    # return fn
    ret_fn = lambda ret: ivy.dev_unify_iter(ret, dev0, 'mean', transpose=True)

    # test loss_fn
    ret_val = ivy.map(loss_fn,
                      constant={'module': ivy_module},
                      unique={'x_': x.values(),
                              'v_': ivy_module.v.dev_clone(devs).values()})[0]
    assert ivy.is_array(ret_val)

    if inplace_update:
        # inplace_update mode does not support gradient propagation
        return

    # train
    loss_tm1 = 1e12
    loss = None
    grads = None
    for i in range(10):
        loss_n_grads = ivy.MultiDevIter(
            ivy.map(map_fn,
                    constant={'module': ivy_module},
                    unique={'dev': devs,
                            'xn': x.values(),
                            'vc': ivy_module.v.dev_clone(devs).values()}),
            len(devs))
        loss, grads = ret_fn(loss_n_grads)
        ivy_module.v = optim.step(ivy_module.v, grads)
        assert loss < loss_tm1
        loss_tm1 = loss

    # type test
    assert ivy.is_array(loss)
    assert isinstance(grads, ivy.Container)
    # cardinality test
    if call is helpers.mx_call:
        # mxnet slicing cannot reduce dimension to zero
        assert loss.shape == (1,)
    else:
        assert loss.shape == ()
    # value test
    assert (abs(grads).reduce_max() > 0).all_true()


# to_ivy_module_distributed
@pytest.mark.parametrize(
    "bs_ic_oc", [([2, 1], 4, 5)])
@pytest.mark.parametrize(
    "from_class_and_args", [True, False])
@pytest.mark.parametrize(
    "inplace_update", [True, False])
def test_to_ivy_module_distributed_multiprocess(bs_ic_oc, from_class_and_args, inplace_update, dev, array_mode, call):

    if array_mode:
        # ToDo: get this test passing
        pytest.skip()

    # smoke test
    if call is not helpers.torch_call:
        # Currently only implemented for PyTorch
        pytest.skip()

    # devices and inputs
    devs = list()
    xs = dict()

    # first device
    dev0 = dev
    devs.append(dev0)

    # first input
    batch_shape, input_channels, output_channels = bs_ic_oc
    dev_batch_shape = [int(batch_shape[0]/2)] + batch_shape[1:]
    xs[dev0] = ivy.cast(ivy.linspace(ivy.zeros(dev_batch_shape), ivy.ones(dev_batch_shape),
                                         input_channels, dev=dev0), 'float32')

    # second device
    if 'gpu' in dev and ivy.num_gpus() > 1:
        idx = ivy.num_gpus() - 1
        dev1 = dev[:-1] + str(idx)
        devs.append(dev1)

        # second input
        xs[dev1] = ivy.cast(ivy.linspace(ivy.zeros(dev_batch_shape), ivy.ones(dev_batch_shape),
                                             input_channels, dev=dev1), 'float32')

    # combined inputs
    x = ivy.DevDistItem(xs)

    # ivy module
    natvie_module_class = NATIVE_MODULES[ivy.current_framework_str()]
    if from_class_and_args:
        ivy_module = ivy.to_ivy_module(native_module_class=natvie_module_class,
                                       args=[input_channels, output_channels],
                                       devs=devs, inplace_update=False)
    else:
        native_module = natvie_module_class(input_channels, output_channels)
        ivy_module = ivy.to_ivy_module(native_module, devs=devs, inplace_update=False)

    # optimizer
    optim = ivy.SGD(1e-4)

    # return fn
    ret_fn = lambda ret: ivy.dev_unify_iter(ret, dev0, 'mean', transpose=True)

    # test loss_fn
    ret_val = ivy.map(loss_fn,
                      constant={'module': ivy_module},
                      unique={'x_': x.values(),
                              'v_': ivy_module.v.dev_clone(devs).values()})[0]
    assert ivy.is_array(ret_val)

    if inplace_update:
        # inplace_update mode does not support gradient propagation
        return

    # device mapper
    dev_mapper = ivy.DevMapperMultiProc(map_fn, ret_fn, devs, constant={'module': ivy_module})

    # train
    loss_tm1 = 1e12
    loss = None
    grads = None
    for i in range(10):
        loss, grads = dev_mapper.map(xn=x, vc=ivy_module.v.dev_clone(devs))
        ivy_module.v = optim.step(ivy_module.v, grads)
        assert loss < loss_tm1
        loss_tm1 = loss

    # type test
    assert ivy.is_array(loss)
    assert isinstance(grads, ivy.Container)
    # cardinality test
    if call is helpers.mx_call:
        # mxnet slicing cannot reduce dimension to zero
        assert loss.shape == (1,)
    else:
        assert loss.shape == ()
    # value test
    assert (abs(grads).reduce_max() > 0).all_true()
    # delete dev mapper
    dev_mapper.__del__()
    del dev_mapper


# device manager wrapped tuning
@pytest.mark.parametrize(
    # "bs_ic_oc", [([384, 1], 2048, 2048)])
    "bs_ic_oc", [([2, 1], 4, 5)])
@pytest.mark.parametrize(
    "tune_dev_alloc", [True, False])
@pytest.mark.parametrize(
    "tune_dev_splits", [True, False])
def test_device_manager_wrapped_tuning(bs_ic_oc, tune_dev_alloc, tune_dev_splits, dev, array_mode, call):

    if array_mode:
        # ToDo: get this test passing
        pytest.skip()

    # smoke test
    if call is helpers.np_call:
        # NumPy does not support gradients
        pytest.skip()

    if call is not helpers.torch_call:
        # ToDo: add support for other frameworks, currently only supported for torch
        pytest.skip()

    # devices
    devs = list()
    dev0 = dev
    devs.append(dev0)
    if 'gpu' in dev and ivy.num_gpus() > 1:
        idx = ivy.num_gpus() - 1
        dev1 = dev[:-1] + str(idx)
        devs.append(dev1)

    # input
    batch_shape, input_channels, output_channels = bs_ic_oc
    x = ivy.cast(ivy.linspace(ivy.zeros(batch_shape), ivy.ones(batch_shape),
                              input_channels, dev=dev0), 'float32')

    # module for processes
    module = TrainableModuleWithSplit(input_channels, output_channels,
                                      dev=dev0, store_vars=False)  # , hidden_size=2048)

    # optimizer
    optim = ivy.SGD(1e-4)

    # return fn
    ret_fn = lambda ret: ivy.dev_unify_iter(ret, dev0, 'mean', transpose=True)

    # device mapper
    dev_mapper = ivy.DevMapperMultiProc(map_fn, ret_fn, devs, constant={'module': module})

    # device manager
    dev_manager = ivy.DevManager(dev_mapper, devs, batch_shape[0], tune_dev_alloc=tune_dev_alloc,
                                 tune_dev_splits=tune_dev_splits)

    # local module
    module = TrainableModuleWithSplit(input_channels, output_channels,
                                      dev=dev0, store_vars=True)  # , hidden_size=2048)
    module.build()

    # train
    loss_tm1 = 1e12
    loss = None
    grads = None
    # for i in range(1000):
    for i in range(10):
        loss, grads = dev_manager.map(to_distribute={'xn': x}, to_clone={'vc': module.v})
        module.v = optim.step(module.v, grads)
        assert loss < loss_tm1
        loss_tm1 = loss

    # type test
    assert ivy.is_array(loss)
    assert isinstance(grads, ivy.Container)
    # cardinality test
    if call is helpers.mx_call:
        # mxnet slicing cannot reduce dimension to zero
        assert loss.shape == (1,)
    else:
        assert loss.shape == ()
    # value test
    assert ivy.reduce_max(ivy.abs(grads.linear0.b)) > 0
    assert ivy.reduce_max(ivy.abs(grads.linear0.w)) > 0
    assert ivy.reduce_max(ivy.abs(grads.linear1.b)) > 0
    assert ivy.reduce_max(ivy.abs(grads.linear1.w)) > 0
    assert ivy.reduce_max(ivy.abs(grads.linear2.b)) > 0
    assert ivy.reduce_max(ivy.abs(grads.linear2.w)) > 0
    # delete dev manager
    dev_manager.__del__()
    del dev_manager
    # compilation test
    if call is helpers.torch_call:
        # pytest scripting does not support **kwargs
        return
    if not ivy.array_mode():
        helpers.assert_compilable(loss_fn)


# device manager unwrapped tuning
@pytest.mark.parametrize(
    # "bs_ic_oc", [([384, 1], 2048, 2048)])
    "bs_ic_oc", [([2, 1], 4, 5)])
def test_device_manager_unwrapped_tuning(bs_ic_oc, dev, call):
    # smoke test
    if call is helpers.np_call:
        # NumPy does not support gradients
        pytest.skip()

    if call is not helpers.torch_call:
        # ToDo: add support for other frameworks, currently only supported for torch
        pytest.skip()

    # input
    batch_shape, input_channels, output_channels = bs_ic_oc
    x = ivy.cast(ivy.linspace(ivy.zeros(batch_shape), ivy.ones(batch_shape),
                              input_channels, dev=dev), 'float32')

    # optimizer
    optim = ivy.SGD(1e-4)

    # device manager
    dev_manager = ivy.DevManager(devs=[dev], tune_dev_alloc=False)

    # module
    module = TrainableModuleWithSplit(input_channels, output_channels,
                                      dev=dev, store_vars=True)  # , hidden_size=2048)
    module.build()

    # train
    loss_tm1 = 1e12
    loss = None
    grads = None
    # for i in range(1000):
    for i in range(10):
        loss, grads = map_fn(module, dev, x, module.v)
        dev_manager.tune_step()
        module.v = optim.step(module.v, grads)
        assert loss < loss_tm1
        loss_tm1 = loss

    # type test
    assert ivy.is_array(loss)
    assert isinstance(grads, ivy.Container)
    # cardinality test
    if call is helpers.mx_call:
        # mxnet slicing cannot reduce dimension to zero
        assert loss.shape == (1,)
    else:
        assert loss.shape == ()
    # value test
    assert ivy.reduce_max(ivy.abs(grads.linear0.b)) > 0
    assert ivy.reduce_max(ivy.abs(grads.linear0.w)) > 0
    assert ivy.reduce_max(ivy.abs(grads.linear1.b)) > 0
    assert ivy.reduce_max(ivy.abs(grads.linear1.w)) > 0
    assert ivy.reduce_max(ivy.abs(grads.linear2.b)) > 0
    assert ivy.reduce_max(ivy.abs(grads.linear2.w)) > 0
    # delete dev manager
    dev_manager.__del__()
    del dev_manager
    # compilation test
    if call is helpers.torch_call:
        # pytest scripting does not support **kwargs
        return
    if not ivy.array_mode():
        helpers.assert_compilable(loss_fn)
