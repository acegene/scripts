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
import logging.config
import logging.handlers
import os
import sys
import traceback
from collections.abc import Callable
from collections.abc import Iterable
from contextlib import contextmanager
from typing import Any
from typing import NoReturn

from utils import path_utils

LVL_D = logging.getLevelName(logging.DEBUG)
LVL_I = logging.getLevelName(logging.INFO)
LVL_W = logging.getLevelName(logging.WARNING)
LVL_E = logging.getLevelName(logging.ERROR)
LVL_F = logging.getLevelName(logging.FATAL)
LVL_C = logging.getLevelName(logging.CRITICAL)

_LOG_CFG_DEFAULT = os.path.join(os.path.dirname(__file__), "log_manager_logging_cfg.json")

ExceptableException = tuple[type[BaseException], ...] | tuple[()] | type[BaseException]
MaybeCatchableExceptions = Iterable[type[BaseException]] | type[BaseException] | None
RaisableException = BaseException | type[BaseException]
MaybeRaisableException = RaisableException | None


def _get_exceptions_tuple(excs: MaybeCatchableExceptions) -> ExceptableException:
    if excs is None:
        return ()
    if isinstance(excs, Iterable):
        if not all(inspect.isclass(exc) and issubclass(exc, BaseException) for exc in excs):
            raise ValueError
        return tuple(excs)
    if inspect.isclass(excs) and issubclass(excs, BaseException):
        return excs
    raise ValueError


def _cfg_replace_w_global_vars(cfg, globals_: dict):
    if isinstance(cfg, dict):
        for key, value in cfg.items():
            if isinstance(value, dict):
                _cfg_replace_w_global_vars(value, globals_)
            elif isinstance(value, list):
                for idx, item in enumerate(value):
                    value[idx] = _cfg_replace_w_global_vars(item, globals_)
            elif isinstance(value, str) and value.startswith("global_var://"):
                global_var_name = value[len("global_var://") :]
                global_var_value = globals_.get(global_var_name)
                if global_var_value is not None:
                    cfg[key] = global_var_value
    return cfg


def _get_cfg_file_as_cfg_dict(cfg_file: str | None, globals_: dict | None = None):
    with path_utils.open_unix_safely(_LOG_CFG_DEFAULT if (cfg_file is None or cfg_file == "") else cfg_file) as f:
        if globals_ is None:
            return json.load(f)
        return _cfg_replace_w_global_vars(json.load(f), globals_)


def _full_stack(stacklevel: int = 0, include_exc: bool = True):
    """Get full calling stack of calling function as a string.

    https://stackoverflow.com/a/16589622
    """

    exc = sys.exc_info()[0]
    stack = traceback.extract_stack()[: -(1 + stacklevel)]  # last one would be _full_stack()
    if exc is not None:  # i.e. an exception is present
        del stack[-1]  # remove call of _full_stack, the printed exception
    trc = "Traceback (most recent call last):\n"
    stackstr = trc + "".join(traceback.format_list(stack))
    if include_exc is True and exc is not None:
        tb_str = traceback.format_exc()
        stackstr += tb_str[len(trc) :] if tb_str.startswith(trc) else ""
    return stackstr.rstrip("\n")


## TODO: unused
@contextmanager
def _disable_raise_exception_traceback_print():
    """All traceback information is suppressed and only the exception type and value are printed.

    https://stackoverflow.com/a/63657211
    """
    default_value = getattr(sys, "tracebacklimit", 1000)
    sys.tracebacklimit = 0
    yield
    sys.tracebacklimit = default_value  # revert changes


@contextmanager
def _disable_raise_exception_print():
    """Suppresses printing of the exception details (type, value, traceback)"""
    original_hook = sys.excepthook

    def custom_excepthook(_type, _value, _traceback):
        pass  # print(value) # to print only the exception msg

    sys.excepthook = custom_excepthook
    yield
    sys.excepthook = original_hook  # revert changes


def get_default_log_paths(file_path: str) -> tuple[str, str]:
    log_base = os.path.splitext(os.path.basename(file_path))[0]
    log_file_path = f'{os.environ["TEMP"]}/{log_base}.log' if os.name == "nt" else f"/tmp/{log_base}.log"
    log_cfg_default = os.path.join(os.path.dirname(os.path.realpath(file_path)), f"{log_base}_logging_cfg.json")
    return log_file_path, log_cfg_default


class LFFileHandler(logging.handlers.RotatingFileHandler):
    def _open(self):
        return path_utils.open_unix_safely(self.baseFilename, self.mode, encoding=self.encoding)


class UTCFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.datetime.fromtimestamp(record.created, tz=datetime.timezone.utc)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()


class LogManager:
    """Wrapper for python logging module that enables consolidated settings and helper logging/exception handling."""

    # pylint: disable=[too-many-arguments, too-many-public-methods]

    def __init__(self, name: str | None = None):
        ## specify logger to be root or not depending on source of instantiation
        self._logger = logging.getLogger(name)

    def add_stderr_hdlr(self, formatter=None, datefmt="%y%m%dT%H%M%S%z"):
        formatter = LogManager.make_default_formatter(datefmt) if formatter is None else formatter
        std_err_handler = logging.StreamHandler(sys.stderr)
        std_err_handler.setFormatter(formatter)
        self._logger.addHandler(std_err_handler)

    def __enter__(self):
        return self

    def __exit__(self, type_, value, _tb):
        if type_ is not None:
            self.error("%s", f"\n{_full_stack()}")

    def __getattr__(self, attr: Any) -> Any:
        """Pass unknown attributes to self._logger."""
        return getattr(self._logger, attr)

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
        print_exc: bool | None = None,
        raise_exc: MaybeRaisableException = None,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> None:
        """Log <msg> and throw <exc_to_log> if <expr_result> == False."""
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
        print_exc: bool | None = None,
        raise_exc: MaybeRaisableException = None,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> None:
        """Log <msg> and throw <exc_to_log> if <expr_result> == False."""
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
        print_exc: bool | None = None,
        raise_exc: MaybeRaisableException = None,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> None:
        """Log <msg> and throw <exc_to_log> if <expr_result> == False."""
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
        print_exc: bool | None = None,
        raise_exc: MaybeRaisableException = None,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> None:
        """Log <msg> and throw <exc_to_log> if <expr_result> == False."""
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
        print_exc: bool | None = None,
        raise_exc: MaybeRaisableException = None,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> None:
        """Log <msg> and throw <exc_to_log> if <expr_result> == False."""
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
        print_exc: bool | None = None,
        raise_exc: MaybeRaisableException = None,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> None:
        """Log <msg> and throw <exc_to_log> if <expr_result> == False."""
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
        print_exc: bool | None = None,
        raise_exc: MaybeRaisableException = None,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> None:
        """Log and throw <exc_to_log> if <expr_result> == False."""
        if not expr_result:
            tb_str = f"\n{_full_stack(stacklevel+1)}" if log_exc else ""
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
                    with _disable_raise_exception_print():
                        raise AssertionError() if raise_exc is None else raise_exc
                raise AssertionError() if raise_exc is None else raise_exc
            self._logger.log(
                level,
                msg,
                LogManager._err_to_str(exc_to_log),
                *msg_objs,
                tb_str,
                stacklevel=stacklevel + 2,
                **kwargs,
            )
            if print_exc is False or (print_exc is None and log_exc is True):
                with _disable_raise_exception_print():
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
        print_exc: bool | None = None,
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
        print_exc: bool | None = None,
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
        print_exc: bool | None = None,
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
        print_exc: bool | None = None,
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
        print_exc: bool | None = None,
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
        print_exc: bool | None = None,
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
        print_exc: bool | None = None,
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
                tb_str = f"\n{_full_stack(stacklevel)}" if log_exc else ""
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
                        with _disable_raise_exception_print():
                            raise raise_exc from e  # TODO: should this have a 'from e', does this matter in a with?
                    raise raise_exc from e  # TODO: should this have a 'from e'
                if skip_hndld_excs:
                    return None
                if print_exc is False or (print_exc is None and log_exc is True):
                    with _disable_raise_exception_print():
                        raise e
                raise e
            except BaseException as e:  # pylint: disable=broad-exception-caught
                tb_str = _full_stack(stacklevel)
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
                with _disable_raise_exception_print():
                    raise e if raise_unhdld_exc is None else raise_unhdld_exc

        return _callable_with_log_and_exc_handling

    def debug_raise(
        self,
        exc_to_log: RaisableException,
        msg: Any = None,
        /,
        *msg_objs: Any,
        log_exc: bool = True,
        print_exc: bool | None = None,
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
        print_exc: bool | None = None,
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
        print_exc: bool | None = None,
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
        print_exc: bool | None = None,
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
        print_exc: bool | None = None,
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
        print_exc: bool | None = None,
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
        print_exc: bool | None = None,
        raise_exc: MaybeRaisableException = None,
        stacklevel: int = 0,
        **kwargs: Any,
    ) -> NoReturn:
        """Log then throw <err>"""
        msg = "%s" * (len(msg_objs) + 2) if msg is None else msg  # + 2 from tb_str and exc_to_log
        tb_str = f"\n{_full_stack(stacklevel + 1)}" if log_exc else ""
        self._logger.log(
            level,
            msg,
            LogManager._err_to_str(exc_to_log),
            *msg_objs,
            tb_str,
            stacklevel=stacklevel + 2,
            **kwargs,
        )
        if print_exc is False or (print_exc is None and log_exc is True):
            with _disable_raise_exception_print():
                raise exc_to_log if raise_exc is None else raise_exc
        raise exc_to_log if raise_exc is None else raise_exc

    def exception(self, msg: Any, *msg_objs: Any, stacklevel: int = 0, **kwargs: Any) -> None:
        self._logger.exception(msg, *msg_objs, stacklevel=stacklevel + 3, **kwargs)

    @staticmethod
    def _err_to_str(err: RaisableException) -> str:
        return f"{err.__class__.__name__}: {err}"

    @staticmethod
    def make_default_formatter(datefmt: str = "%y%m%dT%H%M%S%z") -> logging.Formatter:
        return logging.Formatter(
            "%(asctime)s %(levelname)s: %(module)s:L%(lineno)d: %(message)s",
            datefmt=datefmt,
        )

    @staticmethod
    def set_cfg(cfg_dict: dict) -> None:
        logging.config.dictConfig(cfg_dict)

    @staticmethod
    def set_cfg_from_cfg_file(cfg_file: str | None, globals_=None) -> None:
        logging.config.dictConfig(_get_cfg_file_as_cfg_dict(cfg_file, globals_=globals_))

    @staticmethod
    def setup_logger(
        globals_: dict,
        /,
        name: str | None = None,
        log_cfg: str | None = None,
        log_file: str | None = None,
        log_file_var_name: str = "_LOG_FILE_PATH",
        logger_var_name: str = "logger",
    ) -> None:
        if name is None:
            stack = inspect.stack()
            caller_frame = stack[1]
            name = caller_frame[0].f_globals["__name__"]

        if log_file is not None:
            globals_[log_file_var_name] = log_file
        LogManager.set_cfg_from_cfg_file(log_cfg, globals_)

        globals_[logger_var_name] = LogManager(name)
