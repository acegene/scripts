# exc_utils.py
#
# brief:  python module for tools related to exceptions
#
# usage:  * from utils import exc_utils
#               - adding this to a python file allows usage of functions as exc_utils.func()
#
# author: acegene <acegene22@gmail.com>

from typing import Any, Callable, Optional, Sequence, Union


def raise_if_false(expression: bool, exception: Exception, err_msg: Optional[str] = None) -> None:
    """Throw <exception> if <expression> == False

    Args:
        expression (bool): Expression that determines whether to raise <exception>
        exception (Exception): Exception to be raised if <expression> == False
        err_msg (str): String to print if <expression> == False

    Returns:
        None

    Raises:
        Type(<exception>): This is raised if <expression> == False
    """
    if not expression:
        if err_msg != None:
            print(err_msg)
        raise exception


def try_with_default(
    exceptions: Union[Exception, Sequence[Exception]], default: Any, callable: Callable, *args: Any, **kargs: Any
) -> Any:
    """Returns result from calling <callable>(<*args>, <**kargs>); if an exception in <exceptions> occurs return <default>

    Imports:
        from typing import Any, Callable, Union

    Args:
        exceptions (Union[Exception, Sequence[Exception]]): Exceptions that cause <default> to be selected.
        default (Any): Value to return if an exception in <exceptions> occurs
        callable (Callable): Function like object to call as <callable>(*<args>, **<kwargs>)
        args (Any): Positional args to pass to <callable>
        kwargs (Any): Keyword args to pass to <callable>

    Returns:
        bool: <callable>(*<args>, **<kwargs>) if no exception; <default> if exception in <exceptions> is raised
    """
    try:
        return callable(*args, **kargs)
    except (exceptions):
        return default
