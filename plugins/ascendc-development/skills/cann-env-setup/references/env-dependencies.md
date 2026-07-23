# CANN Dependency Inventory

Do not use one global dependency list for every CANN release. Build the installation plan from the official documentation for the selected release and host platform.

## Host Inventory

Collect these facts before choosing packages:

```bash
uname -m
cat /etc/os-release
python3 --version
python3 -m pip --version
npu-smi info
```

Also record:

- Ascend SoC or product model
- driver and firmware versions
- installation owner and destination path
- system-wide, user-local, container, compile-only, or runtime requirement
- network restrictions and availability of offline packages

## Compatibility Sources

Use the selected CANN release notes and installation guide to determine:

- supported OS releases and CPU architecture
- supported Python versions and Python packages
- matching driver and firmware versions
- required toolkit, compiler, runtime, ops, and optional component packages
- disk-space and filesystem requirements
- supported installation methods

Treat package-manager metadata and vendor `version.info` files as supporting evidence, not as a replacement for the release matrix.

## Installation Planning

For every package, record the exact version, official source, checksum when published, destination, privilege requirement, and rollback method. Use the host's native package manager only after verifying the repository configuration and package names for that release.

Do not add third-party mirrors, replace system Python, or modify a shell profile unless the user explicitly approves that change.

## Verification

After installation, verify the vendor environment script in the current shell, inspect the resolved paths, and run a minimal compile before persisting configuration. Runtime validation requires a visible supported NPU and a bounded smoke test.
