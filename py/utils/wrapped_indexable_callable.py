# Python module for the class 'WrappedIndexableCallable'
#
# usage
#   * from utils.wrapped_indexable_callable import WrappedIndexableCallable
#   * func_name = WrappedIndexableCallable(func_that_accepts_a_single_int)
#
# author: acegene <acegene22@gmail.com>

# type: ignore # TODO

from __future__ import annotations
from typing import Any, Callable, Optional, overload, Sequence, TypeVar, Union

from utils import slice_utils

T = TypeVar("T", covariant=True)


class WrappedIndexableCallable:
    """Wraps <callable_> and exposes it as an iterable container"""

    def __init__(self, callable_: Union[Callable, Sequence[T]], length: int, slice_: Optional[slice] = None) -> None:
        """Takes <callable_> with a single positive int param, where <length> is less than the largest index <callable_> can accept

        Args:
            callable_ (Union[Callable, Sequence[T]]): Object to be wrapped and exposed as an iterable container
            length (int): A size smaller than the largest index that <callable_> will accept
            slice_ (slice): A slice used to simulate slicing of the internal container
        """
        self._callable = callable_
        self._length = length
        self._slice = slice_ if slice_ != None else slice(0, self._length, 1)

    @overload
    def __getitem__(self, index: int) -> T:
        ...

    @overload
    def __getitem__(self, slice_: slice) -> WrappedIndexableCallable[T]:
        ...

    def __getitem__(self, item):
        if isinstance(item, slice):
            return WrappedIndexableCallable(
                self._callable, self._length, slice_utils.slice_merge([self._slice, item], self._length)
            )
        elif isinstance(item, int):
            indexable_index = slice_utils.slice_index(item, self._slice, self._length)
            try:
                return (
                    self._callable[indexable_index]
                    if hasattr(self._callable, "__getitem__")
                    else self._callable(indexable_index)
                )
            except IndexError:
                raise ValueError(
                    f"Param <callable_> provided to {type(self)} did not contain index {item} that was implied to exist by <length> {self._length}"
                )
        raise ValueError(f"WrappedIndexableCallable indices must be integers or slices, not {type(item)}")

    def __iter__(self) -> _WrappedIndexableCallableIterator[T]:
        return self._WrappedIndexableCallableIterator(self._callable, self._length, self._slice)

    def __len__(self) -> int:
        return slice_utils.slice_length(self._slice, self._length)

    def __reversed__(self) -> WrappedIndexableCallable[T]:
        return WrappedIndexableCallable(
            self._callable, self._length, slice_utils.slice_merge([self._slice, slice(None, None, -1)], self._length)
        )

    def __repr__(self) -> str:
        return f"[{', '.join(str(x) for x in self)}]"

    class _WrappedIndexableCallableIterator:
        def __init__(self, callable_: Union[Callable, Sequence[Any]], length: int, slice_: slice) -> None:
            self._callable = callable_
            self._length = length
            self._slice = slice_utils.slice_clean(slice_, self._length, True)
            self._index = self._slice.start

        def __iter__(self) -> _WrappedIndexableCallableIterator:
            return self

        def __next__(self) -> T:
            current = self._index
            self._index += self._slice.step
            if self._slice.stop != None:
                if self._slice.step > 0:
                    if current >= self._slice.stop:
                        raise StopIteration
                else:
                    if current <= self._slice.stop:
                        raise StopIteration
            else:
                if self._slice.step < 0 and current <= -1:
                    raise StopIteration
            try:
                return self._callable[current] if hasattr(self._callable, "__getitem__") else self._callable(current)
            except IndexError:
                raise ValueError(
                    f"Param <callable_> provided to {type(self)} did not contain index {current} that was implied to exist by <length> {self._length}."
                )
