# Reduce Pattern Interfaces

This reference captures the high-level `ReduceMax` workflow verified against CANN 9.0. Kernel overloads, supported patterns and types, temporary-space rules, and product support can change; retrieve the exact target-release page before copying a signature.

## Pattern and Shape

`ReducePattern::AR` reduces the second axis of a two-dimensional input; `ReducePattern::RA` reduces the first. Do not assume every listed `ReducePattern` enum value is supported by every Reduce API.

The Kernel API commonly has two forms:

```text
ReduceMax<T, pattern, isReuseSource>(dst, src, sharedTmpBuffer, srcShape, isSrcInnerPad)
ReduceMax<T, pattern, isReuseSource>(dst, src, srcShape, isSrcInnerPad)
```

This is a schematic call shape, not a version-independent C++ declaration. In the first form the caller passes temporary UB explicitly. In the second the framework manages the temporary tensor according to that release's documented reservation mechanism.

`isSrcInnerPad` describes the actual data being reduced on the innermost axis:

- `true`: that innermost-axis data is 32-byte aligned;
- `false`: it is not 32-byte aligned.

It is not a fixed SoC selector, and `srcShape` should not be silently replaced with an aligned shape unless the selected API contract explicitly requires that representation.

## Host-Side Temporary Size

CANN 9.0 documents this Host-side helper:

```cpp
void GetReduceMaxMaxMinTmpSize(
    const ge::Shape& srcShape,
    const ge::DataType dataType,
    ReducePattern pattern,
    bool isSrcInnerPad,
    bool isReuseSource,
    uint32_t& maxValue,
    uint32_t& minValue);
```

Example Host-side calculation for a 16 by 32 FP32 input:

```cpp
ge::Shape srcShape({16, 32});
uint32_t maxValue = 0;
uint32_t minValue = 0;
AscendC::GetReduceMaxMaxMinTmpSize(
    srcShape,
    ge::DataType::DT_FLOAT,
    AscendC::ReducePattern::AR,
    true,
    false,
    maxValue,
    minValue);
```

Pass a selected size through Tiling data and ensure the Kernel receives at least `minValue` bytes. `maxValue` is a performance-oriented upper reference and can exceed available UB; it is not an instruction to allocate blindly. Keep `pattern`, alignment, reuse, shape, and data type identical between the Host query and Kernel call.

## Review Checklist

- Match the exact Kernel overload and template parameter names in target headers.
- Verify `srcShape`, `isSrcInnerPad`, and `isReuseSource` describe the real input.
- Keep the Host temporary-size query and Kernel call parameters consistent.
- Check the selected temporary size against remaining UB and the documented minimum.
- Verify destination size and layout for the selected pattern.
- Compile with the target CANN release; do not infer support from enum declarations alone.

## Evidence

- CANN 9.0 `GetReduceMaxMaxMinTmpSize`: https://www.hiascend.com/document/detail/zh/canncommercial/900/API/ascendcopapi/atlasascendc_api_07_10147.html
- CANN 9.0 high-level `ReduceMax`: https://www.hiascend.com/document/detail/zh/canncommercial/900/API/ascendcopapi/atlasascendc_api_07_10055.html
