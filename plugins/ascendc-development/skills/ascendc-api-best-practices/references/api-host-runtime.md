# Host Runtime API Use

This reference applies to Host code that initializes ACL Runtime, queries devices, allocates resources, and launches a Kernel. Verify the exact lifecycle and attribute enum against the target Runtime release.

## Query Before Launch

CANN 9.0 documents `aclrtGetDeviceInfo` as:

```cpp
aclError aclrtGetDeviceInfo(uint32_t deviceId, aclrtDevAttr attr, int64_t* value);
```

Its documented `deviceId` range is obtained from `aclrtGetDeviceCount`. The API page does not state that `aclrtSetDevice` must be called before this query, so do not report that sequence as a universal requirement.

Use `aclrtSetDevice` before operations that require a current device context, and pair every successful set with the release's documented reset/cleanup path. Check every return value, including initialization and cleanup where the project can act on failures.

## Bounded Example

```cpp
aclError ret = aclInit(nullptr);
if (ret != ACL_SUCCESS) {
    return ret;
}

uint32_t deviceCount = 0;
ret = aclrtGetDeviceCount(&deviceCount);
if (ret != ACL_SUCCESS || deviceCount == 0) {
    aclFinalize();
    return ret != ACL_SUCCESS ? ret : ACL_ERROR_INVALID_PARAM;
}

const uint32_t deviceId = 0;
int64_t vectorCoreCount = 0;
ret = aclrtGetDeviceInfo(deviceId, ACL_DEV_ATTR_VECTOR_CORE_NUM, &vectorCoreCount);
if (ret != ACL_SUCCESS) {
    aclFinalize();
    return ret;
}

ret = aclrtSetDevice(deviceId);
if (ret != ACL_SUCCESS) {
    aclFinalize();
    return ret;
}

// Allocate resources and launch work for deviceId here.

aclError resetRet = aclrtResetDevice(deviceId);
aclError finalizeRet = aclFinalize();
return resetRet != ACL_SUCCESS ? resetRet : finalizeRet;
```

Adapt error constants and cleanup style to the target headers and project policy; the example demonstrates checked boundaries, not a complete application.

## Core Counts and Launch Dimensions

- Select a documented `aclrtDevAttr` that matches the Kernel's execution model and target product.
- Do not embed one product's AI, Cube, or Vector core count as a fallback.
- A reported hardware core count is an upper resource fact, not necessarily the correct launch block count.
- Cap and partition work from actual shapes, Kernel behavior, workspace, and product limits.
- Treat unsupported attributes as a compatibility finding, not as permission to use a guessed count.

## Evidence

- CANN 9.0 `aclrtGetDeviceInfo`: https://www.hiascend.com/document/detail/zh/canncommercial/900/API/runtimeapi/aclcppdevg_03_1867.html
- Use `$ascendc-docs-search` for the target release's `aclrtSetDevice`, `aclrtResetDevice`, and `aclrtDevAttr` documentation.
