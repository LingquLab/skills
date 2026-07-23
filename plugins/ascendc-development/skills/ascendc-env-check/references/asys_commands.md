# Read-Only `asys` Commands

Use `asys` only when it is on `PATH` or is found below the toolkit root selected by the environment check. Do not claim one fixed installation path.

## Status Queries

```bash
asys health
asys info -r status
asys info -r hardware
asys info -r software
```

Subcommands and selectors can vary by release. Inspect `asys --help` and the version-matched official documentation before adding a selector such as `-d`; do not assume it shares an identifier namespace with `npu-smi` or a runtime API.

Treat `Healthy`, `Warning`, and other states as raw diagnostic evidence. A warning is not proof that a device is usable for the requested workload.

Hardware diagnostic modes may stress or change device state. Do not run them as part of the default environment check.
