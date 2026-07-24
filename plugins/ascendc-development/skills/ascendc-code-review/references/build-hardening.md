# Build Hardening Review

Apply these checks to Host and Tiling binaries where the target toolchain supports them. Kernel device compilation uses a different model and must be reviewed against its own compiler documentation.

## Checks

- Confirm release builds do not silently disable required warnings or security checks.
- Check compiler and linker flags for stack protection, relocation hardening, immediate binding, and non-executable data where supported.
- Verify `_FORTIFY_SOURCE` is paired with an optimization level that enables it.
- Confirm debug-only flags, sanitizers, and verbose diagnostics do not leak into production artifacts unintentionally.
- Inspect the final link command or ELF properties rather than relying only on source CMake options.
- Distinguish shared libraries, executables, static archives, and device objects; not every property applies to every artifact.

Example ELF inspection commands:

```bash
readelf -W -l '<binary>'
readelf -W -d '<binary>'
readelf -W -s '<binary>'
```

Use the target platform's approved build policy when it specifies stricter or different flags.
