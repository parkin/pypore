import sys

import numpy as np

ALLOWED_INDEX_TYPES = [int]
if sys.version_info < (3, 0):
    ALLOWED_INDEX_TYPES.append(long)

try:
    xrange
except NameError:
    xrange = range


def process_range(start, stop, step, length):
    """
    Returns the start, stop, and step of a slice. Ensures that start, stop, and step
    are given a value, which can be based on the length of the dimension of interest.

    :param start: The start of a range.
    :param stop: The stopping point of the range.
    :param step:
    :param length: The max length of the range.
    :return: Tuple of the following:

        #. start - the starting index of the range
        #. stop - the ending index of the range [start, stop)
        #. step - the step size of the range

    """
    if step is None:
        step = 1
    elif step == 0:
        raise ValueError("Step cannot be 0.")

    if start is None:
        if step > 0:
            start = 0
        else:
            start = length - 1
    elif start < 0:
        start += length
    if start < 0:
        start = 0
    if start > length:
        start = length - 1

    if stop is None:
        if step > 0:
            stop = length
        else:
            stop = -1
    elif stop < 0:
        stop += length
        if stop < 0:
            stop = -1 if step < 0 else 0
    elif stop > length:
        stop = length

    return start, stop, step


def is_index(index):
    """Checks if an object can work as an index or not."""

    if type(index) in ALLOWED_INDEX_TYPES:
        return True
    elif isinstance(index, np.integer):
        return True

    return False


def interpret_indexing(keys, obj_shape):
    """
    Interprets slice information sent to __getitem__.

    :param keys: Slice info sent as parameter to __getitem__.
    :param obj_shape: The shape of the object you are trying to slice.
    :return: Returns a tuple of the following things.

        #. starts - numpy array of starting indices for each slice dimension.
        #. stops - numpy array of stopping indices for each slice dimension.
        #. steps - numpy array of step size for each slice dimension.
        #. shape - Final shape that slice will assume.
    """
    max_keys = len(obj_shape)
    shape = (max_keys,)
    starts = np.empty(shape=shape, dtype=np.integer)
    stops = np.empty(shape=shape, dtype=np.integer)
    steps = np.empty(shape=shape, dtype=np.integer)
    # make the keys a tuple if not already
    if not isinstance(keys, tuple):
        keys = (keys,)
    nkeys = len(keys)
    # check if we were asked for too many dimensions
    if nkeys > max_keys:
        raise IndexError("Too many indices for shape {0}.".format(obj_shape))
    dim = 0
    for key in keys:
        # Check if it's an index
        if is_index(key):
            if abs(key) >= obj_shape[dim]:
                raise IndexError("Index out of range.")
            if key < 0:
                key += obj_shape[dim]
            start, stop, step = process_range(key, key + 1, 1, obj_shape[dim])

        elif isinstance(key, slice):
            start, stop, step = process_range(key.start, key.stop, key.step, obj_shape[dim])
        else:
            raise TypeError("Non-valid index or slice {0}".format(key))
        starts[dim] = start
        stops[dim] = stop
        steps[dim] = step
        dim += 1

    # finish the extra dimensions
    if dim < max_keys:
        for j in range(dim, max_keys):
            starts[j] = 0
            stops[j] = obj_shape[j]
            steps[j] = 1

    # compute the new shape for the slice
    shape = []
    for j in range(max_keys):
        # new_dim = abs(stops[j] - starts[j])/steps[j]
        new_dim = len(xrange(starts[j], stops[j], steps[j]))
        shape.append(new_dim)

    return starts, stops, steps, tuple(shape)


def slice_combine(length, *slices):
    """
    Combines slices in series.
    Usage:
    >>> import numpy as np
    >>> x = np.arange(100)
    >>> slice1 = slice(0, 90, 1)
    >>> slice2 = slice(None, None, -2)
    >>> combined = slice_combine(len(x), slice1, slice2)
    >>> np.testing.assert_array_equal(x[slice1][slice2], x[combined])
    :param length: The length of the first dimension of data being sliced. (eg len(x))
    :param *slices: Pass in one or many slices.
    :returns: A slice that is a combination of the series input slices.
    """

    if len(slices) < 1:
        return slice(0, 0, 1)

    slice_final = slices[0]

    for i in xrange(1, len(slices)):
        slice1 = slice_final
        slice2 = slices[i]

        # First get the step sizes of the two slices.
        slice1_step = (slice1.step if slice1.step is not None else 1)
        slice2_step = (slice2.step if slice2.step is not None else 1)

        # The final step size
        step = slice1_step * slice2_step

        # Use slice1.indices to get the actual indices returned from slicing with slice1
        slice1_indices = slice1.indices(length)

        # We calculate the length of the first slice
        slice1_length = (abs(slice1_indices[1] - slice1_indices[0]) - 1) // abs(slice1_indices[2])

        # If we step in the same direction as the start,stop, we get at least one datapoint
        if (slice1_indices[1] - slice1_indices[0]) * slice1_step > 0:
            slice1_length += 1
        else:
            # Otherwise, The slice is zero length.
            return slice(0, 0, step)

        # Use the length after the first slice to get the indices returned from a
        # second slice starting at 0.
        slice2_indices = slice2.indices(slice1_length)

        # if the final range length = 0, return
        if not (slice2_indices[1] - slice2_indices[0]) * slice2_step > 0:
            return slice(0, 0, step)

        # We shift slice2_indices by the starting index in slice1 and the
        # step size of slice1
        start = slice1_indices[0] + slice2_indices[0] * slice1_step
        stop = slice1_indices[0] + slice2_indices[1] * slice1_step

        # slice.indices will return -1 as the stop index when slice.stop should be set to None.
        if start > stop:
            if stop < 0:
                stop = None

        slice_final = slice(start, stop, step)

    return slice_final


def get_slice_length(length, s):
    """
    Calculates the length of the slice s used on a data set of length.
    :param length: length of the data set that the slice is applied to.
    :param s: The slice.
    :return: The length of the sliced data set.
    """
    indices = s.indices(length)

    new_length = (abs(indices[1] - indices[0]) - 1) // abs(indices[2])

    if (indices[1] - indices[0]) * indices[2] > 0:
        new_length += 1
    else:
        return 0

    return new_length
