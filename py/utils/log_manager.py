# Python module for the class 'LogManager'
#
# usage
#   * from utils.log_manager import LogManager
#   * logger = LogManager(__name__)
#
# author: acegene <acegene22@gmail.com>

# type: ignore

import logging
import sys
from traceback import format_exception

from typing import Any, Callable, List, Optional, Sequence

_LVL_D = logging.getLevelName("DEBUG")
_LVL_I = logging.getLevelName("INFO")
_LVL_W = logging.getLevelName("WARNING")
_LVL_E = logging.getLevelName("ERROR")
_LVL_F = logging.getLevelName("FATAL")
_LVL_C = logging.getLevelName("CRITICAL")


class LogManager:
    """Wrapper for python logging module that enables consolidated settings and helper logging/exception handling"""

    def __init__(self, name: str = None, log_lvl: int = _LVL_W, filename: str = None, stderr: bool = True):
        #### specify logger to be root or not depending on source of instantion
        self._logger = logging.getLogger(name)
        #### specify logger generic formatter
        self._formatter = logging.Formatter(
            "%(levelname)s: %(asctime)s %(filename)s:%(lineno)s: %(message)s",
            datefmt="%Y%m%dT%H%M%S",
        )
        #### clear handlers to avoid double logs
        if self._logger.hasHandlers():
            self._logger.handlers.clear()
        #### setup handlers
        handlers: List[Any] = []
        if stderr:
            handlers.append(logging.StreamHandler(sys.stderr))
        if filename is not None:
            handlers.append(logging.FileHandler(filename))
        for handler in handlers:
            handler.setFormatter(self._formatter)
            self._logger.addHandler(handler)
        #### set initial logging level
        self._logger.setLevel(log_lvl)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if type != None:
            if type == SystemExit:
                self.error(f"SystemExit: {value}")
            else:
                self.error(f"Exception occurred:\n{''.join(format_exception(type, value, traceback))}")

    def __getattr__(self, attr: Any) -> Any:
        """Pass unknown attributes to self._logger"""
        return getattr(self._logger, attr)

    def _err_to_str(err: BaseException) -> str:
        return f"{err.__class__.__name__}: {err}"

    def _sys_exit(err: Optional[Exception] = None) -> None:
        """Exit by raising SystemError with <err>.errorno if it exists"""
        try:
            sys.exit(err.errno)
        except AttributeError:
            sys.exit(1)

    def debug(self, msg: Any, *msg_strs, stacklevel: int = 0, **kwargs: Any) -> None:
        """Log <msg>"""
        self._logger.debug(msg, *msg_strs, stacklevel=stacklevel + 2, **kwargs)

    def info(self, msg: Any, *msg_strs, stacklevel: int = 0, **kwargs: Any) -> None:
        """Log <msg>"""
        self._logger.info(msg, *msg_strs, stacklevel=stacklevel + 2, **kwargs)

    def warning(self, msg: Any, *msg_strs, stacklevel: int = 0, **kwargs: Any) -> None:
        """Log <msg>"""
        self._logger.warning(msg, *msg_strs, stacklevel=stacklevel + 2, **kwargs)

    def error(self, msg: Any, *msg_strs, stacklevel: int = 0, **kwargs: Any) -> None:
        """Log <msg>"""
        self._logger.error(msg, *msg_strs, stacklevel=stacklevel + 2, **kwargs)

    def fatal(self, msg: Any, *msg_strs, stacklevel: int = 0, **kwargs: Any) -> None:
        """Log <msg>"""
        self._logger.fatal(msg, *msg_strs, stacklevel=stacklevel + 2, **kwargs)

    def critical(self, msg: Any, *msg_strs, stacklevel: int = 0, **kwargs: Any) -> None:
        """Log <msg>"""
        self._logger.critical(msg, *msg_strs, stacklevel=stacklevel + 2, **kwargs)

    def log(self, level: bool, msg: Any, *msg_strs, stacklevel: int = 0, **kwargs: Any) -> None:
        """Log <msg>"""
        self._logger.log(level, msg, *msg_strs, stacklevel=stacklevel + 3, **kwargs)

    def debug_exit(
        self, err: Optional[Exception] = None, sys_exit: bool = False, stacklevel: int = 0, **kwargs: Any
    ) -> None:
        """Log then throw <err>"""
        self.log_exit(_LVL_D, err, sys_exit=sys_exit, stacklevel=stacklevel, **kwargs)

    def info_exit(
        self, err: Optional[Exception] = None, sys_exit: bool = False, stacklevel: int = 0, **kwargs: Any
    ) -> None:
        """Log then throw <err>"""
        self.log_exit(_LVL_I, err, sys_exit=sys_exit, stacklevel=stacklevel, **kwargs)

    def warning_exit(
        self, err: Optional[Exception] = None, sys_exit: bool = False, stacklevel: int = 0, **kwargs: Any
    ) -> None:
        """Log then throw <err>"""
        self.log_exit(_LVL_W, err, sys_exit=sys_exit, stacklevel=stacklevel, **kwargs)

    def error_exit(
        self, err: Optional[Exception] = None, sys_exit: bool = False, stacklevel: int = 0, **kwargs: Any
    ) -> None:
        """Log then throw <err>"""
        self.log_exit(_LVL_E, err, sys_exit=sys_exit, stacklevel=stacklevel, **kwargs)

    def fatal_exit(
        self, err: Optional[Exception] = None, sys_exit: bool = False, stacklevel: int = 0, **kwargs: Any
    ) -> None:
        """Log then throw <err>"""
        self.log_exit(_LVL_F, err, sys_exit=sys_exit, stacklevel=stacklevel, **kwargs)

    def critical_exit(
        self, err: Optional[Exception] = None, sys_exit: bool = False, stacklevel: int = 0, **kwargs: Any
    ):
        """Log then throw <err>"""
        self.log_exit(_LVL_C, err, sys_exit=sys_exit, stacklevel=stacklevel, **kwargs)

    def log_exit(
        self, level: bool, err: Optional[Exception] = None, sys_exit: bool = False, stacklevel: int = 0, **kwargs: Any
    ):
        """Log then throw <err>"""
        self._logger.log(level, LogManager._err_to_str(err), stacklevel=stacklevel + 3, **kwargs)
        if sys_exit or Exception == None:
            LogManager._sys_exit(err)
        else:
            raise err

    def debug_false(
        self,
        expr: bool,
        msg: Any = None,
        *args: Any,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> None:
        """Log <msg> if <expr> == False"""
        self.log_false(_LVL_D, expr, msg, *args, stacklevel=stacklevel, **kwargs)

    def info_false(
        self,
        expr: bool,
        msg: Any = None,
        *args: Any,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> None:
        """Log <msg> if <expr> == False"""
        self.log_false(_LVL_I, expr, msg, *args, stacklevel=stacklevel, **kwargs)

    def warning_false(
        self,
        expr: bool,
        msg: Any = None,
        *args: Any,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> None:
        """Log <msg> if <expr> == False"""
        self.log_false(_LVL_W, expr, msg, *args, stacklevel=stacklevel, **kwargs)

    def error_false(
        self,
        expr: bool,
        msg: Any = None,
        *args: Any,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> None:
        """Log <msg> if <expr> == False"""
        self.log_false(_LVL_E, expr, msg, *args, stacklevel=stacklevel, **kwargs)

    def fatal_false(
        self,
        expr: bool,
        msg: Any = None,
        *args: Any,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> None:
        """Log <msg> if <expr> == False"""
        self.log_false(_LVL_F, expr, msg, *args, stacklevel=stacklevel, **kwargs)

    def critical_false(
        self,
        expr: bool,
        msg: Any = None,
        *args: Any,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> None:
        """Log <msg> if <expr> == False"""
        self.log_false(_LVL_C, expr, msg, *args, stacklevel=stacklevel, **kwargs)

    def log_false(
        self,
        level: bool,
        expr: bool,
        msg: Any = None,
        *args: Any,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> None:
        """Log and throw <err> if <expr> == False"""
        if msg == None and len(args) != 0:
            err = ValueError("Cannot have <msg>==None and len(<args>)!=0.")
            self._logger.log(level, err, stacklevel=0, **kwargs)
            raise err
        if not expr:
            msg_to_use = msg if msg != None else "Expression was false."
            self._logger.log(level, msg_to_use, *args, stacklevel=stacklevel + 3, **kwargs)

    def debug_assert(
        self,
        expr: bool,
        err: BaseException = None,
        *args: Any,
        sys_exit: bool = False,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> None:
        """Log <msg> and throw <err> if <expr> == False"""
        self.log_assert(_LVL_D, expr, err, *args, sys_exit=sys_exit, stacklevel=stacklevel, **kwargs)

    def info_assert(
        self,
        expr: bool,
        err: BaseException = None,
        *args: Any,
        sys_exit: bool = False,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> None:
        """Log <msg> and throw <err> if <expr> == False"""
        self.log_assert(_LVL_I, expr, err, *args, sys_exit=sys_exit, stacklevel=stacklevel, **kwargs)

    def warning_assert(
        self,
        expr: bool,
        err: BaseException = None,
        *args: Any,
        sys_exit: bool = False,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> None:
        """Log <msg> and throw <err> if <expr> == False"""
        self.log_assert(_LVL_W, expr, err, *args, sys_exit=sys_exit, stacklevel=stacklevel, **kwargs)

    def error_assert(
        self,
        expr: bool,
        err: BaseException = None,
        *args: Any,
        sys_exit: bool = False,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> None:
        """Log <msg> and throw <err> if <expr> == False"""
        self.log_assert(_LVL_E, expr, err, *args, sys_exit=sys_exit, stacklevel=stacklevel, **kwargs)

    def fatal_assert(
        self,
        expr: bool,
        err: BaseException = None,
        *args: Any,
        sys_exit: bool = False,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> None:
        """Log <msg> and throw <err> if <expr> == False"""
        self.log_assert(_LVL_F, expr, err, *args, sys_exit=sys_exit, stacklevel=stacklevel, **kwargs)

    def critical_assert(
        self,
        expr: bool,
        err: BaseException = None,
        *args: Any,
        sys_exit: bool = False,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> None:
        """Log <msg> and throw <err> if <expr> == False"""
        self.log_assert(_LVL_C, expr, err, *args, sys_exit=sys_exit, stacklevel=stacklevel, **kwargs)

    def log_assert(
        self,
        level: bool,
        expr: bool,
        err: BaseException = None,
        *args: Any,
        sys_exit: bool = False,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> None:
        """Log and throw <err> if <expr> == False"""
        if err == None and len(args) != 0:
            err_tmp = ValueError("Cannot have <err>==None and len(<args>)!=0.")
            self._logger.log(level, LogManager._err_to_str(err_tmp), stacklevel=0, **kwargs)
            raise err_tmp
        if not expr:
            if err != None:
                self._logger.log(level, LogManager._err_to_str(err), *args, stacklevel=stacklevel + 3, **kwargs)
                if sys_exit:
                    LogManager._sys_exit(err)
                else:
                    raise err
            else:
                if sys_exit:
                    self._logger.log(level, "SystemExit: <expr> == False.", *args, stacklevel=stacklevel + 3, **kwargs)
                    LogManager._sys_exit(err)
                else:
                    self._logger.log(level, "Exception: <expr> == False.", *args, stacklevel=stacklevel + 3, **kwargs)
                    raise err

    def debug_exc_handle(
        self,
        callable: Callable,
        msg: Any = None,
        *args_log: Any,
        exc: Exception = None,
        excs: Sequence[Exception] = None,
        skip_raise: bool = False,
        sys_exit: bool = False,
        stacklevel: int = 0,
        **kwargs_log: Any,
    ):
        return self.log_exc_handle(
            _LVL_D,
            callable,
            msg,
            *args_log,
            exc=exc,
            excs=excs,
            skip_raise=skip_raise,
            stacklevel=stacklevel,
            sys_exit=sys_exit,
            **kwargs_log,
        )

    def info_exc_handle(
        self,
        callable: Callable,
        msg: Any = None,
        *args_log: Any,
        exc: Exception = None,
        excs: Sequence[Exception] = None,
        skip_raise: bool = False,
        sys_exit: bool = False,
        stacklevel: int = 0,
        **kwargs_log: Any,
    ):
        return self.log_exc_handle(
            _LVL_I,
            callable,
            msg,
            *args_log,
            exc=exc,
            excs=excs,
            skip_raise=skip_raise,
            stacklevel=stacklevel,
            sys_exit=sys_exit,
            **kwargs_log,
        )

    def warning_exc_handle(
        self,
        callable: Callable,
        msg: Any = None,
        *args_log: Any,
        exc: Exception = None,
        excs: Sequence[Exception] = None,
        skip_raise: bool = False,
        sys_exit: bool = False,
        stacklevel: int = 0,
        **kwargs_log: Any,
    ):
        return self.log_exc_handle(
            _LVL_W,
            callable,
            msg,
            *args_log,
            exc=exc,
            excs=excs,
            skip_raise=skip_raise,
            stacklevel=stacklevel,
            sys_exit=sys_exit,
            **kwargs_log,
        )

    def error_exc_handle(
        self,
        callable: Callable,
        msg: Any = None,
        *args_log: Any,
        exc: Exception = None,
        excs: Sequence[Exception] = None,
        skip_raise: bool = False,
        sys_exit: bool = False,
        stacklevel: int = 0,
        **kwargs_log: Any,
    ):
        return self.log_exc_handle(
            _LVL_E,
            callable,
            msg,
            *args_log,
            exc=exc,
            excs=excs,
            skip_raise=skip_raise,
            stacklevel=stacklevel,
            sys_exit=sys_exit,
            **kwargs_log,
        )

    def fatal_exc_handle(
        self,
        callable: Callable,
        msg: Any = None,
        *args_log: Any,
        exc: Exception = None,
        excs: Sequence[Exception] = None,
        skip_raise: bool = False,
        sys_exit: bool = False,
        stacklevel: int = 0,
        **kwargs_log: Any,
    ):
        return self.log_exc_handle(
            _LVL_F,
            callable,
            msg,
            *args_log,
            exc=exc,
            excs=excs,
            skip_raise=skip_raise,
            stacklevel=stacklevel,
            sys_exit=sys_exit,
            **kwargs_log,
        )

    def critical_exc_handle(
        self,
        callable: Callable,
        msg: Any = None,
        *args_log: Any,
        exc: Exception = None,
        excs: Sequence[Exception] = None,
        skip_raise: bool = False,
        sys_exit: bool = False,
        stacklevel: int = 0,
        **kwargs_log: Any,
    ):
        return self.log_exc_handle(
            _LVL_C,
            callable,
            msg,
            *args_log,
            exc=exc,
            excs=excs,
            skip_raise=skip_raise,
            stacklevel=stacklevel,
            sys_exit=sys_exit,
            **kwargs_log,
        )

    def log_exc_handle(
        self,
        level: int,
        callable: Callable,
        msg: Any = None,
        *args_log: Any,
        exc: Exception = None,
        excs: Sequence[Exception] = None,
        skip_raise: bool = False,
        sys_exit: bool = False,
        stacklevel: int = 0,
        **kwargs_log: Any,
    ):
        excs_lst = []
        if exc != None:
            excs_lst.append(exc)
        if excs != None:
            excs_lst += [e for e in excs]

        def _callable_with_log_and_exc_handling(*args, **kwargs: Any) -> None:
            try:
                return callable(*args, **kwargs)
            except tuple(excs_lst) as err:
                if msg != None:
                    self._logger.log(
                        level, msg, *args_log, stacklevel=stacklevel + 2, extra=kwargs_log.get("extra", None)
                    )
                else:
                    self._logger.log(level, err, stacklevel=stacklevel + 2, **kwargs_log)
                if sys_exit:
                    LogManager._sys_exit(err)
                if not skip_raise:
                    raise err
            except Exception as err:
                self._logger.log(
                    _LVL_E,
                    "Unexpected exception below, Traceback may print twice.",
                    *args_log,
                    stacklevel=stacklevel + 2,
                    extra=kwargs_log.get("extra", None),
                )
                self._logger.log(
                    _LVL_E, err, stacklevel=stacklevel + 2, extra=kwargs_log.get("extra", None), exc_info=err
                )
                raise err

        return _callable_with_log_and_exc_handling

    def exception(self, err, stacklevel: int = 0, **kwargs: Any) -> None:
        self._logger.exception(err, stacklevel=stacklevel + 3, **kwargs)
