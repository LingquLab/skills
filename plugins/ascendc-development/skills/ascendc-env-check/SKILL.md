---
name: ascendc-env-check
description: Inspect an Ascend development or runtime host for CANN environment variables, installed version metadata, toolkit and operator paths, diagnostic tools, and NPU visibility. Use for environment checks, npu-smi or asys diagnostics, CANN setup verification, missing-tool investigation, and read-only triage on a local or named remote machine.
---

# Ascend C Environment Check

Keep this skill read-only unless the user separately asks to change the environment.

## Workflow

1. Confirm the target machine. When a remote host is named, run checks on that host rather than assuming local state.
2. Verify identity and scope when permissions matter (`whoami`, `id`, and, only when relevant, `sudo -n true`).
3. Resolve paths relative to this skill directory and run:

```bash
bash scripts/check_env.sh
bash scripts/npu_info.sh
```

4. If a script is unavailable or its output format is not recognized, fall back to the commands in `references/npu_commands.md` and `references/asys_commands.md`.
5. Correlate environment variables with discovered toolkit roots, tool locations, real paths, and version metadata. A missing `ASCEND_HOME_PATH` means the current shell is not configured; it does not prove that CANN is absent.
6. Interpret `[error]` as an invalid active configuration, `[warn]` as missing or incomplete development evidence, and `[info]` as optional or discovered state. Warnings do not change the script's zero exit status; errors do.
7. Preserve the raw bounded device output from `npu_info.sh`. Do not infer card count, health, or identifier semantics by parsing one assumed table layout.
8. Keep host discovery, compile proof, and real-hardware runtime proof as separate conclusions.

## Reference Routing

- Environment variables and version metadata: `references/env_config_guide.md`
- NPU commands: `references/npu_commands.md`
- `asys` fallback: `references/asys_commands.md`
- Symptom-based diagnosis: `references/troubleshooting.md`

## Safety

- Do not install packages, source user profiles permanently, modify shell startup files, reset devices, or terminate workloads during an environment check.
- Avoid interactive monitors such as `npu-smi top` in automation; use bounded status commands.
- Do not infer device availability from command presence alone. Capture command exit status and the bounded raw device output.
- Redact tokens, credentials, and unrelated environment variables.

## Output

State the target host and user, selected or discovered toolkit root, detected CANN version and metadata source, operator repository evidence, NPU visibility, and the exact failing boundary. Distinguish an installed toolkit from an environment loaded in the current shell. Give the next diagnostic or setup action without performing a mutation unless requested.
