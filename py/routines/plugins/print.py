"""Plugin adding a print job."""

from dataclasses import dataclass

from typing import Any, Dict, Sequence, Tuple

from core import factory


@dataclass
class Print:
    def __init__(self, name, *, kw_name):
        self.name = name
        self.kw_name = kw_name

    def run(self, *args, **kwargs) -> Tuple[Sequence[Any], Dict[str, Any]]:
        print(f"I am {self.name}; of the print job variety with kws={self.kw_name}.")
        if len(args) != 0:
            print(args)
        if len(kwargs) != 0:
            print(kwargs)
        return ([], {})


def register() -> None:
    factory.register("print", Print)
