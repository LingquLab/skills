# CANN Installation Evidence and Dependency Inventory

Do not use one global dependency list for every CANN release. Build the plan from the official installation guide and release notes for the selected release, installation channel, host platform, and Ascend product.

## Host Inventory

Collect these facts without changing the host:

```bash
uname -m
cat /etc/os-release
python3 --version
python3 -m pip --version
npu-smi info
```

Also record:

- exact Ascend SoC or product model and device count
- driver and firmware versions from raw tool output
- any discovered CANN roots and their version metadata files
- installation owner and destination path
- system-wide, user-local, container, compile-only, or runtime requirement
- shell, network restrictions, offline artifact location, free space, and rollback constraints

A failed optional inventory command is evidence to report, not a reason to guess a value.

## Version-Matched Official Evidence

Use the bundled official documentation client before constructing commands:

```bash
python3 <skill-dir>/../ascendc-docs-search/scripts/search_ascend_docs.py \
  'CANN installation package toolkit ops' --version <release> \
  --fetch --max-results 5

python3 <skill-dir>/../ascendc-docs-search/scripts/search_ascend_docs.py \
  'CANN release notes driver firmware compatibility' --version <release> \
  --fetch --max-results 5
```

Record the direct official URLs, returned document versions, and the relevant package or compatibility text. Search separately for the chosen channel (run package, operating-system repository, Conda, Pip, or container) because their package names and boundaries differ.

From the matching documents, determine:

- supported OS release and CPU architecture
- supported Python versions and exact Python dependencies
- matching driver and firmware releases
- required toolkit, compiler/runtime, ops or kernel packages for the target SoC
- whether components must share one installation path
- supported installation order, privilege model, disk space, and filesystem requirements
- official integrity verification and uninstall/rollback procedure

Do not use search summaries alone when the fetched page or direct official page is available.

## Exact Package Plan

Use one row per selected component:

| Role | Exact artifact/package | Release | Arch/SoC | Official source | Integrity evidence | Destination | Privilege | Rollback |
|---|---|---|---|---|---|---|---|---|
| toolkit | `<exact name>` | `<release>` | `<arch>` | `<official URL/repo>` | `<published checksum/signature>` | `<path>` | `<user/root>` | `<official method>` |
| ops/kernel | `<exact name>` | `<release>` | `<SoC>` | `<official URL/repo>` | `<published checksum/signature>` | `<path>` | `<user/root>` | `<official method>` |

Add driver, firmware, runtime, compiler, NNAL, or framework packages only when the selected release documentation requires them. Do not assume that every release uses the same package split.

## Offline Artifact Inspection

Enumerate candidate files without installing them:

```bash
python3 <skill-dir>/scripts/inspect_packages.py --directory <download-directory> \
  --require-role toolkit --require-role ops \
  --expected-version <exact-release-token> --sha256
```

The script rejects an empty set, a missing required role, multiple candidates for one recognized role, and filenames without an exact underscore-delimited release field matching the expected value. To resolve ambiguity, pass only the explicitly selected files:

```bash
python3 <skill-dir>/scripts/inspect_packages.py <exact-toolkit-file> <exact-ops-file> \
  --require-role toolkit --require-role ops \
  --expected-version <exact-release-token> --sha256
```

The generated SHA-256 identifies the local bytes. Compare it with an official published checksum or validate the official signature; a locally computed hash alone does not establish authenticity or compatibility.

## Approval Packet

Before mutation, present:

- host and compatibility evidence
- completed exact package plan
- exact download, integrity-check, install, and rollback commands
- files, repositories, users, groups, services, profiles, and installation paths that will change
- expected downtime or workload impact
- which actions require network access, elevated privilege, or persistence

Obtain approval before downloads, repository/key changes, privileged commands, installation, service changes, or profile edits. Sourcing the selected vendor environment script in a disposable shell is preferable for initial verification; persistence is a separate approval.

## Layered Verification

1. Verify local artifact integrity or installed package-manager identity.
2. Verify installed version metadata and cross-package release agreement.
3. In a disposable shell, verify toolkit, compiler, runtime, and operator paths resolve.
4. Run the read-only environment and NPU checks.
5. Compile a minimal source with the intended compiler and headers.
6. Run a bounded hardware smoke test only when runtime proof is required and a device is available.

Report each layer independently. Host discovery is not compile proof, and compile success is not real-device runtime proof.
