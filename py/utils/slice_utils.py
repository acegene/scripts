# Python module for tools related to slice objects
#
# usage:
#   * from utils import slice_utils
#       * adding this to a python file allows usage of functions as slice_utils.func()
#
# author: acegene <acegene22@gmail.com>
import functools
from collections.abc import Sequence


def in_slice(index: int, slice_: slice, length: int) -> bool:
    """Return 'container[<index>] in container[<slice_>]' when len(container) = <length>

    Args:
        index (int): Index to check for existence of in <slice_>
        slice_ (slice): Slice to check if <index> is contained within
        length (int): Length of the first dimension of the container being sliced

    Returns:
        bool: True if 'container[<index>] in container[<slice_>]' when len(container) = <length>
    """
    start, stop, step = slice_.indices(length)
    index_normalized = index + length if index < 0 else index
    if step > 0:
        if index_normalized < start or index_normalized >= stop:
            return False
    else:
        if index_normalized > start or index_normalized <= stop:
            return False
    _, r = divmod(index_normalized - start, step)
    return r == 0


def is_slice_empty(slice_: slice, length: int) -> bool:
    """Return 'len(container[<slice_>]) == 0' when len(container) = <length>

    Args:
        slice_ (slice): Slice to check for emptiness of
        length (int): Length of the first dimension of the container being sliced

    Returns:
        bool: 'len(container[<slice_>]) == 0' when len(container) = <length>
    """
    #### if start == stop and start is not None then return True
    start, stop, step = slice_.indices(length)
    if start == stop:
        return True
    if ((stop - start) > 0) is not (step > 0):
        return True
    return False


def slice_clean(slice_: slice, length: int, allow_nones: bool = True) -> slice:
    """Return a cleaned slice object equivalent to <slice_> when len(container) = <length>

    slice_cleaned.start is bounded by [0,length]
    slice_cleaned.stop is bounded by [0, length] or set to None/-length-1 when necessary
    slice_cleaned.step = 1 if <slice_>.step is None else <slice_.step>

    https://stackoverflow.com/q/33943533/10630957

    Args:
        slice_: Slice to be cleaned
        length: Length of the first dimension of the container being sliced
        allow_nones: If stop would be -length-1, set it to None instead

    Returns:
        A cleaned slice object equivalent to <slice_> when len(container) = <length>
    """
    # pylint: disable=[too-many-branches,too-many-return-statements]
    #### initialize outputs
    start = slice_.start
    stop = slice_.stop
    step = 1 if slice_.step is None else slice_.step
    #### if start == stop and start is not None then return empty slice
    if start is not None and start == stop:
        return slice(0, 0, step)
    if step > 0:
        #### set value of start when step > 0
        if start is None:
            start = 0
        elif start > length - 1:
            return slice(0, 0, step)
        elif start < 0:
            start = start + length if start > -length else 0
        #### set value of stop when step > 0
        if stop is None:
            stop = length
        elif stop in {0, -length}:
            return slice(0, 0, step)
        elif stop < 0:
            if stop > -length:
                stop = stop + length
            else:
                return slice(0, 0, step)
    else:
        #### set value of start when step < 0
        if start is None:
            start = length - 1
        elif start < 0:
            if start < -length:
                return slice(0, 0, step)
            start = start + length
        elif start > length - 1:
            start = length - 1
        #### set value of stop when step < 0
        if stop is None:
            stop = None if allow_nones else -length - 1
        elif stop > length - 2 or stop == -1:
            return slice(0, 0, step)
        elif stop < 0:
            if stop < -length:
                stop = None if allow_nones else -length - 1
            else:
                stop = stop + length
    #### return slice cleaned slice
    return slice(start, stop, step)


def slice_index(index: int, slice_: slice, length: int) -> int:
    """Return <index_slice> such that 'cntnr[<index_slice>] == cntnr[<slice_>][<index>]' when len(cntnr) == <length>

    Args:
        index: Index of <slice_> to locate in original cntnr
        slice_: Slice to find the corresponding containers index from
        length: Length of the first dimension of the cntnr being sliced

    Returns:
        index_slice such that 'cntnr[<index_slice>] == cntnr[<slice_>][<index>]' when len(cntnr) == <length>

    Raises:
        IndexError: If cntnr[<slice_>][<index>] would raise a IndexError when len(cntnr) = <length>
    """
    start, _, step = slice_.indices(length)
    if index < 0:
        index_normalized = index + slice_length(slice_, length)
        if index_normalized < 0:
            raise IndexError
        index_slice = start + (step * index_normalized)
        if in_slice(index_slice, slice_, length):
            return index_slice
        raise IndexError
    index_slice = start + (step * index)
    if index_slice < 0:
        raise IndexError
    if in_slice(index_slice, slice_, length):
        return index_slice
    raise IndexError


def slice_length(slice_: slice, length: int) -> int:
    """Return len(container[<slice_>]) when len(container) = <length>

    https://stackoverflow.com/a/36188683/10630957

    Args:
        slice_ (slice): Slices to find the length of
        length (int): Length of the first dimension of the container being sliced

    Returns:
        int: len(container[<slice_>]) when len(container) = <length>
    """
    return len(range(*slice_.indices(length)))


def slice_merge(slices: Sequence[slice], length: int, allow_nones: bool = True) -> slice:
    """Combine slices such that 'container[s1][s2] == container[slice_merge(s1, s2, len(container))]'.

    Args:
        slices (Sequence[slice]): Slices to be merged
        length (int): Length of the first dimension of the container being sliced
        allow_nones (bool): If stop would be -length-1, set it to None instead

    Returns:
        slice: A merged representation of <slices> when len(container) = <length>
    """

    def slice_merge_impl(lhs: slice, rhs: slice, length: int, allow_nones: bool) -> slice:
        #### get step sizes
        lhs_step = lhs.step if lhs.step is not None else 1
        rhs_step = rhs.step if rhs.step is not None else 1
        step = lhs_step * rhs_step
        #### get indices from slicing with <lhs> assuming length=<length>
        lhs_indices = lhs.indices(length)
        #### length of <lhs>
        lhs_length = (abs(lhs_indices[1] - lhs_indices[0]) - 1) // abs(lhs_indices[2])
        #### deterimine there is at least one datapoint when stepping from start to stop with <lhs>
        if (lhs_indices[1] - lhs_indices[0]) * lhs_step > 0:
            lhs_length += 1
        else:
            return slice(0, 0, step)  # slice of zero length
        #### get indices from slicing with <lhs> assuming length=<lhs_length>
        rhs_indices = rhs.indices(lhs_length)
        #### return empty slice if the resulting range is 0
        if not (rhs_indices[1] - rhs_indices[0]) * rhs_step > 0:
            return slice(0, 0, step)  # slice of zero length
        #### transform <rhs_indices> using <lhs_indices[0]> and <lhs_step>
        start = lhs_indices[0] + rhs_indices[0] * lhs_step
        stop = lhs_indices[0] + rhs_indices[1] * lhs_step
        #### if stop == -1: stop = None
        if start > stop and stop < 0:
            stop = None if allow_nones else -length - 1
        #### return successfully merged slice
        return slice(start, stop, step)

    return functools.reduce(lambda x, y: slice_merge_impl(x, y, length, allow_nones), slices)
