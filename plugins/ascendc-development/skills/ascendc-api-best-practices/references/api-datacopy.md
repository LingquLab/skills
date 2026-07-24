# DataCopy / DataCopyPad Selection

GM, UB, and other local-memory transfers expose multiple API families. Parameter
types, units, padding behavior, supported directions, types, and products vary
by CANN release, SoC, and overload. Record the exact declaration before writing
Tiling or Kernel code.

## Contents

- [Select the Exact Declaration](#select-the-exact-declaration)
- [CANN 9.1 Header Calibration](#cann-91-header-calibration)
- [Schematic Direction Patterns](#schematic-direction-patterns)
- [Layout and Bounds](#layout-and-bounds)
- [Synchronization and Lifetime](#synchronization-and-lifetime)
- [Diagnose a Suspected Tail Defect](#diagnose-a-suspected-tail-defect)
- [Performance](#performance)
- [Evidence](#evidence)

## Select the Exact Declaration

1. Identify source and destination memory positions and the execution pipeline.
2. Enumerate `DataCopy` and `DataCopyPad` declarations that match that direction.
3. Record the parameter structure (`DataCopyParams`, `DataCopyExtParams`, or
   another target-specific form) and every field's unit and range.
4. Check supported types, alignment, padding, stride, block-count, and alias
   restrictions in the version-matched page or implementation checks.
5. Derive GM and local allocation bounds for full blocks, the last block, and
   every padded lane before choosing the call.

Do not select `DataCopyPad` solely because a logical byte count is unaligned.
First confirm that a matching overload exists and that its padding semantics fit
the downstream computation.

## CANN 9.1 Header Calibration

The installed CANN 9.1 interface used for migration calibration declares
different GM-to-UB and UB-to-GM call shapes:

```cpp
template <typename T>
__aicore__ inline void DataCopyPad(
    const LocalTensor<T>& dst,
    const GlobalTensor<T>& src,
    const DataCopyParams& dataCopyParams,
    const DataCopyPadParams& padParams);

template <typename T>
__aicore__ inline void DataCopyPad(
    const GlobalTensor<T>& dst,
    const LocalTensor<T>& src,
    const DataCopyParams& dataCopyParams);
```

The same header also provides `DataCopyExtParams` forms. In this release, the
GM-to-UB form receives a separate padding structure while the corresponding
UB-to-GM form does not. This is evidence for these CANN 9.1 declarations, not a
version-independent promise.

The calibrated `DataCopyPadParams` layout is:

```cpp
struct DataCopyPadParams {
    bool isPad = false;
    uint8_t leftPadding = 0;
    uint8_t rightPadding = 0;
    uint64_t paddingValue = 0;
};
```

Field presence does not establish field semantics for another overload. Read
the target documentation and implementation checks before deciding which lanes
are initialized, which value is legal, or whether padded lanes may be consumed.

## Schematic Direction Patterns

After constructing parameters from the target declaration:

```cpp
// GM -> UB form that exposes explicit padding parameters.
DataCopyPad(localDst, globalSrc, copyParams, padParams);

// UB -> GM form in the calibrated CANN 9.1 interface.
DataCopyPad(globalDst, localSrc, copyParams);
```

These calls intentionally omit numeric initializers. Copying a field list or
stride constant from another direction or parameter structure is not safe.

## Layout and Bounds

Keep these quantities distinct:

- logical elements used by the operator;
- bytes transferred by each block;
- allocated GM span;
- allocated local-memory row stride;
- padding lanes that the selected overload may write;
- source and destination stride units;
- the parameter field widths that bound block and repeat counts.

For a multi-row transfer, prove both the start of the last row and the end of
its transferred or padded span are within allocation. When downstream vector or
Reduce code can read padded lanes, initialize them to a value that is neutral
for that exact computation; otherwise restrict the compute count so those lanes
are never observed.

## Synchronization and Lifetime

- Match `AllocTensor`, `EnQue`, `DeQue`, and `FreeTensor` to the real queue path.
- Verify ordering between MTE and vector pipelines using the target queue/event
  model; the transfer function name alone does not prove synchronization.
- Keep input and output directions separate during diagnosis. A working CopyIn
  does not prove that CopyOut uses compatible units or tail behavior.

## Diagnose a Suspected Tail Defect

1. Reproduce with aligned and minimally unaligned logical lengths.
2. Reduce the path to CopyIn followed by CopyOut where that is semantically
   valid, while preserving the real allocations and parameter structures.
3. Compare the exact overloads and field units for both directions.
4. Check the last block's GM and local spans, including any documented padding.
5. Inspect padded lanes only when the target contract defines their value.
6. Run a target-version compile, then a bounded hardware test when runtime proof
   is required.

A historical 16-byte failure from one `DataCopy` form is not proof that all
16-byte `DataCopy` calls are invalid or that every `DataCopyPad` form is a valid
replacement.

## Performance

Per-element `GlobalTensor::GetValue` or `SetValue` in a material hot path can be
a performance risk, but replacing it with DMA is a target- and workload-specific
decision. Measure transfer setup, padding work, synchronization, occupancy, and
tail frequency on the target device before making a speedup claim.

## Evidence

- CANN 9.1 installed header:
  `aarch64-linux/ascendc/include/basic_api/interface/kernel_operator_data_copy_intf.h`
- CANN 9.1 installed parameter definitions:
  `aarch64-linux/ascendc/include/basic_api/interface/kernel_struct_data_copy.h`
- For another release or product, locate the exact declaration and official page
  with `$ascendc-docs-search`.
