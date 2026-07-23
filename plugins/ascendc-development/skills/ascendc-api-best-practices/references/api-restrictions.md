# Ascend C API 使用限制与替代方案

> **重要**：这是常见限制的迁移快照。每条限制都要先匹配执行侧、目标 CANN 版本、SoC 和具体重载。

---

## 1. 编译期限制

### 1.1 Kernel 中的标准库可用性

**原因**：许多 AI Core Kernel 编译模式不提供完整 C++ 标准库；可用范围以目标编译器和头文件为准。

**触发场景**：目标 Kernel 编译模式拒绝某个标准库头文件或调用

**候选替代路线**：

| Operation | Candidate when the selected mode lacks `std::` support | Required verification |
|---|---|---|
| scalar min/max | conditional expression | operand type, signedness, NaN and tie behavior |
| vector abs/min/max | target-matched `Abs`, `Min`, or `Max` overload | supported type, mask/count, alias and product table |
| vector sqrt/exp/log | target-matched `Sqrt`, `Exp`, or `Log` overload | API existence, accuracy, special values and product table |
| power/trigonometric/rounding | an API explicitly present in the target headers | exact function name, supported types and numerical contract |
| `isnan`/`isinf` | target-supported special-value API or a tested implementation | NaN/Inf representation and compiler behavior |

The names in this table are search candidates, not a promise that every listed
API exists for every release or type. Compile the selected alternative with the
target compiler.

**Conditional example**:
```cpp
// These calls are a problem only when the selected Kernel compilation mode
// does not provide the included standard-library surface.
#include <algorithm>
#include <cmath>

uint32_t result = std::min(a, b);
float sqrtValue = std::sqrt(x);
float expValue = std::exp(x);
```

**Candidate fallback after overload verification**:
```cpp
uint32_t minimum = (a < b) ? a : b;

AscendC::LocalTensor<T> minLocal = minBuf.Get<T>();
AscendC::LocalTensor<T> srcLocal = srcBuf.Get<T>();
AscendC::Min<T>(minLocal, srcLocal, src2Local, count);

AscendC::LocalTensor<T> dstLocal = dstBuf.Get<T>();
AscendC::Sqrt<T>(dstLocal, srcLocal, count);
```

**重要**：不要把 Host/Tiling 侧的标准库规则套到 Kernel，也不要在未
编译目标模式时断言某个 `std::` API 可用或不可用。

### 1.2 Kernel dynamic allocation

Many AI Core Kernel compilation modes do not provide general-purpose dynamic
allocation. Confirm the target compiler model; when it is unavailable, plan UB
through TPipe/TQue/TBuf and Tiling rather than using `new`, `malloc`, or
standard containers that allocate dynamically.

**触发场景**：创建数组、缓冲区等

**错误示例**：
```cpp
std::vector<int> vec;       // ❌ 动态分配
int* ptr = new int[10];     // ❌ 动态分配
int* arr = malloc(100);     // ❌ 动态分配
```

**Kernel-side alternative**:
```cpp
pipe.InitBuffer(inQueue, bufferCount, bufferBytes);
```

### 1.3 Host/Kernel 头文件隔离

Keep Kernel-only headers out of translation units that are compiled only by the
Host compiler. File extensions alone do not prove the compilation role; inspect
the build command and project layout before reporting a violation.

**错误示例**：
```cpp
// A Host-only translation unit compiled without Kernel headers
#include "kernel_operator.h"  // wrong for this build role
```

**正确用法**：
```cpp
// Host-only translation unit
#include "tiling.h"  // ✅ 仅必要头文件
#include <cstring>

// kernel/operator.h
#include "kernel_operator.h"  // ✅ Kernel 侧允许
```

---

## 2. API 使用限制索引

以下限制在各专题文档中详细说明：

| 限制类型 | 详细文档 | 核心要点 |
|---------|---------|---------|
| **GM 数据搬运** | [api-datacopy.md](api-datacopy.md) | 检查逐元素热路径、重载和尾部对齐 |
| **Reduce API** | [api-reduce.md](api-reduce.md) | 核对目标重载的 alias、临时空间和 shape 规则 |
| **Compare 对齐** | 见下文 2.1 | 按目标重载核对 count、mask 和 padding |
| **repeatTime 限制** | [api-repeat-limits.md](api-repeat-limits.md) | uint8_t 最大 255，需分批处理 |
| **流水线同步** | [api-pipeline.md](api-pipeline.md) | 按队列模型和真实依赖选择同步方式 |

### 2.1 Compare API 对齐示例

某些版本和重载要求 `count` 对应的空间满足 256 字节对齐。不要把这个示例推广到所有 `Compare` 形式；先查目标文档。

**处理方案**：Padding 策略

```cpp
// 1. 计算对齐大小（float 类型：64 的倍数）
constexpr uint32_t A0 = 32;
constexpr uint32_t A0_ALIGN = (A0 + 63) / 64 * 64;  // = 64

// 2. UB Buffer 使用对齐大小
pipe.InitBuffer(inQueue, 1, R * A0_ALIGN * sizeof(float));

// 3. CopyIn 时填充极值
Duplicate(xLocal, -FLT_MAX, R * A0_ALIGN);  // ArgMax 用极小值
// 再拷贝实际数据到前 A0 个位置

// 4. API 调用使用对齐大小
Compare(cmpLocal, srcLocal, maxLocal, CMPMODE::GT, A0_ALIGN);

// 5. CopyOut 只输出有效数据
DataCopy(dstGm, yLocal, A0);  // 只输出 A0 个
```

**极值选择**：
- ArgMax / 找最大值：`-FLT_MAX` 或 `-INFINITY`
- ArgMin / 找最小值：`FLT_MAX` 或 `INFINITY`

---

## 3. 类型与常量规范

### 3.1 编译期常量

Use `constexpr` for values that are genuinely compile-time constants. Shapes,
tiling values, product capacities, and workload-dependent loop bounds must stay
runtime values. Do not report an ordinary `const` as a performance defect
without compiler evidence.

```cpp
// ✅ 正确：编译期常量
constexpr uint32_t BUFFER_NUM = 2;
constexpr uint32_t BLOCK_SIZE = 32;

// Runtime tiling value
const uint32_t tileRows = tilingData.tileRows;
const uint64_t availableUb = tilingData.availableUb;
```

### 3.2 类型转换

Derive the expression type before adding a cast. Cast before an integer
multiplication that could overflow; do not add a cast merely for style or assume
that promotion to `float` loses precision relative to a `half` operand.

```cpp
// ✅ 正确：显式转换
T sumVal = scalarLocal.GetValue(0);
T invSumVal = static_cast<T>(1.0f / static_cast<float>(sumVal));
Muls<T>(dst, src, invSumVal, count);
```

---

## 4. 快速诊断清单

遇到编译错误时，检查：

- [ ] Kernel 使用的 `std::` 函数是否被目标编译模式支持；不支持时改用已验证的 Ascend C API 或基础操作
- [ ] 是否使用了动态内存（`std::vector`, `new`）→ 改用静态分配
- [ ] Host-only 编译单元是否错误引入了目标编译器不可用的 Kernel-only 头文件
- [ ] Reduce API 的 dst、src 和 tmp alias 是否满足目标重载
- [ ] 所选 Reduce 层级是否满足功能、支持范围和实测性能要求
- [ ] 编译期常量和运行时 Tiling 值是否被正确区分
- [ ] 使用的 shape、tensor 和参数类型是否确实存在于目标版本头文件
- [ ] Compare API 的 count、mask 和 padding 是否满足目标版本对应重载的约束

---

## 5. 相关文档

- [api-datacopy.md](api-datacopy.md)：DataCopyPad 使用规范
- [api-reduce.md](api-reduce.md)：Reduce API 详细用法
- [api-repeat-limits.md](api-repeat-limits.md)：repeatTime 限制与处理
- [api-buffer.md](api-buffer.md)：Buffer 管理最佳实践
- [api-precision.md](api-precision.md)：精度转换规范
