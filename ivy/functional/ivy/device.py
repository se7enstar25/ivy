"""
Collection of device Ivy functions.
"""

# global
import os
import gc
import abc
import math
import time
import queue
import psutil
import inspect
import logging
import nvidia_smi

from typing import Optional

# noinspection PyUnresolvedReferences
try:
    nvidia_smi.nvmlInit()
except nvidia_smi.NVMLError_LibraryNotFound:
    pass
from typing import Union, Type, Callable, Iterable, Dict, Any

# local
import ivy
from ivy.framework_handler import current_framework as _cur_framework

default_device_stack = list()
dev_handles = dict()
split_factors = dict()
max_chunk_sizes = dict()


# Extra #
# ------#

class DefaultDevice:
    # noinspection PyShadowingNames
    def __init__(self, dev):
        self._dev = dev

    def __enter__(self):
        set_default_device(self._dev)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        unset_default_device()
        return self

# Helpers #

# noinspection PyShadowingNames
def _get_nvml_gpu_handle(dev):
    global dev_handles
    if dev in dev_handles:
        return dev_handles[dev]
    gpu_idx = int(dev.split(':')[-1])
    handle = nvidia_smi.nvmlDeviceGetHandleByIndex(gpu_idx)
    dev_handles[dev] = handle
    return handle


# Device Queries #

# Array Printing

# noinspection PyShadowingNames
def get_all_arrays_on_dev(dev):
    """
    Gets all arrays which are currently alive on the specified device.
    """
    all_arrays = list()
    for obj in gc.get_objects():
        # noinspection PyBroadException
        try:
            if ivy.is_native_array(obj) and ivy.dev(obj) == dev:
                all_arrays.append(obj)
        except Exception:
            pass
    return ivy.Container(dict(zip([str(id(a)) for a in all_arrays], all_arrays)))


# noinspection PyShadowingNames
def num_arrays_on_dev(dev):
    """
    Returns the number of arrays which are currently alive on the specified device.
    """
    return len(get_all_arrays_on_dev(dev))


# noinspection PyShadowingNames
def print_all_arrays_on_dev(dev):
    """
    Prints all arrays which are currently alive on the specified device.
    """
    for arr in get_all_arrays_on_dev(dev):
        print(type(arr), arr.shape)


# Retreival

def dev(x: Union[ivy.Array, ivy.NativeArray], as_str: bool = False)\
        -> Union[ivy.Device, str]:
    """
    Get the native device handle for input array x.

    :param x: Tensor for which to get the device handle.
    :type x: array
    :param as_str: Whether or not to return the dev in string format. Default is False.
    :type as_str: bool, optional
    :return: Device handle for the array, in native framework format.
    """
    return _cur_framework(x).dev(x, as_str)


# Conversions

# noinspection PyShadowingNames
def dev_to_str(dev: Union[ivy.Device, str]) \
        -> str:
    """
    Convert native data type to string representation.

    :param dev: The device handle to convert to string.
    :type dev: device handle
    :return: Device string e.g. 'cuda:0'.
    """
    return _cur_framework().dev_to_str(dev)


# noinspection PyShadowingNames
def dev_from_str(dev: Union[ivy.Device, str]) \
        -> ivy.Device:
    """
    Convert device string representation to native device type.

    :param dev: The device string to conver to native device handle.
    :type dev: Device
    :return: Native device handle.
    """
    return _cur_framework().dev_from_str(dev)


# Memory

# noinspection PyShadowingNames
def clear_mem_on_dev(dev: ivy.Device)\
        -> None:
    """
    Clear memory cache on target device.

    :param dev: The device string to conver to native device handle.
    :type dev: Device
    """
    return _cur_framework(None).clear_mem_on_dev(dev)


# noinspection PyShadowingNames
def total_mem_on_dev(dev: ivy.Device)\
        -> float:
    """
    Get the total amount of memory (in GB) for a given device string. In case of CPU, the total RAM is returned.

    :param dev: The device string to conver to native device handle.
    :type dev: Device
    :return: The total memory on the device in GB.
    """
    if 'gpu' in dev:
        handle = _get_nvml_gpu_handle(dev)
        info = nvidia_smi.nvmlDeviceGetMemoryInfo(handle)
        return info.total/1e9
    elif dev == 'cpu':
        return psutil.virtual_memory().total/1e9
    else:
        raise Exception('Invalid device string input, must be on the form "gpu:idx" or "cpu", '
                        'but found {}'.format(dev))


# noinspection PyShadowingNames
def used_mem_on_dev(dev: ivy.Device, process_specific=False)\
        -> float:
    """
    Get the used memory (in GB) for a given device string. In case of CPU, the used RAM is returned.

    :param dev: The device string to conver to native device handle.
    :type dev: Device
    :param process_specific: Whether the check the memory used by this python process alone. Default is False.
    :type process_specific: bool, optional
    :return: The used memory on the device in GB.
    """
    ivy.clear_mem_on_dev(dev)
    if 'gpu' in dev:
        if process_specific:
            raise Exception('process-specific GPU queries are currently not supported')
        handle = _get_nvml_gpu_handle(dev)
        info = nvidia_smi.nvmlDeviceGetMemoryInfo(handle)
        return info.used/1e9
    elif dev == 'cpu':
        if process_specific:
            return psutil.Process(os.getpid()).memory_info().rss
        vm = psutil.virtual_memory()
        return (vm.total - vm.available)/1e9
    else:
        raise Exception('Invalid device string input, must be on the form "gpu:idx" or "cpu", '
                        'but found {}'.format(dev))


# noinspection PyShadowingNames
def percent_used_mem_on_dev(dev: ivy.Device, process_specific=False)\
        -> float:
    """
    Get the percentage used memory for a given device string. In case of CPU, the used RAM is returned.

    :param dev: The device string to conver to native device handle.
    :type dev: Device
    :param process_specific: Whether the check the memory used by this python process alone. Default is False.
    :type process_specific: bool, optional
    :return: The percentage used memory on the device.
    """
    ivy.clear_mem_on_dev(dev)
    if 'gpu' in dev:
        if process_specific:
            raise Exception('process-specific GPU queries are currently not supported')
        handle = _get_nvml_gpu_handle(dev)
        info = nvidia_smi.nvmlDeviceGetMemoryInfo(handle)
        return (info.used/info.total)*100
    elif dev == 'cpu':
        vm = psutil.virtual_memory()
        if process_specific:
            return (psutil.Process(os.getpid()).memory_info().rss/vm.total)*100
        return (1-(vm.available/vm.total))*100
    else:
        raise Exception('Invalid device string input, must be on the form "gpu:idx" or "cpu", '
                        'but found {}'.format(dev))


# Utilization

# noinspection PyShadowingNames
def dev_util(dev: ivy.Device)\
        -> float:
    """
    Get the current utilization (%) for a given device.

    :param dev: The device string of the device to query utilization for.
    :type dev: Device
    :return: The device utilization (%)
    """
    if dev == 'cpu':
        return psutil.cpu_percent()
    elif 'gpu' in dev:
        handle = _get_nvml_gpu_handle(dev)
        return nvidia_smi.nvmlDeviceGetUtilizationRates(handle).gpu
    else:
        raise Exception('Invalid device string input, must be on the form "gpu:idx" or "cpu", '
                        'but found {}'.format(dev))


# Availability

def gpu_is_available() -> bool:
    """
    Determine whether a GPU is available to use, with the backend framework.

    :return: Boolean, as to whether a gpu is available.
    """
    return _cur_framework().gpu_is_available()


def num_cpu_cores() -> int:
    """
    Determine the number of cores available in the cpu.
    """
    return psutil.cpu_count()


def num_gpus() -> int:
    """
    Determine the number of available GPUs, with the backend framework.

    :return: Number of available GPUs.
    """
    return _cur_framework().num_gpus()


def tpu_is_available() -> bool:
    """
    Determine whether a TPU is available to use, with the backend framework.

    :return: Boolean, as to whether a tpu is available.
    """
    return _cur_framework().tpu_is_available()


# Default Device #

# noinspection PyShadowingNames
def _assert_dev_correct_formatting(dev):
    assert dev[0:3] in ['gpu', 'tpu', 'cpu']
    if dev != 'cpu':
        assert dev[3] == ':'
        assert dev[4:].isnumeric()


# noinspection PyShadowingNames
def default_device(dev=None):
    """
    Return the input dev if provided, otherwise return the global default device.
    """
    if ivy.exists(dev):
        _assert_dev_correct_formatting(ivy.dev_to_str(dev))
        return dev
    global default_device_stack
    if not default_device_stack:
        ret = 'gpu:0' if ivy.gpu_is_available() else 'cpu'
    else:
        ret = default_device_stack[-1]
    return ivy.dev_from_str(ret)


# noinspection PyShadowingNames
def set_default_device(dev):
    _assert_dev_correct_formatting(dev)
    global default_device_stack
    default_device_stack.append(dev)


def unset_default_device():
    global default_device_stack
    if default_device_stack:
        default_device_stack.pop(-1)


# Device Allocation #

# noinspection PyShadowingNames
def to_dev(x: Union[ivy.Array, ivy.NativeArray], dev: ivy.Device = None, \
           out: Optional[Union[ivy.Array, ivy.NativeArray]] = None) \
        -> Union[ivy.Array, ivy.NativeArray]:
    """
    Move the input array x to the desired device, specified by device string.

    Parameters
    ----------
    x:
       input array to be moved to the desired device
    dev:
        device to move the input array `x` to
    out:
        optional output array, for writing the result to. It must have a shape that the inputs broadcast to.

    Returns
    -------
    x:
        input array x placed on the desired device

    Examples
    -------
    >>> x = ivy.array([1., 2., 3.])
    >>> x = ivy.to_dev(x, dev)
    """
    return _cur_framework(x).to_dev(x, dev, out)


# Function Splitting #

# noinspection PyShadowingNames
def split_factor(dev=None):
    """
    Get the global split factor for a given device, which can be used to scale batch splitting chunk sizes for the
    device across the codebase. Default global value for each device is 1.

    :param dev: The device to query the split factor for. Sets the default device by default.
    :type dev: Device, optional
    :return: The split factor for the specified device.
    """
    global split_factors
    dev = ivy.default(dev, default_device())
    if dev in split_factors:
        return split_factors[dev]
    split_factors[dev] = 0.
    return split_factors[dev]


# noinspection PyShadowingNames
def set_split_factor(factor, dev=None):
    """
    Set the global split factor for a given device, which can be used to scale batch splitting chunk sizes for the
    device across the codebase.

    :param factor: The factor to set the device-specific split factor to.
    :type factor: float
    :param dev: The device to set the split factor for. Sets the default device by default.
    :type dev: Device, optional
    """
    assert 0 <= factor
    global split_factors
    dev = ivy.default(dev, default_device())
    split_factors[dev] = factor


# noinspection PyShadowingNames
def split_func_call(func: Callable, inputs: Iterable[Union[Union[ivy.Array, ivy.NativeArray], ivy.Container]],
                    mode: str, max_chunk_size: int = None, chunk_size: int = None,
                    input_axes: Union[int, Iterable[int]] = 0, output_axes: Union[int, Iterable[int]] = None,
                    stop_gradients: bool = False, dev=None)\
        -> Iterable[Union[Union[ivy.Array, ivy.NativeArray], ivy.Container]]:
    """
    Call a function by splitting its inputs along a given axis, and calling the function in chunks, rather than feeding
    the entire input array at once. This can be useful to reduce memory usage of the device the arrays are on.
    :param func: The function to be called.
    :type func: callable
    :param inputs: A list of inputs to pass into the function.
    :type inputs: sequence of arrays
    :param mode: The mode by which to unify the return values, must be one of [ concat | mean | sum ]
    :type mode: str
    :param max_chunk_size: The maximum size of each of the chunks to be fed into the function.
    :type max_chunk_size: int
    :param chunk_size: The size of each of the chunks to be fed into the function. Specifying this arg overwrites the
                       global split factor. Default is None.
    :type chunk_size: int, optional
    :param input_axes: The axes along which to split each of the inputs, before passing to the function. Default is 0.
    :type input_axes: int or sequence of ints, optional
    :param output_axes: The axes along which to concat each of the returned outputs. Default is same as fist input axis.
    :type output_axes: int or sequence of ints, optional
    :param stop_gradients: Whether to stop the gradients for each computed return. Default is False.
    :type stop_gradients: bool, optional
    :param dev: The device to set the split factor for. Sets the default device by default.
    :type dev: Device, optional
    :return: The return from the function, following input splitting and re-concattenation.
    """
    if isinstance(input_axes, int):
        input_axes = [input_axes]*len(inputs)
    if not ivy.exists(max_chunk_size) and not ivy.exists(chunk_size):
        shape_key = '_'.join([str(inp.shape) for inp in inputs])
        if shape_key in max_chunk_sizes:
            max_chunk_size = max_chunk_sizes[shape_key]
        else:
            max_chunk_size = 0
        max_dim = max([inp.shape[inp_ax] for inp, inp_ax in zip(inputs, input_axes)])
        if max_dim > max_chunk_size:
            max_chunk_sizes[shape_key] = max_dim
            max_chunk_size = max_dim
    chunk_size = ivy.default(
        chunk_size, lambda: 1 + int(round((max_chunk_size-1) * ivy.split_factor(ivy.default_device(dev)))), True)
    dim_size = inputs[0].shape[input_axes[0]]
    if chunk_size >= dim_size:
        return func(*inputs)
    num_chunks = dim_size / chunk_size
    num_chunks_floored = math.floor(num_chunks)
    num_chunks_ceiled = math.ceil(num_chunks)
    chunk_sizes = [chunk_size] * num_chunks_floored
    if num_chunks != num_chunks_floored:
        chunk_sizes.append(dim_size - chunk_size * num_chunks_floored)
    inputs_split = [ivy.split(inp, chunk_sizes, input_axes[i], True) if ivy.is_native_array(inp)
                    else inp.split(chunk_sizes, input_axes[i], True) for i, inp in enumerate(inputs)]
    is_mean = mode == 'mean'
    is_sum = mode == 'sum'
    post_fn = ivy.stop_gradient if stop_gradients else lambda x: x
    if is_mean or is_sum:
        sums = None
        for inps in zip(*inputs_split):
            if not sums:
                sums = func(*inps)
                sums = [post_fn(s) for s in sums] if isinstance(sums, tuple) else [post_fn(sums)]
            else:
                ret = func(*inps)
                if isinstance(ret, tuple):
                    for i, r in enumerate(ret):
                        sums[i] = sums[i] + post_fn(r)
                else:
                    sums[0] = sums[0] + post_fn(ret)
        sums_or_means = [s/num_chunks_ceiled for s in sums] if is_mean else sums
        return sums_or_means[0] if len(sums_or_means) == 1 else tuple(sums_or_means)
    rets = [func(*i) for i in zip(*inputs_split)]
    rets = [tuple([post_fn(r) for r in ret]) if isinstance(ret, tuple) else (post_fn(ret),) for ret in rets]
    num_outputs = len(rets[0])
    if output_axes is None:
        output_axes = [input_axes[0]] * num_outputs
    elif isinstance(output_axes, int):
        output_axes = [output_axes] * num_outputs
    ret = [ivy.concat([r[i] for r in rets], output_axes[i]) if ivy.is_native_array(rets[0][i])
           else ivy.Container.concat([r[i] for r in rets], output_axes[i]) for i in range(num_outputs)]
    return ret[0] if len(ret) == 1 else ret


# Multi-Device #

class MultiDev:

    def __init__(self, data: Iterable, axis=0):
        if isinstance(data, MultiDev):
            # noinspection PyUnresolvedReferences,PyProtectedMember
            data = data._dict
        self._axis = axis
        self._data = data
        self._length = len(data)
        self._counter = 0

    def __len__(self):
        return self._length

    def __repr__(self):
        return 'MultiDev(' + self._data.__repr__() + ')'


class MultiDevItem(MultiDev):

    def __init__(self, data: Dict[ivy.Device, Any], axis=0):
        super().__init__(data, axis)

    @property
    def shape(self):
        shapes = [list(x.shape) if hasattr(x, 'shape') else None for x in self._data.values()]
        if not shapes or None in shapes:
            return None
        shape0 = shapes[0]
        for shp in shapes[1:]:
            assert shp == shape0
        shape0[self._axis] = shape0[self._axis]*len(self)
        return tuple(shape0)

    def _slice(self, slice_obj: slice):
        stacked_dim_size = 0
        ret_dict = dict()
        for ds, sub_item in self._data.items():
            if not hasattr(sub_item, 'shape'):
                continue
            shp = sub_item.shape
            rel_slice_obj = slice(slice_obj.start-stacked_dim_size, slice_obj.stop-stacked_dim_size, 1)
            stacked_dim_size += shp[self._axis]
            if slice_obj.start < stacked_dim_size:
                if slice_obj.stop < stacked_dim_size:
                    ret_dict[ds] = sub_item[rel_slice_obj]
                    return MultiDevItem(ret_dict)
                else:
                    ret_dict[ds] = sub_item[rel_slice_obj.start:]
        return MultiDevItem(ret_dict)

    def __getitem__(self, query):
        if isinstance(query, str):
            return self._data[query]
        elif isinstance(query, int):
            return self._slice(slice(query, query+1, 1))
        elif isinstance(query, slice):
            return self._slice(query)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def __repr__(self):
        return 'MultiDevItem(' + self._data.__repr__() + ')'


class MultiDevIter(MultiDev):

    def __init__(self, data: Iterable, devs):
        self._devs = devs
        super().__init__(data)

    # noinspection PyShadowingNames
    def at_dev(self, dev):
        return [x[dev] if isinstance(x, MultiDevItem) else x for x in self._data]

    def at_devs(self):
        return {ds: self.at_dev(ds) for ds in self._devs}

    def __getitem__(self, item):
        return self._data[item]

    def __iter__(self):
        self._counter = 0
        return self

    def __next__(self):
        if self._counter == self._length:
            raise StopIteration
        ret = self.__getitem__(self._counter)
        self._counter += 1
        return ret

    def __repr__(self):
        return 'MultiDevIter(' + self._data.__repr__() + ')'


class MultiDevNest(MultiDevIter):

    def __init__(self, data: Iterable, devs, max_depth=1):
        self._max_depth = max_depth
        super().__init__(data, devs)

    # noinspection PyShadowingNames
    def at_dev(self, dev):
        return ivy.nested_map(self._data, lambda x: x[dev] if isinstance(x, MultiDevItem) else x,
                              max_depth=self._max_depth)

    def __repr__(self):
        return 'MultiDevNest(' + self._data.__repr__() + ')'


# Device Distribution #

class DevDistItem(MultiDevItem):

    def __repr__(self):
        return 'DevDistItem(' + self._data.__repr__() + ')'


class DevDistIter(MultiDevIter):

    def __repr__(self):
        return 'DevDistIter(' + self._data.__repr__() + ')'


class DevDistNest(MultiDevNest):

    def __repr__(self):
        return 'DevDistNest(' + self._data.__repr__() + ')'


def dev_dist_array(x, devs: Union[Iterable[str], Dict[str, int]], axis=0):
    """
    Distribute an array across the specified devices, returning a list of sub-arrays, each on a different device.

    :param x: The array to distribute across devices.
    :type x: array
    :param devs: The devices to distribute the array across.
    :type devs: sequence of strs or dict of split sizes
    :param axis: The axis along which to split the array. Default is 0.
    :type axis: int, optional
    :return: array distributed across the target devices
    """
    split_arg = list(devs.values()) if isinstance(devs, dict) else len(devs)
    return DevDistItem(
        {ds: ivy.to_dev(x_sub, ds) for x_sub, ds in zip(ivy.split(x, split_arg, axis, with_remainder=True), devs)})


def dev_dist(x, devs: Union[Iterable[str], Dict[str, int]], axis=0):
    """
    Distribute the input item across the specified devices, returning a list of sub-items, each on a different device.

    :param x: The input array or container to distribute across devices.
    :type x: array or container
    :param devs: The devices to distribute the input across.
    :type devs: sequence of strs or dict of split sizes
    :param axis: The axis along which to split the input. Default is 0.
    :type axis: int, optional
    :return: array or container distributed across the target devices
    """
    if ivy.is_native_array(x):
        return dev_dist_array(x, devs, axis)
    elif isinstance(x, ivy.Container):
        return x.dev_dist(devs, axis)
    return x


def dev_dist_iter(xs, devs: Union[Iterable[str], Dict[str, int]], axis=0):
    """
    Distribute elements of the iterbale xs across the specified devices.

    :param xs: The iterable of items to distribute.
    :type xs: iterable of any
    :param devs: The devices to distribute the iterable elements across.
    :type devs: sequence of strs or dict of split sizes
    :param axis: The axis along which to split the arrays in the iterable xs. Default is 0.
    :type axis: int, optional
    :return: iterable with each element distributed to the target devices
    """
    if isinstance(devs, str):
        devs = [devs]
    return DevDistIter([dev_dist(x, devs, axis) for x in xs], devs)


def dev_dist_nest(args, kwargs, devs: Union[Iterable[str], Dict[str, int]], axis=0, max_depth=1):
    """
    Distribute the nested input arguments across the specified devices.

    :param args: The positional nested arguments to distribute.
    :type args: list of any
    :param kwargs: The keyword nested arguments to distribute.
    :type kwargs: dict of any
    :param devs: The devices to distribute the nested arguments across.
    :type devs: sequence of strs or dict of split sizes
    :param axis: The axis along which to split the arrays in the arguments. Default is 0.
    :type axis: int, optional
    :param max_depth: The maximum nested depth to reach. Default is 1. Increase this if the nest is deeper.
    :type max_depth: int, optional
    :return: nested arguments distributed to the target devices
    """
    if isinstance(devs, str):
        devs = [devs]
    args_dist = ivy.nested_map(args, lambda x: dev_dist(x, devs, axis), max_depth=max_depth)
    kwargs_dist = ivy.nested_map(kwargs, lambda x: dev_dist(x, devs, axis), max_depth=max_depth)
    return DevDistNest(args_dist, devs), DevDistNest(kwargs_dist, devs)


# Device Cloning #

class DevClonedItem(MultiDevItem):

    def __repr__(self):
        return 'DevClonedItem(' + self._data.__repr__() + ')'


class DevClonedIter(MultiDevIter):

    def __repr__(self):
        return 'DevClonedIter(' + self._data.__repr__() + ')'


class DevClonedNest(MultiDevNest):

    def __repr__(self):
        return 'DevClonedNest(' + self._data.__repr__() + ')'


def dev_clone_array(x, devs):
    """
    Clone an array across the specified devices, returning a list of cloned arrays, each on a different device.

    :param x: The array to clone across devices.
    :type x: array
    :param devs: The devices to clone the array to.
    :type devs: sequence of strs
    :return: array cloned to each of the target devices
    """
    return DevClonedItem({ds: ivy.stop_gradient(ivy.to_dev(x, ds)) for ds in devs})


def dev_clone(x, devs):
    """
    Clone the input item to each of the specified devices, returning a list of cloned items, each on a different device.

    :param x: The input array or container to clone to each device.
    :type x: array or container
    :param devs: The devices to clone the input to.
    :type devs: sequence of strs
    :return: array or container distributed across the target devices
    """
    if ivy.is_native_array(x):
        return dev_clone_array(x, devs)
    elif isinstance(x, ivy.Container):
        return x.dev_clone(devs)
    return x


def dev_clone_iter(xs, devs):
    """
    Clone elements of the iterbale xs to each of the specified devices.

    :param xs: The iterable of items to clone.
    :type xs: iterable of any
    :param devs: The devices to clone each of the iterable elements to.
    :type devs: sequence of strs
    :return: iterable with each element cloned to each of the target devices
    """
    if isinstance(devs, str):
        devs = [devs]
    return DevClonedIter([dev_clone(x, devs) for x in xs], devs)


def dev_clone_nest(args, kwargs, devs, max_depth=1):
    """
    Clone the input arguments across the specified devices.

    :param args: The positional arguments to clone.
    :type args: list of any
    :param kwargs: The keyword arguments to clone.
    :type kwargs: dict of any
    :param devs: The devices to clone the arguments to.
    :type devs: sequence of strs
    :param max_depth: The maximum nested depth to reach. Default is 1. Increase this if the nest is deeper.
    :type max_depth: int, optional
    :return: arguments cloned to each of the target devices
    """
    if isinstance(devs, str):
        devs = [devs]
    args_cloned = ivy.nested_map(args, lambda x: dev_clone(x, devs), max_depth=max_depth)
    kwargs_cloned = ivy.nested_map(kwargs, lambda x: dev_clone(x, devs), max_depth=max_depth)
    return DevClonedNest(args_cloned, devs), DevClonedNest(kwargs_cloned, devs)


# Device Unification #

# noinspection PyShadowingNames
def _concat_unify_array(xs, dev, axis):
    return ivy.concat([ivy.to_dev(x_sub, dev) for x_sub in xs.values()], axis)


# noinspection PyShadowingNames
def _sum_unify_array(xs, dev, _=None):
    return sum([ivy.to_dev(x_sub, dev) for x_sub in xs.values()])


# noinspection PyShadowingNames
def _mean_unify_array(xs, dev, _=None):
    return _sum_unify_array(xs, dev) / len(xs)


# noinspection PyShadowingNames
def dev_unify_array(xs, dev, mode, axis=0):
    """
    Unify a list of sub-arrays, on arbitrary devices, to a single array on the specified device.

    :param xs: The list of arrays to unify onto the specified device.
    :type xs: sequence of arrays
    :param dev: The device to unify the arrays to.
    :type dev: Device
    :param mode: The mode by which to unify, must be one of [ concat | mean | sum ]
    :type mode: str
    :param axis: The axis along which to concattenate the array, if concat mode is set. Default is 0.
    :type axis: int, optional
    :return: array unified to the target device
    """
    return {'concat': _concat_unify_array,
            'sum': _sum_unify_array,
            'mean': _mean_unify_array}[mode](xs, dev, axis)


# noinspection PyShadowingNames
def dev_unify(xs, dev, mode, axis=0):
    """
    Unify a list of sub-arrays, on arbitrary devices, to a single concattenated array on the specified device.

    :param xs: The list of sub-arrays to unify onto the specified device.
    :type xs: sequence of arrays
    :param dev: The device to unify the sub-arrays to.
    :type dev: Device
    :param mode: The mode by which to unify, must be one of [ concat | mean | sum ]
    :type mode: str
    :param axis: The axis along which to concattenate the array, if concat mode is set. Default is 0.
    :type axis: int, optional
    :return: array unified to the target device
    """
    if isinstance(xs, ivy.MultiDevContainer):
        xs = MultiDevItem(xs.at_devs())
    elif not isinstance(xs, MultiDevItem):
        return xs
    # noinspection PyProtectedMember
    xs0 = next(iter(xs.items()))[1]
    if ivy.is_native_array(xs0):
        return dev_unify_array(xs, dev, mode, axis)
    elif isinstance(xs0, ivy.Container):
        return ivy.Container.unify(xs, dev, mode, axis)
    return xs


# noinspection PyShadowingNames
def dev_unify_iter(xs, dev, mode, axis=0, transpose=False):
    """
    Unify elements of the iterbale xs to a single target device.

    :param xs: The iterable of items to unify.
    :type xs: iterable of any
    :param dev: The device to unify the elements of the iterable to.
    :type dev: Device
    :param mode: The mode by which to unify, must be one of [ concat | mean | sum ]
    :type mode: str
    :param axis: The axis along which to concattenate the sub-arrays. Default is 0.
    :type axis: int, optional
    :param transpose: Whether to transpose the first and second dimensions of the iterator. Default is False.
    :type transpose: bool, optional
    :return: iterable with each element unified to a single target devices
    """
    # noinspection PyProtectedMember
    xs = xs._data if isinstance(xs, MultiDevIter) else xs
    if transpose:
        # ToDo: make this more elegant, this method should not be responsible for transposing iterators
        xs_t = [MultiDevItem({ivy.dev(i) if ivy.is_native_array(i) else i.dev: i
                              for i in mdi}) for mdi in list(map(list, zip(*xs)))]
        return [dev_unify(x, dev, mode, axis) for x in xs_t]
    return dev_unify(xs, dev, mode, axis)


# noinspection PyShadowingNames,PyProtectedMember
def dev_unify_nest(args: Type[MultiDev], kwargs: Type[MultiDev], dev, mode, axis=0, max_depth=1):
    """
    Unify the input nested arguments, which consist of sub-arrays spread across arbitrary devices, to unified arrays
    on the single target device.

    :param args: The nested positional arguments to unify.
    :type args: MultiDev
    :param kwargs: The nested keyword arguments to unify.
    :type kwargs: MultiDev
    :param dev: The device to unify the nested arguments to.
    :type dev: Device
    :param mode: The mode by which to unify, must be one of [ concat | mean | sum ]
    :type mode: str
    :param axis: The axis along which to concattenate the sub-arrays. Default is 0.
    :type axis: int, optional
    :param max_depth: The maximum nested depth to reach. Default is 1. Increase this if the nest is deeper.
    :type max_depth: int, optional
    :return: nested arguments unified to the target device
    """
    args = args._data if isinstance(args, MultiDevIter) else args
    kwargs = kwargs._data if isinstance(kwargs, MultiDevIter) else kwargs
    args_uni = ivy.nested_map(args, lambda x: dev_unify(x, dev, mode, axis), max_depth=max_depth)
    kwargs_uni = ivy.nested_map(kwargs, lambda x: dev_unify(x, dev, mode, axis), max_depth=max_depth)
    return args_uni, kwargs_uni


# Device Mappers #

class DevMapper(abc.ABC):

    def __init__(self, fn, ret_fn, queue_class, worker_class, devs, timeout=None, constant=None, unique=None):
        """
        Device Mapper base class.

        :param fn: The function which the device mapper parallelises across devices.
        :type fn: callable
        :param ret_fn: The function which receives the ivy.MultiDevIter as input, and produces a single device output.
        :type ret_fn: callable
        :param queue_class: The class to use for creating queues.
        :type queue_class: class
        :param worker_class: The class to use for creating parallel workers.
        :type worker_class: class
        :param devs: A list of devices on which to parallelise the function.
        :type devs: sequence of str
        :param timeout: The timeout for getting items from the queues. Default is global.
        :type timeout: float, optional
        :param constant: A dict of keyword arguments which are the same for each process. Default is None.
        :type constant: dict of any, optional
        :param unique: A dict of keyword argument sequences which are unique for each process. Default is None.
        :type unique: dict of iterables of any, optional
        """
        constant_kwargs = ivy.default(constant, {})
        unique_kwargs = ivy.default(unique, {})
        self._fn = fn
        self._ret_fn = ret_fn
        self._devs = devs
        self._num_workers = len(devs)
        self._timeout = ivy.default(timeout, ivy.queue_timeout())
        self._workers = dict()
        self._input_queues = dict()
        self._output_queues = dict()
        self._worker_class = worker_class
        for i, ds in enumerate(self._devs):
            input_queue = queue_class()
            output_queue = queue_class()
            worker_kwargs = dict(**constant_kwargs, **{k: v[i] for k, v in unique_kwargs.items()})
            worker = self._worker_class(target=self._worker_fn, args=(input_queue, output_queue, devs[i],
                                                                      worker_kwargs, ivy.current_framework_str()))
            worker.start()
            self._input_queues[ds] = input_queue
            self._output_queues[ds] = output_queue
            self._workers[ds] = worker

    def __getstate__(self):
        # prevent already running processes from being pickled as sent to new processes
        state = self.__dict__.copy()
        state['_workers'] = None
        state['_ret_fn'] = None
        return state

    # noinspection PyShadowingNames
    def _worker_fn(self, input_queue, output_queue, dev, kwargs, framework_str):
        ivy.set_framework(framework_str)
        ivy.set_default_device(dev)
        for k, v in kwargs.items():
            if isinstance(v, ivy.Module) and not v.built:
                v.build(dev=dev)
        if 'dev' in inspect.getfullargspec(self._fn).args:
            kwargs['dev'] = dev
        while True:
            try:
                loaded_kwargs = input_queue.get(timeout=self._timeout)
            except queue.Empty:
                continue
            if loaded_kwargs is None:
                return
            if 'split_factor' in loaded_kwargs:
                ivy.set_split_factor(loaded_kwargs['split_factor'], dev)
                del loaded_kwargs['split_factor']
            ret = self._fn(**loaded_kwargs, **kwargs)
            output_queue.put(ret)

    def map(self, used_devs=None, split_factors=None, **kwargs):
        """
        Map the function fn to each of the MultiDevice args and kwargs, running each function in parallel with CUDA-safe
        multiprocessing.

        :param used_devs: The devices used in the current mapping pass. Default is all devs.
        :type used_devs: sequence of str, optional
        :param split_factors: The updated split factors 0 < sf < 1 for each device. Default is None.
        :type split_factors: dict of floats, optional
        :param kwargs: The MutliDevice keyword arguments to map the function to.
        :type kwargs: dict of any
        :return: The results of the function, returned as a MultiDevice instance.
        """
        if ivy.exists(split_factors):
            kwargs['split_factor'] = split_factors
        used_devs = ivy.default(used_devs, self._devs)
        [self._input_queues[ds].put({k: v[ds] for k, v in kwargs.items()}) for ds in used_devs]
        return self._ret_fn(
            ivy.MultiDevIter([self._output_queues[ds].get(timeout=self._timeout) for ds in used_devs],
                             self._num_workers))

    @abc.abstractmethod
    def __del__(self):
        raise NotImplementedError


class DevMapperMultiProc(DevMapper):

    def __init__(self, fn, ret_fn, devs, timeout=None, constant=None, unique=None):
        multiprocessing = ivy.multiprocessing('forkserver')
        super().__init__(fn, ret_fn, multiprocessing.Queue, multiprocessing.Process, devs, timeout,
                         constant, unique)

    def __del__(self):
        # noinspection PyBroadException
        try:
            for i, w in enumerate(self._workers.values()):
                self._input_queues[i].put(None)
                w.join(timeout=0.25)
            for q in self._input_queues.values():
                q.cancel_join_thread()
                q.close()
            for q in self._output_queues.values():
                q.cancel_join_thread()
                q.close()
        except Exception:
            pass
        finally:
            for w in self._workers.values():
                if w.is_alive():
                    w.terminate()


# Device Manager #

class DevManager:

    def __init__(self, dev_mapper=None, devs: Union[Iterable[str], Dict[str, int]] = None, da_dim_size=None,
                 safety_factor=1.1, min_dev_dim_size=0, max_dev_dim_step_ratio=0.1, min_unit_dev_tune_steps=10,
                 min_sf_tune_steps=10, starting_split_factor=0., max_split_factor_step_size=0.05, tune_dev_alloc=True,
                 tune_dev_splits=True):
        """
        Create device manager, which unlike the device mapper, handles all argument cloning and distributing internally.
        The device manager only receivess a specification regarding the ratio of the batch each device should consume.

        :param dev_mapper: The pre-built device mapper used by the manager internally.
        :type dev_mapper: DevMapper
        :param devs: The devices to distribute and clone the arguments across.
        :type devs: sequence of strs or dict of split sizes
        :param da_dim_size: The size of the dimension along which the device allocation splitting is performed.
        :type da_dim_size: int
        :param safety_factor: The factor by which to be safe in the avoidance of OOM GPU errors. Default is 1.1.
        :type safety_factor: float, optional
        :param min_dev_dim_size: The minimum dimension size to pass to a device. Default is 0.
        :type min_dev_dim_size: int, optional
        :param max_dev_dim_step_ratio: The maximum step ratio for changing the dimension for a device. Default is 0.1.
        :type max_dev_dim_step_ratio: int, optional
        :param min_unit_dev_tune_steps: The minimum number of tune steps to make when optimizing with unit step size.
                                   Default is 10.
        :type min_unit_dev_tune_steps: int, optional
        :param min_sf_tune_steps: Minimum number of split factor tune steps. Default is 10.
        :type min_sf_tune_steps: int, optional
        :param starting_split_factor: The initial device-specific split factor. Default is 0.
        :type starting_split_factor: float, optional
        :param max_split_factor_step_size: The maximum step size for changing the split factor for a device.
                                           Default is 0.05.
        :type max_split_factor_step_size: float, optional
        :param tune_dev_alloc: Whether to tune the device split sizes internally based on device utilization tracking,
                               and use the provided values for initialization. Default is True.
        :type tune_dev_alloc: bool, optional
        :param tune_dev_splits: Whether to tune the per-device split sizes internally. Default is True.
        :type tune_dev_splits: bool, optional
        """
        with_dev_mapping = True if ivy.exists(dev_mapper) else False
        tune_dev_alloc = False if not with_dev_mapping else tune_dev_alloc
        self._dev_mapper = dev_mapper
        devs = ivy.default(devs, [ivy.default_device()])
        self._num_devs = len(devs)
        self._dim_size = da_dim_size
        assert 1 <= safety_factor
        self._safety_factor = safety_factor
        self._min_dev_dim_size = min_dev_dim_size
        self._max_dev_dim_step_ratio = max_dev_dim_step_ratio
        if self._dim_size:
            self._max_dev_dim_step_size = max(int(round(self._max_dev_dim_step_ratio * self._dim_size)), 1)
        self._min_unit_dev_tune_steps = min_unit_dev_tune_steps
        self._min_sf_tune_steps = min_sf_tune_steps
        self._max_split_factor_step_size = max_split_factor_step_size
        self._with_dev_mappig = with_dev_mapping
        self._tune_da = tune_dev_alloc
        self._tune_ds = tune_dev_splits
        self._tuned = ((not tune_dev_alloc or self._num_devs == 1) and not tune_dev_splits)
        self._first_da_tune_step = True
        self._first_ds_tune_step = True
        self._da_tune_count = 0
        self._unit_da_tune_count = 0
        self._ds_tune_count = 0
        if tune_dev_alloc:
            self._tune_step = self.da_tune_step
        elif tune_dev_splits:
            self._tune_step = self.ds_tune_step
        else:
            self._tune_step = None
        self._observed_configs = set()
        self._da_directions = dict()
        self._da_directions_flipped = dict()
        if isinstance(devs, dict):
            self._dev_da_ratios = devs
        else:
            self._dev_da_ratios = dict(zip(devs, [1 / self._num_devs] * self._num_devs))
        self._devs_keys = self._dev_da_ratios.keys()
        self._percent_mem_inc_per_unit_da_dim = dict(zip(self._devs_keys, [0] * self._num_devs))
        self._percent_mem_inc_per_sf = dict(zip(self._devs_keys, [0] * self._num_devs))
        self._percent_util_inc_per_unit_da_dim = dict(zip(self._devs_keys, [1] * self._num_devs))
        self._delta_da_dim_sizes = dict(zip(self._devs_keys, [0] * self._num_devs))
        self._delta_sfs = dict(zip(self._devs_keys, [0] * self._num_devs))
        self._dev_percent_mems = None
        self._dev_utils = None
        if with_dev_mapping and ivy.exists(self._dim_size):
            self._compute_devs_da()
        self._devs_ds = {ds: starting_split_factor for ds in self._devs_keys}
        if self._tune_ds and not with_dev_mapping:
            [ivy.set_split_factor(starting_split_factor, ds) for ds in self._devs_keys]
        self._da_time = time.perf_counter()
        self._da_step_time = 0
        self._ds_time = time.perf_counter()
        self._ds_step_time = 0

    # Device Allocation #

    def _shift_da_splits(self, ordered_dev_util_keys, deltas):
        for i in range(math.floor(self._num_devs / 2)):

            # less and more utilized keys
            less_util_dev = ordered_dev_util_keys[i]
            more_util_dev = ordered_dev_util_keys[-i - 1]

            # less utilized
            delta = max(min(deltas[less_util_dev],
                            self._devs_da[more_util_dev] - self._min_dev_dim_size), 1)
            if ivy.exists(self._max_dev_dim_step_size):
                delta = min(delta, self._max_dev_dim_step_size)
            self._devs_da[less_util_dev] += delta
            self._delta_da_dim_sizes[less_util_dev] = delta

            # more utilized
            self._devs_da[more_util_dev] -= delta
            self._delta_da_dim_sizes[more_util_dev] = -delta

    def _compute_devs_da(self):
        split_sizes = [int(round(r * self._dim_size)) for r in self._dev_da_ratios.values()]
        combined_batch_size = sum(split_sizes)
        excess_size = combined_batch_size - self._dim_size
        if excess_size > 0:
            for i in range(abs(excess_size)):
                split_sizes[i] -= 1
        elif excess_size < 0:
            for i in range(abs(excess_size)):
                split_sizes[i] += 1
        self._devs_da = {k: v for k, v in zip(self._devs_keys, split_sizes)}

    def _compute_dev_da_ratios(self):
        self._dev_da_ratios = {k: v / self._dim_size for k, v in self._devs_da.items()}

    def da_tune_step(self, oom=False):
        if self._tuned:
            return
        new_dev_utils = dict(sorted({k: dev_util(k) for k in self._devs_keys}.items(), key=lambda item: item[1]))
        new_dev_utils_keys = list(new_dev_utils.keys())
        highest_util_dev = new_dev_utils_keys[-1]
        highest_util = new_dev_utils[highest_util_dev]
        if oom:
            new_dev_percent_mems = {k: 100 for k in self._devs_keys}
        else:
            new_dev_percent_mems = dict(sorted({k: percent_used_mem_on_dev(k) for k in self._devs_keys}.items(),
                                               key=lambda item: item[1]))

        # first step
        if self._first_da_tune_step:

            # log
            logging.info('tuning device allocation...')

            # shift the device splits by 1
            self._shift_da_splits(new_dev_utils_keys, {k: 1 for k in self._devs_keys})

            # update device percentage memory usages and utilizations
            self._dev_percent_mems = new_dev_percent_mems
            self._dev_utils = new_dev_utils

            # increment count, update ratios and tune step, and return
            self._da_tune_count += 1
            self._first_da_tune_step = False
            self._compute_dev_da_ratios()
            if self._tune_ds:
                self._tune_step = self.ds_tune_step
            self._da_time = time.perf_counter()
            return

        # otherwise

        # check if all directions have changed, and if so, half the max dev dim step size
        if self._max_dev_dim_step_size > 1:
            da_directions = {k: 1 if i < math.floor(self._num_devs/2) else -1
                             for i, (k, v) in enumerate(new_dev_utils.items())}
            if len(self._da_directions) == 0:
                self._da_directions = da_directions
                self._da_directions_flipped = {k: False for k in self._devs_keys}
            else:
                self._da_directions_flipped = {k: da_directions[k] * v < 0 for k, v in self._da_directions.items()}
            if sum(self._da_directions_flipped.values()) == self._num_devs:
                self._da_directions.clear()
                self._max_dev_dim_step_size = max(int(round(self._max_dev_dim_step_size/2)), 1)

        # percentage memory increase per unit dim
        delta_percent_mems = {k: new_dev_percent_mems[k] - self._dev_percent_mems[k] for k in self._devs_keys}
        self._percent_mem_inc_per_unit_da_dim = \
            {k: (((self._da_tune_count - 1) * self._percent_mem_inc_per_unit_da_dim[k] +
                  (delta_percent_mems[k]/delta_dim_size)) / self._da_tune_count)
            if delta_dim_size != 0 else self._percent_mem_inc_per_unit_da_dim[k]
             for k, delta_dim_size in self._delta_da_dim_sizes.items()}

        # percentage utility increase per unit dim
        delta_utils = {k: new_dev_utils[k] - self._dev_utils[k] for k in self._devs_keys}
        self._percent_util_inc_per_unit_da_dim = \
            {k: max((((self._da_tune_count - 1) * self._percent_util_inc_per_unit_da_dim[k] +
                      (delta_utils[k]/delta_dim_size)) / self._da_tune_count), 0.1)
            if delta_dim_size != 0 else self._percent_util_inc_per_unit_da_dim[k]
             for k, delta_dim_size in self._delta_da_dim_sizes.items()}

        # shift the device splits
        desired_percent_increases = {k: highest_util - new_dev_utils[k] for k in self._devs_keys}
        raw_deltas = {k: int(round(desired_percent_increases[k] / self._percent_util_inc_per_unit_da_dim[k]))
                      for k in self._devs_keys}
        permissable_steps = \
            {k: min(math.floor(((100-new_dev_percent_mems[k]) / max(self._percent_mem_inc_per_unit_da_dim[k], 0.1))
                               / self._safety_factor), self._dim_size) for k in self._devs_keys}
        deltas = {k: min(v, pm) for (k, v), pm in zip(raw_deltas.items(), permissable_steps.values())}
        self._shift_da_splits(new_dev_utils_keys, deltas)

        # update device utilizations and percentage memory usages
        self._dev_utils = new_dev_utils
        self._dev_percent_mems = new_dev_percent_mems

        # increment count, update ratios and tune step
        self._compute_dev_da_ratios()
        self._da_tune_count += 1
        if self._tune_ds:
            self._tune_step = self.ds_tune_step

        # if step size is 1, check if tuning is complete, and return if so
        if self._max_dev_dim_step_size == 1:

            # check if da tuning is complete
            if self.repeated_config_check() and self._unit_da_tune_count >= self._min_unit_dev_tune_steps and \
                    not self._tune_ds or (self._ds_tune_count >= self._min_sf_tune_steps):
                self._observed_configs.clear()
                self._percent_mem_inc_per_unit_da_dim.clear()
                self._delta_da_dim_sizes.clear()
                self._dev_percent_mems.clear()
                logging.info('device allocation tuning complete!')
                self._tuned = True

            self._unit_da_tune_count += 1

        # log time
        now = time.perf_counter()
        self._da_step_time = now - self._da_time
        self._da_time = now
        if self._tuned:
            return
        logging.info('new allocation sizes {}, still tuning...'.format(
            str(['{:.2f}'.format(v) for v in self._devs_da.values()])))

    # Device Splitting #

    def _shift_ds(self, deltas):
        for ds, delta in deltas.items():
            clipped_delta = min(delta, self._max_split_factor_step_size)
            self._devs_ds[ds] = min(self._devs_ds[ds] + clipped_delta, 1)
            self._delta_sfs[ds] = clipped_delta
            if not self._with_dev_mappig:
                ivy.set_split_factor(min(self._devs_ds[ds] + clipped_delta, 1), ds)

    def ds_tune_step(self, oom=False):
        if self._tuned:
            return
        if oom:
            new_dev_percent_mems = {k: 100 for k in self._devs_keys}
        else:
            new_dev_percent_mems = dict(sorted({k: percent_used_mem_on_dev(k) for k in self._devs_keys}.items(),
                                               key=lambda item: item[1]))

        # first step
        if self._first_ds_tune_step:

            # log
            logging.info('tuning device splitting...')

            # shift the device splits by 1%
            self._shift_ds({k: 0.01 for k in self._devs_keys})

            # update device percentage memory usages and utilizations
            self._dev_percent_mems = new_dev_percent_mems

            # increment count, update ratios and tune step, and return
            self._ds_tune_count += 1
            self._first_ds_tune_step = False
            if self._tune_da:
                self._tune_step = self.da_tune_step
            self._ds_time = time.perf_counter()
            return

        # otherwise

        # percentage memory increase per unit dim
        delta_percent_mems = {k: new_dev_percent_mems[k] - self._dev_percent_mems[k] for k in self._devs_keys}
        self._percent_mem_inc_per_sf = \
            {k: (((self._ds_tune_count - 1) * self._percent_mem_inc_per_sf[k] +
                  (delta_percent_mems[k]/delta_sf)) / self._ds_tune_count)
            if delta_sf != 0 else self._percent_mem_inc_per_sf[k]
             for k, delta_sf in self._delta_sfs.items()}

        # shift the device splits
        deltas =\
            {k: min((max(100/self._safety_factor-new_dev_percent_mems[k], 0)) / max(self._percent_mem_inc_per_sf[k], 1),
                    self._max_split_factor_step_size) for k in self._devs_keys}
        self._shift_ds(deltas)

        # update device percentage memory usages
        self._dev_percent_mems = new_dev_percent_mems

        # increment count, update ratios and tune step
        self._ds_tune_count += 1
        if self._tune_da:
            self._tune_step = self.da_tune_step

        # check whether device allocation tuning is ready to terminate
        da_can_terminate = not self._tune_da or self._max_dev_dim_step_size == 1

        # check if ds tuning is complete
        if da_can_terminate and self.repeated_config_check() and self._ds_tune_count >= self._min_sf_tune_steps and \
                not self._tune_da or (self._unit_da_tune_count >= self._min_unit_dev_tune_steps):
            self._observed_configs.clear()
            self._percent_mem_inc_per_sf.clear()
            self._dev_percent_mems.clear()
            logging.info('device splitting tuning complete!')
            self._tuned = True

        # log time
        now = time.perf_counter()
        self._ds_step_time = now - self._ds_time
        self._ds_time = now
        if self._tuned:
            return
        logging.info('new split factors {}, still tuning...'.format(
            str(['{:.2f}'.format(ivy.split_factor(k)) for k in self._devs_keys])))

    # Repeated Config Checking #

    def repeated_config_check(self):

        # check if ds tuning is complete, and return if so
        config_list = list()
        if self._tune_da:
            config_list += list(self._devs_da.values())
        if self._tune_ds:
            config_list += [self._devs_ds[ds] for ds in self._devs_keys]
        config = tuple(config_list)
        if config in self._observed_configs:
            return True

        # otherwise add the current config to those observed
        self._observed_configs.add(config)

        return False

    # Mapping #

    def map(self, cloned=None, to_clone=None, distributed=None, to_distribute=None):
        """
        Map the function fn to each of the MultiDevice args and kwargs, running each function in parallel with CUDA-safe
        multiprocessing.

        :param cloned: The MutliDevice keyword arguments which are already cloned. Default is None.
        :type cloned: dict of any, optional
        :param to_clone: The MutliDevice keyword arguments to clone and map to the function. Default is None.
        :type to_clone: dict of any, optional
        :param distributed: The MutliDevice keyword arguments which already distributed. Default is None.
        :type distributed: dict of any, optional
        :param to_distribute: The MutliDevice keyword arguments to distribute and map to the function. Default is None.
        :type to_distribute: dict of any, optional
        :return: The results of the function, returned as a MultiDevice instance.
        """
        used_devs_dict = {k: v for k, v in self._devs_da.items() if v > 0}
        used_devs = list(used_devs_dict.keys())
        cloned = ivy.default(cloned, {})
        if ivy.exists(to_clone):
            to_clone = {k: ivy.dev_clone(v, used_devs) for k, v in to_clone.items()}
        else:
            to_clone = {}
        distributed = ivy.default(distributed, {})
        if ivy.exists(to_distribute):
            to_distribute = {k: ivy.dev_dist(v, used_devs_dict) for k, v in to_distribute.items()}
        else:
            to_distribute = {}
        if self._tune_ds:
            ret = self._dev_mapper.map(**cloned, **to_clone, **distributed, **to_distribute,
                                       used_devs=used_devs, split_factors=self._devs_ds)
        else:
            ret = self._dev_mapper.map(**cloned, **to_clone, **distributed, **to_distribute,
                                       used_devs=used_devs)
        if self._tuned:
            return ret
        self._tune_step()
        return ret

    def __del__(self):
        if ivy.exists(self._dev_mapper):
            self._dev_mapper.__del__()
            del self._dev_mapper

    @property
    def dim_size(self):
        return self._dim_size

    @dim_size.setter
    def dim_size(self, batch_size):
        self._dim_size = batch_size
        if self._tune_da:
            self._max_dev_dim_step_size = max(int(round(self._max_dev_dim_step_ratio * self._dim_size)), 1)
            self._compute_devs_da()

    @property
    def tune_step(self):
        return self._tune_step

    @property
    def tuned(self):
        return self._tuned


# Profiler #

class Profiler(abc.ABC):

    def __init__(self, save_dir):
        self._save_dir = save_dir

    @abc.abstractmethod
    def start(self):
        raise NotImplementedError

    @abc.abstractmethod
    def stop(self):
        raise NotImplementedError

    @abc.abstractmethod
    def __enter__(self):
        raise NotImplementedError

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        raise NotImplementedError
