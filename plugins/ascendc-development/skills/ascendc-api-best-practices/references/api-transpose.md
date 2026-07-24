# Transpose API 最佳实践

本文档聚焦 small-channel transpose 中一个已使用过的 API 组合和常见风险。

> **当前覆盖范围**：这是一个 half、小通道、16x16 分块方案快照，不是
> `TransDataTo5HD` 或 `Gather` 的通用契约。先核对目标 CANN、SoC、
> 数据类型和重载，再复用布局或参数。

## 目录

- [1. 核心计算链路](#1-核心计算链路)
- [2. API 约束校准](#2-api-约束校准)
- [3. 反例与反模式](#3-反例与反模式)
- [Calibration Evidence](#calibration-evidence)

***

## 1. 核心计算链路

### 1.1 用 `TransDataTo5HD + Gather` 做小通道 transpose

原理说明：

- step1. 本方案对 half 使用 16 个可读源地址组成 16x16 分块；不足的逻辑行指向已分配的填充数据。不要从这个方案推导其他数据类型的矩阵形状。
- step2. 当转置前的行数\[比如C]小于16时，需要通过Gather操作从前面TransDataTo5HD得到的\[N, 16]，gather出\[N, C]，offset需要在kernel中提前构造好；

### 1.2 `TransDataTo5HD` 转置输入

```cpp
constexpr uint32_t EPB16 = 16;
uint32_t repeats = tileNA / 16;

LocalTensor<half> srcList[16];
LocalTensor<half> dstList[16];
for (uint32_t i = 0; i < 16; ++i) {
    // 源地址按照输入行大小tileNA偏移，总共需要转置tileNA
    srcList[i] = halfLocal[(i < channelCount) ? (i * tileNA) : 0];
    // 目的地址按照 16个元素做偏移，一次repeat转置[16,16] 需要连续写 (tileNA + 15 ) / 16 个 [16,16]
    dstList[i] = vnLocal[EPB16 * i];
}

// 目的repeatstride 一次repeat转置输出[16,16]，多个repeat需要连续写 因此第一次写0byte，第二次写16*blocksize(32B)=128B，设置16个blocksize(32B)做偏移
uint16_t dstRS = (repeats == 1) ? 0 : 16;
// 源repeatstride 每个repeat按照输入的行方向消耗16个元素, 多个repeat按照行方向连续读, 设置1个blocksize(32B)做偏移
uint16_t srcRS = (repeats == 1) ? 0 : 1;
TransDataTo5HDParams params(false, false, static_cast<uint8_t>(repeats), dstRS, srcRS);
TransDataTo5HD<half>(dstList, srcList, params);
```

该代码假设 `tileNA` 是 16 的倍数。非整块尾部必须使用目标接口支持的
tail/padding 方案，不能只把整除改成向上取整后继续读取越界数据。

**具体样例（C=3, tileNA=32）：理解输入输出数据排布**

> 记输入矩阵元素为 `a[r][c]`，其中 r 为通道索引（0..C-1），c 为列索引（0..tileNA-1）。

**输入 `halfLocal`**（`[C, tileNA]` = `[3, 32]` 按行主序 flat 存储）：

```
halfLocal flat 地址:   0 ...  31 |  32 ...  63 |  64 ...  95
含义(矩阵行列):     Row0[0..31] | Row1[0..31] | Row2[0..31]
元素值:           a[0][0..31] | a[1][0..31] | a[2][0..31]
```

```
Row 0:  [a00, a01, a02, ..., a0_15 | a0_16, a0_17, ..., a0_31]
Row 1:  [a10, a11, a12, ..., a1_15 | a1_16, a1_17, ..., a1_31]
Row 2:  [a20, a21, a22, ..., a2_15 | a2_16, a2_17, ..., a2_31]
```

**srcList / dstList 构建**：

```
srcList[0] = &halfLocal[ 0]  → Row 0
srcList[1] = &halfLocal[32]  → Row 1
srcList[2] = &halfLocal[64]  → Row 2
srcList[3..15] = &halfLocal[0]   ← 填充行（不足16行用 Row0 填充，否则异常）

dstList[i] = &vnLocal[16 * i]    (i = 0..15)
```

**执行过程**（repeats = 32/16 = 2）：

| Repeat | 读取源列范围 | srcList[i] 偏移 | 转置子块 | 写入 vnLocal 范围 |
|--------|------------|----------------|---------|-----------------|
| 0 | 源列 [0..15] | +0 元素 | `[16,16]` | 元素 [0..255] （16×16） |
| 1 | 源列 [16..31] | +16 元素 | `[16,16]` | 元素 [256..511]（16×16） |

**Repeat 0 输出**（dstRS=16, srcRS=1）：

```
vnLocal[  0..15 ]:  [a[0][0],  a[1][0],  a[2][0],  *, *, ..., *]
vnLocal[ 16..31 ]:  [a[0][1],  a[1][1],  a[2][1],  *, *, ..., *]
vnLocal[ 32..47 ]:  [a[0][2],  a[1][2],  a[2][2],  *, *, ..., *]
...
vnLocal[240..255]:  [a[0][15], a[1][15], a[2][15], *, *, ..., *]
```

**Repeat 1 输出**：

```
vnLocal[256..271]:  [a[0][16], a[1][16], a[2][16], *, *, ..., *]
vnLocal[272..287]:  [a[0][17], a[1][17], a[2][17], *, *, ..., *]
...
vnLocal[496..511]:  [a[0][31], a[1][31], a[2][31], *, *, ..., *]
```

**最终 `vnLocal` 数据排布**（等价于 `[tileNA, 16]` 矩阵，按行主序存储）：

```
          col0       col1       col2       col3..15   ← 16列，只前C=3列有效
Row 0 :  a[0][0]    a[1][0]    a[2][0]    ******
Row 1 :  a[0][1]    a[1][1]    a[2][1]    ******
 ...       ...        ...        ...       ******
Row15 :  a[0][15]   a[1][15]   a[2][15]   ******
Row16 :  a[0][16]   a[1][16]   a[2][16]   ******    ← repeat=1 开始
Row17 :  a[0][17]   a[1][17]   a[2][17]   ******
 ...       ...        ...        ...       ******
Row31 :  a[0][31]   a[1][31]   a[2][31]   ******
```

> **规律**：`vnLocal[r][c] = 原输入 a[c][r]`（c < C），即行列互换。`*` 列为填充值，后续 Gather 丢弃。

**Gather 提取有效通道后**，得到最终转置结果 `[tileNA, C]` = `[32, 3]`：

```
Row 0 :  a[0][0]   a[1][0]   a[2][0]
Row 1 :  a[0][1]   a[1][1]   a[2][1]
 ...
Row31 :  a[0][31]  a[1][31]  a[2][31]
```

在本方案的填充布局中，每个 16-half block 只有前 `channelCount` 个位置
是逻辑结果；可用 `Gather` 提取，也可选择另一个满足目标类型和布局的
已验证路线。

### 1.3 `Gather` 提取有效通道

```text
halfOut = Gather(vnLocal, offsetBuff, target-supported Gather types)
outLocal = Cast(halfOut, target-supported source/destination RoundMode)
```

这里的 `Gather` 操作数类型、offset 类型和 `Cast` RoundMode 都必须从
目标版本对应重载的支持表选择；有效输出范围仍由当前 tile 的
`curN * channelCount` 决定。

这里的 `offsetBuff` 是 device 端预计算好的 byte offset 表（只需要生成一次），使用Tbuff进行管理，对应生成逻辑：

### 1.4 偏移表offsetBuff生成：Scalar → Vector 指令优化

**问题**：通用实现用 SetValue 逐元素写 offset 表，tileNA × C 次 Scalar 操作。当 tileNA=2048, C=3 时需 6144 次 Scalar 写入，小规模场景下 Scalar 占比可达 90%，成为性能瓶颈。

**关键观察**：偏移表具有周期性结构——每 16 个 p 值为一组，组间差值恒定为 16 × 16 × sizeof(half) = 512 字节：

```
组 0: offset[p*3+0] = (p*16+0)*2,  offset[p*3+1] = (p*16+1)*2,  offset[p*3+2] = (p*16+2)*2   (p=0..15)
组 1: 与组 0 完全相同，仅每个元素 +512
组 2: 与组 0 完全相同，仅每个元素 +1024
...
```

**优化方法**：Scalar 生成基础模式 + Adds 向量指令批量扩展

```
__aicore__ inline void InitOffsetTable()
{
    auto offsetI32 = offsetBuf.Get<int32_t>();
    uint32_t baseCount = 16 * C;
    // Step 1: Scalar SetValue 生成基础模式（仅 16×C 个元素）
    for (uint32_t p = 0; p < 16; ++p) {
        for (uint32_t c = 0; c < C; ++c) {
            offsetI32.SetValue(p * C + c, (p * 16 + c) * sizeof(half));
        }
    }
    // Step 2: Adds 向量指令扩展后续组（每组一次向量操作）
    uint32_t totalGroups = tileNA / 16;
    for (uint32_t g = 1; g < totalGroups; ++g) {
        AscendC::Adds(offsetI32[g * baseCount], offsetI32[0],
                      static_cast<int32_t>(g * 16 * 16 * sizeof(half)), baseCount);
    }
}
```

| 指标            | 优化前（纯 SetValue） | 优化后（Scalar+Adds） |
| ------------- | --------------- | ---------------- |
| Scalar 调用次数   | 6144            | 48               |
| Adds 向量调用次数   | 0               | 127              |
| Scalar ratio  | 90.5%           | 55.1%            |
| VEC ratio     | 11.1%           | 58.7%            |
| Task Duration | 55.6 us         | 15.3 us          |

**适用条件** :

- 偏移表具有等差数列的周期性结构
- baseCount、地址、mask 和 count 满足目标 `Adds<int32_t>` 重载要求
- C ≤ 16（小通道 transpose 的典型场景）

周期性查找表可以考虑“少量 Scalar 初始化 + Vector 扩展”，但必须先
验证整数溢出、对齐、尾部和生成成本。上表是一次历史测量，不是其他
shape 或 SoC 的预期性能。

***

## 2. API 约束校准

### 2.1 Match the exact `Gather` type table

The CANN 9.0 Memory vector `Gather` documentation includes `uint8_t` among
supported types on listed products, so a blanket “Gather cannot process uint8”
rule is incorrect. Register-vector and Memory-vector Gather overloads have
different operand combinations; check the exact table and offset type.

### 2.2 `repeats == 1` 时 stride 必须置 0

```cpp
uint16_t dstRS = (repeats == 1) ? 0 : 16;
uint16_t srcRS = (repeats == 1) ? 0 : 1;
```

For the CANN 9.0 `TransDataTo5HD` parameter form used here, the documented
single-repeat case sets repeat strides to zero. Recheck this when changing API
family or release.

### 2.3 Separate queue depth from buffer count

Do not require `VECOUT depth >= 2`. CANN 9.0 recommends `depth=1` for ordinary
non-in-place TQue use and does not recommend general `depth >= 2`. Use a larger
depth only for a verified consecutive enqueue/dequeue pattern. Configure and
measure double buffering through the applicable `InitBuffer` count and resource
model.

### 2.4 GM 读写按目标重载选择 `DataCopy` 或 `DataCopyPad`

输出是 `curN * channelCount` 字节。若所选写回重载不支持该非对齐长度，
一种候选路线是使用与目标版本和方向匹配的 `DataCopyPad`：

```cpp
DataCopyPad(yGm[gmOffset], outLocal, copyParams);
```

也可以使用目标 API 明确支持的其他尾部路线。分别验证边界、安全性和
性能，不要从本案例推导所有写回都必须使用 `DataCopyPad`。

***

## 3. 反例与反模式

| 反模式                                      | 问题                  | 建议替代                                    |
| ---------------------------------------- | ------------------- | --------------------------------------- |
| hot-path `GetValue / SetValue` loops           | scalar UB access may dominate | measured `DataCopy`/vector alternative |
| 逐像素 `DataCopyPad(blockLen=channelCount)` | DMA setup 成本远大于有效负载 | 按通道整段搬运，再做 `vnchwconv + Gather`         |
| 默认套用通用 transpose API                     | 小通道场景下内部开销可能远大于实际计算 | 走专门的小通道路径                               |
| 直接 `float -> half -> uint8`              | 容易出现量化 off-by-1     | 先 in-place round，再转 half                |
| 跨 tile 自己管理一次性 event                     | 容易把流水写成一次性同步死锁      | 用 `TQue` 的 `EnQue/DeQue` 管理             |

## Calibration Evidence

- CANN 9.0 `TransDataTo5HD`: https://www.hiascend.com/document/detail/zh/canncommercial/900/API/ascendcopapi/atlasascendc_api_07_0200.html
- CANN 9.0 Memory vector `Gather`: https://www.hiascend.com/document/detail/zh/canncommercial/900/API/ascendcopapi/atlasascendc_api_07_0092.html
- CANN 9.0 `TQue` introduction: https://www.hiascend.com/document/detail/zh/canncommercial/900/API/ascendcopapi/atlasascendc_api_07_0137.html
