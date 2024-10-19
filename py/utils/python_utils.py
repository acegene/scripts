import importlib.util
import logging
import os
import platform
import sys
from importlib.machinery import ModuleSpec
from types import ModuleType
from typing import NoReturn

logger = logging.getLogger(__name__)


def get_os() -> str:
    """Returns Darwin, Linux, or Windows; Darwin means Mac."""
    return platform.system()


def is_os_linux() -> bool:
    return get_os() == "Linux"


def is_os_mac() -> bool:
    return get_os() == "Darwin"


def is_os_windows() -> bool:
    return get_os() == "Windows"


def is_python_version_at_least(minimum_python_version, python_version=None, printer=None) -> bool:
    python_version = sys.version_info if python_version is None else python_version
    if python_version < minimum_python_version:
        if printer is not None:
            printer(f"python_version={python_version}; minimum_python_version={minimum_python_version}")
        return False
    return True


def within_a_venv() -> bool:
    return hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and (sys.base_prefix != sys.prefix))


def load_module_from_path(path: str) -> ModuleType:
    module_name = os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(module_name, path)
    if not isinstance(spec, ModuleSpec):
        logger.fatal(f"could not load as module: path={path}")
        raise ImportError(f"could not load as module: path={path}")
    if spec.loader is None:
        logger.fatal(f"could not load as module: path={path}; spec.loader=None")
        raise ImportError(f"could not load as module: path={path}; spec.loader=None")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DummyThrowingModule(ModuleType):
    def __init__(self, module_name: str = "unspecified"):
        self.module_name = module_name

    def __getattr__(self, name) -> NoReturn:
        raise ImportError(f"Module '{self.module_name}' unavailable, attempted getattr({name}).")

    def __call__(self, *args, **kwargs) -> NoReturn:
        raise ImportError(f"Module '{self.module_name}' unavailable. args={args}; kwargs={kwargs}")
