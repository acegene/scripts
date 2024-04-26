# Python module for tools related to exceptions
#
# usage
#   * from utils import exc_utils
#       * adding this to a python file allows usage of functions as exc_utils.func()
#
# author: acegene <acegene22@gmail.com>

from typing import Any, Callable, Optional, Tuple, Type, Union


def raise_if_false(do_not_raise: bool, exception: Exception, print_object: Optional[Any] = None) -> None:
    """Throw <exception> if <do_not_raise> == False

    Args:
        do_not_raise (bool): Determines whether to raise <exception>
        exception (Exception): Exception to be raised if <do_not_raise> == False
        print_object (str): Object to print if <do_not_raise> == False

    Returns:
        None

    Raises:
        Type(<exception>): This is raised if <do_not_raise> == False
    """
    if not do_not_raise:
        if print_object is not None:
            print(print_object)
        raise exception


def try_with_default(
    exceptions: Union[Type[BaseException], Tuple[Type[BaseException]]],
    default: Any,
    callable_: Callable,
    *args: Any,
    **kargs: Any
) -> Any:
    """Returns <callable_>(<*args>, <**kargs>); if an exc in <exceptions> occurs instead return <default>

    Args:
        exceptions: Exceptions that cause <default> to be selected.
        default: Value to return if an exception in <exceptions> occurs
        callable_: Function like object to call as <callable_>(*<args>, **<kwargs>)
        args: Positional args to pass to <callable_>
        kwargs: Keyword args to pass to <callable_>

    Returns:
        <callable_>(*<args>, **<kwargs>) if no exception; <default> if exception in <exceptions> is raised
    """
    try:
        return callable_(*args, **kargs)
    except exceptions:
        return default
