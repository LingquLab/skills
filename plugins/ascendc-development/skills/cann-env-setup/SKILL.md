---
name: cann-env-setup
description: Plan, install, configure, or repair a CANN development environment for Ascend hardware with explicit version and platform compatibility checks. Use when selecting CANN packages, preparing offline or repository-based installation, configuring environment scripts, resolving driver/toolkit/ops mismatches, or verifying a new CANN setup.
---

# CANN Environment Setup

Treat installation commands and version matrices as time-sensitive. Verify them against current official CANN documentation before changing the host.

## Prepare

1. Identify the target host, OS and release, architecture, Ascend SoC, driver and firmware versions, current CANN state, required workload, and whether installation must be system-wide or user-local.
2. Check device and existing environment state with `$ascendc-env-check` when available.
3. Determine the exact CANN release and package set required by the workload. Use official release notes and download documentation to verify driver, firmware, toolkit, ops, compiler, and Python compatibility.
4. Choose the supported installation channel for that release: vendor run packages, official package repositories, containers, or another documented method. Do not mix components from different releases without an explicit compatibility statement.

Read `references/env-dependencies.md` for the dependency-inventory process. Treat commands there as examples to adapt to the detected OS, not as unconditional installation commands.

## Change Boundary

Before downloading packages, using `sudo`, adding repositories, installing software, or editing shell profiles:

1. Show the exact packages, versions, source URLs, destination paths, and commands.
2. Explain whether the action changes system state or only the current shell.
3. Obtain user approval for privileged or persistent changes.

Never append to `.bashrc`, `.zshrc`, or another startup file as an implicit side effect. Prefer sourcing the vendor `set_env.sh` in the current shell first, then persist only when requested.

## Verify

After installation or repair, verify in layers:

1. Package files and version metadata exist at the selected path.
2. The vendor environment script sets paths that resolve to real directories and libraries.
3. Driver and NPU diagnostics succeed on the target host.
4. A minimal compile uses the intended compiler and headers.
5. A bounded runtime smoke test succeeds on real hardware when runtime proof is required.

Keep compile-only, simulator, and real-hardware results as separate claims. Report the installed versions, commands run, and any rollback or cleanup needed.
