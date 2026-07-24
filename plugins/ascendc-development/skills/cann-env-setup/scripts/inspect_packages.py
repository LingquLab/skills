#!/usr/bin/env python3
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# Licensed under the CANN Open Software License Agreement Version 2.0.
"""Inventory local CANN package candidates without installing them."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import stat
import sys
from collections import Counter


PACKAGE_SUFFIXES = (".run", ".deb", ".rpm", ".whl", ".tar", ".tar.gz", ".tgz", ".zip")
MAX_PACKAGE_BYTES = 16 * 1024 * 1024 * 1024
MAX_DIRECTORY_ENTRIES = 4096
KNOWN_ROLES = ("toolkit", "ops", "kernels", "runtime", "compiler", "nnal")
KNOWN_COMPONENTS = (
    "toolkit",
    "ops",
    "kernels",
    "runtime",
    "compiler",
    "nnal",
    "asc-devkit",
    "asc-tools",
    "ops-nn",
    "ops-transformer",
    "ops-tensor",
    "simulator",
)
SPECIFIC_COMPONENTS = (
    "asc-devkit",
    "asc-tools",
    "ops-nn",
    "ops-transformer",
    "ops-tensor",
    "simulator",
)
GENERIC_COMPONENTS = tuple(
    component for component in KNOWN_COMPONENTS if component not in SPECIFIC_COMPONENTS
)
COMPONENT_ALIASES = {"kernels": ("kernel", "kernels")}
COMPONENT_ROLES = {
    "toolkit": "toolkit",
    "ops": "ops",
    "kernels": "kernels",
    "runtime": "runtime",
    "compiler": "compiler",
    "nnal": "nnal",
    "ops-nn": "ops",
    "ops-transformer": "ops",
    "ops-tensor": "ops",
}
RELEASE_FIELD_PATTERN = re.compile(
    r"^[0-9]+(?:\.[0-9A-Za-z]+)+(?:[-+][0-9A-Za-z][0-9A-Za-z.-]*)?$"
)


def has_component_token(normalized: str, component: str) -> bool:
    aliases = COMPONENT_ALIASES.get(component, (component,))
    return any(
        re.search(rf"(?:^|-){re.escape(alias)}(?:-|\.|$)", normalized) is not None
        for alias in aliases
    )


def component_hint(filename: str) -> str:
    normalized = filename.casefold().replace("_", "-")
    specific_matches = [
        component
        for component in SPECIFIC_COMPONENTS
        if has_component_token(normalized, component)
    ]
    if len(specific_matches) == 1:
        return specific_matches[0]
    if specific_matches:
        return "unknown"

    generic_matches = [
        component
        for component in GENERIC_COMPONENTS
        if has_component_token(normalized, component)
    ]
    if len(generic_matches) == 1:
        return generic_matches[0]
    return "unknown"


def role_hint(filename: str) -> str:
    return COMPONENT_ROLES.get(component_hint(filename), "unknown")


def has_package_suffix(path: pathlib.Path) -> bool:
    name = path.name.lower()
    return any(name.endswith(suffix) for suffix in PACKAGE_SUFFIXES)


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


def inspect_package_file(path: pathlib.Path, *, hash_file: bool) -> tuple[int, str | None]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    if path.is_symlink():
        raise ValueError("symbolic links are not accepted")
    descriptor = os.open(path, flags)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError("not a regular file")
        if metadata.st_size > MAX_PACKAGE_BYTES:
            raise ValueError(f"file exceeds the {MAX_PACKAGE_BYTES}-byte inspection limit")
        if not hash_file:
            return metadata.st_size, None

        digest = hashlib.sha256()
        total = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_PACKAGE_BYTES:
                raise ValueError(f"file exceeds the {MAX_PACKAGE_BYTES}-byte inspection limit")
            digest.update(chunk)
        return total, digest.hexdigest()
    finally:
        os.close(descriptor)


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
        "--require-component", action="append", default=[], choices=KNOWN_COMPONENTS,
        help="require exactly one candidate with this filename component hint",
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
        try:
            directory_root = args.directory.resolve(strict=True)
        except (OSError, RuntimeError):
            directory_root = None
        if directory_root is None or not directory_root.is_dir():
            input_errors.append(f"directory does not exist: {args.directory}")
        else:
            try:
                for index, path in enumerate(directory_root.iterdir()):
                    if index >= MAX_DIRECTORY_ENTRIES:
                        input_errors.append(
                            f"directory scan exceeds the {MAX_DIRECTORY_ENTRIES}-entry limit: "
                            f"{args.directory}"
                        )
                        break
                    if has_package_suffix(path):
                        candidates.append(path)
            except OSError as error:
                input_errors.append(f"cannot scan directory {args.directory}: {error}")

    unique: dict[str, pathlib.Path] = {}
    for path in candidates:
        if not has_package_suffix(path):
            input_errors.append(f"not a recognized package file: {path}")
            continue
        absolute = pathlib.Path(os.path.abspath(path))
        unique[str(absolute)] = absolute

    packages = []
    for path in sorted(unique.values(), key=lambda item: item.name):
        try:
            size_bytes, digest = inspect_package_file(path, hash_file=args.sha256)
        except (OSError, ValueError) as error:
            input_errors.append(f"cannot inspect package file {path}: {error}")
            continue
        item = {
            "path": str(path),
            "filename": path.name,
            "role_hint": role_hint(path.name),
            "component_hint": component_hint(path.name),
            "release_fields": list(release_fields(path.name)),
            "size_bytes": size_bytes,
        }
        if digest is not None:
            item["sha256"] = digest
        packages.append(item)

    role_counts = Counter(item["role_hint"] for item in packages)
    component_counts = Counter(item["component_hint"] for item in packages)
    required_roles = set(args.require_role)
    required_components = set(args.require_component)
    ambiguous_roles = sorted(
        role for role in required_roles if role_counts[role] > 1
    )
    ambiguous_components = sorted(
        component
        for component in required_components
        if component_counts[component] > 1
    )
    missing_roles = sorted(role for role in required_roles if role_counts[role] == 0)
    missing_components = sorted(
        component
        for component in required_components
        if component_counts[component] == 0
    )
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
    if ambiguous_components:
        errors.append(
            "multiple candidates for component(s): " + ", ".join(ambiguous_components)
        )
    if missing_roles:
        errors.append("missing required role(s): " + ", ".join(missing_roles))
    if missing_components:
        errors.append("missing required component(s): " + ", ".join(missing_components))
    if version_mismatches:
        errors.append(
            "exact underscore-delimited release field is absent from: "
            + ", ".join(version_mismatches)
        )

    result = {
        "success": not errors,
        "expected_version_token": args.expected_version,
        "packages": packages,
        "role_counts": dict(sorted(role_counts.items())),
        "component_counts": dict(sorted(component_counts.items())),
        "ambiguous_roles": ambiguous_roles,
        "ambiguous_components": ambiguous_components,
        "missing_roles": missing_roles,
        "missing_components": missing_components,
        "errors": errors,
        "note": "Filename role/component/version checks and local hashes are not compatibility or authenticity proof.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
