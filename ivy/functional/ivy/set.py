# global
from typing import Union, Tuple, Optional

# local
import ivy
from ivy.backend_handler import current_backend as _cur_backend


# Array API Standard #
# -------------------#


def unique_all(
    x: Union[ivy.Array, ivy.NativeArray]
) -> Tuple[ivy.Array, ivy.Array, ivy.Array, ivy.Array]:
    """Returns the unique elements of an input array ``x``, the first occurring indices
    for each unique element in ``x``, the indices from the set of unique elements that
    reconstruct ``x``, and the corresponding counts for each unique element in ``x``.

    .. admonition:: Data-dependent output shape
        :class: important

        The shapes of two of the output arrays for this function depend on the data
        values in the input array; hence, array libraries which build computation graphs
        (e.g., JAX, Dask, etc.) may find this function difficult to implement without
        knowing array values. Accordingly, such libraries may choose to omit this
        function. See :ref:`data-dependent-output-shapes` section for more details.

    .. note::
       Uniqueness should be determined based on value equality (i.e., ``x_i == x_j``).
       For input arrays having floating-point data types, value-based equality implies
       the following behavior.

       -   As ``nan`` values compare as ``False``, ``nan`` values should be considered
           distinct.

       -   As ``-0`` and ``+0`` compare as ``True``, signed zeros should not be
           considered distinct, and the corresponding unique element will be
           implementation-dependent (e.g., an implementation could choose to return
           ``-0`` if ``-0`` occurs before ``+0``).

       As signed zeros are not distinct, using ``inverse_indices`` to reconstruct the
       input array is not guaranteed to return an array having the exact same values.

       Each ``nan`` value should have a count of one, while the counts for signed zeros
       should be aggregated as a single count.

    Parameters
    ----------
    x
        input array. If ``x`` has more than one dimension, the function must flatten
        ``x`` and return the unique elements of the flattened array.

    Returns
    -------
    out
        a namedtuple ``(values, indices, inverse_indices, counts)`` whose
        - first element must have the field name ``values`` and must be an array
          containing the unique elements of ``x``. The array must have the same data
          type as ``x``.
        - second element must have the field name ``indices`` and must be an array
          containing the indices (first occurrences) of ``x`` that result in ``values``.
          The array must have the same shape as ``values`` and must have the default
          array index data type.
        - third element must have the field name ``inverse_indices`` and must be an
          array containing the indices of ``values`` that reconstruct ``x``. The array
          must have the same shape as ``x`` and must have the default array index data
          type.
        - fourth element must have the field name ``counts`` and must be an array
          containing the number of times each unique element occurs in ``x``. The
          returned array must have same shape as ``values`` and must have the default
          array index data type.

        .. note::
           The order of unique elements is not specified and may vary between
           implementations.

    """
    return _cur_backend(x).unique_all(x)


def unique_inverse(x: Union[ivy.Array, ivy.NativeArray]) -> Tuple[ivy.Array, ivy.Array]:
    """Returns a tuple of two arrays, one being the unique elements of an input array x
    and the other one the indices from the set of uniques elements that reconstruct x.

    Parameters
    ----------
    x
        input array.

    Returns
    -------
    ret
        tuple of two arrays (values, inverse_indices)

    """
    return _cur_backend(x).unique_inverse(x)


def unique_values(
    x: Union[ivy.Array, ivy.NativeArray],
    *,
    out: Optional[Union[ivy.Array, ivy.NativeArray]] = None,
) -> ivy.Array:
    """Returns the unique elements of an input array ``x``.

    .. admonition:: Data-dependent output shape
        :class: important

        The shapes of two of the output arrays for this function depend on the data
        values in the input array; hence, array libraries which build computation graphs
        (e.g., JAX, Dask, etc.) may find this function difficult to implement without
        knowing array values. Accordingly, such libraries may choose to omit this
        function. See :ref:`data-dependent-output-shapes` section for more details.

    .. note::
       Uniqueness should be determined based on value equality (i.e., ``x_i == x_j``).
       For input arrays having floating-point data types, value-based equality implies
       the following behavior.

       -   As ``nan`` values compare as ``False``, ``nan`` values should be considered
           distinct.
       -   As ``-0`` and ``+0`` compare as ``True``, signed zeros should not be
           considered distinct, and the corresponding unique element will be
           implementation-dependent (e.g., an implementation could choose to return
           ``-0`` if ``-0`` occurs before ``+0``).

    Parameters
    ----------
    x
        input array. If ``x`` has more than one dimension, the function must flatten
        ``x`` and return the unique elements of the flattened array.

    Returns
    -------
    ret
        an array containing the set of unique elements in ``x``. The returned array must
        have the same data type as ``x``.

        .. note::
           The order of unique elements is not specified and may vary between
           implementations.

    """
    return _cur_backend(x).unique_values(x, out=out)


def unique_counts(
        x: Union[ivy.Array, ivy.NativeArray]
) -> Tuple[ivy.Array, ivy.Array]:
    """Returns the unique elements of an input array ``x`` and the corresponding counts for
    each unique element in ``x``.

    .. admonition:: Data-dependent output shape
        :class: important

        The shapes of two of the output arrays for this function depend on the data
        values in the input array; hence, array libraries which build computation graphs
        (e.g., JAX, Dask, etc.) may find this function difficult to implement without
        knowing array values. Accordingly, such libraries may choose to omit this
        function. See :ref:`data-dependent-output-shapes` section for more details.

    .. note::
       Uniqueness should be determined based on value equality (i.e., ``x_i == x_j``).
       For input arrays having floating-point data types, value-based equality implies
       the following behavior.

       -   As ``nan`` values compare as ``False``, ``nan`` values should be considered
           distinct.
       -   As ``-0`` and ``+0`` compare as ``True``, signed zeros should not be
           considered distinct, and the corresponding unique element will be
           implementation-dependent (e.g., an implementation could choose to return
           ``-0`` if ``-0`` occurs before ``+0``).

    Parameters
    ----------
    x
        input array. If ``x`` has more than one dimension, the function must flatten 
        ``x`` and return the unique elements of the flattened array.

    Returns
    -------
    ret
        a namedtuple ``(values, counts)`` whose

        - first element must have the field name ``values`` and must be an 
          array containing the unique elements of ``x``.
          The array must have the same data type as ``x``.
        - second element must have the field name ``counts`` and must be an array 
          containing the number of times each unique element occurs in ``x``.
          The returned array must have same shape as ``values`` and must
          have the default array index data type.

    .. note::
           The order of unique elements is not specified and may vary between
           implementations.

    This method conforms to the `Array API Standard
    <https://data-apis.org/array-api/latest/>`_. This docstring is an extension of 
    the `docstring <https://data-apis.org/array-api/latest/API_specification/
    generated/signatures.elementwise_functions.tan.html>`_
    in the standard. The descriptions above assume an array input for simplicity, but
    the method also accepts :code:`ivy.Container` instances in place of
    :code:`ivy.Array` or :code:`ivy.NativeArray` instances, as shown in the type hints
    and also the examples below.

    Functional Examples
    -------------------

    With :code: 'ivy.Array' input:

    >>> x = ivy.array([1,2,1,3,4,1,3])
    >>> y = unique_counts(x)
    >>> print(y)
    Tuple([1,2,3,4],[3,1,2,1])

    >>> x = ivy.asarray([1,2,3,4],[2,3,4,5],[3,4,5,6])
    >>> y = unique_counts(x)
    >>> print(y)
    Tuple([1,2,3,4,5,6],[1,2,3,3,2,1])

    With :code: 'ivy.NativeArray' input:

    >>> x = ivy.native_array([0.2,0.3,0.4,0.2,1.4,2.3,0.2])
    >>> y = ivy.unique_counts(x)
    >>> print(y)
    Tuple([0.2,0.3,0.4,1.4,2.3],[3,1,1,1,1]

    Instance Method Examples
    ------------------------

    Using :code:`ivy.Array` instance method:
    >>> x = ivy.array([0., 1., 3. , 2. , 1. , 0.])
    >>> y = x.unique_counts()
    >>> print(y)
    Tuple([0., 1., 2., 3.],[2,2,1,1])
    """
    return _cur_backend(x).unique_counts(x)
