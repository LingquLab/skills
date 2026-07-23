#!/usr/bin/env python3
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# Licensed under the CANN Open Software License Agreement Version 2.0.
"""Inventory local CANN package candidates without installing them."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
from collections import Counter


PACKAGE_SUFFIXES = (".run", ".deb", ".rpm", ".whl", ".tar", ".tar.gz", ".tgz", ".zip")
KNOWN_ROLES = ("toolkit", "ops", "kernels", "runtime", "compiler", "nnal")
RELEASE_FIELD_PATTERN = re.compile(
    r"^[0-9]+(?:\.[0-9A-Za-z]+)+(?:[-+][0-9A-Za-z][0-9A-Za-z.-]*)?$"
)


def role_hint(filename: str) -> str:
    normalized = filename.lower().replace("_", "-")
    for role in KNOWN_ROLES:
        tokens = ("kernel", "kernels") if role == "kernels" else (role,)
        for token in tokens:
            if re.search(rf"(?:^|-){re.escape(token)}(?:-|\.|$)", normalized):
                return role
    return "unknown"


def is_package(path: pathlib.Path) -> bool:
    name = path.name.lower()
    return path.is_file() and any(name.endswith(suffix) for suffix in PACKAGE_SUFFIXES)


def release_fields(filename: str) -> tuple[str, ...]:
    """Return exact underscore-delimited release fields from a CANN artifact name."""
    lowered = filename.casefold()
    for suffix in sorted(PACKAGE_SUFFIXES, key=len, reverse=True):
        if lowered.endswith(suffix):
            filename = filename[: -len(suffix)]
            break
    return tuple(
        field
        for field in filename.split("_")
        if RELEASE_FIELD_PATTERN.fullmatch(field) is not None
    )


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect exact local CANN package candidates without installing them."
    )
    parser.add_argument("packages", nargs="*", type=pathlib.Path)
    parser.add_argument("--directory", type=pathlib.Path, help="scan one directory, non-recursively")
    parser.add_argument(
        "--require-role", action="append", default=[], choices=KNOWN_ROLES,
        help="require exactly one candidate with this filename role hint",
    )
    parser.add_argument(
        "--expected-version",
        help="require this case-insensitive release token in every candidate filename",
    )
    parser.add_argument("--sha256", action="store_true", help="hash each local artifact")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    candidates = list(args.packages)
    input_errors: list[str] = []

    if args.directory is not None:
        if not args.directory.is_dir():
            input_errors.append(f"directory does not exist: {args.directory}")
        else:
            candidates.extend(path for path in args.directory.iterdir() if is_package(path))

    unique: dict[str, pathlib.Path] = {}
    for path in candidates:
        if not is_package(path):
            input_errors.append(f"not a recognized package file: {path}")
            continue
        resolved = path.resolve()
        unique[str(resolved)] = resolved

    packages = []
    for path in sorted(unique.values(), key=lambda item: item.name):
        item = {
            "path": str(path),
            "filename": path.name,
            "role_hint": role_hint(path.name),
            "release_fields": list(release_fields(path.name)),
            "size_bytes": path.stat().st_size,
        }
        if args.sha256:
            item["sha256"] = sha256(path)
        packages.append(item)

    counts = Counter(item["role_hint"] for item in packages)
    ambiguous_roles = sorted(
        role for role, count in counts.items() if role != "unknown" and count > 1
    )
    missing_roles = sorted(role for role in set(args.require_role) if counts[role] == 0)
    version_mismatches = []
    if args.expected_version:
        expected = args.expected_version.casefold()
        version_mismatches = [
            item["filename"]
            for item in packages
            if expected not in {field.casefold() for field in item["release_fields"]}
        ]

    errors = list(input_errors)
    if not packages:
        errors.append("no package candidates selected")
    if ambiguous_roles:
        errors.append("multiple candidates for role(s): " + ", ".join(ambiguous_roles))
    if missing_roles:
        errors.append("missing required role(s): " + ", ".join(missing_roles))
    if version_mismatches:
        errors.append(
            "exact underscore-delimited release field is absent from: "
            + ", ".join(version_mismatches)
        )

    result = {
        "success": not errors,
        "expected_version_token": args.expected_version,
        "packages": packages,
        "role_counts": dict(sorted(counts.items())),
        "ambiguous_roles": ambiguous_roles,
        "missing_roles": missing_roles,
        "errors": errors,
        "note": "Filename role/version checks and local hashes are not compatibility or authenticity proof.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
