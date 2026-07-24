# Operator Invocation Paths

Select one authoritative path for the target use case. Names and generated files vary by CANN and framework release, so verify them in the target repository and installed headers.

## Registered Custom Operator

Trace the complete chain:

1. public schema and registration identity;
2. `OpDef`, input/output/attribute declarations, `InferShape`, and `InferDataType`;
3. Host Tiling entry, `TilingData`, TilingKey, `blockDim`, and workspace;
4. compiled Kernel variants and dispatch;
5. build targets, package metadata, vendor layout, and runtime lookup path;
6. exposed ACLNN/opapi or framework binding and its tests.

Registration and package generation are not runtime proof. Confirm the selected process resolves the intended package and binary.

## ACLNN Two-Stage Lifecycle

Treat workspace-size/executor preparation and execution as one stateful contract:

- Preparation validates tensors and attributes, performs or selects inference/Tiling behavior, reports the exact workspace size, and returns the executor or equivalent state required by execution.
- The caller allocates the documented workspace in the correct device/context, preserves input/output/executor lifetimes, and executes on the intended stream.
- Execution receives the same logical tensors, executor, workspace pointer/size, device context, and stream assumptions established during preparation.
- Every status is checked. Cleanup must cover preparation failure, allocation failure, launch failure, and asynchronous failure surfaced at synchronization.

Confirm exact names and ownership rules in the target headers; do not generalize one ACLNN API generation to another.

## Direct Kernel Launch

The caller must explicitly own the guarantees otherwise supplied by registration/runtime:

- validate shapes, ranks, data types, formats, attributes, empty inputs, and capacity limits;
- build and serialize version-matched Tiling data and choose a compiled TilingKey variant;
- allocate workspace and device buffers with correct lifetime and alignment;
- locate the exact Kernel binary/function and match argument order, widths, address spaces, and launch dimensions;
- preserve asynchronous input/output/workspace lifetime through stream completion and retrieve execution errors at the documented boundary.

For a PyTorch-facing direct launcher, also verify device/stream selection, tensor contiguity and storage offsets, dtype/shape checks, current-stream semantics, build-extension ABI, and error propagation into Python. Do not assume a Python wrapper makes a launch synchronous.

## Migration Matrix

| Responsibility | Registered path | Direct path | Migration question |
|---|---|---|---|
| schema and inference | registry/framework | caller or wrapper | Where are invalid inputs rejected now? |
| Tiling and variants | registered Host Tiling | caller-supplied/embedded | Is every key compiled and dispatched? |
| workspace | executor/runtime contract | caller | Are size, device, alignment, and lifetime preserved? |
| binary discovery | package/runtime | build output/launcher | Which exact artifact is loaded? |
| launch and stream | ACLNN/framework | caller | Are context, dimensions, async lifetime, and errors preserved? |
| installation | vendor/package layout | may be unnecessary | Has stale package lookup been removed or intentionally retained? |

During migration, keep a differential test until both paths agree on representative full, tail, empty, dynamic, and error cases. Remove the old path only after the new path owns every required responsibility.
