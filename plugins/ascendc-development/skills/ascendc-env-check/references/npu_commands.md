# Read-Only NPU Commands

`npu-smi` subcommands vary by driver release. Start with commands supported by the installed binary and inspect `npu-smi --help` before using optional selectors.

## Basic Status

```bash
npu-smi -v
npu-smi info
npu-smi info -i 0
```

Where supported, bounded detail queries may include:

```bash
npu-smi info -t memory -i 0
npu-smi info -t temp -i 0
npu-smi info -t power -i 0
npu-smi info -t usages -i 0
```

Do not use `npu-smi top` in an automated check because it is interactive. Do not run process release, device reset, lock, unlock, or performance-mode commands during diagnosis unless the user explicitly requests that state change and the affected workloads are understood.

## Interpretation

- Capture the full command output and exit status; table formats differ between releases.
- Distinguish card, device, and chip identifiers before selecting an `-i` value.
- A device listed with a warning is not automatically safe for a workload. Inspect the reported health details and active processes.
- Command presence proves only that the tool is installed, not that a supported device is visible.
