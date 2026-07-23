#!/usr/bin/env python3
"""Offline tests for Ascend environment and package-inspection scripts."""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
ENV_SKILL = ROOT / "plugins/ascendc-development/skills/ascendc-env-check"
SETUP_SKILL = ROOT / "plugins/ascendc-development/skills/cann-env-setup"


def clean_env() -> dict[str, str]:
    env = os.environ.copy()
    for name in (
        "ASCEND_HOME_PATH",
        "ASCEND_OPP_PATH",
        "ASCEND_TOOLKIT_HOME",
        "ASCEND_HOME",
        "CANN_HOME",
        "ASCEND_ENV_CHECK_ROOTS",
    ):
        env.pop(name, None)
    return env


class EnvironmentScriptsTest(unittest.TestCase):
    def test_check_env_discovers_toolkit_without_ascend_home_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = pathlib.Path(temporary)
            toolkit = base / "cann-9.1.0"
            (toolkit / "compiler").mkdir(parents=True)
            (toolkit / "runtime").mkdir()
            (toolkit / "opp/vendors/custom").mkdir(parents=True)
            (toolkit / "compiler/version.info").write_text(
                'Version=9.1.0\nrequired_package_runtime_version="9.1.0"\n',
                encoding="utf-8",
            )
            (toolkit / "opp/version.info").write_text("Version=9.1.0\n", encoding="utf-8")
            (toolkit / "set_env.sh").write_text("# fixture\n", encoding="utf-8")

            env = clean_env()
            env["ASCEND_ENV_CHECK_ROOTS"] = str(toolkit)
            completed = subprocess.run(
                ["bash", str(ENV_SKILL / "scripts/check_env.sh")],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("[info] ASCEND_HOME_PATH is not set", completed.stdout)
        canonical_toolkit = pathlib.Path(os.path.realpath(toolkit))
        self.assertIn(f"toolkit root={canonical_toolkit} (source: discovery)", completed.stdout)
        self.assertIn("CANN version=9.1.0", completed.stdout)
        self.assertIn("OPP version=9.1.0", completed.stdout)
        self.assertIn("summary: errors=0", completed.stdout)

    def test_check_env_rejects_invalid_active_path_even_if_another_root_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = pathlib.Path(temporary)
            toolkit = base / "toolkit"
            (toolkit / "compiler").mkdir(parents=True)
            (toolkit / "set_env.sh").write_text("# fixture\n", encoding="utf-8")
            env = clean_env()
            env["ASCEND_HOME_PATH"] = str(base / "missing")
            env["ASCEND_ENV_CHECK_ROOTS"] = str(toolkit)
            completed = subprocess.run(
                ["bash", str(ENV_SKILL / "scripts/check_env.sh")],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 1)
        self.assertIn("[error] ASCEND_HOME_PATH does not exist", completed.stdout)
        canonical_toolkit = pathlib.Path(os.path.realpath(toolkit))
        self.assertIn(f"toolkit root={canonical_toolkit} (source: discovery)", completed.stdout)

    def test_check_env_does_not_treat_driver_version_root_as_toolkit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            driver_root = pathlib.Path(temporary) / "Ascend"
            driver_root.mkdir()
            (driver_root / "version.info").write_text("version=25.5.0\n", encoding="utf-8")
            env = clean_env()
            env["ASCEND_HOME_PATH"] = str(driver_root)
            env["ASCEND_ENV_CHECK_ROOTS"] = str(driver_root)
            env["HOME"] = temporary
            completed = subprocess.run(
                ["bash", str(ENV_SKILL / "scripts/check_env.sh")],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertIn("is not recognizable as a CANN toolkit root", completed.stdout)
        self.assertNotIn("25.5.0", completed.stdout)

    def test_npu_info_preserves_bounded_raw_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            bindir = pathlib.Path(temporary)
            npu_smi = bindir / "npu-smi"
            npu_smi.write_text(
                "#!/usr/bin/env bash\nprintf 'raw-line-1\\nraw-line-2\\nraw-line-3\\nraw-line-4\\n'\n",
                encoding="utf-8",
            )
            npu_smi.chmod(0o755)
            env = clean_env()
            env["PATH"] = f"{bindir}{os.pathsep}{env['PATH']}"
            env["ASCEND_NPU_MAX_LINES"] = "3"
            completed = subprocess.run(
                ["bash", str(ENV_SKILL / "scripts/npu_info.sh")],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("raw-line-1", completed.stdout)
        self.assertIn("raw-line-3", completed.stdout)
        self.assertNotIn("raw-line-4", completed.stdout)
        self.assertIn("[output truncated after 3 lines]", completed.stdout)

    def test_npu_info_caps_capture_bytes_before_rendering(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            bindir = pathlib.Path(temporary) / "bin"
            bindir.mkdir()
            npu_smi = bindir / "npu-smi"
            npu_smi.write_text(
                "#!/usr/bin/env bash\n"
                "for ((i = 0; i < 10000; i++)); do\n"
                "  printf 'abcdefghijklmnopqrstuvwxyz'\n"
                "done\n",
                encoding="utf-8",
            )
            npu_smi.chmod(0o755)
            env = clean_env()
            env["PATH"] = f"{bindir}{os.pathsep}{env['PATH']}"
            env["ASCEND_NPU_MAX_BYTES"] = "16"
            completed = subprocess.run(
                ["bash", str(ENV_SKILL / "scripts/npu_info.sh")],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("abcdefghijklmnop", completed.stdout)
        self.assertNotIn("qrstuvwxyz", completed.stdout)
        self.assertIn("[output truncated after 16 bytes]", completed.stdout)

    def test_npu_info_discovers_asys_from_common_user_toolkit_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = pathlib.Path(temporary) / "home"
            bindir = pathlib.Path(temporary) / "bin"
            toolkit = home / "Ascend/cann"
            asys = toolkit / "tools/ascend_system_advisor/asys/asys"
            bindir.mkdir()
            asys.parent.mkdir(parents=True)
            (toolkit / "compiler").mkdir()
            (toolkit / "set_env.sh").write_text("# fixture\n", encoding="utf-8")
            asys.write_text(
                "#!/usr/bin/env bash\nprintf 'asys-common-root-health\\n'\n",
                encoding="utf-8",
            )
            asys.chmod(0o755)
            npu_smi = bindir / "npu-smi"
            npu_smi.write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
            npu_smi.chmod(0o755)
            env = clean_env()
            env["HOME"] = str(home)
            env["PATH"] = f"{bindir}{os.pathsep}{env['PATH']}"
            completed = subprocess.run(
                ["bash", str(ENV_SKILL / "scripts/npu_info.sh")],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn(f"source: asys ({asys})", completed.stdout)
        self.assertIn("asys-common-root-health", completed.stdout)


class PackageInspectorTest(unittest.TestCase):
    def run_inspector(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SETUP_SKILL / "scripts/inspect_packages.py"), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_rejects_ambiguous_same_role_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = pathlib.Path(temporary)
            (directory / "Ascend-cann-toolkit_9.1.0_linux-aarch64.run").write_bytes(b"one")
            (directory / "Ascend-cann-toolkit_9.1.0_linux-aarch64-copy.run").write_bytes(b"two")
            (directory / "Ascend-cann-910b-ops_9.1.0_linux-aarch64.run").write_bytes(b"ops")
            completed = self.run_inspector(
                "--directory", str(directory), "--require-role", "toolkit", "--require-role", "ops"
            )

        payload = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(payload["ambiguous_roles"], ["toolkit"])

    def test_recognizes_real_kernels_package_role(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = pathlib.Path(temporary) / "Ascend-cann-kernels-910b_9.1.0_linux-aarch64.run"
            package.write_bytes(b"kernels")
            completed = self.run_inspector(
                str(package), "--require-role", "kernels", "--expected-version", "9.1.0"
            )

        payload = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(payload["role_counts"], {"kernels": 1})

    def test_rejects_version_substring_collision(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = pathlib.Path(temporary) / "Ascend-cann-toolkit_19.1.0_linux-aarch64.run"
            package.write_bytes(b"wrong release")
            completed = self.run_inspector(
                str(package), "--require-role", "toolkit", "--expected-version", "9.1.0"
            )

        payload = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 2)
        self.assertIn(package.name, payload["errors"][0])

    def test_exact_candidates_include_hash_and_version_sanity_check(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = pathlib.Path(temporary)
            toolkit = directory / "Ascend-cann-toolkit_9.1.0_linux-aarch64.run"
            ops = directory / "Ascend-cann-910b-ops_9.1.0_linux-aarch64.run"
            toolkit.write_bytes(b"toolkit")
            ops.write_bytes(b"ops")
            completed = self.run_inspector(
                str(toolkit), str(ops), "--require-role", "toolkit", "--require-role", "ops",
                "--expected-version", "9.1.0", "--sha256",
            )

        payload = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(payload["success"])
        self.assertEqual(payload["role_counts"], {"ops": 1, "toolkit": 1})
        self.assertTrue(all(len(item["sha256"]) == 64 for item in payload["packages"]))


if __name__ == "__main__":
    unittest.main()
