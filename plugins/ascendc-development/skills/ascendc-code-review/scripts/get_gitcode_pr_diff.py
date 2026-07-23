#!/usr/bin/env python3
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# Licensed under the CANN Open Software License Agreement Version 2.0.
"""Fetch a GitCode pull request diff without requiring an API token."""

from __future__ import annotations

import argparse
import dataclasses
import logging
import os
import pathlib
import re
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from urllib.parse import urlsplit


ALLOWED_HOST = "gitcode.com"
GIT_TIMEOUT_SECONDS = 120
HEAD_FETCH_DEPTH = 128
MERGE_FETCH_DEPTH = 2
TEMP_DIR_PREFIX = "gitcode-pr-diff-"
COMPONENT_PATTERN = r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}"
REPO_PATH_PATTERN = re.compile(
    rf"^/({COMPONENT_PATTERN})/({COMPONENT_PATTERN}?)(?:\.git)?"
    r"(?:/pulls/([1-9][0-9]*))?/?$"
)
BRANCH_PATTERN = re.compile(
    rf"{COMPONENT_PATTERN}(?:/{COMPONENT_PATTERN})*$"
)
LOGGER = logging.getLogger("gitcode-pr-diff")


class GitCodeDiffError(RuntimeError):
    """An expected repository or Git failure."""


@dataclasses.dataclass(frozen=True)
class RepoLocation:
    owner: str
    repository: str
    url: str
    pr_number: int | None


def _positive_pr_number(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("PR number must be a positive integer")
    return value


def normalize_repo_url(value: str, *, expected_pr: int | None = None) -> RepoLocation:
    """Validate a canonical GitCode repository or pull-request URL."""
    if not isinstance(value, str) or not value:
        raise ValueError("repository URL must be a non-empty string")
    if any(ord(character) <= 0x20 or ord(character) == 0x7F for character in value):
        raise ValueError("repository URL must not contain whitespace or control characters")
    if expected_pr is not None:
        _positive_pr_number(expected_pr)

    parsed = urlsplit(value)
    if parsed.scheme != "https" or parsed.netloc != ALLOWED_HOST:
        raise ValueError("repository URL must use exactly https://gitcode.com")
    if parsed.username is not None or parsed.password is not None or parsed.port is not None:
        raise ValueError("repository URL must not contain credentials or a port")
    if parsed.query or parsed.fragment:
        raise ValueError("repository URL must not contain a query or fragment")

    match = REPO_PATH_PATTERN.fullmatch(parsed.path)
    if match is None:
        raise ValueError(
            "repository path must be /owner/repository[.git] or "
            "/owner/repository/pulls/NUMBER"
        )
    owner, repository, embedded_pr_text = match.groups()
    if owner in {".", ".."} or repository in {".", ".."}:
        raise ValueError("repository path contains an invalid component")

    embedded_pr = int(embedded_pr_text) if embedded_pr_text else None
    if expected_pr is not None and embedded_pr is not None and embedded_pr != expected_pr:
        raise ValueError(
            f"pull request URL number {embedded_pr} does not match --pr {expected_pr}"
        )
    return RepoLocation(
        owner=owner,
        repository=repository,
        url=f"https://{ALLOWED_HOST}/{owner}/{repository}.git",
        pr_number=embedded_pr,
    )


def normalize_file_filter(value: str) -> str:
    """Validate a repository-relative Git glob used as a diff pathspec."""
    if not isinstance(value, str) or not value or len(value) > 512:
        raise ValueError("file filter must contain 1-512 characters")
    if any(character in value for character in ("\0", "\n", "\r", "\\")):
        raise ValueError("file filter contains an unsupported character")
    if value.startswith("/"):
        raise ValueError("file filter must be repository-relative")
    components = value.split("/")
    if any(component in {"", ".", ".."} for component in components):
        raise ValueError("file filter must not contain empty, dot, or parent components")
    return value


def _git_pathspec(file_filter: str) -> str:
    pattern = normalize_file_filter(file_filter)
    if "/" not in pattern:
        pattern = f"**/{pattern}"
    return f":(glob){pattern}"


def _git_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for key in list(environment):
        if key.startswith("GIT_") or key in {"SSH_ASKPASS"}:
            environment.pop(key)
    environment.update(
        {
            "GCM_INTERACTIVE": "Never",
            "GIT_ALLOW_PROTOCOL": "https",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "LC_ALL": "C",
        }
    )
    return environment


def normalize_branch(value: str) -> str:
    """Validate one explicit Git branch name used as a PR target."""
    if not isinstance(value, str) or not value:
        raise ValueError("base branch must be a non-empty string")
    if (
        BRANCH_PATTERN.fullmatch(value) is None
        or ".." in value
        or value.endswith(".lock")
    ):
        raise ValueError("base branch contains unsupported ref syntax")
    return value


def run_git(
    args: Sequence[str],
    *,
    cwd: pathlib.Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run Git noninteractively without shell or user-config URL rewrites."""
    command = [
        "git",
        "-c",
        "credential.helper=",
        "-c",
        "core.askPass=",
        *args,
    ]
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=_git_environment(),
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as error:
        raise GitCodeDiffError("git executable was not found") from error
    except subprocess.TimeoutExpired as error:
        raise GitCodeDiffError(
            f"git command exceeded the {GIT_TIMEOUT_SECONDS}-second timeout"
        ) from error

    if check and result.returncode != 0:
        detail = result.stderr.strip().splitlines()
        message = detail[-1] if detail else f"exit status {result.returncode}"
        raise GitCodeDiffError(f"git {args[0]} failed: {message}")
    return result


def _fetch_args(depth: int, source_ref: str, destination_ref: str) -> list[str]:
    return [
        "fetch",
        "--quiet",
        "--no-tags",
        "--no-recurse-submodules",
        f"--depth={depth}",
        "origin",
        f"+{source_ref}:{destination_ref}",
    ]


def _diff_args(
    base: str,
    head: str,
    *,
    stat_only: bool,
    file_filter: str | None,
) -> list[str]:
    args = ["diff", "--no-color", "--no-ext-diff", "--no-textconv"]
    if stat_only:
        args.append("--stat")
    args.extend([base, head])
    if file_filter is not None:
        args.extend(["--", _git_pathspec(file_filter)])
    return args


def _diff_merge_ref(
    repo_dir: pathlib.Path,
    pr_number: int,
    *,
    stat_only: bool,
    file_filter: str | None,
) -> str | None:
    merge_fetch = run_git(
        _fetch_args(
            MERGE_FETCH_DEPTH,
            f"refs/merge-requests/{pr_number}/merge",
            "refs/pr/merge",
        ),
        cwd=repo_dir,
        check=False,
    )
    if merge_fetch.returncode != 0:
        return None

    parent = run_git(
        ["rev-parse", "--verify", "--quiet", "refs/pr/merge^1"],
        cwd=repo_dir,
        check=False,
    )
    if parent.returncode != 0:
        LOGGER.info("merge ref has no available first parent; trying the head ref")
        return None

    result = run_git(
        _diff_args(
            "refs/pr/merge^1",
            "refs/pr/merge",
            stat_only=stat_only,
            file_filter=file_filter,
        ),
        cwd=repo_dir,
    )
    return result.stdout


def _diff_head_ref(
    repo_dir: pathlib.Path,
    pr_number: int,
    base_branch: str,
    *,
    stat_only: bool,
    file_filter: str | None,
) -> str:
    branch = normalize_branch(base_branch)
    run_git(
        _fetch_args(
            HEAD_FETCH_DEPTH,
            f"refs/merge-requests/{pr_number}/head",
            "refs/pr/head",
        ),
        cwd=repo_dir,
    )
    run_git(
        _fetch_args(HEAD_FETCH_DEPTH, f"refs/heads/{branch}", "refs/pr/base"),
        cwd=repo_dir,
    )
    merge_base = run_git(
        ["merge-base", "refs/pr/base", "refs/pr/head"],
        cwd=repo_dir,
        check=False,
    )
    base_commit = merge_base.stdout.strip()
    if merge_base.returncode != 0 or not re.fullmatch(r"[0-9a-fA-F]{4,64}", base_commit):
        raise GitCodeDiffError(
            "no merge base was found within the bounded shallow history; "
            "use a local checkout for this pull request"
        )
    result = run_git(
        _diff_args(
            base_commit,
            "refs/pr/head",
            stat_only=stat_only,
            file_filter=file_filter,
        ),
        cwd=repo_dir,
    )
    return result.stdout


def fetch_pr_diff(
    repo_url: str,
    pr_number: int,
    *,
    base_branch: str | None = None,
    file_filter: str | None = None,
    stat_only: bool = False,
) -> str:
    """Fetch a pull request merge/head ref and return its diff or stat."""
    pr_number = _positive_pr_number(pr_number)
    location = normalize_repo_url(repo_url, expected_pr=pr_number)
    if file_filter is not None:
        normalize_file_filter(file_filter)
    if base_branch is not None:
        normalize_branch(base_branch)

    with tempfile.TemporaryDirectory(prefix=TEMP_DIR_PREFIX) as temp_name:
        repo_dir = pathlib.Path(temp_name) / "repository.git"
        run_git(["init", "--bare", "--quiet", str(repo_dir)])
        run_git(["remote", "add", "origin", location.url], cwd=repo_dir)
        content = _diff_merge_ref(
            repo_dir,
            pr_number,
            stat_only=stat_only,
            file_filter=file_filter,
        )
        if content is not None:
            return content
        if base_branch is None:
            raise GitCodeDiffError(
                "merge ref unavailable; rerun with --base set to the pull request target branch"
            )
        LOGGER.warning(
            "merge ref unavailable; comparing the head ref with explicit target branch %s",
            base_branch,
        )
        return _diff_head_ref(
            repo_dir,
            pr_number,
            base_branch,
            stat_only=stat_only,
            file_filter=file_filter,
        )


def write_output(content: str, output: pathlib.Path | None) -> None:
    if output is None:
        sys.stdout.write(content)
        return
    output.write_text(content, encoding="utf-8")


def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch a GitCode pull request diff without an API token."
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="exact https://gitcode.com/owner/repository URL (a matching /pulls/N URL is accepted)",
    )
    parser.add_argument("--pr", required=True, type=int, help="positive pull request number")
    parser.add_argument(
        "--base",
        help="explicit PR target branch, required only when the GitCode merge ref is unavailable",
    )
    parser.add_argument("--stat", action="store_true", help="show only the diff stat")
    parser.add_argument(
        "--file-filter",
        help="repository-relative Git glob, for example '**/*.asc'",
    )
    parser.add_argument("--output", type=pathlib.Path, help="write to this file instead of stdout")
    parser.add_argument("--verbose", action="store_true", help="show fetch decisions on stderr")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = create_argument_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )
    try:
        content = fetch_pr_diff(
            args.repo,
            args.pr,
            base_branch=args.base,
            file_filter=args.file_filter,
            stat_only=args.stat,
        )
        write_output(content, args.output)
    except (GitCodeDiffError, OSError, ValueError) as error:
        LOGGER.error("%s", error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
