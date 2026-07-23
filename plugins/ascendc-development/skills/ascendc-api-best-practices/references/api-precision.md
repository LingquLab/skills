# Precision Conversion and Mixed Precision

`Cast` support is a matrix of API family, source type, destination type, round mode, SoC, and CANN release. Do not select a round mode from its name alone.

## Select a Cast Overload

Before writing a call:

1. Identify whether the code uses the Memory vector, Register vector, or scalar `Cast` API.
2. Find the exact source/destination type row in the target release documentation.
3. Select only a `RoundMode` listed for that row.
4. Confirm whether the operator accuracy contract wants truncation, nearest rounding, saturation, odd rounding, or a bit-preserving conversion.
5. Test boundary values, signed zero, infinities, NaNs, and values just above and below representable limits when they matter to the operator.

Do not use this older shortcut:

```text
low precision -> high precision = CAST_NONE
high precision -> low precision = CAST_ROUND
```

It is not a general API contract. For example, the CANN 9.0 Memory vector `Cast` table lists `CAST_NONE` and `CAST_ODD` for `float -> half`; it does not list `CAST_ROUND` for that pair. Other API families and releases have different tables.

## Mixed Precision

Promoting FP16 or BF16 inputs to FP32 can improve the stability of reductions, exponentials, normalization, and long accumulation chains, but promotion is not an unconditional rule for every `Add` or `Sub`.

Choose the compute type from:

- the operator's documented accuracy tolerance and reference behavior;
- input ranges and accumulation length;
- the target API's supported data types and aliasing rules;
- available UB and the extra conversion cost;
- measured error and performance on representative data.

A common pattern is:

```text
low-precision input
  -> version-supported Cast to FP32
  -> FP32 compute
  -> version-supported Cast to the output type
```

The down-conversion mode must still come from the exact `Cast` support table. Mantissa widths can explain why small addends disappear, but a fixed magnitude-ratio threshold is not a sufficient operator-wide decision rule.

## Evidence

- CANN 9.0 Memory vector `Cast`: https://www.hiascend.com/document/detail/zh/canncommercial/900/API/ascendcopapi/atlasascendc_api_07_0073.html
- For another release or API family, locate the exact page with `$ascendc-docs-search` and treat the 9.0 page only as calibration evidence.
