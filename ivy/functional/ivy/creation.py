# global
import numpy as np
from numbers import Number
from typing import Union, Tuple, Optional, List, Iterable

# local
import ivy
from ivy.framework_handler import current_framework as _cur_framework


# Array API Standard #
# -------------------#

def arange(start: Number, stop: Number = None, step: Number = 1, dtype: ivy.Dtype = None, device: ivy.Device = None,
           ) -> Union[ivy.Array, ivy.NativeArray]:
    """Returns evenly spaced values within a given interval, with the spacing being specified.

    Values are generated within the half-open interval [start, stop) (in other words, the interval including start but
    excluding stop). For integer arguments the function is equivalent to the Python built-in range function,
    but returns an array in the chosen ml_framework rather than a list.

    See :math:`linspace` for a certain number of evenly spaced values in an interval.

    Parameters
    ----------
    stop
        End of interval. The interval does not include this value, except in some cases where step is not an
        integer and floating point round-off affects the length of out.
    start
        Start of interval. The interval includes this value. The default start value is 0.
    step
        Spacing between values. For any output out, this is the distance between two adjacent values,
        out[i+1] - out[i]. The default step size is 1. If step is specified as a position argument,
        start must also be given.
    dtype
        The desired data-type for the array in string format, i.e. 'float32' or 'int64'.
        If not given, then the type will be determined as the minimum type required to hold the objects in the
        sequence.
    device
        device on which to create the array 'cuda:0', 'cuda:1', 'cpu' etc.

    Returns
    -------
     ret
        Tensor of evenly spaced values.

        For floating point arguments, the length of the result is ceil((stop - start)/step).
        Because of floating point overflow, this rule may result in the last element of out being greater than stop.

    """
    return _cur_framework().arange(start, stop, step, dtype, device)


def asarray(x: Union[ivy.Array, ivy.NativeArray, List[Number], Tuple[Number], np.ndarray],
            dtype: Optional[Union[ivy.Dtype, str]] = None,
            device: Optional[Union[ivy.Device, str]] = None
            ) -> ivy.Array:
    """
    Converts the input to an array.

    Parameters
    ----------
    x
        input data, in any form that can be converted to an array.
        This includes lists, lists of tuples, tuples, tuples of tuples, tuples of lists and ndarrays.

    dtype
        datatype, optional. Datatype is inferred from the input data.

    device
        device on which to place the created array. Default: None.

    Returns
    --------
    An array interpretation of x.
    """
    return _cur_framework(x).asarray(x, dtype, device)


def zeros(shape: Union[int, Tuple[int], List[int]],
          dtype: Optional[ivy.Dtype] = None,
          device: Optional[ivy.Device] = None) \
        -> ivy.Array:
    """
    Returns a new array having a specified ``shape`` and filled with zeros.

    Parameters
    ----------
    shape
       output array shape.
    dtype
       output array data type. If ``dtype`` is ``None``, the output array data type must be the default floating-point data type. Default  ``None``.
    device
       device on which to place the created array. Default: ``None``.

    Returns
     -------
    ret
       an array containing zeros.

    Examples:
    ---------
    >>> shape = (3, 5)
    >>> x = ivy.zeros(shape)
    >>> print(x)
    ivy.array([[0., 0., 0., 0., 0.],
               [0., 0., 0., 0., 0.],
               [0., 0., 0., 0., 0.]])
    """
    return _cur_framework().zeros(shape, dtype, device)


def ones(shape: Union[int, Tuple[int], List[int]],
         dtype: Optional[ivy.Dtype] = None,
         device: Optional[ivy.Device] = None) \
        -> ivy.Array:
    """
    Returns a new array having a specified ``shape`` and filled with ones.

    Parameters
    ----------
    shape
        output array shape.
    dtype
        output array data type. If ``dtype`` is ``None``, the output array data type must be the default floating-point data type. Default  ``None``.
    device
        device on which to place the created array. Default: ``None``.

    Returns
     -------
    ret
        an array containing ones.

    Examples:
    ---------

    >>> shape = (2,2)
    >>> y = ivy.ones(shape)
    >>> print(y)
    ivy.array([[1.,  1.],
               [1.,  1.]])
    """
    return _cur_framework().ones(shape, dtype, device)


def full_like(x: Union[ivy.Array, ivy.NativeArray],
              fill_value: Union[int, float],
              dtype: Optional[Union[ivy.Dtype, str]] = None,
              device: Optional[Union[ivy.Device, str]] = None) \
        -> ivy.Array:
    """
    Returns a new array filled with ``fill_value`` and having the same ``shape`` as an input array ``x``.

    Parameters
    ----------
    x
        input array from which to derive the output array shape.

    fill_value
        Scalar fill value

    dtype
        output array data type. If ``dtype`` is `None`, the output array data type must be inferred from ``x``.
        Default: ``None``.

    device
        device on which to place the created array. If ``device`` is ``None``, the output array device must be inferred from ``x``.
        Default: ``None``.

    Returns
    -------
    ret:
        an array having the same shape as ``x`` and where every element is equal to ``fill_value``.

    Examples
    --------
    >>> x = ivy.array([1, 2, 3, 4, 5, 6])
    >>> fill_value = 1
    >>> y = ivy.full_like(x, fill_value)
    >>> print(y)
    ivy.array([1, 1, 1, 1, 1, 1])
    """
    return _cur_framework(x).full_like(x, fill_value, dtype=dtype, device=device)


def ones_like(x: Union[ivy.Array, ivy.NativeArray],
              dtype: Optional[Union[ivy.Dtype, str]] = None,
              device: Optional[Union[ivy.Device, str]] = None, ) \
        -> ivy.Array:
    """
    Returns a new array filled with ones and having the same shape as an input array x.

    Parameters
    ----------
    x
        input array from which to derive the output array shape.
    dtype
        output array data type. If ``dtype`` is ``None``, the output array data type must be inferred from x.
        Default  ``None``.
    device
        device on which to place the created array. If device is ``None``, the output array device must be inferred from x.
        Default: ``None``.

    Returns
     -------
    ret
        an array having the same shape as x and filled with ones.

    Examples:
    ---------

    >>> x = ivy.array([[0, 1, 2],[3, 4, 5]])
    >>> y = ivy.ones_like(x)
    >>> print(y)
    ivy.array([[1, 1, 1],[1, 1, 1]])
    """
    return _cur_framework(x).ones_like(x, dtype, device)


def zeros_like(x: Union[ivy.Array, ivy.NativeArray],
               dtype: Optional[Union[ivy.Dtype, str]] = None,
               device: Optional[Union[ivy.Device, str]] = None)\
        -> ivy.Array:
    """
    Returns a new array filled with zeros and having the same ``shape`` as an input array ``x``.

    Parameters
    ----------
    x
         input array from which to derive the output array shape.

    dtype
        output array data type. If ``dtype`` is ``None``, the output array data type must be inferred from ``x``.
        Default: ``None``.

    device
        device on which to place the created array. If ``device`` is ``None``, the output array device must be inferred from ``x``.
        Default: ``None``.

    Returns
    -------
    ret
        an array having the same shape as ``x`` and filled with ``zeros``.

    Examples
    --------
    >>> x = ivy.array([[0, 1, 2],[3, 4, 5]])
    >>> y = ivy.zeros_like(x)
    >>> print(y)
    ivy.array([[0, 0, 0],
               [0, 0, 0]])
    """
    return _cur_framework(x).zeros_like(x, dtype, device)


def tril(x: Union[ivy.Array, ivy.NativeArray],
         k: int = 0) \
        -> ivy.Array:
    """
    Returns the lower triangular part of a matrix (or a stack of matrices) x.

    Parameters
    ----------
    x
        input array having shape (..., M, N) and whose innermost two dimensions form MxN matrices.
    k
        diagonal above which to zero elements. If k = 0, the diagonal is the main diagonal. If k < 0, the diagonal is
        below the main diagonal. If k > 0, the diagonal is above the main diagonal. Default: 0.

    Returns
     -------
    ret
        an array containing the lower triangular part(s). The returned array must have the same shape and data type as
        x. All elements above the specified diagonal k must be zeroed. The returned array should be allocated on the
        same device as x.
    """
    return _cur_framework(x).tril(x, k)


def triu(x: Union[ivy.Array, ivy.NativeArray],
         k: int = 0) \
        -> ivy.Array:
    """
    Returns the upper triangular part of a matrix (or a stack of matrices) x.

    Parameters
    ----------
    x
        input array having shape (..., M, N) and whose innermost two dimensions form MxN matrices.
    k
        diagonal below which to zero elements. If k = 0, the diagonal is the main diagonal. If k < 0, the diagonal is
        below the main diagonal. If k > 0, the diagonal is above the main diagonal. Default: 0.

    Returns
     -------
    ret
        an array containing the upper triangular part(s). The returned array must have the same shape and data type as
        x. All elements below the specified diagonal k must be zeroed. The returned array should be allocated on the
        same device as x.
    """
    return _cur_framework(x).triu(x, k)


def empty(shape: Union[int, Tuple[int], List[int]],
          dtype: Optional[ivy.Dtype] = None,
          device: Optional[ivy.Device] = None) \
        -> ivy.Array:
    """Return a new array of given shape and type, filled with zeros.

    Parameters
    ----------
    shape
        output array shape.
    dtype
        output array data type. If dtype is None, the output array data type must be the default
        floating-point data type. Default: None.
    device
        device on which to place the created array. Default: None.

    Returns
     -------
    ret
        an uninitialized array having a specified shape

    """
    return _cur_framework().empty(shape, dtype, device)


def empty_like(x: Union[ivy.Array, ivy.NativeArray],
               dtype: Optional[Union[ivy.Dtype, str]] = None,
               device: Optional[Union[ivy.Device, str]] = None) \
        -> ivy.Array:
    """Returns an uninitialized array with the same shape as an input array x.

    Parameters
    ----------
    x
        input array from which to derive the output array shape.
    dtype
        output array data type. If dtype is None, the output array data type must be inferred from x. Default  None.
    device
        device on which to place the created array. If device is None, the output array device must be inferred from x. Default: None.

    Returns
     -------
    ret
        an array having the same shape as x and containing uninitialized data.

    """
    return _cur_framework(x).empty_like(x, dtype, device)


def eye(n_rows: int,
        n_cols: Optional[int] = None,
        k: Optional[int] = 0,
        dtype: Optional[ivy.Dtype] = None,
        device: Optional[ivy.Device] = None) \
        -> ivy.Array:
    """Returns a two-dimensional array with ones on the k h diagonal and zeros elsewhere.

    Parameters

    Parameters
    ----------
    n_rows
        number of rows in the output array.
    n_cols
        number of columns in the output array. If None, the default number of columns in the output array is
        equal to n_rows. Default: None.
    k
        index of the diagonal. A positive value refers to an upper diagonal, a negative value to a lower diagonal,
        and 0 to the main diagonal. Default: 0.
    dtype
        output array data type. If dtype is None, the output array data type must be the default floating-
        point data type. Default: None.
    device
         device on which to place the created array.

    Returns
     -------
    ret
        device on which to place the created array. Default: None.

    """
    return _cur_framework().eye(n_rows, n_cols, k, dtype, device)


# noinspection PyShadowingNames
def linspace(start: Union[ivy.Array, ivy.NativeArray, int], stop: Union[ivy.Array, ivy.NativeArray, int],
             num: int, axis: int = None, device: ivy.Device = None) \
        -> Union[ivy.Array, ivy.NativeArray]:
    """Generates a certain number of evenly-spaced values in an interval along a given axis.

    See :math:`arange` that allows to specify the step size of evenly spaced values in an interval.

    Parameters
    ----------
    start
        First entry in the range.
    stop
        Final entry in the range.
    num
        Number of values to generate.
    axis
        Axis along which the operation is performed.
    device
        device on which to create the array 'cuda:0', 'cuda:1', 'cpu' etc.

    Returns
     -------
    ret
        Tensor of evenly-spaced values.

    """
    return _cur_framework(start).linspace(start, stop, num, axis, device)


def meshgrid(*arrays: Union[ivy.Array, ivy.NativeArray], indexing: Optional[str] = 'xy') \
        -> List[ivy.Array]:
    """
    Returns coordinate matrices from coordinate vectors.
    Parameters
    ----------
    arrays
        an arbitrary number of one-dimensional arrays representing grid coordinates. Each array should have the same numeric data type.
    indexing
        Cartesian ``'xy'`` or matrix ``'ij'`` indexing of output. If provided zero or one one-dimensional vector(s) (i.e., the zero- and one-dimensional cases, respectively), the ``indexing`` keyword has no effect and should be ignored. Default: ``'xy'``.
    Returns
     -------
    ret List[array]
        list of N arrays, where ``N`` is the number of provided one-dimensional input arrays. Each returned array must have rank ``N``. For ``N`` one-dimensional arrays having lengths ``Ni = len(xi)``,
        - if matrix indexing ``ij``, then each returned array must have the shape ``(N1, N2, N3, ..., Nn)``.
        - if Cartesian indexing ``xy``, then each returned array must have shape ``(N2, N1, N3, ..., Nn)``.
        Accordingly, for the two-dimensional case with input one-dimensional arrays of length ``M`` and ``N``, if matrix indexing ``ij``, then each returned array must have shape ``(M, N)``, and, if Cartesian indexing ``xy``, then each returned array must have shape ``(N, M)``.
        Similarly, for the three-dimensional case with input one-dimensional arrays of length ``M``, ``N``, and ``P``, if matrix indexing ``ij``, then each returned array must have shape ``(M, N, P)``, and, if Cartesian indexing ``xy``, then each returned array must have shape ``(N, M, P)``.
        Each returned array should have the same data type as the input arrays.
    """
    return _cur_framework().meshgrid(*arrays, indexing=indexing)


def full(shape: Union[int, Tuple[int, ...]],
         fill_value: Union[int, float],
         dtype: Optional[ivy.Dtype] = None,
         device: Optional[ivy.Device] = None) \
        -> ivy.Array:
    """
    Returns a new array having a specified ``shape`` and filled with ``fill_value``.

    Parameters
    ----------
    shape
        output array shape.
    fill_value
        fill value.
    dtype
        output array data type. If ``dtype`` is `None`, the output array data type must be inferred from ``fill_value``. If the fill value is an ``int``, the output array data type must be the default integer data type. If the fill value is a ``float``, the output array data type must be the default floating-point data type. If the fill value is a ``bool``, the output array must have boolean data type. Default: ``None``.
    device
        device on which to place the created array. Default: ``None``.

    Returns
    -------
    ret
        an array where every element is equal to `fill_value`.

    Examples
    --------
    >>> shape = (2,2)
    >>> fill_value = 10
    >>> y = ivy.full(shape, fill_value)
    >>> print(y)
    ivy.array([[10, 10],
               [10, 10]])
    """
    return _cur_framework().full(shape, fill_value, dtype, device)


def from_dlpack(x: Union[ivy.Array, ivy.NativeArray]) -> ivy.Array:
    """
    Returns a new array containing the data from another (array) object with a ``__dlpack__`` method.

    Parameters
    ----------
    x  object
        input (array) object.

    Returns
     -------
    ret
        an array containing the data in `x`.

        .. admonition:: Note
           :class: note

           The returned array may be either a copy or a view. See :ref:`data-interchange` for details.
    """
    return _cur_framework(x).from_dlpack(x)


# Extra #
# ------#

array = asarray


# noinspection PyShadowingNames
def logspace(start: Union[ivy.Array, ivy.NativeArray, int], stop: Union[ivy.Array, ivy.NativeArray, int],
             num: int, base: float = 10., axis: int = None, device: ivy.Device = None) \
        -> Union[ivy.Array, ivy.NativeArray]:
    """Generates a certain number of evenly-spaced values in log space, in an interval along a given axis.

    See :math:`arange` that allows to specify the step size of evenly spaced values in an interval.

    Parameters
    ----------
    start
        First entry in the range.
    stop
        Final entry in the range.
    num
        Number of values to generate.
    base
        The base of the log space. Default is 10.0
    axis
        Axis along which the operation is performed.
    device
        device on which to create the array 'cuda:0', 'cuda:1', 'cpu' etc.

    Returns
     -------
    ret
        Tensor of evenly-spaced values.

    """
    return _cur_framework(start).logspace(start, stop, num, base, axis, device)
