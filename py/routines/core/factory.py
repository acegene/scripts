"""Factory for creating a game character."""

from typing import Any, Callable, Dict

from core.job import Job

JobCreator = Callable[..., Job]

jobs: Dict[str, JobCreator] = {}


def register(job: str, creator_fn: JobCreator) -> None:
    """Register a job type."""
    jobs[job] = creator_fn


def unregister(job: str) -> None:
    """Unregister a job type."""
    jobs.pop(job, None)


def create(arguments: Dict[str, Any]) -> Job:
    """Create a job of a specific type, given JSON data."""
    try:
        job_creator = jobs[arguments["type"]]
    except KeyError:
        raise ValueError(f"unknown job {arguments['type']!r}") from None

    try:
        return job_creator(*arguments.get("args", []), **arguments.get("kwargs", {}))
    except TypeError as e:
        raise ValueError(f"cannot initialize job {arguments['type']!r}: {e}") from e
