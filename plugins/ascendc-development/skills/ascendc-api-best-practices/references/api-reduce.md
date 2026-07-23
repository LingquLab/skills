# Reduce API Selection and Data Layout

Ascend C exposes multiple Reduce API families. Similar names do not imply the same signature, temporary-buffer type, alignment model, output layout, alias rules, or product support.

## Choose the Exact Family

Use the target headers and documentation to distinguish at least:

- count-based basic APIs that reduce a bounded element range;
- high-level `ReducePattern` APIs that describe axes with shape metadata;
- Register-vector, Memory-vector, and scalar variants;
- APIs that return only values from variants that also return indices.

Do not call one family “Level 2” or “Pattern” and then copy constraints to every same-name overload. Record the exact signature before sizing buffers.

## Count-Based Workflow

For a row-wise reduction:

1. Keep the logical row length separate from its allocated or DMA-padded stride.
2. Compute the row address from the allocated stride.
3. Pass the element count expected by the selected overload, not a byte count.
4. Allocate the destination and temporary tensor with the types and sizes documented for that overload.
5. Verify whether value/index output, source reuse, or aliasing changes those requirements.

Schematic layout:

```text
row_start = row_index * allocated_row_stride_elements
reduce(dst, src[row_start], temporary, logical_row_elements, ...)
```

This avoids the common error of using a logical row length as the UB row stride. It does not assert that every Reduce API accepts an unaligned logical count.

## ReducePattern Workflow

For a high-level pattern call:

1. Select a `ReducePattern` actually supported by that API and release.
2. Pass the real logical shape representation expected by the target signature.
3. Set `isSrcInnerPad` from whether the innermost data being reduced is 32-byte aligned; do not hard-code it by SoC.
4. Keep `isReuseSource` consistent with the intended alias plan.
5. Query the Host-side maximum/minimum temporary size with identical shape, type, pattern, alignment, and reuse values.
6. Pass a selected size through Tiling and allocate no less than the documented minimum.

See [api-reduce-pattern.md](api-reduce-pattern.md) for the CANN 9.0-calibrated Host helper and evidence links.

## Padding and Tails

Padding introduced for DMA storage and `isSrcInnerPad` are related but not interchangeable:

- DMA padding controls how data is stored and copied.
- `srcShape` describes the shape expected by the selected Reduce API.
- `isSrcInnerPad` describes alignment of the actual innermost-axis data.
- Padding values must be neutral for the reduction when padded elements participate.

For maximum, minimum, sum, and index-producing reductions, the correct neutral value and tie behavior differ. Confirm whether the API ignores padding or computes over it before choosing a fill value.

## Accuracy and Special Values

- Check accumulation or intermediate precision against the operator tolerance.
- Verify NaN propagation, infinities, signed zero, empty axes, and tie/index semantics when relevant.
- Do not assume FP32 promotion is always required or always available.
- Compare with a reference implementation over boundary and representative shapes.

## Review Checklist

- Exact API family, signature, product, and CANN release identified.
- Logical counts, byte counts, and allocated strides are not mixed.
- Source, destination, and temporary tensor types and sizes match the overload.
- Alias and source-reuse rules are verified, not inferred from another overload.
- Host temporary-size query matches the Kernel call.
- Full tiles, last tile, empty input, and non-aligned tails stay in bounds.
- Output layout and optional index output match downstream consumers.
- Accuracy and performance claims have target-specific evidence.

## Source Discovery

Use `$ascendc-docs-search` for `ReduceMax`, `ReduceMin`, `ReduceSum`, or the relevant API plus the target release. Prefer installed headers and examples when they match the actual toolchain.
