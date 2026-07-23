# SIMT Review

SIMT API naming and availability can change across CANN releases. First inspect the target headers and project migration policy.

## Version Check

Locate definitions and call sites for the API under review:

```bash
rg -n '\b(GetThreadNum|GetThreadIdx|GetBlockIdx|GetBlockNum|VF_CALL|Dim3|UintDiv)\b' <roots>
rg -n '\b(threadIdx|blockIdx|blockDim|gridDim)\b' <roots>
```

Compare the C++-style and C-style forms in the selected headers. Do not assume one form is forbidden merely because the other exists.

## Migration Checks

- Preserve the original x/y/z dimension when replacing thread or block index helpers.
- Avoid local identifiers that collide with built-in names such as `threadIdx`, `blockIdx`, `blockDim`, or `gridDim` when those built-ins are active.
- Confirm launch wrappers, dimension types, math helpers, atomics, barriers, and shuffle operations have equivalent semantics before replacement.
- Keep an API such as `UintDiv` when the target headers provide no documented equivalent.
- Check namespace and header placement required by the selected compiler.
- Compile the migrated Kernel with the real target toolchain; textual replacement is not sufficient evidence.

Report a style migration as required only when the target headers, compiler diagnostics, or repository policy establish that requirement.
