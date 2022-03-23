"""Represents a basic job."""

from typing import Any, Dict, Protocol, Sequence, Tuple

JobReturnType = Tuple[Sequence[Any], Dict[str, Any]]


class Job(Protocol):
    """Basic representation of a job."""

    def run(self, *args, **kwargs) -> JobReturnType:
        """Execute job and return result."""
