import json

from typing import Any, Dict, Sequence

from core import factory, loader

# jobs = []

# for job in jobs:
#     for task in job.tasks:
#         pass


def main() -> None:
    """Create jobs from a file containg a level definition."""

    # # register a couple of character types
    # factory.register("sorcerer", Sorcerer)
    # factory.register("wizard", Wizard)
    # factory.register("witcher", Witcher)

    # read data from a JSON file
    with open("routines.json", encoding="utf8") as file:
        data = json.load(file)

        # load the plugins
        loader.load_plugins(data["plugins"])

        # create the jobs
        routines = [[factory.create(job) for job in routine["jobs"]] for routine in data["routines"]]

        # do something with the jobs
        for routine in routines:
            job_args: Sequence[Any] = []
            job_kw_args: Dict[str, Any] = {}
            for job in routine:
                job_args, job_kw_args = job.run(*job_args, **job_kw_args)


if __name__ == "__main__":
    main()
