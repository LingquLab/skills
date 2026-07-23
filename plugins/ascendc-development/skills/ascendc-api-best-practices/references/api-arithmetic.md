# Arithmetic API Pattern Guide

> **Scope**: These are candidate Add/Sub/Mul/Div transformations from specific
> shapes and overloads. Verify mask, stride, alias, data type, numerical
> semantics, and measured runtime before calling one pattern optimal.

---

## 目录

- [概述](#概述)
- [场景1：标量操作（单行）](#场景1标量操作单行)
  - [方案对比](#方案对比)
  - [API 接口](#api-接口)
  - [完整示例](#完整示例)
- [场景2：广播操作（多行）](#场景2广播操作多行)
  - [方案对比-1](#方案对比-1)
  - [核心原理](#核心原理)
  - [分批处理](#分批处理)
- [场景3：半精度加减法精度决策](#场景3半精度加减法精度决策)
  - [问题根因](#问题根因)
  - [选择策略](#选择策略)
  - [标准范式](#标准范式)
  - [Kernel 集成要点](#kernel-集成要点)
- [性能对比](#性能对比)
- [适用 API](#适用-api)
- [常见错误](#常见错误)

---

## 概述

算术运算 API（Add/Sub/Mul/Div）支持两种使用模式：

| 模式 | API | 适用场景 | Buffer 需求 |
|-----|-----|---------|------------|
| **标量操作** | `Adds/Muls` | 单行处理（Softmax AR 模板） | 32B |
| **广播操作** | `Sub/Div + BinaryRepeatParams` | 多行处理（Softmax ARA 模板） | alignedCols×4 |

**Candidate transformations**:
- Single row: compare `Adds/Muls` with Duplicate plus binary operations.
- Multiple rows: use `src1RepStride=0` only when that exact overload defines zero as the intended broadcast stride.

---

## 场景1：标量操作（单行）

### 方案对比

**问题**：需要对 tensor 每个元素执行 `x - scalar` 或 `x / scalar`

**典型场景**：
- Softmax AR 模板：`x - max_val`（数值稳定）
- Softmax AR 模板：`exp(x) / sum`（归一化）
- LayerNorm：`x - mean`（中心化）
- BatchNorm：`x * gamma + beta`

**方案对比**：

| 方案 | 指令数 | Buffer 需求 | 推荐度 |
|-----|--------|------------|--------|
| Duplicate + Sub | 2 条 | `rLength × sizeof(T)` | ⭐⭐ |
| Duplicate + Div | 2 条 | `rLength × sizeof(T)` | ⭐⭐ |
| **Adds(-scalar)** | **1 条** | **32B** | **⭐⭐⭐⭐⭐** |
| **Muls(1/scalar)** | **1 条** | **32B** | **⭐⭐⭐⭐⭐** |

### API 接口

**Adds（标量加法）**：
```cpp
template <typename T, bool isSetMask = true>
__aicore__ inline void Adds(
    const LocalTensor<T>& dst,
    const LocalTensor<T>& src,
    const T& scalarValue,
    const int32_t& count);

// 功能: dst[i] = src[i] + scalarValue
// 示例: Adds(dst, src, -maxVal, count)  // 减法转加法
```

**Muls（标量乘法）**：
```cpp
template <typename T, bool isSetMask = true>
__aicore__ inline void Muls(
    const LocalTensor<T>& dst,
    const LocalTensor<T>& src,
    const T& scalarValue,
    const int32_t& count);

// 功能: dst[i] = src[i] * scalarValue
// 示例: Muls(dst, src, 1.0/sum, count)  // 除法转乘法
```

### 完整示例

#### 优化前（Sub/Div + Duplicate）

```cpp
// Buffer 初始化
uint32_t broadcastBufSize = rLengthAlign * sizeof(T);  // 例如：512B (rLength=128, FP32)
pipe.InitBuffer(broadcastBuf, broadcastBufSize);
pipe.InitBuffer(reduceBuf, reduceBufSize);

// Compute
LocalTensor<T> broadcastLocal = broadcastBuf.Get<T>();

for (uint32_t row = 0; row < rowsThisLoop; row++) {
    uint32_t rowOffset = row * rLengthAlign;

    // Step 1: ReduceMax
    ReduceMax<T>(broadcastLocal, xLocal[rowOffset], reduceTmpLocal, rLength, false);

    // Step 2: Duplicate + Sub（需要广播 buffer）
    T maxVal = broadcastLocal.GetValue(0);
    Duplicate<T>(broadcastLocal, maxVal, rLength);  // 指令 1
    Sub<T>(yLocal[rowOffset], xLocal[rowOffset], broadcastLocal, rLength);  // 指令 2

    // Step 3: Exp
    Exp<T>(yLocal[rowOffset], yLocal[rowOffset], rLength);

    // Step 4: ReduceSum
    ReduceSum<T, true>(broadcastLocal, yLocal[rowOffset], reduceTmpLocal, rLength);

    // Step 5: Duplicate + Div（需要广播 buffer）
    T sumVal = broadcastLocal.GetValue(0);
    Duplicate<T>(broadcastLocal, sumVal, rLength);  // 指令 3
    Div<T>(yLocal[rowOffset], yLocal[rowOffset], broadcastLocal, rLength);  // 指令 4
}

// 总计：6 条指令/行，需要 broadcastBuf (512B for rLength=128)
```

#### 优化后（Adds/Muls + 标量）

```cpp
// Buffer 初始化（节省 broadcastBuf）
uint32_t scalarBufSize = 32;  // 最小对齐要求，仅需存储 1 个标量
pipe.InitBuffer(scalarBuf, scalarBufSize);
pipe.InitBuffer(reduceBuf, reduceBufSize);

// Compute
LocalTensor<T> scalarLocal = scalarBuf.Get<T>();

for (uint32_t row = 0; row < rowsThisLoop; row++) {
    uint32_t rowOffset = row * rLengthAlign;

    // Step 1: ReduceMax
    ReduceMax<T>(scalarLocal, xLocal[rowOffset], reduceTmpLocal, rLength, false);

    // Step 2: Adds（直接标量操作，无需广播）
    T maxVal = scalarLocal.GetValue(0);
    Adds<T>(yLocal[rowOffset], xLocal[rowOffset], -maxVal, rLength);  // 指令 1

    // Step 3: Exp
    Exp<T>(yLocal[rowOffset], yLocal[rowOffset], rLength);

    // Step 4: ReduceSum
    ReduceSum<T, true>(scalarLocal, yLocal[rowOffset], reduceTmpLocal, rLength);

    // Step 5: Muls（除法转乘法，直接标量操作）
    T sumVal = scalarLocal.GetValue(0);
    T invSumVal = (T)1.0 / sumVal;  // CPU 端计算 1/sum
    Muls<T>(yLocal[rowOffset], yLocal[rowOffset], invSumVal, rLength);  // 指令 2
}

// 总计：4 条指令/行，节省 broadcastBuf (480B for rLength=128)
```

---

## 场景2：广播操作（多行）

### 方案对比

**问题**：需要对多行数据执行相同的标量操作（如 `x - max`、`exp / sum`）

**方案对比**：

| 方案 | API 调用 | Buffer 需求 | 推荐度 |
|-----|---------|------------|--------|
| 逐行循环 | R 次 | alignedCols×4 | ⭐⭐ |
| 单次广播（R ≤ 64） | 1 次 | alignedCols×4 | ⭐⭐⭐⭐⭐ |
| 分批广播（R > 64） | ceil(R/64) 次 | alignedCols×4 | ⭐⭐⭐⭐⭐ |

### 核心原理

**BinaryRepeatParams.src1RepStride=0 实现广播**：

```cpp
struct BinaryRepeatParams {
    uint8_t dstBlkStride;    // 单次迭代内，dst 的 block 步长
    uint8_t src0BlkStride;   // 单次迭代内，src0 的 block 步长
    uint8_t src1BlkStride;   // 单次迭代内，src1 的 block 步长
    uint8_t dstRepStride;    // 相邻迭代间，dst 的 block 步长
    uint8_t src0RepStride;   // 相邻迭代间，src0 的 block 步长
    uint8_t src1RepStride;   // =0 实现广播
};
```

**工作原理**：
- `dstRepStride = alignedCols/8`：每次迭代，dst 前进 `alignedCols` 个元素
- `src0RepStride = alignedCols/8`：每次迭代，src0 前进 `alignedCols` 个元素
- `src1RepStride = 0`：每次迭代，src1 **不前进**，重复读取相同位置

**效果**：
```
迭代 0: dst[0:cols]     = src0[0:cols]     - src1[0:cols]
迭代 1: dst[cols:2cols] = src0[cols:2cols] - src1[0:cols]  ← 重复读取
迭代 2: dst[2cols:3cols]= src0[2cols:3cols]- src1[0:cols]  ← 重复读取
```

### 分批处理

#### 方案1：逐行循环（低效）

```cpp
for (uint32_t r = 0; r < R; r++) {
    Sub(dstLocal[r * alignedCols], srcLocal[r * alignedCols], scalarLocal, alignedCols);
}
// API 调用：R 次
```

#### 方案2：单次广播（高效，R ≤ 64）

```cpp
uint64_t mask = alignedCols;
uint8_t repeatTime = R;

Sub(dstLocal, srcLocal, scalarLocal, mask, repeatTime,
    {1, 1, 1, alignedCols/8, alignedCols/8, 0});
// API 调用：1 次
// API 调用数从 R 次降为 1 次；实际耗时需测量
```

#### 方案3：分批广播（高效，R > 64）

```cpp
constexpr uint32_t BATCH_SIZE = 64;
uint32_t totalBatches = (R + BATCH_SIZE - 1) / BATCH_SIZE;  // ceil(R/64)

for (uint32_t batch = 0; batch < totalBatches; batch++) {
    uint32_t startRow = batch * BATCH_SIZE;
    uint8_t repeatTime = (startRow + BATCH_SIZE <= R) ? BATCH_SIZE : (R - startRow);
    uint32_t offset = startRow * alignedCols;

    Sub(dstLocal[offset], srcLocal[offset], scalarLocal,
        mask, repeatTime, {1, 1, 1, alignedCols/8, alignedCols/8, 0});
}
// API 调用：ceil(R/64) 次
// API 调用数约减少 64 倍；实际耗时需测量
```

---

## 场景3：半精度加减法精度决策

### 问题根因

半精度（FP16=10 位尾数，BF16=7 位）两数量级差异大时会"**大数吃小数**"，Add 和 Sub 面临相同风险：

```
a = 1024.0, b = 0.0625
  Add<half>  : 1024.0     ← b 被丢弃     Sub<half>  : 1024.0     ← b 被丢弃
  Add<float> : 1024.0625  ← 正确         Sub<float> : 1023.9375  ← 正确
```

尾数宽度可以解释现象，但不能据此给所有输入分布设定一个固定的“必须升精度”比例阈值。舍入模式、subnormal、硬件实现、累加长度和算子误差标准都会影响结果。

### 选择策略

先从算子精度标准、输入范围和目标 API 支持确定计算类型。对归约、归一化、长累加或已观察到半精度误差的路径，升 FP32 是常用候选；对误差标准允许且已验证的逐元素路径，直接半精度计算也可能合理。

| Evidence | Candidate implementation | Verification |
|---|---|---|
| FP32 reference shows unacceptable half/BF16 error | `Cast -> Add/Sub<float> -> Cast` | Check target Cast modes, UB, aliasing, error, and runtime |
| Direct half/BF16 meets the operator tolerance | Direct `Add/Sub<T>` | Retain boundary and representative accuracy tests |

### 标准范式

When the exact target overload permits destination/source aliasing, one FP32 input buffer can be reused for the output. Verify that contract before applying this pattern:

```text
// Get<T>(len) 的 len 是元素数；偏移用 tensor[N]
src0Fp32 = Cast(src0, target-supported upcast mode)
src1Fp32 = Cast(src1, target-supported upcast mode)
fp32Output = Add/Sub(src0Fp32, src1Fp32)  # reuse only if aliasing is supported
dst = Cast(fp32Output, target-supported downcast mode)
```

The promotion path adds conversions and FP32 UB; BF16 support must be checked independently.

> **API alias rules determine buffer reuse**: do not transfer an alias result from one Add/Sub or Reduce overload to another without checking its contract.

### Kernel 集成要点

> Size FP32 temporary buffers from the selected aliasing plan. RoundMode and mixed-precision selection are covered in [api-precision.md](api-precision.md).

---

## 性能对比

### 标量操作（单行）

| 项目 | 优化前 | 优化后 | 改善 |
|-----|--------|--------|------|
| **指令数/行** | 6 条 | 4 条 | **-33%** |
| **Buffer 大小** | 512B (rLength=128) | 32B | **-94%** |
| **UB 节省** | - | ~480B | 可用于更大 rowsPerLoop |

### 广播操作（多行）

| R (行数) | 逐行循环调用数 | 单次广播调用数 | 分批广播调用数 | 调用数减少 |
|---------|---------|---------|---------|---------|
| 32 | 32 次 | 1 次 | - | **32×** |
| 64 | 64 次 | 1 次 | - | **64×** |
| 100 | 100 次 | - | 2 次 | **50×** |
| 128 | 128 次 | - | 2 次 | **64×** |
| 200 | 200 次 | - | 4 次 | **50×** |

API call count is not elapsed-time speedup. Validate occupancy, instruction latency, synchronization, and tails on the target device before making a performance claim.

### 半精度加减法（FP16/BF16 Add/Sub）

升精度路径相对直接 `Add/Sub<half>` 增加 Cast 指令和 FP32 UB。适用场景见[场景3 选择策略](#选择策略)。

### 调用次数示例（Softmax ARA 分支）

**场景**：R=128, alignedCols=64, FP32

| 操作 | 优化前调用数 | 优化后调用数 | 调用数减少 |
|-----|--------|--------|------|
| Sub (x-max) | 128 次 | 2 次 | 64× |
| Div (exp/sum) | 128 次 | 2 次 | 64× |
| **总计** | **256 次** | **4 次** | **64×** |

---

## 候选 API

以下 API 的部分重载常见 `BinaryRepeatParams` 形式。逐项核对目标头文件；
表格不是对所有同名重载、数据类型或产品的支持声明：

| API | 用途 | 单行优化 | 多行优化 |
|-----|------|---------|---------|
| **Add** | 加法 | Adds | selected overload's broadcast stride |
| **Sub** | 减法 | Adds(-val) | selected overload's broadcast stride |
| **Mul** | 乘法 | Muls | selected overload's broadcast stride |
| **Div** | 除法 | Muls(1/val), when numerically equivalent | selected overload's broadcast stride |
| **Max** | 最大值 | - | selected overload's broadcast stride |
| **Min** | 最小值 | - | selected overload's broadcast stride |

---

## 常见错误

| 错误 | 原因 | 解决方案 |
|-----|------|---------|
| 编译错误：mask 超限 | mask 超过目标重载范围 | 按文档分批处理或回退循环 |
| 广播数据错误 | stride 未按目标重载表达广播 | 核对该字段的单位和广播取值；仅在文档定义时使用 0 |
| 部分行正确 | offset 计算错误 | `offset = startRow * alignedCols` |
| 越界崩溃 | repeatTime 计算错误 | 使用三目运算 |
| 标量方案 Buffer 不足 | 为 Duplicate 分配了额外 Tensor | 仅在目标类型、别名和数值语义允许时比较 Adds/Muls 方案 |
| FP16/BF16 结果超出误差约束 | 中间精度或舍入不满足算子契约 | 对比直接计算与目标版本支持的升精度方案，再按实测选择 |
| Cast 路径越界 | 临时 Tensor 与实际转换/别名计划不一致 | 从目标重载和实际存活 Tensor 推导空间，不套固定倍数 |
| `Get<T>(len)` 取出长度异常 | 误把字节数当成元素数 | `len` 是元素数，不是字节数 |

---

## 检查清单

使用算术运算 API 时，确保：

**标量操作（单行）**：
- [ ] Compare `Adds(-scalar)` with `Duplicate + Sub` for the selected types and alias rules
- [ ] Convert division to reciprocal multiplication only when zero, infinity, NaN, rounding, and error behavior remain compliant

**广播操作（多行）**：
- [ ] mask, stride, repeat, and alignedCols satisfy the exact overload
- [ ] use the selected overload's documented stride value to express broadcast
- [ ] batch when repeat or stride fields would exceed their documented type/range
- [ ] offset 计算正确：`offset = startRow * alignedCols`

**半精度加减法（FP16/BF16 Add/Sub）**：
- [ ] use measured error and the operator tolerance to choose direct or promoted compute
- [ ] size temporary buffers from the target overload's verified aliasing plan
- [ ] `Get<T>(len)` 的 len 是元素数；偏移用 `tensor[N]`
- [ ] select each Cast RoundMode from the exact source/destination support matrix

---

## 参考资料

- `BinaryRepeatParams`, `Adds`, `Muls`, `Sub`, and `Div`: locate the exact
  version-matched documents and overloads with `$ascendc-docs-search`.
