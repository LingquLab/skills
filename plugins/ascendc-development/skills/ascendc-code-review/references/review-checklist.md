# Ascend C Review Checklist

Apply only the sections relevant to the changed code. Project policy and version-matched source take precedence.

## Host and Tiling

- Validate external shapes, attributes, ranks, and data types before arithmetic or indexing.
- Derive concrete bounds for additions, multiplications, divisions, alignments, and byte-size calculations.
- Guard zero divisors and the signed `MIN / -1` case when reachable.
- Check every array, vector, pointer, and serialized field access against its real lifetime and capacity.
- Check allocation, handle, context, stream, file, and lock cleanup on success and error paths.
- Verify public struct layout, enum values, kernel signatures, and serialized tiling data for compatibility.
- Obtain SoC capacities and core counts from supported platform APIs or validated configuration; flag hard-coded values only when they violate the target contract.
- Check that Host code and Kernel-only headers are separated according to the real build model.

## Kernel

- Match logical element counts, aligned element counts, byte counts, and API-specific stride units.
- Prove GM and UB accesses remain within allocated ranges for full tiles, tails, empty inputs, and the last block.
- Verify queue and tensor lifecycles such as allocation, enqueue, dequeue, and release on all relevant paths.
- Verify cross-pipeline and cross-core synchronization from the selected API's documented ordering model.
- Check repeat counts, block counts, strides, masks, temporary buffers, and padding against the exact overload.
- Confirm in-place operations and buffer aliasing are supported by the selected overload.
- Check intermediate precision, cast rounding, special values, and reduction accumulation against the operator's accuracy contract.
- Treat single-element GM access and per-row API calls as performance findings only when they are on a material hot path and a better version-matched pattern exists.

## Operator Integration

- Trace attributes from framework context through Tiling data to Kernel use.
- Compare every `OpDef` input, output, attribute, optional/dynamic marker, data-type set, and format with the public API and registration entry.
- Verify `InferShape` and `InferDataType` handle the same ranks, empty/scalar tensors, dynamic dimensions, broadcast rules, and supported types declared by `OpDef`; check their unit tests use the registered schemas rather than a parallel test-only contract.
- Treat `TilingData` as a serialized ABI: compare field order, width, signedness, alignment, initialization, capacity checks, serialization length, Kernel declaration, and every read site.
- Trace TilingKey end to end: declared key/template set, Host assignment, build-generated variants, Kernel dispatch, fallback behavior, and tests. A Host key with no compiled Kernel branch is a runtime failure; a dispatch branch with no reachable Host key is dead coverage.
- Verify `blockDim`, per-core partitioning, workspace sizes, and any atomic-clear requirement are set by Host code and consumed with the same units and layout by the actual launch path.
- Check descriptor and attribute access against the target framework lifecycle and IR schema: validate nullable or fallible results when the selected API permits failure, and require the retrieved type to match the registered attribute type. Do not reject `GetInputTensor`, `CompileInfo`, or another access path by name without a version-matched contract that excludes it.
- Verify shape inference, empty tensors, scalar tensors, broadcast rules, and dynamic shapes.
- Confirm workspace and temporary-buffer sizes are calculated with the same layout the Kernel uses.
- Check launch dimensions and per-core partitioning for gaps, overlaps, and imbalance.
- Widen shape products and GM offset arithmetic before an operation can exceed the current operand type; require `int64_t` or another wider type only when the supported size range needs it.
- For floating-point operators, test `NaN`, infinities, signed zero, and range boundaries when the operator contract distinguishes or promises behavior for them.
- For atomic accumulation, prove the destination has the algorithm's required initial value, the UB source is fully initialized for the written range, and the atomic mode is disabled at the documented boundary. Do not require blanket zeroing when overwrite semantics or prior initialization already establishes the value.
- For fused communication or multi-core stages, require synchronization only across real producer-consumer dependencies and verify every participating path reaches the matching protocol; do not prescribe a global barrier without that dependency analysis.
- Treat `thread_local` in a dynamically loaded library as a lifecycle finding only when the library can unload while owning threads, objects, destructors, or later accesses remain live.
- Verify error codes and logging preserve the actionable failure boundary without exposing sensitive data.
- Separate compile support, simulator support, and real-device behavior.

## Invocation Paths

- For registered custom operators, follow registration through inference, Tiling, Kernel build, package metadata, installation lookup, ACLNN exposure, and the framework call site. Verify package search order and operator identity rather than assuming a successful build means the runtime loaded that artifact.
- For ACLNN two-stage APIs, check that workspace-size/executor preparation validates inputs and produces the exact executor consumed by execution. Verify workspace size/type, allocation ownership, stream/device context, tensor lifetime, error propagation, and cleanup on every exit.
- For direct Kernel launch, match the launcher declaration to the compiled Kernel name and ABI. Check tiling and workspace buffers, argument order and address space, launch dimensions, asynchronous lifetime, stream synchronization, and error retrieval.
- When migrating between registered and direct invocation, list which guarantees move to the caller: shape/type inference, validation, Tiling, workspace, binary discovery, lifecycle, and error reporting. Do not leave both paths active accidentally.

## Architecture Migration

- Treat a `220x` to `351x` or other architecture change as a build, API, binary, and runtime migration, not a macro rename. Verify the target names against the selected toolchain instead of assuming those labels exist in every release.
- Audit target flags, generated code directories, architecture macros, headers, Kernel source selection, supported APIs/data types, queue or allocator model, synchronization, workspace, and package metadata.
- Remove stale source or binary fallbacks only after proving the new target path is selected. Reject a package that builds one architecture while advertising or loading another.
- Require target-toolchain compilation and real target evidence for runtime claims. Host tests or a simulator can validate logic but cannot establish device compatibility or performance.

## Performance Claims

- Require measurements or a defensible hardware model for claimed speedups or regressions.
- Do not prescribe double buffering, a fixed tile threshold, or a fixed UB capacity without checking the target SoC and workload.
- Check whether barriers are necessary for actual dependencies; both missing and redundant synchronization can matter.
- Confirm tail handling before accepting a vectorized or batched rewrite.

## Evidence

For a finding, provide the concrete input or state that reaches the defect, the relevant code path, and the version-matched API or project rule. Do not report a generic checklist item as a bug without that connection.
