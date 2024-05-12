## TODO:
## - add relative option for generating file lists

import logging

from typing import List, Optional, Sequence, Union

import git


## tracking branch given branch https://stackoverflow.com/a/9753364
## git for-each-ref --format='%(upstream:short)' $(git rev-parse --symbolic-full-name <SOMEBRANCH>)

logger = logging.getLogger(__name__)


def _build_git_cmd_str(prefix: str, args: Sequence[str]) -> str:
    if len(args) == 0:
        return prefix
    args_delim = "' '"
    return f"{prefix} '{args_delim.join(args)}'"


####
#### Get python object for git reference
####


## TODO: works for origin/master, still need func that looks through tracking_branches or remote branches directly
def get_commit_obj(repo: git.Repo, ref_name: str) -> Optional[git.Commit]:
    try:
        return repo.commit(ref_name)
    except git.BadName:
        return None


def get_current_branch(repo: git.Repo) -> Optional[git.Head]:
    try:
        return repo.active_branch
    except TypeError:
        return None


def get_local_branch_obj(repo: git.Repo, ref_name: str) -> Optional[git.Head]:
    try:
        return repo.heads[ref_name]
    except IndexError:
        return None


def get_tag_obj(repo: git.Repo, ref_name: str) -> Optional[git.TagObject]:
    try:
        return repo.tags[ref_name]
    except IndexError:
        return None


def get_ref_obj(repo: git.Repo, ref_name: str) -> Optional[Union[git.Commit, git.Head, git.Reference, git.TagObject]]:
    obj = get_local_branch_obj(repo, ref_name)
    if obj is not None:
        return obj

    obj = get_tag_obj(repo, ref_name)
    if obj is not None:
        return obj

    obj = get_commit_obj(repo, ref_name)
    if obj is not None:
        return obj

    try:
        return repo.refs[ref_name]  # type: ignore [index, no-any-return]
    except IndexError:
        return None


####
#### Interact with repo's files
####


def does_file_exist_on_git_ref(repo: git.Repo, git_ref: str, file: str) -> bool:
    try:
        repo.git.cat_file("-e", f"{git_ref}:{file}")
        return True
    except git.exc.GitCommandError as e:
        assert e.status in (1, 128), e.status
        return False


def get_conflict_files(repo: git.Repo) -> List[str]:
    conflict_files: str = repo.git.diff("--name-only", "--diff-filter=U", "-z").strip("\x00")
    return [] if conflict_files == "" else conflict_files.split("\x00")


def get_changed_files_between_git_refs(repo: git.Repo, git_ref_lhs: str, git_ref_rhs: str) -> List[str]:
    changed_files: str = repo.git.diff("--name-only", "-z", f"{git_ref_lhs}..{git_ref_rhs}").strip("\x00")
    return [] if changed_files == "" else changed_files.split("\x00")


def get_changed_files_between_index_and_git_ref(repo: git.Repo, git_ref: str) -> List[str]:
    changed_files: str = repo.git.diff("--name-only", "--staged", "-z", f"{git_ref}").strip("\x00")
    return [] if changed_files == "" else changed_files.split("\x00")


def get_changed_files_between_working_tree_and_git_ref(repo: git.Repo, git_ref: str) -> List[str]:
    changed_files: str = repo.git.diff("--name-only", "-z", f"{git_ref}").strip("\x00")
    return [] if changed_files == "" else changed_files.split("\x00")


def get_staged_files(repo: git.Repo) -> List[str]:
    staged_files: str = repo.git.diff("--name-only", "--cached", "-z").strip("\x00")
    return [] if staged_files == "" else staged_files.split("\x00")


## includes conflict files
def get_tracked_changed_files(repo: git.Repo) -> List[str]:
    tracked_changed_files: str = repo.git.diff("--name-only", "-z").strip("\x00")
    return [] if tracked_changed_files == "" else tracked_changed_files.split("\x00")


def get_untracked_ignored_files(repo: git.Repo) -> List[str]:
    untracked_ignored_files: str = repo.git.ls_files("--exclude-standard", "--others", "--ignored", "-z").strip("\x00")
    return [] if untracked_ignored_files == "" else untracked_ignored_files.split("\x00")


####
#### Repo modifying operations
####


def fetch_all_remotes(repo: git.Repo, ignore_no_remotes: bool = False, dry_run: bool = False) -> bool:
    if len(repo.remotes) == 0 and not ignore_no_remotes:
        logger.error("there are no remotes for this repo")
        return False
    try:
        for remote in repo.remotes:
            if dry_run:
                logger.info("DRYRUN: EXEC: git fetch %s", remote)
            else:
                logger.info("EXEC: git fetch %s", remote)
                remote.fetch()
    except git.exc.GitCommandError as e:
        logger.error("failed fetch of remote=%s, printing error msg:", remote)
        logger.error(e)
        return False
    return True


def merge_fast_forward(repo: git.Repo, local_branch_obj: git.Head, git_ref: str, dry_run: bool = False) -> bool:
    if dry_run:
        logger.info("DRYRUN: EXEC: git merge --ff-only %s %s", local_branch_obj, git_ref)
        return True

    try:
        logger.info("EXEC: git merge --ff-only %s %s", local_branch_obj, git_ref)
        repo.git.merge("--ff-only", local_branch_obj, git_ref)
        return True
    except git.exc.GitCommandError as e:
        logger.error("merge fast forward resulted in error, printing error msg:")
        logger.error(e)
        assert e.status == 1
        return False


def stash_apply(repo: git.Repo, log_conflict_msg: bool = False, dry_run: bool = False) -> bool:
    try:
        if dry_run:
            logger.info("DRYRUN: EXEC: git stash apply")
        else:
            logger.info("EXEC: git stash apply")
            repo.git.stash("apply")
    except git.exc.GitCommandError as e:
        logger.error("stash apply resulted in error, printing error msg:")
        logger.error(e)
        if log_conflict_msg and len(get_conflict_files(repo)) > 0:
            logger.warning("stash apply resulted in conflicts")
        return False
    return True


def stash_pop(repo: git.Repo, log_conflict_msg: bool = False, dry_run: bool = False) -> bool:
    try:
        if dry_run:
            logger.info("DRYRUN: EXEC: git stash pop")
        else:
            logger.info("EXEC: git stash pop")
            repo.git.stash("pop")
    except git.exc.GitCommandError as e:
        logger.error("stash pop resulted in error, printing error msg:")
        logger.error(e)
        if log_conflict_msg and len(get_conflict_files(repo)) > 0:
            logger.warning("stash pop resulted in conflicts (stash not dropped), please resolve conflicts")
        return False
    return True


def stash_push_w_behavior(repo: git.Repo, stash_behavior: str, msg: str = None, dry_run: bool = False) -> None:
    msg_args = [] if msg is None else ["-m", msg]
    if stash_behavior == "all":
        stash_args = tuple("push", "--all", *msg_args)
    elif stash_behavior == "no":
        stash_args = None
    elif stash_behavior == "staged":
        stash_args = tuple("push", "--staged", *msg_args)
    elif stash_behavior == "tracked":
        stash_args = tuple("push", *msg_args)
    elif stash_behavior == "tracked_w_untracked":
        stash_args = tuple("push", "--include-untracked", *msg_args)
    else:
        assert False, stash_behavior

    if stash_args is not None:
        if dry_run:
            logger.info("DRYRUN: EXEC: %s", _build_git_cmd_str("git stash", stash_args))
        else:
            logger.info("EXEC: %s", _build_git_cmd_str("git stash", stash_args))
            stash_result = repo.git.stash(*stash_args)
            assert stash_result != "No local changes to save"


def reset_hard(repo: git.Repo, git_ref: str, dry_run: bool = False) -> None:
    if dry_run:
        logger.info("DRYRUN: EXEC: git reset --hard %s", git_ref)
    else:
        logger.info("EXEC: git reset --hard %s", git_ref)
        repo.git.reset("--hard", git_ref)


####
#### Misc
####

GIT_FORMAT_OPTIONS_ONE_LINE = (
    "--date=format:%y-%m-%d %H:%M",
    "--pretty=format:%h%x20%x20%Cred%ad%x20%x20%Cblue%an%x20%x20%Creset%s",
)


def get_hash(git_ref_obj: Union[git.Commit, git.Reference]) -> str:
    if isinstance(git_ref_obj, git.Commit):
        return git_ref_obj.hexsha
    if isinstance(git_ref_obj, git.Reference):
        return git_ref_obj.commit.hexsha  # type: ignore [no-any-return]
    assert False, (type(git_ref_obj), git_ref_obj)


## https://stackoverflow.com/a/27940027
def get_ahead_behind_status(repo: git.Repo, git_ref_lhs: str, git_ref_rhs: str):
    counts_str = repo.git.rev_list("--left-right", "--count", f"{git_ref_lhs}...{git_ref_rhs}")
    counts = [int(c) for c in counts_str.split("\t")]
    assert len(counts) == 2
    return counts


def get_ahead_behind_status_str(repo: git.Repo, git_ref_lhs: str, git_ref_rhs: str):
    counts = get_ahead_behind_status(repo, git_ref_lhs, git_ref_rhs)
    lhs_relative = counts[0]
    rhs_relative = counts[1]
    if lhs_relative == 0 and rhs_relative == 0:
        return f"'{git_ref_lhs}' is up to date with '{git_ref_rhs}'."
    if lhs_relative > 0 and rhs_relative == 0:
        return f"'{git_ref_lhs}' is ahead of '{git_ref_rhs}' by {lhs_relative} commit."
    if lhs_relative == 0 and rhs_relative > 0:
        return f"'{git_ref_lhs}' is behind '{git_ref_rhs}' by {rhs_relative} commit, and can be fast-forwarded."
    if lhs_relative > 0 and rhs_relative > 0:
        return (
            f"'{git_ref_lhs}' and '{git_ref_rhs}' have diverged, and have "
            f"{lhs_relative} and {rhs_relative} different commits each, respectively."
        )
    assert False, f"lhs_relative={lhs_relative}, rhs_relative={rhs_relative}"


def get_merge_base(repo: git.Repo, git_ref_lhs: str, git_ref_rhs: str) -> str:
    return repo.git.merge_base(git_ref_lhs, git_ref_rhs)  # type: ignore [no-any-return]


def is_ancestor(repo: git.Repo, git_ref_potential_ancestor: str, git_ref: str) -> bool:
    try:
        logger.debug("EXEC: git merge-base --is-ancestor %s %s", git_ref_potential_ancestor, git_ref)
        repo.git.merge_base(git_ref_potential_ancestor, git_ref, is_ancestor=True)
        return True
    except git.GitCommandError as err:
        assert err.status == 1
        return False
