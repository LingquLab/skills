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
5. Correlate environment variables with real paths and version metadata. Do not treat a set variable alone as proof of a usable installation.
6. Report errors, warnings, and unavailable checks separately. A host-only environment check does not prove that a kernel compiles or runs correctly on hardware.

## Reference Routing

- Environment variables and version metadata: `references/env_config_guide.md`
- NPU commands: `references/npu_commands.md`
- `asys` fallback: `references/asys_commands.md`
- Symptom-based diagnosis: `references/troubleshooting.md`

## Safety

- Do not install packages, source user profiles permanently, modify shell startup files, reset devices, or terminate workloads during an environment check.
- Avoid interactive monitors such as `npu-smi top` in automation; use bounded status commands.
- Do not infer device availability from command presence alone. Capture command exit status and actual device output.
- Redact tokens, credentials, and unrelated environment variables.

## Output

State the target host and user, detected CANN version and source path, relevant toolkit/operator variables, NPU visibility, and the exact failing boundary. Give the next diagnostic or setup action without performing a mutation unless requested.
