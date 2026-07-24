# Environment Check Troubleshooting

Keep this workflow read-only. Identify the failing layer before proposing a setup change.

## Toolkit Files Exist but the Shell Is Unconfigured

Evidence:

- `check_env.sh` reports an unset `ASCEND_HOME_PATH` and a discovered toolkit root.
- Version metadata exists under that root.
- Compiler tools may exist below the root but not on `PATH`.

Conclusion: CANN is installed, but the current shell has not selected that installation. Locate the vendor environment script near the reported root and hand the path to `$cann-env-setup`; do not source it or persist it during a read-only check.

## Active Path Is Invalid

Evidence:

- `ASCEND_HOME_PATH` or `ASCEND_OPP_PATH` is set to a missing or unrecognized directory.
- The script reports `[error]` and exits 1.

Conclusion: the active process environment is invalid even if a separate toolkit is discovered. Report both paths rather than silently substituting the discovered installation.

## Operator Repository Is Unclear

An unset `ASCEND_OPP_PATH` does not prove that an ops package is absent. Check whether an `opp` directory exists below the selected toolkit root and inspect package/version metadata. A `vendors` directory establishes only that vendor directories exist; it does not prove that their binaries can be loaded.

## No NPU Status Output

1. Run `npu-smi --help` if `npu-smi` exists, because supported subcommands vary by driver release.
2. Run `bash '<skill-dir>/scripts/npu_info.sh'` and preserve its stderr and exit status.
3. If it falls back to `asys`, record the exact executable and raw health output.
4. Treat a missing tool, a command failure, an empty result, and an unhealthy device as different boundaries.

Do not reset devices, release processes, switch performance modes, or inspect privileged kernel logs without a separate reason and approval.

## Device Selection

Do not use `ASCEND_DEVICE_ID` as a universal multi-card selector. Official environment-variable documentation defines it as a logical device ID for specified framework and AOE scenarios. Other runtimes may select devices through APIs, rank configuration, container visibility, or other documented variables. Determine the workload first and use its version-matched documentation.

Do not assume that an `npu-smi -i` selector is the same namespace as a runtime logical device ID. Confirm card, device, chip, and logical identifiers from the installed tool's help and raw status table.

## Container Boundary

Report separately whether device nodes are exposed to the container, whether driver utilities are callable, whether toolkit files exist in the container, and whether the current process environment selects them. Success at one layer does not prove the others.
