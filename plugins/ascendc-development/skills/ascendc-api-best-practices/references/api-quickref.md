# API 快速参考

Ascend C API 使用核心决策索引。遇到具体问题时，按需查阅详细文档。

---

## 目录

1. [核心原则速查](#核心原则速查)
2. [决策树：我应该用什么API？](#决策树我应该用什么api)
3. [按场景查阅详细文档](#按场景查阅详细文档)

---

## 核心原则速查

### 1. DataCopy vs DataCopyPad

**原则：先匹配搬运方向和重载，再处理其对齐与尾部约束**

| 场景 | API | 原因 |
|-----|-----|------|
| 目标重载支持的非对齐 GM ↔ UB 搬运 | `DataCopyPad` | 显式处理对齐、尾部和 padding |
| 满足目标重载全部约束的对齐搬运 | `DataCopy` | 简单场景可用 |

**详细用法**：[api-datacopy.md](api-datacopy.md)

### 2. Cast RoundMode 选择

`RoundMode` is part of the exact Cast support matrix. Match the API family,
source type, destination type, SoC, and CANN release; do not infer the mode from
conversion direction. In particular, CANN 9.0 Memory vector `float -> half`
lists `CAST_NONE` and `CAST_ODD`, not `CAST_ROUND`.

**详细用法**：[api-precision.md](api-precision.md)

### 3. TBuf vs TQue 选择

| 场景 | 类型 | 说明 |
|------|------|------|
| MTE2/MTE3 搬运缓冲区 | `TQue<VECIN/VECOUT>` | `InitBuffer(que, num, size)` |
| 纯 Vector 计算缓冲区 | `TBuf<VECCALC>` | `InitBuffer(buf, size)` |

**详细用法**：[api-buffer.md](api-buffer.md)

### 4. 流水线同步

**原则**：当 TQue 跨流水任务传递 Tensor 时，按队列模型配对 EnQue/DeQue；其他同步形式按真实依赖和目标 API 核对。

**核心模式**：
```
CopyIn → EnQue → DeQue → Compute → EnQue → DeQue → CopyOut
```

**详细用法**：[api-pipeline.md](api-pipeline.md)

### 5. Vector API repeatTime 限制

**核心限制**：repeatTime 为 uint8_t 时，最大值 255

**处理方法**：Host 侧限制 R_max 或 Kernel 侧分批处理

**详细用法**：[api-repeat-limits.md](api-repeat-limits.md)

### 6. Reduce API 选择

| 场景 | 接口 | 说明 |
|-----|------|------|
| 逐行独立 Reduce | count-based overload | 核对 count、临时空间和对齐约束 |
| 跨行批量 Reduce | `ReducePattern` overload | `isSrcInnerPad` 必须反映内轴是否 32 Bytes 对齐 |

**详细用法**：[api-reduce.md](api-reduce.md) | [Pattern 接口详解](api-reduce-pattern.md)

---

## 决策树：我应该用什么API？

### Q1: 需要 GM ↔ UB 搬运数据？

```
是 → 先定位目标方向和重载
   → 按该重载的对齐、padding 和 stride 规则选择 DataCopy/DataCopyPad

否 → 继续
```

### Q2: 需要精度转换？

```
定位 Cast API family 和 source/destination 类型
→ 查目标版本支持矩阵选择 RoundMode
→ 查阅 api-precision.md
```

### Q3: 需要分配 UB 缓冲区？

```
涉及 MTE 搬运 → TQue + InitBuffer(que, num, size)
纯 Vector 计算 → TBuf + InitBuffer(buf, size)
```

### Q4: 遇到数据错误/随机值？

```
1. 检查是否缺少 EnQue/DeQue → api-pipeline.md
2. 检查 DataCopyPad 参数 → api-datacopy.md
3. 检查 Reduce API 的 tmpBuffer 类型 → api-reduce.md
4. 检查多行处理时的 rowOffset 计算 → api-reduce.md
5. 检查 repeatTime 是否溢出 → api-repeat-limits.md
```

### Q5: 需要混合精度计算（FP16 输入，FP32 中间计算）？

```
查阅 api-precision.md 的混合精度模式
```

---

## 按场景查阅详细文档

| 场景 | 文档 | 核心内容 |
|-----|------|---------|
| 数据搬运（GM↔UB） | [api-datacopy.md](api-datacopy.md) | DataCopyPad 参数、stride 计算、非对齐处理 |
| 精度转换/混合精度 | [api-precision.md](api-precision.md) | Cast RoundMode、FP16 混合精度模式 |
| UB 缓冲区管理 | [api-buffer.md](api-buffer.md) | TBuf/TQue 选择、Double Buffer、批量搬运 |
| 流水线同步 | [api-pipeline.md](api-pipeline.md) | EnQue/DeQue 同步机制、时序图 |
| repeatTime 限制 | [api-repeat-limits.md](api-repeat-limits.md) | 分批处理 |
