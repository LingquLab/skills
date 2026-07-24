# Operator Validation Matrix

Scale evidence with the changed contract and report each layer separately.

| Layer | What it can establish | Minimum useful cases | What it cannot establish |
|---|---|---|---|
| schema/inference unit tests | `OpDef`, shape, type, attribute behavior | valid, invalid, scalar/empty, dynamic, broadcast boundaries | Host Tiling, compile, device behavior |
| Host Tiling unit tests | checked arithmetic, fields, keys, partition, workspace | smallest, tail, zero/invalid capacity, max supported, every key | Kernel ABI or execution |
| target compile | API availability, templates, generated variants, resource/compiler acceptance | every supported type/key/model | numerical or runtime correctness |
| Kernel unit/CPU/simulator | selected algorithm paths and some bounds | full tile, tail, empty if supported, special values | complete hardware ordering/performance |
| ACLNN/opapi integration | registration, package lookup, executor/workspace lifecycle | success and invalid input, zero/nonzero workspace | unsupported framework paths or performance |
| direct-launch integration | binary/ABI, tiling/workspace, stream/error path | success, tail, invalid input, async completion | registered package behavior |
| real hardware | device correctness, exceptions, hangs, precision, timing | representative and boundary shapes on target SoC | other products/releases |

## Required Consistency Tests

- Every declared supported data type and TilingKey compiles and has a reachable test.
- Host-produced serialized Tiling data is consumed by the same Kernel ABI and field units.
- `blockDim` partition covers the logical range without gaps, overlaps, or out-of-bounds last-core access.
- Workspace zero and nonzero paths use the exact size and lifetime promised by the invocation API.
- Registered and direct paths produce equivalent results during migration, including errors and tails.
- Floating-point contracts cover tolerance, accumulation type, `NaN`/Inf/signed-zero behavior when promised, and representative magnitude ranges.

## Performance Evidence

Warm up, synchronize at the documented boundary, use device-side timing or a version-matched official profiler, retain shape/dtype/layout/target/build metadata, and compare a stable baseline. Compile success, simulator timing, or one unrepeatable sample is not a speedup.

## Handoff

When a layer is unavailable, record the exact missing tool/hardware/package, the command or test that remains, expected invariant, and artifact needed. Do not collapse “not run” into “passed.”
