#!/usr/bin/env python3
import argparse
import os
import sys
from collections.abc import Iterable
from collections.abc import Sequence

import git
from utils import argparse_utils
from utils import git_utils
from utils import log_manager

## TODO:
## - for updates which leave the working tree dirty, consider option to destroy all local content to match git_ref
## - are there submodule considerations?

## https://stackoverflow.com/a/4157435

_LOG_FILE_PATH, _LOG_CFG_DEFAULT = log_manager.get_default_log_paths(__file__)
logger = log_manager.LogManager()

_stash_behaviors_to_file_types: dict[str, set[str]] = {
    "all": {"staged", "tracked_changed", "untracked", "untracked_ignored"},
    "no": set(),
    "staged": {"staged"},
    "tracked": {"tracked_changed"},
    "tracked_w_untracked": {"tracked_changed", "untracked"},
}

_FilesDict = dict[str, list[str]]


def _removeprefix(s: str, prefix: str) -> str:
    return s[len(prefix) :] if s.startswith(prefix) else s


def _get_final_override_ff_only(
    override_simple_ff_only: str,
    git_ref_lhs: str,
    git_ref_rhs: str,
    can_fast_forward: bool,
) -> bool:
    if override_simple_ff_only == "ask":
        while True:
            if can_fast_forward:
                user_input = input(
                    f"PROMPT: '{git_ref_lhs}' cannot simply fast forward to '{git_ref_rhs}' due to local "
                    "modifications listed above which will be overwritten, continue anyway? (yes/no): ",
                ).lower()
            else:
                user_input = input(
                    f"PROMPT: '{git_ref_lhs}' cannot fast forward to '{git_ref_rhs}', they may have diverged "
                    "or be otherwise incompatible, continue anyway? (yes/no): ",
                ).lower()
            if user_input == "no":
                return False
            if user_input == "yes":
                return True
            logger.error(f"invalid user_input={user_input}")
    elif override_simple_ff_only == "no":
        return False
    elif override_simple_ff_only == "yes":
        return True
    else:
        assert False, override_simple_ff_only


def _get_categorized_files(repo: git.Repo, branch: str, git_ref: str) -> _FilesDict:
    return {
        "changed": git_utils.get_changed_files_between_git_refs(repo, branch, git_ref),
        "changed_wrt_tree": git_utils.get_changed_files_between_working_tree_and_git_ref(repo, git_ref),
        "changed_wrt_index": git_utils.get_changed_files_between_index_and_git_ref(repo, git_ref),
        "staged": git_utils.get_staged_files(repo),
        "tracked_changed": git_utils.get_tracked_changed_files(repo),
        "untracked": repo.untracked_files,
        "untracked_ignored": git_utils.get_untracked_ignored_files(repo),
    }


def _get_merge_fast_forward_conflict_files(repo: git.Repo, git_ref: str, categorized_files: _FilesDict) -> _FilesDict:
    dfe = lambda f: git_utils.does_file_exist_on_git_ref(repo, git_ref, f)
    return {
        "staged": [f for f in categorized_files["staged"] if dfe(f) and f in categorized_files["changed"]],
        "tracked_changed": [
            f for f in categorized_files["tracked_changed"] if dfe(f) and f in categorized_files["changed"]
        ],
        "untracked": [f for f in categorized_files["untracked"] if dfe(f)],
        "untracked_ignored": [f for f in categorized_files["untracked_ignored"] if dfe(f)],
    }


def _is_merge_fast_forward_possible(
    repo: git.Repo,
    git_ref: str,
    categorized_files: _FilesDict,
    stashable_file_types: Iterable[str],
) -> bool:
    conflict_files = _get_merge_fast_forward_conflict_files(repo, git_ref, categorized_files)
    return sum((len(v) for k, v in conflict_files.items() if k not in stashable_file_types)) == 0


def _get_to_be_overwritten_files(repo: git.Repo, git_ref: str, categorized_files: _FilesDict) -> _FilesDict:
    dfe = lambda f: git_utils.does_file_exist_on_git_ref(repo, git_ref, f)
    return {
        "staged": [f for f in categorized_files["staged"] if dfe(f) and f in categorized_files["changed_wrt_index"]],
        "tracked_changed": [
            f for f in categorized_files["tracked_changed"] if dfe(f) and f in categorized_files["changed_wrt_tree"]
        ],
        "untracked": [f for f in categorized_files["untracked"] if dfe(f)],
        "untracked_ignored": [f for f in categorized_files["untracked_ignored"] if dfe(f)],
    }


def _log_files_w_overwrite_flag_details(
    files: list[str],
    file_type: str,
    stash_behavior: str,
    overwrite_flag: str | None,
) -> None:
    s_base = f"the following {len(files)} '{file_type}' "
    o_str = f"overwrite_flag='{overwrite_flag}'"
    s_str = f"stash_behavior={stash_behavior}"
    files_str = "\n".join(f"  {f}" for f in files)
    if overwrite_flag is None:
        logger.info(f"{s_base}files will be overwritten; {s_str} includes '{file_type}':\n{files_str}")
    elif overwrite_flag == "ask":
        logger.warning(
            f"{s_base}files will be overwritten; {o_str} for '{file_type}', will prompt for user feedback:\n{files_str}",
        )
    elif overwrite_flag == "no":
        logger.error(
            f"{s_base}files can NOT be overwritten as {o_str} and {s_str} does not include '{file_type}':\n{files_str}",
        )
    elif overwrite_flag == "yes":
        logger.info(f"{s_base}files will be overwritten; {o_str} for '{file_type}':\n{files_str}")
    else:
        assert False, overwrite_flag


def _log_overwritable_files(
    to_be_overwritten_files: _FilesDict,
    overwrite_flags: dict[str, str],
    stashable_file_types: Iterable[str],
    stash_behavior: str,
) -> None:
    assert all(k in overwrite_flags for k in to_be_overwritten_files.keys())
    for file_type, files in to_be_overwritten_files.items():
        if len(files) == 0:
            continue
        if file_type in stashable_file_types:
            _log_files_w_overwrite_flag_details(files, file_type, stash_behavior, None)
        else:
            _log_files_w_overwrite_flag_details(files, file_type, stash_behavior, overwrite_flags[file_type])


def _check_if_can_overwrite_files(
    to_be_overwritten_files: _FilesDict,
    overwrite_flags: dict[str, str],
    stashable_file_types: Iterable[str],
) -> bool:
    ret_val = True
    assert all(k in overwrite_flags for k in to_be_overwritten_files.keys())
    file_types_to_prompt_for_overwrite = []
    for file_type, files in to_be_overwritten_files.items():
        if len(files) == 0:
            continue
        if file_type in stashable_file_types:
            continue
        overwrite_option = overwrite_flags[file_type]
        if overwrite_option == "yes":
            pass
        elif overwrite_option == "no":
            ret_val = False
        elif overwrite_option == "ask":
            file_types_to_prompt_for_overwrite.append(file_type)
        else:
            assert False, overwrite_option
    if ret_val is True and len(file_types_to_prompt_for_overwrite) > 0:
        while True:
            user_input = input(
                f"PROMPT: file_types={file_types_to_prompt_for_overwrite} have their overwrite flags set to 'ask' and "
                "are listed in the above warnings; should they be overwritten? (yes/no): ",
            ).lower()
            if user_input == "yes":
                ret_val = True
                break
            if user_input == "no":
                ret_val = False
                break
            logger.error(f"invalid user_input={user_input}")
    return ret_val


def _checkout_branch(repo: git.Repo, branch: str, current_branch: str, dry_run: bool):
    if current_branch != branch:
        if dry_run:
            logger.info(f"DRYRUN: EXEC: git checkout {branch}")
        else:
            logger.info(f"EXEC: git checkout {branch}")
            repo.git.checkout(branch)


def _update_branch_head_to_git_ref(repo: git.Repo, branch: str, git_ref: str, git_ref_msg: str, dry_run: bool) -> None:
    if dry_run:
        logger.info(f"DRYRUN: EXEC: git update-ref -m '{git_ref_msg}' refs/heads/{branch} {git_ref}")
    else:
        logger.info(f"EXEC: git update-ref -m '{git_ref_msg}' refs/heads/{branch} {git_ref}")
        repo.git.update_ref("-m", git_ref_msg, f"refs/heads/{branch}", git_ref)


def main(argparse_args: Sequence[str] | None = None) -> None:
    # pylint: disable=[too-many-branches,too-many-locals,too-many-statements]

    ask_no_yes_options: dict[str, tuple[str, ...] | str] = {"choices": ("ask", "no", "yes"), "default": "ask"}
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch", "-b")
    parser.add_argument("--checkout", "-c", action="store_true")
    parser.add_argument("--cmd-execute-dir", "-C")
    parser.add_argument("--dry-run", "-d", action="store_true")
    parser.add_argument("--git-ref", "--gr")
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--log")
    parser.add_argument("--log-cfg", default=_LOG_CFG_DEFAULT, help="Log cfg; empty str uses LogManager default cfg")
    parser.add_argument("--override-simple-ff-only", "--osfo", "-o", **ask_no_yes_options)  # type: ignore[arg-type]
    parser.add_argument("--overwrite-staged", "--os", **ask_no_yes_options)  # type: ignore[arg-type]
    parser.add_argument("--overwrite-tracked-changed", "--ot", **ask_no_yes_options)  # type: ignore[arg-type]
    parser.add_argument("--overwrite-untracked", "--ou", **ask_no_yes_options)  # type: ignore[arg-type]
    parser.add_argument("--overwrite-untracked-ignored", "--oui", **ask_no_yes_options)  # type: ignore[arg-type]
    parser.add_argument("--stash-behavior", "--sb", choices=_stash_behaviors_to_file_types.keys(), default="tracked")
    parser.add_argument("--skip-log-changes", "--slc", action="store_true")
    stash_group = parser.add_mutually_exclusive_group()
    stash_group.add_argument("--stash-apply", "--sa", action="store_true")
    stash_group.add_argument("--stash-pop", "--sp", action="store_true")
    args = parser.parse_args(args=argparse_args)

    log_manager.LogManager.setup_logger(globals(), log_cfg=args.log_cfg, log_file=args.log)

    logger.debug(f"argparse args:\n{argparse_utils.parsed_args_to_str(args)}")

    cmd_execute_dir = os.getcwd() if args.cmd_execute_dir is None else args.cmd_execute_dir
    repo = git.Repo(cmd_execute_dir, search_parent_directories=True)
    current_branch = git_utils.get_current_branch(repo)

    overwrite_flags = {
        _removeprefix(arg, "overwrite_"): getattr(args, arg) for arg in vars(args) if arg.startswith("overwrite_")
    }

    branch = current_branch if args.branch is None else git_utils.get_local_branch_obj(repo, args.branch)
    if branch is None:
        logger.error(f"the following is not a branch: '{'HEAD' if args.branch is None else args.branch}'")
        sys.exit(1)

    if current_branch is None:
        logger.error("current_branch is None")  # TODO: is this necessary, there might need to be a way to continue
        sys.exit(1)

    if args.fetch:
        fetch_result = git_utils.fetch_all_remotes(repo, dry_run=args.dry_run)
        if not fetch_result:
            sys.exit(1)

    git_ref_obj = branch.tracking_branch() if args.git_ref is None else git_utils.get_ref_obj(repo, args.git_ref)

    if git_ref_obj is None:
        if args.git_ref is None:
            logger.error(f"no tracking branch on remote for '{args.branch}'")
        else:
            logger.error(f"invalid git reference: args.git_ref={args.git_ref}")
        sys.exit(1)

    can_fast_forward = git_utils.is_ancestor(repo, branch, git_ref_obj)
    if not can_fast_forward:
        logger.warning(f"{branch} is not an ancestor of {git_ref_obj}")

    if git_utils.get_hash(branch) == git_utils.get_hash(git_ref_obj):
        logger.info(f"skipped update: hash for {branch} and {git_ref_obj} are the same")
        if args.checkout is True:
            _checkout_branch(repo, branch, current_branch, dry_run=args.dry_run)
        sys.exit(0)

    do_fast_forward = False
    do_stash_push = False
    override_simple_ff_only = False
    if current_branch == branch:
        stashable_file_types = _stash_behaviors_to_file_types[args.stash_behavior]
        categorized_files = _get_categorized_files(repo, branch, git_ref_obj)
        do_fast_forward = can_fast_forward and _is_merge_fast_forward_possible(
            repo,
            git_ref_obj,
            categorized_files,
            stashable_file_types,
        )
        to_be_overwritten_files = _get_to_be_overwritten_files(repo, git_ref_obj, categorized_files)
        if not do_fast_forward:
            _log_overwritable_files(to_be_overwritten_files, overwrite_flags, stashable_file_types, args.stash_behavior)
            if not can_fast_forward:
                merge_base = git_utils.get_merge_base(repo, branch, git_ref_obj)
                merge_base_log = repo.git.log(
                    "--oneline",
                    "-n",
                    "1",
                    *git_utils.GIT_FORMAT_OPTIONS_ONE_LINE,
                    merge_base,
                )
                ahead_behind_status = git_utils.get_ahead_behind_status_str(repo, branch, git_ref_obj)
                logger.warning(
                    f"cannot fast forward as '{branch}' is not an ancestor of '{git_ref_obj}', "
                    "see the following details about the divergence:\n"
                    f"  common ancestor: {merge_base_log}\n"
                    f"  {ahead_behind_status}",
                )
            override_simple_ff_only = _get_final_override_ff_only(
                args.override_simple_ff_only,
                branch,
                git_ref_obj,
                can_fast_forward,
            )
            change_str = "fast forward" if can_fast_forward else "update"
            error_str_prefix = f"Force {change_str} of '{branch}' to '{git_ref_obj}' not allowed due to"
            if not override_simple_ff_only:
                logger.error(f"{error_str_prefix} override_simple_ff_only={override_simple_ff_only}")
                sys.exit(1)
            if not _check_if_can_overwrite_files(to_be_overwritten_files, overwrite_flags, stashable_file_types):
                logger.error(f"{error_str_prefix} override flags set by cli options and/or user prompt inputs")
                sys.exit(1)

        file_types_to_stash = [
            ft for ft, fs in to_be_overwritten_files.items() if len(fs) != 0 and ft in stashable_file_types
        ]
        do_stash_push = len(file_types_to_stash) > 0
        if do_stash_push:
            logger.info(f"executing stash to prevent overwriting file_types={file_types_to_stash}")
            git_utils.stash_push_w_behavior(repo, args.stash_behavior, None, dry_run=args.dry_run)

        if do_fast_forward:
            logger.info(f"fast forwarding '{branch}' to '{git_ref_obj}'")
            merge_fast_forward_result = git_utils.merge_fast_forward(repo, branch, git_ref_obj, dry_run=args.dry_run)
            assert merge_fast_forward_result is True
        else:
            assert override_simple_ff_only is True
            logger.info(f"Forcing {'fast forward' if can_fast_forward else 'update'} of '{branch}' to '{git_ref_obj}''")
            git_utils.reset_hard(repo, git_ref_obj, dry_run=args.dry_run)
    else:
        change_str = "fast forwarding" if can_fast_forward else "cannot fast forward, forcing"
        logger.info(f"{change_str} non-checked out branch='{branch}' to '{git_ref_obj}'")
        if not can_fast_forward:
            override_simple_ff_only = _get_final_override_ff_only(
                args.override_simple_ff_only,
                branch,
                git_ref_obj,
                can_fast_forward,
            )
            if not override_simple_ff_only:
                logger.error(
                    f"Cannot force update of '{branch}' to '{git_ref_obj}' as "
                    f"override_simple_ff_only={override_simple_ff_only}",
                )
                sys.exit(1)
        git_ref_msg = f"merge {git_ref_obj}: {'Fast forward' if can_fast_forward else 'Force ref update'}"
        _update_branch_head_to_git_ref(repo, branch, git_ref_obj, git_ref_msg, dry_run=args.dry_run)

    if not args.dry_run:
        if not args.skip_log_changes:
            at_1 = "@{1}"
            logger.info(
                f"git diff --stat {branch}{at_1} {branch}%s",
                repo.git.diff("--stat", f"{branch}{at_1}", branch),
            )
        logger.info(f"{'fast forwarded' if can_fast_forward else 'updated'} '{branch}' to '{git_ref_obj}'")

    if do_stash_push:
        if args.stash_pop:
            logger.info("executing: git stash pop")
            git_utils.stash_pop(repo, log_conflict_msg=True, dry_run=args.dry_run)
        elif args.stash_apply:
            logger.info("executing: git stash apply")
            git_utils.stash_apply(repo, log_conflict_msg=True, dry_run=args.dry_run)
        else:
            logger.info(f"a stash is available with the changes before updating '{branch}' to '{git_ref_obj}'")

    if args.checkout is True:
        _checkout_branch(repo, branch, current_branch, dry_run=args.dry_run)

    if args.dry_run:
        logger.info("dry-run complete, no anticipated errors")


if __name__ == "__main__":
    main()
