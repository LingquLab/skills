# Host, Tiling, and Kernel Contract

Use one table in the implementation or review notes to keep each layer aligned.

## Contract Matrix

| Concern | Definition/inference | Host Tiling | Kernel/launch | Required proof |
|---|---|---|---|---|
| inputs/outputs | count, names, optional/dynamic markers | descriptors checked before access | ABI argument order and address spaces | schema and integration tests |
| shape | rank, scalar/empty/dynamic/broadcast rules | checked products, partition, tail | GM/UB bounds for every tile/core | inference and boundary-shape tests |
| data type/format | declared support and inference | byte width, alignment, API selection | compiled template and accumulation type | type matrix and precision tests |
| attributes | name, type, default, range | fallible lookup and validation | serialized field or compile-time variant | default/boundary/invalid tests |
| Tiling data | serialized ABI declaration | every field initialized, size checked | matching declaration and units | round-trip or Host/Kernel fixture |
| TilingKey | declared template set | one reachable key selected | compiled branch and explicit dispatch | one test per supported key |
| partition | logical total | `blockDim`, per-core range, no zero divisor | no gaps, overlaps, or last-core OOB | small/tail/max-shape tests |
| workspace | public/runtime contract | checked size and layout | same offsets, alignment, lifetime | zero/nonzero and failure tests |
| errors | documented invalid inputs | explicit failure without partial state | launch/async error surfaced | negative-path tests |

## Checked Tiling Arithmetic

- Widen each operand before addition or multiplication; checking a narrow result does not recover overflowed information.
- Guard zero divisors, signed `MIN / -1`, alignment-rounding overflow, and unsigned subtraction before the operation.
- Reject `overhead >= capacity`, a zero byte width, or a computed tile count of zero. Do not clamp zero to one when one tile cannot fit.
- Keep element, byte, block, stride, repeat, and workspace units explicit in field names or comments.
- Validate serialized values before narrowing to the Kernel field type.
- Derive tail reads and writes from both logical and padded allocations; padding one side does not authorize an out-of-range access on the other.

## Programming Model

Select MemBase (`TPipe`/`TQue`/`TBuf`), Basic C++ Tensor API/`LocalMemoryAllocator`, RegBase, SIMT, hybrid SIMD+SIMT, or a Blaze/Tensor matmul API only when target-version headers and examples support it. Each model has different allocation, synchronization, lifetime, and resource contracts. Use `$ascendc-api-best-practices` and its programming-model reference for details.

## Build and Package Wiring

- Verify architecture/compiler flags, source selection, generated variants, Kernel names, and Host ABI belong to the same target.
- Inspect generated code before retaining it; do not overwrite repository-owned customization with a stale template.
- Make package operator identity, vendor path, version, architecture, Tiling metadata, and binary names agree with runtime lookup.
- Treat a 220x-to-351x or other target migration as an API and binary migration, not a string substitution.
- Keep installation separate from build. Installing, replacing a vendor package, or changing persistent search paths requires explicit user authority and rollback instructions.
