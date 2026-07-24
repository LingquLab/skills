---
name: ascendc-api-best-practices
description: Verify and explain Ascend C API usage for arithmetic, reduction, data movement, transpose, UB buffers, precision conversion, pipeline synchronization, repeat limits, and host runtime calls. Use when implementing or debugging an Ascend C kernel, resolving alignment or overload errors, reviewing API choices, or comparing an implementation with CANN documentation and examples.
---

# Ascend C API Best Practices

Use the bundled references as a reviewed snapshot of common patterns, not as a substitute for the documentation and headers matching the target CANN installation.

## Workflow

1. Identify the target SoC, CANN version, and execution side: Host/Tiling or Kernel.
2. If any of those are unknown and materially affect the answer, inspect the repository, build files, installed `version.info`, or ask for the missing fact.
3. Read only the reference files relevant to the API or failure:
   - Programming-model selection and mixed-model boundaries: `references/programming-models.md`
   - Arithmetic and broadcast: `references/api-arithmetic.md`
   - Reduction: `references/api-reduce.md` and, when using pattern overloads, `references/api-reduce-pattern.md`
   - Data movement and alignment: `references/api-datacopy.md`
   - Transpose and gather: `references/api-transpose.md`
   - UB buffers and queues: `references/api-buffer.md`
   - Precision conversion: `references/api-precision.md`
   - Pipeline synchronization: `references/api-pipeline.md`
   - Repeat limits: `references/api-repeat-limits.md`
   - Kernel restrictions: `references/api-restrictions.md`
   - Host runtime initialization: `references/api-host-runtime.md`
   - Quick routing only: `references/api-quickref.md`
4. Confirm the exact overload, parameter units, alignment rule, supported data types, and SoC restrictions against version-matched headers or official documentation. Use `$ascendc-docs-search` when the local source is not already available.
5. Compare the guidance with the actual code, including tiling values, buffer sizes, tail handling, and synchronization.
6. State the target version and evidence source. Mark any conclusion that is based only on the bundled snapshot as provisional.

Several references include calibrated CANN 9.0 examples solely to disprove or
narrow older blanket rules. Treat those links as evidence for 9.0, not as the
default target release. A reference without target-matched evidence supplies a
hypothesis or search route, not a final compatibility conclusion.

## Judgment Rules

- Distinguish correctness constraints from performance guidance. Do not call an API forbidden merely because another pattern is usually faster.
- Do not generalize one overload's alignment, stride, repeat, or temporary-buffer rule to every overload with the same API name.
- Treat API variants and numeric filename suffixes as separate candidates until their signatures and restrictions are compared.
- Check element counts versus byte counts explicitly; many data-movement defects come from mixing those units.
- For non-aligned tails, verify both the GM-to-UB and UB-to-GM directions. Their padding semantics can differ.
- When recommending an in-place operation or buffer reuse, verify that the selected overload permits aliasing.
- Prefer a compilable, version-matched example from the installed source tree over a generic snippet.
- Identify the programming model before applying a rule. MemBase queues, Basic C++ Tensor allocation, RegBase register operations, SIMT threads, hybrid SIMD/SIMT regions, and Blaze/Tensor matmul APIs have different ownership, synchronization, and launch contracts.

## Output

Give the applicable API signature or pattern, the relevant constraints, a minimal corrected example when useful, and the source/version used for the conclusion. If the evidence is incomplete, name the exact header, document, compile check, or hardware test still needed.
