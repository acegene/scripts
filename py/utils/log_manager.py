# Python module for the class 'LogManager'
#
# usage
#   * from utils.log_manager import LogManager
#   * logger = LogManager(__name__)
#
# author: acegene <acegene22@gmail.com>

import datetime
import inspect
import json
import logging
import logging.config
import logging.handlers
import os
import sys
import traceback

from contextlib import contextmanager
from typing import Any, Callable, Iterable, NoReturn, Optional, Tuple, Type, Union

LVL_D = logging.getLevelName("DEBUG")
LVL_I = logging.getLevelName("INFO")
LVL_W = logging.getLevelName("WARNING")
LVL_E = logging.getLevelName("ERROR")
LVL_F = logging.getLevelName("FATAL")
LVL_C = logging.getLevelName("CRITICAL")

_LOG_MANAGER_DEFAULT_LOGGING_CFG = os.path.join(os.path.dirname(__file__), "log-manager-logging-cfg.json")

ExceptableException = Union[Tuple[Type[BaseException], ...], Tuple[()], Type[BaseException]]
MaybeCatchableExceptions = Optional[Union[Iterable[Type[BaseException]], Type[BaseException]]]
RaisableException = Union[BaseException, Type[BaseException]]
MaybeRaisableException = Optional[RaisableException]


def _get_exceptions_tuple(excs: MaybeCatchableExceptions) -> ExceptableException:
    if excs is None:
        return tuple()
    if isinstance(excs, Iterable):
        if not all(inspect.isclass(exc) and issubclass(exc, BaseException) for exc in excs):
            raise ValueError
        return tuple(excs)
    if inspect.isclass(excs) and issubclass(excs, BaseException):
        return excs
    raise ValueError


def cfg_replace_w_global_vars(cfg, globals_):
    if isinstance(cfg, dict):
        for key, value in cfg.items():
            if isinstance(value, dict):
                cfg_replace_w_global_vars(value, globals_)
            elif isinstance(value, list):
                for idx, item in enumerate(value):
                    value[idx] = cfg_replace_w_global_vars(item, globals_)
            elif isinstance(value, str) and value.startswith("global_var://"):
                global_var_name = value[len("global_var://") :]
                global_var_value = globals_.get(global_var_name)
                if global_var_value is not None:
                    cfg[key] = global_var_value
    return cfg


def get_cfg_file_as_cfg_dict(cfg_file, globals_=None):
    with open(_LOG_MANAGER_DEFAULT_LOGGING_CFG if cfg_file is None else cfg_file, encoding="utf-8") as f:
        if globals_ is None:
            return json.load(f)
        return cfg_replace_w_global_vars(json.load(f), globals_)


def full_stack(stacklevel=0, include_exc=True):
    """
    Get full calling stack of calling function as a string

    https://stackoverflow.com/a/16589622
    """

    exc = sys.exc_info()[0]
    stack = traceback.extract_stack()[: -(1 + stacklevel)]  # last one would be full_stack()
    if exc is not None:  # i.e. an exception is present
        del stack[-1]  # remove call of full_stack, the printed exception
    trc = "Traceback (most recent call last):\n"
    stackstr = trc + "".join(traceback.format_list(stack))
    if include_exc is True and exc is not None:
        tb_str = traceback.format_exc()
        stackstr += tb_str[len(trc) :] if tb_str.startswith(trc) else ""
    return stackstr.rstrip("\n")


@contextmanager
def disable_raise_exception_traceback_print():
    """
    All traceback information is suppressed and only the exception type and value are printed

    https://stackoverflow.com/a/63657211
    """
    default_value = getattr(sys, "tracebacklimit", 1000)
    sys.tracebacklimit = 0
    yield
    sys.tracebacklimit = default_value  # revert changes


@contextmanager
def disable_raise_exception_print():
    """
    Suppresses printing of the exception details (type, value, traceback)
    """
    original_hook = sys.excepthook

    def custom_excepthook(_type, _value, _traceback):
        pass  # print(value) # to print only the exception msg

    sys.excepthook = custom_excepthook
    yield
    sys.excepthook = original_hook  # revert changes


class LFFileHandler(logging.handlers.RotatingFileHandler):
    def _open(self):
        return open(self.baseFilename, self.mode, encoding=self.encoding, newline="\n")


class UTCFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.datetime.fromtimestamp(record.created, tz=datetime.timezone.utc)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()


class LogManager:
    """Wrapper for python logging module that enables consolidated settings and helper logging/exception handling"""

    # pylint: disable=[too-many-arguments, too-many-public-methods]

    def __init__(self, name: Optional[str] = None, cfg_dict=None):
        ## specify logger to be root or not depending on source of instantion
        self._logger = logging.getLogger(name)
        if cfg_dict is None:
            formatter = logging.Formatter(
                "%(asctime)s %(levelname)s: %(module)s:L%(lineno)d: %(message)s",
                datefmt="%y%m%dT%H%M%S%z",
            )
            #### clear handlers to avoid double logs
            # if self._logger.hasHandlers():
            #     self._logger.handlers.clear()
            #### setup handlers
            std_err_handler = logging.StreamHandler(sys.stderr)
            std_err_handler.setFormatter(formatter)
            self._logger.addHandler(std_err_handler)
        else:
            logging.config.dictConfig(cfg_dict)

    def __enter__(self):
        return self

    def __exit__(self, type_, value, _tb):
        if type_ is not None:
            self.error("%s", f"\n{full_stack()}")

    def __getattr__(self, attr: Any) -> Any:
        """Pass unknown attributes to self._logger"""
        return getattr(self._logger, attr)

    @staticmethod
    def _err_to_str(err: RaisableException) -> str:
        return f"{err.__class__.__name__}: {err}"

    def debug(self, msg: Any, *msg_objs, stacklevel: int = 0, **kwargs: Any) -> None:
        """Log <msg>"""
        self._logger.debug(msg, *msg_objs, stacklevel=stacklevel + 2, **kwargs)

    def info(self, msg: Any, *msg_objs, stacklevel: int = 0, **kwargs: Any) -> None:
        """Log <msg>"""
        self._logger.info(msg, *msg_objs, stacklevel=stacklevel + 2, **kwargs)

    def warning(self, msg: Any, *msg_objs, stacklevel: int = 0, **kwargs: Any) -> None:
        """Log <msg>"""
        self._logger.warning(msg, *msg_objs, stacklevel=stacklevel + 2, **kwargs)

    def error(self, msg: Any, *msg_objs, stacklevel: int = 0, **kwargs: Any) -> None:
        """Log <msg>"""
        self._logger.error(msg, *msg_objs, stacklevel=stacklevel + 2, **kwargs)

    def fatal(self, msg: Any, *msg_objs, stacklevel: int = 0, **kwargs: Any) -> None:
        """Log <msg>"""
        self._logger.fatal(msg, *msg_objs, stacklevel=stacklevel + 2, **kwargs)

    def critical(self, msg: Any, *msg_objs, stacklevel: int = 0, **kwargs: Any) -> None:
        """Log <msg>"""
        self._logger.critical(msg, *msg_objs, stacklevel=stacklevel + 2, **kwargs)

    def log(self, level: bool, msg: Any, *msg_objs, stacklevel: int = 0, **kwargs: Any) -> None:
        """Log <msg>"""
        self._logger.log(level, msg, *msg_objs, stacklevel=stacklevel + 2, **kwargs)

    def debug_assert(
        self,
        expr_result: bool,
        exc_to_log: MaybeRaisableException = None,
        msg: Any = None,
        /,
        *msg_objs: Any,
        log_exc: bool = True,
        print_exc: Optional[bool] = None,
        raise_exc: MaybeRaisableException = None,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> None:
        """Log <msg> and throw <exc_to_log> if <expr_result> == False"""
        self.log_assert(
            LVL_D,
            expr_result,
            exc_to_log,
            msg,
            *msg_objs,
            log_exc=log_exc,
            print_exc=print_exc,
            raise_exc=raise_exc,
            stacklevel=stacklevel + 1,
            **kwargs,
        )

    def info_assert(
        self,
        expr_result: bool,
        exc_to_log: MaybeRaisableException = None,
        msg: Any = None,
        /,
        *msg_objs: Any,
        log_exc: bool = True,
        print_exc: Optional[bool] = None,
        raise_exc: MaybeRaisableException = None,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> None:
        """Log <msg> and throw <exc_to_log> if <expr_result> == False"""
        self.log_assert(
            LVL_I,
            expr_result,
            exc_to_log,
            msg,
            *msg_objs,
            log_exc=log_exc,
            print_exc=print_exc,
            raise_exc=raise_exc,
            stacklevel=stacklevel + 1,
            **kwargs,
        )

    def warning_assert(
        self,
        expr_result: bool,
        exc_to_log: MaybeRaisableException = None,
        msg: Any = None,
        /,
        *msg_objs: Any,
        log_exc: bool = True,
        print_exc: Optional[bool] = None,
        raise_exc: MaybeRaisableException = None,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> None:
        """Log <msg> and throw <exc_to_log> if <expr_result> == False"""
        self.log_assert(
            LVL_W,
            expr_result,
            exc_to_log,
            msg,
            *msg_objs,
            log_exc=log_exc,
            print_exc=print_exc,
            raise_exc=raise_exc,
            stacklevel=stacklevel + 1,
            **kwargs,
        )

    def error_assert(
        self,
        expr_result: bool,
        exc_to_log: MaybeRaisableException = None,
        msg: Any = None,
        /,
        *msg_objs: Any,
        log_exc: bool = True,
        print_exc: Optional[bool] = None,
        raise_exc: MaybeRaisableException = None,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> None:
        """Log <msg> and throw <exc_to_log> if <expr_result> == False"""
        self.log_assert(
            LVL_E,
            expr_result,
            exc_to_log,
            msg,
            *msg_objs,
            log_exc=log_exc,
            print_exc=print_exc,
            raise_exc=raise_exc,
            stacklevel=stacklevel + 1,
            **kwargs,
        )

    def fatal_assert(
        self,
        expr_result: bool,
        exc_to_log: MaybeRaisableException = None,
        msg: Any = None,
        /,
        *msg_objs: Any,
        log_exc: bool = True,
        print_exc: Optional[bool] = None,
        raise_exc: MaybeRaisableException = None,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> None:
        """Log <msg> and throw <exc_to_log> if <expr_result> == False"""
        self.log_assert(
            LVL_F,
            expr_result,
            exc_to_log,
            msg,
            *msg_objs,
            log_exc=log_exc,
            print_exc=print_exc,
            raise_exc=raise_exc,
            stacklevel=stacklevel + 1,
            **kwargs,
        )

    def critical_assert(
        self,
        expr_result: bool,
        exc_to_log: MaybeRaisableException = None,
        msg: Any = None,
        /,
        *msg_objs: Any,
        log_exc: bool = True,
        print_exc: Optional[bool] = None,
        raise_exc: MaybeRaisableException = None,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> None:
        """Log <msg> and throw <exc_to_log> if <expr_result> == False"""
        self.log_assert(
            LVL_C,
            expr_result,
            exc_to_log,
            msg,
            *msg_objs,
            log_exc=log_exc,
            print_exc=print_exc,
            raise_exc=raise_exc,
            stacklevel=stacklevel + 1,
            **kwargs,
        )

    def log_assert(
        self,
        level: bool,
        expr_result: bool,
        exc_to_log: MaybeRaisableException = None,
        msg: Any = None,
        /,
        *msg_objs: Any,
        log_exc: bool = True,
        print_exc: Optional[bool] = None,
        raise_exc: MaybeRaisableException = None,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> None:
        """Log and throw <exc_to_log> if <expr_result> == False"""
        if not expr_result:
            tb_str = f"\n{full_stack(stacklevel+1)}" if log_exc else ""
            msg = "%s" * (len(msg_objs) + 2) if msg is None else msg  # + 2 from tb_str and exc_to_log
            if exc_to_log is None:
                self._logger.log(
                    level,
                    msg,
                    "AssertionError: <expr_result> == False",
                    *msg_objs,
                    tb_str,
                    stacklevel=stacklevel + 2,
                    **kwargs,
                )
                if print_exc is False or (print_exc is None and log_exc is True):
                    with disable_raise_exception_print():
                        raise AssertionError() if raise_exc is None else raise_exc
                raise AssertionError() if raise_exc is None else raise_exc
            self._logger.log(
                level, msg, LogManager._err_to_str(exc_to_log), *msg_objs, tb_str, stacklevel=stacklevel + 2, **kwargs
            )
            if print_exc is False or (print_exc is None and log_exc is True):
                with disable_raise_exception_print():
                    raise exc_to_log if raise_exc is None else raise_exc
            raise exc_to_log if raise_exc is None else raise_exc

    def debug_make_excs_hdlr(
        self,
        callable_: Callable,
        msg: Any = None,
        /,
        *msg_objs: Any,
        catch_excs: MaybeCatchableExceptions = None,
        log_exc: bool = True,
        msg_unhdld: Any = None,
        print_exc: Optional[bool] = None,
        raise_exc: MaybeRaisableException = None,
        raise_unhdld_exc: MaybeRaisableException = None,
        skip_hndld_excs: bool = True,
        stacklevel: int = 0,
        **kwargs_log: Any,
    ):
        return self.log_make_excs_hdlr(
            LVL_D,
            callable_,
            msg,
            *msg_objs,
            catch_excs=catch_excs,
            log_exc=log_exc,
            msg_unhdld=msg_unhdld,
            print_exc=print_exc,
            raise_exc=raise_exc,
            raise_unhdld_exc=raise_unhdld_exc,
            skip_hndld_excs=skip_hndld_excs,
            stacklevel=stacklevel,
            **kwargs_log,
        )

    def info_make_excs_hdlr(
        self,
        callable_: Callable,
        msg: Any = None,
        /,
        *msg_objs: Any,
        catch_excs: MaybeCatchableExceptions = None,
        log_exc: bool = True,
        msg_unhdld: Any = None,
        print_exc: Optional[bool] = None,
        raise_exc: MaybeRaisableException = None,
        raise_unhdld_exc: MaybeRaisableException = None,
        skip_hndld_excs: bool = True,
        stacklevel: int = 0,
        **kwargs_log: Any,
    ):
        return self.log_make_excs_hdlr(
            LVL_I,
            callable_,
            msg,
            *msg_objs,
            catch_excs=catch_excs,
            log_exc=log_exc,
            msg_unhdld=msg_unhdld,
            print_exc=print_exc,
            raise_exc=raise_exc,
            raise_unhdld_exc=raise_unhdld_exc,
            skip_hndld_excs=skip_hndld_excs,
            stacklevel=stacklevel,
            **kwargs_log,
        )

    def warning_make_excs_hdlr(
        self,
        callable_: Callable,
        msg: Any = None,
        /,
        *msg_objs: Any,
        catch_excs: MaybeCatchableExceptions = None,
        log_exc: bool = True,
        msg_unhdld: Any = None,
        print_exc: Optional[bool] = None,
        raise_exc: MaybeRaisableException = None,
        raise_unhdld_exc: MaybeRaisableException = None,
        skip_hndld_excs: bool = True,
        stacklevel: int = 0,
        **kwargs_log: Any,
    ):
        return self.log_make_excs_hdlr(
            LVL_W,
            callable_,
            msg,
            *msg_objs,
            catch_excs=catch_excs,
            log_exc=log_exc,
            msg_unhdld=msg_unhdld,
            print_exc=print_exc,
            raise_exc=raise_exc,
            raise_unhdld_exc=raise_unhdld_exc,
            skip_hndld_excs=skip_hndld_excs,
            stacklevel=stacklevel,
            **kwargs_log,
        )

    def error_make_excs_hdlr(
        self,
        callable_: Callable,
        msg: Any = None,
        /,
        *msg_objs: Any,
        catch_excs: MaybeCatchableExceptions = None,
        log_exc: bool = True,
        msg_unhdld: Any = None,
        print_exc: Optional[bool] = None,
        raise_exc: MaybeRaisableException = None,
        raise_unhdld_exc: MaybeRaisableException = None,
        skip_hndld_excs: bool = True,
        stacklevel: int = 0,
        **kwargs_log: Any,
    ):
        return self.log_make_excs_hdlr(
            LVL_E,
            callable_,
            msg,
            *msg_objs,
            catch_excs=catch_excs,
            log_exc=log_exc,
            msg_unhdld=msg_unhdld,
            print_exc=print_exc,
            raise_exc=raise_exc,
            raise_unhdld_exc=raise_unhdld_exc,
            skip_hndld_excs=skip_hndld_excs,
            stacklevel=stacklevel,
            **kwargs_log,
        )

    def fatal_make_excs_hdlr(
        self,
        callable_: Callable,
        msg: Any = None,
        /,
        *msg_objs: Any,
        catch_excs: MaybeCatchableExceptions = None,
        log_exc: bool = True,
        msg_unhdld: Any = None,
        print_exc: Optional[bool] = None,
        raise_exc: MaybeRaisableException = None,
        raise_unhdld_exc: MaybeRaisableException = None,
        skip_hndld_excs: bool = True,
        stacklevel: int = 0,
        **kwargs_log: Any,
    ):
        return self.log_make_excs_hdlr(
            LVL_F,
            callable_,
            msg,
            *msg_objs,
            catch_excs=catch_excs,
            log_exc=log_exc,
            msg_unhdld=msg_unhdld,
            print_exc=print_exc,
            raise_exc=raise_exc,
            raise_unhdld_exc=raise_unhdld_exc,
            skip_hndld_excs=skip_hndld_excs,
            stacklevel=stacklevel,
            **kwargs_log,
        )

    def critical_make_excs_hdlr(
        self,
        callable_: Callable,
        msg: Any = None,
        /,
        *msg_objs: Any,
        catch_excs: MaybeCatchableExceptions = None,
        log_exc: bool = True,
        msg_unhdld: Any = None,
        print_exc: Optional[bool] = None,
        raise_exc: MaybeRaisableException = None,
        raise_unhdld_exc: MaybeRaisableException = None,
        skip_hndld_excs: bool = True,
        stacklevel: int = 0,
        **kwargs_log: Any,
    ):
        return self.log_make_excs_hdlr(
            LVL_C,
            callable_,
            msg,
            *msg_objs,
            catch_excs=catch_excs,
            log_exc=log_exc,
            msg_unhdld=msg_unhdld,
            print_exc=print_exc,
            raise_exc=raise_exc,
            raise_unhdld_exc=raise_unhdld_exc,
            skip_hndld_excs=skip_hndld_excs,
            stacklevel=stacklevel,
            **kwargs_log,
        )

    def log_make_excs_hdlr(
        self,
        level: int,
        callable_: Callable,
        msg: Any = None,
        /,
        *msg_objs: Any,
        catch_excs: MaybeCatchableExceptions = None,
        log_exc: bool = True,
        msg_unhdld: Any = None,
        print_exc: Optional[bool] = None,
        raise_exc: MaybeRaisableException = None,
        raise_unhdld_exc: MaybeRaisableException = None,
        skip_hndld_excs: bool = True,
        stacklevel: int = 0,
        **kwargs_log: Any,
    ):
        msg = "%s" * (len(msg_objs) + 2) if msg is None else msg  # + 2 from tb_str and exc

        def _callable_with_log_and_exc_handling(*args: Any, **kwargs: Any) -> Any:
            try:
                return callable_(*args, **kwargs)
            except _get_exceptions_tuple(catch_excs) as e:  # pylint: disable=[catching-non-exception]
                tb_str = f"\n{full_stack(stacklevel)}" if log_exc else ""
                self._logger.log(
                    level,
                    msg,
                    LogManager._err_to_str(e),
                    *msg_objs,
                    tb_str,
                    stacklevel=stacklevel + 2,
                    **kwargs_log,
                    # extra=kwargs_log.get("extra", None), # TODO: is there a reason this instead of **kwargs_log
                )
                if raise_exc is not None:
                    if print_exc is False or (print_exc is None and log_exc is True):
                        with disable_raise_exception_print():
                            raise raise_exc from e  # TODO: should this have a 'from e', does this matter in a with?
                    raise raise_exc from e  # TODO: should this have a 'from e'
                if skip_hndld_excs:
                    return None
                if print_exc is False or (print_exc is None and log_exc is True):
                    with disable_raise_exception_print():
                        raise e
                raise e
            except BaseException as e:  # pylint: disable=broad-exception-caught
                tb_str = full_stack(stacklevel)
                self._logger.log(
                    LVL_E,
                    f"Unhandled Exception encountered: {msg}" if msg_unhdld is None else msg_unhdld,
                    LogManager._err_to_str(e),
                    *msg_objs,
                    tb_str,
                    stacklevel=stacklevel + 2,
                    **kwargs_log,
                    # extra=kwargs_log.get("extra", None), # TODO: is there a reason this instead of **kwargs_log
                )
                with disable_raise_exception_print():
                    raise e if raise_unhdld_exc is None else raise_unhdld_exc

        return _callable_with_log_and_exc_handling

    def debug_raise(
        self,
        exc_to_log: RaisableException,
        msg: Any = None,
        /,
        *msg_objs: Any,
        log_exc: bool = True,
        print_exc: Optional[bool] = None,
        raise_exc: MaybeRaisableException = None,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> NoReturn:
        """Log then throw <err>"""
        self.log_raise(
            LVL_D,
            exc_to_log,
            msg,
            *msg_objs,
            log_exc=log_exc,
            print_exc=print_exc,
            raise_exc=raise_exc,
            stacklevel=stacklevel + 1,
            **kwargs,
        )

    def info_raise(
        self,
        exc_to_log: RaisableException,
        msg: Any = None,
        /,
        *msg_objs: Any,
        log_exc: bool = True,
        print_exc: Optional[bool] = None,
        raise_exc: MaybeRaisableException = None,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> NoReturn:
        """Log then throw <err>"""
        self.log_raise(
            LVL_I,
            exc_to_log,
            msg,
            *msg_objs,
            log_exc=log_exc,
            print_exc=print_exc,
            raise_exc=raise_exc,
            stacklevel=stacklevel + 1,
            **kwargs,
        )

    def warning_raise(
        self,
        exc_to_log: RaisableException,
        msg: Any = None,
        /,
        *msg_objs: Any,
        log_exc: bool = True,
        print_exc: Optional[bool] = None,
        raise_exc: MaybeRaisableException = None,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> NoReturn:
        """Log then throw <err>"""
        self.log_raise(
            LVL_W,
            exc_to_log,
            msg,
            *msg_objs,
            log_exc=log_exc,
            print_exc=print_exc,
            raise_exc=raise_exc,
            stacklevel=stacklevel + 1,
            **kwargs,
        )

    def error_raise(
        self,
        exc_to_log: RaisableException,
        msg: Any = None,
        /,
        *msg_objs: Any,
        log_exc: bool = True,
        print_exc: Optional[bool] = None,
        raise_exc: MaybeRaisableException = None,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> NoReturn:
        """Log then throw <err>"""
        self.log_raise(
            LVL_E,
            exc_to_log,
            msg,
            *msg_objs,
            log_exc=log_exc,
            print_exc=print_exc,
            raise_exc=raise_exc,
            stacklevel=stacklevel + 1,
            **kwargs,
        )

    def fatal_raise(
        self,
        exc_to_log: RaisableException,
        msg: Any = None,
        /,
        *msg_objs: Any,
        log_exc: bool = True,
        print_exc: Optional[bool] = None,
        raise_exc: MaybeRaisableException = None,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> NoReturn:
        """Log then throw <err>"""
        self.log_raise(
            LVL_F,
            exc_to_log,
            msg,
            *msg_objs,
            log_exc=log_exc,
            print_exc=print_exc,
            raise_exc=raise_exc,
            stacklevel=stacklevel + 1,
            **kwargs,
        )

    def critical_raise(
        self,
        exc_to_log: RaisableException,
        msg: Any = None,
        /,
        *msg_objs: Any,
        log_exc: bool = True,
        print_exc: Optional[bool] = None,
        raise_exc: MaybeRaisableException = None,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> NoReturn:
        """Log then throw <err>"""
        self.log_raise(
            LVL_C,
            exc_to_log,
            msg,
            *msg_objs,
            log_exc=log_exc,
            print_exc=print_exc,
            raise_exc=raise_exc,
            stacklevel=stacklevel + 1,
            **kwargs,
        )

    def log_raise(
        self,
        level: bool,
        exc_to_log: RaisableException,
        msg: Any = None,
        /,
        *msg_objs: Any,
        log_exc: bool = True,
        print_exc: Optional[bool] = None,
        raise_exc: MaybeRaisableException = None,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> NoReturn:
        """Log then throw <err>"""
        msg = "%s" * (len(msg_objs) + 2) if msg is None else msg  # + 2 from tb_str and exc_to_log
        tb_str = f"\n{full_stack(stacklevel + 1)}" if log_exc else ""
        self._logger.log(
            level, msg, LogManager._err_to_str(exc_to_log), *msg_objs, tb_str, stacklevel=stacklevel + 2, **kwargs
        )
        if print_exc is False or (print_exc is None and log_exc is True):
            with disable_raise_exception_print():
                raise exc_to_log if raise_exc is None else raise_exc
        raise exc_to_log if raise_exc is None else raise_exc

    def exception(self, msg: Any, *msg_objs: Any, stacklevel: int = 0, **kwargs: Any) -> None:
        self._logger.exception(msg, *msg_objs, stacklevel=stacklevel + 3, **kwargs)
