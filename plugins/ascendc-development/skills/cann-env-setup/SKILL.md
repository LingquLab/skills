---
name: cann-env-setup
description: Plan, install, configure, or repair a CANN development environment for Ascend hardware with explicit version and platform compatibility checks. Use when selecting CANN packages, preparing offline or repository-based installation, configuring environment scripts, resolving driver/toolkit/ops mismatches, or verifying a new CANN setup.
---

# CANN Environment Setup

Treat installation commands and version matrices as time-sensitive. Verify them against current official CANN documentation before changing the host.

## Prepare

1. Identify the target host, OS and release, architecture, Ascend SoC, driver and firmware versions, current CANN state, required workload, and whether installation must be system-wide or user-local.
2. Check device and existing environment state with `$ascendc-env-check` when available.
3. Determine the exact CANN release and package set required by the workload. Use the sibling `$ascendc-docs-search` script to retrieve the selected release's official installation guide, package list, and release notes; record the direct URLs and returned document version.
4. Verify driver, firmware, toolkit, ops, compiler, Python, OS, architecture, and SoC compatibility from those version-matched sources. Do not apply commands from an unmatched search result.
5. Choose the supported installation channel for that release: vendor run packages, official package repositories, containers, or another documented method. Do not mix components from different releases without an explicit compatibility statement.
6. Build an exact package plan. For each component, record its role, exact filename or repository package name, release, architecture or SoC variant, source URL/repository, published checksum or signature, destination, privilege requirement, dependencies, and rollback method.

Read `references/env-dependencies.md` for the dependency-inventory process. Treat commands there as examples to adapt to the detected OS, not as unconditional installation commands.

Resolve `<skill-dir>` as the directory containing this `SKILL.md`. For offline
artifacts, reject ambiguous glob selections before installation:

```bash
python3 <skill-dir>/scripts/inspect_packages.py --directory <download-directory> \
  --require-role toolkit --require-role ops \
  --expected-version <exact-release-token> --sha256
```

The script requires the expected release to appear as an exact underscore-delimited version field; it is still only a filename and local-integrity check, not compatibility proof. If it reports multiple candidates for one recognized role, select the exact SoC/release artifacts explicitly and rerun it with only those file paths.

## Official Evidence

Resolve the documentation-search script relative to this skill's sibling and query the release requested by the user:

```bash
python3 <skill-dir>/../ascendc-docs-search/scripts/search_ascend_docs.py \
  'CANN installation package toolkit ops' --version <release> \
  --fetch --max-results 5
```

Run additional focused queries for the release notes and the target installation channel. Accept evidence only when the result URL is on the official Huawei Ascend documentation site and its returned version matches the plan. If search cannot retrieve a matching page, stop before installation and report the missing compatibility evidence.

## Change Boundary

Before downloading packages, using `sudo`, adding repositories, installing software, or editing shell profiles:

1. Show the exact packages, versions, source URLs, checksums or signatures, destination paths, commands, and rollback steps.
2. Explain whether the action changes system state or only the current shell.
3. Obtain user approval for privileged or persistent changes.

Never append to `.bashrc`, `.zshrc`, or another startup file as an implicit side effect. Prefer sourcing the vendor `set_env.sh` in the current shell first, then persist only when requested.

Do not install from a shell glob, the first item returned by `ls`, or a directory containing multiple same-role candidates. Do not add a repository until its official URL, signing/key procedure, release, OS, and architecture have been verified.

## Verify

After installation or repair, verify in layers:

1. Local artifact checksum/signature or installed package-manager identity matches the approved plan.
2. Package files and version metadata exist at the selected path and agree on the selected release.
3. In a disposable shell, the vendor environment script sets paths that resolve to real directories and libraries.
4. Read-only driver and NPU diagnostics succeed on the target host.
5. A minimal compile uses the intended compiler and headers.
6. A bounded runtime smoke test succeeds on real hardware when runtime proof is required.

Keep compile-only, simulator, and real-hardware results as separate claims. Report the installed versions, commands run, and any rollback or cleanup needed.
