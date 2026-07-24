# Precision Triage

Treat wrong output as a contract and localization problem before changing tolerances.

## Reproduce and Measure

Record target/build, exact shapes, dtypes, formats, attributes, seed, input range/distribution, invocation path, accumulation type, reference implementation, and comparison metric. Preserve the first mismatching index and a small neighborhood, not only a global pass/fail.

Test deterministic small shapes first: one element, less than one vector/block, exact tile, tail tile, multiple cores, empty/scalar if supported, and magnitude/special-value boundaries promised by the operator.

## Localize

1. Confirm schema/inference and Host Tiling produce the intended logical shape, partition, key, and units.
2. Compare direct and registered paths if both exist; disagreement often identifies wrapper/Tiling/package issues before Kernel math.
3. Inspect GM-to-local tail padding and initialization, intermediate buffers, per-stage output, reduction order, casts/round modes, accumulation precision, atomics, and final local-to-GM writeback.
4. Check every core/thread owns the intended region with no overlap, gap, stale padded lane, or uninitialized source.
5. Compare the exact API overload and supported type/SoC against target-version evidence.

## Judgment

- Do not loosen tolerance until the public numerical contract, reference error, dtype, reduction order, and target behavior justify it.
- Separate deterministic algorithmic error from race-dependent variation by repeated runs and controlled synchronization.
- A CPU reference can establish expected math but not device API behavior. Simulator agreement does not replace a real-target check for ordering or precision.
- For `NaN`, infinities, signed zero, overflow, underflow, and saturation, test only the behavior the operator contract promises and document any implementation-defined boundary.
