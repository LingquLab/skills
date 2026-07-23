# Pipeline Synchronization Guide

This is a TQue-based MTE/Vector pattern. Confirm the selected API's documented
execution and event model; do not assume every same-name data movement call has
identical ordering semantics.

---

## 目录

1. [核心问题](#核心问题)
2. [解决方案](#解决方案)
3. [两种方案对比](#两种方案对比)
4. [完整流水线模板](#完整流水线模板)
5. [调试技巧](#调试技巧)

---

## 核心问题

For asynchronous data movement, directly consuming or freeing a buffer without
the required dependency can race the transfer.

### 硬件架构

```
GM → MTE2 (异步) → UB → Vector (同步) → MTE3 (异步) → GM
```

### 问题场景

```cpp
// ❌ 错误：DataCopyPad 后直接使用数据
AscendC::LocalTensor<float> xLocal = inQueueX.AllocTensor<float>();
AscendC::DataCopyPad(xLocal, xGm[offset], copyParams, padParams);
AscendC::Adds<float>(yLocal, xLocal, 1.0f, count);  // 可能读到未完成搬运的数据！
```

**现象**：输出数据随机、错误

---

## 解决方案

### 方案一：EnQue/DeQue 队列同步（推荐）

**原理**：TQue 的 EnQue/DeQue 机制自动提供硬件同步点。

```cpp
// ✅ 正确：使用 EnQue/DeQue 同步
// Step 1: CopyIn - MTE2 搬运
AscendC::LocalTensor<float> xLocal = inQueueX.AllocTensor<float>();
AscendC::DataCopyPad(xLocal, xGm[gmOffset], copyInParams, padParams);
inQueueX.EnQue(xLocal);                    // 标记"就绪"

// Step 2: Compute - Vector 计算
AscendC::LocalTensor<float> xIn = inQueueX.DeQue<float>();  // 阻塞等待 MTE2 完成
AscendC::LocalTensor<float> yLocal = outQueueY.AllocTensor<float>();
AscendC::Adds<float>(yLocal, xIn, 1.0f, count);
outQueueY.EnQue(yLocal);
inQueueX.FreeTensor(xIn);

// Step 3: CopyOut - MTE3 搬运
AscendC::LocalTensor<float> yOut = outQueueY.DeQue<float>();  // 阻塞等待 Vector 完成
AscendC::DataCopyPad(yGm[gmOffset], yOut, copyOutParams);
outQueueY.FreeTensor(yOut);
```

**关键点**：
- `EnQue(xLocal)` 标记 buffer 数据就绪
- `DeQue<float>()` 阻塞等待数据就绪
- For this documented queue path, `DeQue` establishes the dependency needed by the consumer

### 方案二：PipeBarrier 手动同步

```cpp
// ✅ 可用：使用 PipeBarrier 同步
AscendC::LocalTensor<float> xLocal = inQueueX.AllocTensor<float>();
AscendC::LocalTensor<float> yLocal = outQueueY.AllocTensor<float>();

AscendC::DataCopyPad(xLocal, xGm[gmOffset], copyInParams, padParams);
AscendC::PipeBarrier<PIPE_ALL>();          // 等待 MTE2 完成

AscendC::Adds<float>(yLocal, xLocal, 1.0f, count);

AscendC::DataCopyPad(yGm[gmOffset], yLocal, copyOutParams);
AscendC::PipeBarrier<PIPE_ALL>();          // 等待 MTE3 完成
```

**Tradeoff**: a broad barrier can serialize more work than necessary. Measure it
against a correctly scoped queue/event dependency before reporting a performance
regression.

---

## 两种方案对比

| 特性 | EnQue/DeQue | PipeBarrier |
|-----|-------------|-------------|
| 同步粒度 | buffer 级别 | 全流水线 |
| 性能 potential | can overlap work | may serialize more work |
| 代码复杂度 | 需要队列管理 | 简单直接 |
| Selection | normal queue pipeline candidate | debugging or documented dependency candidate |

### EnQue/DeQue 的双重作用

1. **队列管理**：Double Buffer 场景下管理多 buffer 轮转
2. **硬件同步**：提供 MTE ↔ Vector 之间的同步点

```cpp
// EnQue/DeQue 不仅仅是"队列"，更重要的是同步机制
inQueueX.EnQue(xLocal);    // 1. 标记数据就绪  2. 通知硬件可以等待
xLocal = inQueueX.DeQue(); // 1. 阻塞等待就绪  2. 获取可用 buffer
```

---

## 完整流水线模板

```cpp
__aicore__ inline void ProcessTile(uint32_t tileIdx)
{
    // ========== CopyIn 阶段 ==========
    // MTE2: GM → UB（异步）
    AscendC::LocalTensor<float> xLocal = inQueueX.AllocTensor<float>();
    AscendC::DataCopyPad(xLocal, xGm[tileIdx * tileSize], copyParams, padParams);
    inQueueX.EnQue(xLocal);              // 同步点：标记就绪

    // ========== Compute 阶段 ==========
    // Vector: UB 计算（同步，需等待 MTE2）
    AscendC::LocalTensor<float> xIn = inQueueX.DeQue<float>();  // 同步点：等待 MTE2
    AscendC::LocalTensor<float> yLocal = outQueueY.AllocTensor<float>();
    AscendC::Adds<float>(yLocal, xIn, 1.0f, tileSize);
    outQueueY.EnQue(yLocal);             // 同步点：标记就绪
    inQueueX.FreeTensor(xIn);

    // ========== CopyOut 阶段 ==========
    // MTE3: UB → GM（异步，需等待 Vector）
    AscendC::LocalTensor<float> yOut = outQueueY.DeQue<float>();  // 同步点：等待 Vector
    AscendC::DataCopyPad(yGm[tileIdx * tileSize], yOut, copyParams);
    outQueueY.FreeTensor(yOut);
}
```

### 流水线时序图

```
时间 →

Tile 0:  [MTE2]──EnQue──[Vector]──EnQue──[MTE3]
                      ↑ DeQue等待    ↑ DeQue等待
Tile 1:          [MTE2]──EnQue──[Vector]──EnQue──[MTE3]
                  ↑ 并行！    ↑ DeQue等待    ↑ DeQue等待

关键：DeQue 阻塞等待上一个阶段的异步操作完成
```

---

## 调试技巧

### 检查缺少 EnQue/DeQue

```cpp
// ❌ 错误：AllocTensor 后直接用
LocalTensor<T> x = inQueue.AllocTensor<T>();
DataCopy(x, gm, size);
Compute(x);  // 错！可能读到未完成搬运的数据

// ✅ 正确：DeQue 后再计算
LocalTensor<T> x = inQueue.AllocTensor<T>();
DataCopy(x, gm, size);
inQueue.EnQue(x);
LocalTensor<T> xIn = inQueue.DeQue<T>();  // 等待搬运完成
Compute(xIn);
```

### 临时加 PipeBarrier 调试

```cpp
DataCopy(x, gm, size);
PipeBarrier<PIPE_ALL>();  // 临时加，如果结果正确说明是同步问题
Compute(x);
```

If a barrier changes the result, synchronization is a strong hypothesis, not
complete proof. Verify initialization, bounds, and the exact dependency, then
replace the broad diagnostic barrier with the narrow documented mechanism.

### 常见误区

| 误区 | 正确理解 |
|-----|---------|
| AllocTensor 后数据就可用 | AllocTensor 只分配内存，不等待搬运 |
| Data movement is always synchronous | inspect the selected overload's execution model |
| Every path must use EnQue/DeQue | use the dependency mechanism required by the chosen queue/event model |
| A barrier is automatically slow | measure its actual serialization on the target path |
