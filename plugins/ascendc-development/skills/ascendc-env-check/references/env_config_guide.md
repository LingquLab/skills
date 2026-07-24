# CANN Environment Evidence

Use environment variables as evidence about the current process, not as the only installation inventory.

## Variable Semantics

| Variable | What it establishes | What it does not establish |
|---|---|---|
| `ASCEND_HOME_PATH` | The CANN toolkit root selected in the current shell when it resolves to a real toolkit tree | That no toolkit is installed when the variable is unset |
| `ASCEND_OPP_PATH` | The operator repository root selected in the current shell when it resolves to a directory | That a specific ops package, built-in operator, or custom operator is complete and loadable |
| `ASCEND_CUSTOM_OPP_PATH` | Additional custom-operator search paths for documented framework scenarios | A replacement for every built-in operator path or dynamic-library search path |
| `LD_LIBRARY_PATH` | Additional dynamic-loader search paths for the current process | That all referenced libraries exist or are ABI-compatible |

Do not describe `ASCEND_OPP_PATH` as belonging only to a separately installed ops package. It names an operator repository and may expose built-in and vendor content depending on the selected CANN layout.

## Toolkit Discovery

`check_env.sh` tries the active environment first, then explicit toolkit-related variables, compiler and profiler locations, an optional `ASCEND_ENV_CHECK_ROOTS` colon-separated override, and a small set of common installation locations. It does not scan the whole filesystem.

Use the override when the target uses a nonstandard layout:

```bash
ASCEND_ENV_CHECK_ROOTS='<candidate-root-1>:<candidate-root-2>' \
  bash '<skill-dir>/scripts/check_env.sh'
```

This command changes only the child process environment. A discovered root with an unset `ASCEND_HOME_PATH` proves that toolkit files exist, but also shows that the caller's shell has not selected that root.

## Version Evidence

For the selected toolkit root, inspect these files when present:

| Candidate | Useful fields |
|---|---|
| `<toolkit-root>/compiler/version.info` | `Version`, `required_package_runtime_version`, and other `required_package_*` fields |
| `<toolkit-root>/version.info` | Release-specific package metadata |
| `<toolkit-root>/version.cfg` | Release-specific version text or fields |

Do not infer a version only from a directory basename. Record the exact metadata file used. Compatibility still requires the matching release notes because local metadata does not describe every supported OS, Python, driver, firmware, or SoC combination.

## Component Metadata

Current combined and independent installations can expose component metadata at `<toolkit-root>/share/info/<component-id>/version.info`. Inventory every bounded direct child instead of reducing the installation to one toolkit/ops string. Record:

- component ID and metadata path;
- resolved path and in-root aliases, including a `compiler/version.info` symlink;
- `Version` and its exact field/line provenance;
- `required_package_*` fields separately from the component's own version;
- whether version text is equal, different, or unknown relative to a resolved toolkit claim.

Equal/different is only a text relation. Compatibility must come from the selected release's official component constraints. Refuse symlinks outside the selected toolkit root and report conflicting or oversized metadata instead of selecting the first claim.

## SoC and NpuArch Evidence

`inspect_cann_state.py` correlates only explicit evidence:

| State | Meaning |
|---|---|
| `runtime_soc_correlated` | A named SoC claim from a bounded capture exactly matched one installed platform config with one explicit `NpuArch` field |
| `toolkit_metadata_only` | A user-supplied `--soc` exactly matched toolkit metadata; hardware identity was not detected |
| `build_target_only` | Only `--build-target` supplied an architecture value |
| `unknown` | Evidence was absent, conflicting, ambiguous, or unmatched |

Keep driver claims, runtime SoC claims, toolkit configuration, and build targets as separate provenance. Do not map product names by substring or a hard-coded table. Multiple runtime SoCs or platform matches remain ambiguous.

## Read-Only Verification

```bash
printf 'ASCEND_HOME_PATH=%s\n' "${ASCEND_HOME_PATH:-<unset>}"
printf 'ASCEND_OPP_PATH=%s\n' "${ASCEND_OPP_PATH:-<unset>}"
command -v ccec || command -v bisheng
command -v npu-smi
bash '<skill-dir>/scripts/check_env.sh'
python3 '<skill-dir>/scripts/inspect_cann_state.py' \
  --toolkit-root '<selected-toolkit-root>' --json
```

Do not source an environment script, install an operator package, or alter loader paths as part of this check. Those are setup actions and require a separately reviewed change plan.
