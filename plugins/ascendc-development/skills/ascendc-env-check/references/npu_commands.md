# Read-Only NPU Commands

`npu-smi` subcommands vary by driver release. Start with commands supported by the installed binary and inspect `npu-smi --help` before using optional selectors.

## Basic Status

```bash
npu-smi -v
npu-smi info
npu-smi info -i 0
```

The meaning and accepted values of `-i` can vary with the installed release. Confirm the selector from `npu-smi --help` and the raw status table before using it. Where supported, bounded detail queries may include:

```bash
npu-smi info -t memory -i 0
npu-smi info -t temp -i 0
npu-smi info -t power -i 0
npu-smi info -t usages -i 0
```

Do not use `npu-smi top` in an automated check because it is interactive. Do not run process release, device reset, lock, unlock, or performance-mode commands during diagnosis unless the user explicitly requests that state change and the affected workloads are understood.

## Interpretation

- Capture bounded raw command output and the exit status; table formats differ between releases.
- Distinguish card, device, chip, and runtime logical identifiers before selecting an `-i` value.
- A device listed with a warning is not automatically safe for a workload. Inspect the reported health details and active processes.
- Command presence proves only that the tool is installed, not that a supported device is visible.
- `ASCEND_DEVICE_ID` is documented for specific framework and AOE scenarios; it is not a universal replacement for runtime API or rank-based device selection.
