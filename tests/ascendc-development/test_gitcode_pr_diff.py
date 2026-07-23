#!/usr/bin/env python3
"""Offline regression tests for the GitCode PR diff client."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "plugins"
    / "ascendc-development"
    / "skills"
    / "ascendc-code-review"
    / "scripts"
    / "get_gitcode_pr_diff.py"
)
SPEC = importlib.util.spec_from_file_location("get_gitcode_pr_diff", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT}")
GITCODE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GITCODE
SPEC.loader.exec_module(GITCODE)


def completed(args: list[str], returncode: int = 0, stdout: str = "", stderr: str = ""):
    return subprocess.CompletedProcess(args, returncode, stdout, stderr)


class GitCodeUrlTest(unittest.TestCase):
    def test_normalizes_repository_and_matching_pull_url(self) -> None:
        plain = GITCODE.normalize_repo_url("https://gitcode.com/cann/ops-nn.git/")
        self.assertEqual(plain.url, "https://gitcode.com/cann/ops-nn.git")
        self.assertIsNone(plain.pr_number)

        pull = GITCODE.normalize_repo_url(
            "https://gitcode.com/cann/ops-transformer/pulls/3228", expected_pr=3228
        )
        self.assertEqual(pull.url, "https://gitcode.com/cann/ops-transformer.git")
        self.assertEqual(pull.pr_number, 3228)

    def test_rejects_noncanonical_or_ambiguous_urls(self) -> None:
        invalid = [
            "http://gitcode.com/cann/ops-nn",
            "https://gitcode.com.evil.example/cann/ops-nn",
            "https://user@gitcode.com/cann/ops-nn",
            "https://gitcode.com:443/cann/ops-nn",
            "https://gitcode.com/cann/ops-nn?ref=main",
            "https://gitcode.com/cann/ops-nn#readme",
            "https://gitcode.com/cann/ops-nn/tree/main",
            "https://gitcode.com/cann/%2e%2e",
            "https://gitcode.com/cann%2fops-nn/project",
            " https://gitcode.com/cann/ops-nn",
            "https://gitcode.com/cann/ops-nn\n",
        ]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                GITCODE.normalize_repo_url(value)

    def test_rejects_pull_number_mismatch(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not match"):
            GITCODE.normalize_repo_url(
                "https://gitcode.com/cann/ops-nn/pulls/41", expected_pr=42
            )

    def test_file_filter_rejects_paths_that_escape_the_repository(self) -> None:
        self.assertEqual(GITCODE.normalize_file_filter("src/**/*.asc"), "src/**/*.asc")
        for value in ("/etc/passwd", "../*.asc", "src/../../*.py", "a\nb", "a\0b"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                GITCODE.normalize_file_filter(value)

    def test_base_branch_validation_rejects_ref_syntax(self) -> None:
        self.assertEqual(GITCODE.normalize_branch("release/9.1"), "release/9.1")
        for value in ("", "../main", "main..next", "main.lock", "main@{1}", "-main"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                GITCODE.normalize_branch(value)


class GitCodeFetchTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("git"), "git is required")
    def test_real_git_merge_ref_and_path_filter(self) -> None:
        def git(cwd: pathlib.Path, *args: str) -> str:
            result = subprocess.run(
                ["git", *args],
                cwd=cwd,
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()

        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            work = root / "work"
            remote = root / "remote.git"
            client = root / "client.git"
            work.mkdir()
            git(work, "init", "--quiet")
            git(work, "config", "user.name", "Offline Test")
            git(work, "config", "user.email", "offline@example.invalid")
            (work / "src").mkdir()
            (work / "src" / "kernel.asc").write_text("before\n", encoding="utf-8")
            (work / "notes.txt").write_text("before\n", encoding="utf-8")
            git(work, "add", ".")
            git(work, "commit", "--quiet", "-m", "base")
            base_branch = git(work, "symbolic-ref", "--short", "HEAD")
            git(work, "checkout", "--quiet", "-b", "feature")
            (work / "src" / "kernel.asc").write_text("after\n", encoding="utf-8")
            (work / "notes.txt").write_text("after\n", encoding="utf-8")
            git(work, "commit", "--quiet", "-am", "feature")
            git(work, "checkout", "--quiet", base_branch)
            git(work, "merge", "--quiet", "--no-ff", "feature", "-m", "virtual merge")

            subprocess.run(["git", "init", "--bare", "--quiet", str(remote)], check=True)
            git(work, "remote", "add", "fixture", remote.as_uri())
            git(
                work,
                "push",
                "--quiet",
                "fixture",
                f"{base_branch}:refs/heads/main",
                "feature:refs/merge-requests/1/head",
                "HEAD:refs/merge-requests/1/merge",
            )
            subprocess.run(["git", "init", "--bare", "--quiet", str(client)], check=True)
            git(client, "remote", "add", "origin", remote.as_uri())

            environment = os.environ.copy()
            environment.update(GITCODE._git_environment())
            environment["GIT_ALLOW_PROTOCOL"] = "file"
            with mock.patch.object(GITCODE, "_git_environment", return_value=environment):
                content = GITCODE._diff_merge_ref(
                    client,
                    1,
                    stat_only=False,
                    file_filter="**/*.asc",
                )

        self.assertIsNotNone(content)
        self.assertIn("+after", content)
        self.assertNotIn("notes.txt", content)

    def test_merge_ref_uses_bounded_fetch_and_first_parent_diff(self) -> None:
        calls: list[tuple[list[str], pathlib.Path | None, bool]] = []

        def fake_run(args, *, cwd=None, check=True):
            args = list(args)
            calls.append((args, cwd, check))
            if args[0] == "diff":
                return completed(args, stdout="diff --git a/a.asc b/a.asc\n")
            return completed(args)

        with tempfile.TemporaryDirectory() as parent:
            work = pathlib.Path(parent) / "request"
            work.mkdir()
            with mock.patch.object(GITCODE.tempfile, "mkdtemp", return_value=str(work)):
                with mock.patch.object(GITCODE, "run_git", side_effect=fake_run):
                    result = GITCODE.fetch_pr_diff(
                        "https://gitcode.com/cann/ops-nn",
                        42,
                        file_filter="**/*.asc",
                    )
            self.assertFalse(work.exists())

        self.assertIn("a.asc", result)
        fetch = next(args for args, _cwd, _check in calls if args[0] == "fetch")
        self.assertIn("--depth=2", fetch)
        self.assertIn("--no-tags", fetch)
        self.assertIn("refs/merge-requests/42/merge:refs/pr/merge", fetch[-1])
        self.assertFalse(any(args[0] == "clone" for args, _cwd, _check in calls))

        diff = next(args for args, _cwd, _check in calls if args[0] == "diff")
        self.assertIn("refs/pr/merge^1", diff)
        self.assertIn("refs/pr/merge", diff)
        self.assertEqual(diff[-2:], ["--", ":(glob)**/*.asc"])

    def test_head_ref_fallback_fetches_only_bounded_head_and_base_history(self) -> None:
        calls: list[list[str]] = []

        def fake_run(args, *, cwd=None, check=True):
            del cwd, check
            args = list(args)
            calls.append(args)
            if args[0] == "fetch" and "merge:refs/pr/merge" in args[-1]:
                return completed(args, returncode=128, stderr="missing merge ref")
            if args[0] == "merge-base":
                return completed(args, stdout="abc123\n")
            if args[0] == "diff":
                return completed(args, stdout="fallback diff\n")
            return completed(args)

        with mock.patch.object(GITCODE, "run_git", side_effect=fake_run):
            with self.assertLogs(GITCODE.LOGGER, level="WARNING") as logs:
                result = GITCODE.fetch_pr_diff(
                    "https://gitcode.com/cann/ops-transformer",
                    7,
                    base_branch="release/9.1",
                    stat_only=True,
                )

        self.assertEqual(result, "fallback diff\n")
        self.assertIn("explicit target branch release/9.1", logs.output[0])
        fetches = [args for args in calls if args[0] == "fetch"]
        self.assertEqual(len(fetches), 3)
        self.assertTrue(any("refs/merge-requests/7/head:refs/pr/head" in args[-1] for args in fetches))
        self.assertTrue(any("refs/heads/release/9.1:refs/pr/base" in args[-1] for args in fetches))
        for args in fetches[1:]:
            self.assertIn(f"--depth={GITCODE.HEAD_FETCH_DEPTH}", args)

        diff = next(args for args in calls if args[0] == "diff")
        self.assertIn("--stat", diff)
        self.assertEqual(diff[-2:], ["abc123", "refs/pr/head"])

    def test_head_ref_fallback_requires_explicit_base_branch(self) -> None:
        def fake_run(args, *, cwd=None, check=True):
            del cwd, check
            args = list(args)
            if args[0] == "fetch":
                return completed(args, returncode=128, stderr="missing merge ref")
            return completed(args)

        with mock.patch.object(GITCODE, "run_git", side_effect=fake_run):
            with self.assertRaisesRegex(GITCODE.GitCodeDiffError, "rerun with --base"):
                GITCODE.fetch_pr_diff("https://gitcode.com/cann/ops-nn", 8)

    def test_cleanup_runs_when_git_fails(self) -> None:
        with tempfile.TemporaryDirectory() as parent:
            work = pathlib.Path(parent) / "request"
            work.mkdir()
            with mock.patch.object(GITCODE.tempfile, "mkdtemp", return_value=str(work)):
                with mock.patch.object(
                    GITCODE,
                    "run_git",
                    side_effect=GITCODE.GitCodeDiffError("network failed"),
                ):
                    with self.assertRaisesRegex(GITCODE.GitCodeDiffError, "network failed"):
                        GITCODE.fetch_pr_diff("https://gitcode.com/cann/ops-nn", 9)
            self.assertFalse(work.exists())

    def test_git_subprocess_is_noninteractive_and_has_a_timeout(self) -> None:
        injected = {
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "url.https://evil.invalid/.insteadOf",
            "GIT_CONFIG_VALUE_0": "https://gitcode.com/",
            "GIT_ASKPASS": "/tmp/untrusted-askpass",
            "SSH_ASKPASS": "/tmp/untrusted-askpass",
        }
        with mock.patch.dict(os.environ, injected, clear=False):
            with mock.patch.object(
                GITCODE.subprocess,
                "run",
                return_value=completed(["git", "version"]),
            ) as runner:
                GITCODE.run_git(["version"])

        command = runner.call_args.args[0]
        kwargs = runner.call_args.kwargs
        self.assertEqual(command[0], "git")
        self.assertIn("credential.helper=", command)
        self.assertEqual(kwargs["env"]["GIT_TERMINAL_PROMPT"], "0")
        self.assertEqual(kwargs["env"]["GCM_INTERACTIVE"], "Never")
        self.assertNotIn("GIT_CONFIG_COUNT", kwargs["env"])
        self.assertNotIn("GIT_ASKPASS", kwargs["env"])
        self.assertNotIn("SSH_ASKPASS", kwargs["env"])
        self.assertGreater(kwargs["timeout"], 0)
        self.assertFalse(kwargs.get("shell", False))


class OutputTest(unittest.TestCase):
    def test_stdout_is_default_and_output_file_is_optional(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            GITCODE.write_output("diff\n", None)
        self.assertEqual(stdout.getvalue(), "diff\n")

        with tempfile.TemporaryDirectory() as directory:
            output = pathlib.Path(directory) / "review.diff"
            GITCODE.write_output("diff\n", output)
            self.assertEqual(output.read_text(encoding="utf-8"), "diff\n")


if __name__ == "__main__":
    unittest.main()
