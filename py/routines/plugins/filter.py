"""Plugin adding a filter job."""

from dataclasses import dataclass

from typing import Any, Dict, Sequence, Tuple

from core import factory
from utils import filter_utils


@dataclass
class Filter:
    def __init__(self, *args):
        self.args = args

    def run(self, *args, **kwargs) -> Tuple[Sequence[Any], Dict[str, Any]]:
        del kwargs
        filter_result = filter_utils.main(self.args, *args)
        return (filter_result, {})


def register() -> None:
    factory.register("filter", Filter)
