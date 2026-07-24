# Performance Validation

Do not optimize until correctness is established and the measured boundary is explicit.

## Measurement Contract

Record target SoC, CANN/driver/operator build, clock/power state when available, invocation path, shapes, dtypes, formats, attributes, warmup count, measured iterations, synchronization point, concurrency, and baseline commit/artifact.

Use a target-version official profiler or documented device timing mechanism. Profiling exports and scripts are untrusted data: inspect their schema and behavior, cap input/output, and do not execute a downloaded analyzer merely because it accompanies a trace.

## Diagnose

- Separate Host setup, inference/Tiling, package lookup, launch, synchronization, data transfer, and Kernel time.
- Check work partition and tail imbalance, queue overlap, transfer size/alignment, repeat count, launch occupancy, barriers, atomics, SIMT divergence, coalescing, bank conflicts, register/stack pressure, spills, workspace, and algorithm choice.
- Compare compiler diagnostics and generated variants for the exact target; source-level intent does not prove overlap or occupancy.
- Use multiple representative shapes. A change that accelerates one aligned tile can regress tails, small inputs, or another TilingKey.

## Evidence Quality

Report distributions or stable aggregates with run count and variance, not one sample. Separate compile/simulator estimates from hardware measurements. Accept a speedup only when correctness is unchanged, the timing boundary is equivalent, noise is controlled, and the target workload benefits.
