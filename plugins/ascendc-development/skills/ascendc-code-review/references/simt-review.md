# SIMT Review

SIMT API naming, availability, limits, and memory-ordering behavior can change across CANN releases. First inspect the target headers, compile mode, launch wrapper, and project migration policy.

## Launch and Coverage

- Derive grid, block, and total-thread calculations in a type wide enough for the supported shape. Check zero work, rounding-up overflow, and conversion into the launch API's dimension type.
- Prove every logical element has exactly the intended owner for the smallest input, a partial block, the largest supported shape, and every active dimension.
- Check every per-thread GM, UB, shared/local, and register access after the final index calculation. A launch-bound guard must dominate all accesses and collectives that require participation.
- Verify documented threads-per-block, grid, dynamic UB/shared-memory, stack, register, and launch-bound limits for the target architecture.

## Synchronization and Memory Ordering

- Identify the producer, consumer, address space, participating threads or blocks, and required visibility for every barrier, fence, event, and atomic.
- Ensure all required participants reach a block-level barrier on every path; divergent early returns can deadlock.
- Do not treat a barrier as a memory fence or an atomic as a full synchronization protocol unless the target API documents those semantics.
- For SIMD/SIMT handoff, prove the pipeline/thread ownership transition, completion signal, memory visibility, and tail behavior in both directions.
- Check atomic initialization, scope, ordering, result use, and completion boundary. Distinguish correctness requirements from avoidable contention.

## Performance Risks

- Inspect branch divergence, contiguous/coalesced access, alignment, bank conflicts, redundant transfers, and atomic hot spots against real warp/block organization.
- Estimate register and stack pressure from per-thread arrays, templates, unrolling, and inlining; confirm compiler evidence when spills or occupancy matter.
- Check work distribution for skew across threads and blocks. A mathematically complete launch can still leave most threads idle or serialize one heavy tail.
- Require measurements on representative shapes before accepting performance claims; simulator or compile success is not hardware throughput evidence.

## Version Check

Locate definitions and call sites for the API under review:

```bash
rg -n '\b(GetThreadNum|GetThreadIdx|GetBlockIdx|GetBlockNum|VF_CALL|Dim3|UintDiv)\b' '<roots>'
rg -n '\b(threadIdx|blockIdx|blockDim|gridDim)\b' '<roots>'
```

Compare the C++-style and C-style forms in the selected headers. Do not assume one form is forbidden merely because the other exists.

## Migration Checks

- Preserve the original x/y/z dimension when replacing thread or block index helpers.
- Avoid local identifiers that collide with built-in names such as `threadIdx`, `blockIdx`, `blockDim`, or `gridDim` when those built-ins are active.
- Confirm launch wrappers, dimension types, math helpers, atomics, barriers, and shuffle operations have equivalent semantics before replacement.
- Keep an API such as `UintDiv` when the target headers provide no documented equivalent.
- Check namespace and header placement required by the selected compiler.
- Compile the migrated Kernel with the real target toolchain; textual replacement is not sufficient evidence.

## Evidence Levels

Static reasoning can establish index and synchronization defects. Target compilation establishes API and resource acceptance. Simulator evidence can expose some functional paths. Only a real target run establishes device behavior, hangs, and performance; keep those claims separate.

Report a style migration as required only when the target headers, compiler diagnostics, or repository policy establish that requirement.
