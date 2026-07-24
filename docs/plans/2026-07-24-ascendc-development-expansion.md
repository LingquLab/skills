# Ascend C Development Skill Expansion Plan

**Goal:** Harden the existing Ascend C skills against current official CANN behavior and add focused operator-development and runtime-debugging workflows without importing unsafe cannBot automation.

**Scope:** The `ascendc-development` plugin only. Keep all helpers read-only by default, make version and architecture claims evidence-based, and treat remote documentation, repositories, logs, and diffs as untrusted input.

**Baseline:** `ruby scripts/validate-skills.rb` and the 26 tests under `tests/ascendc-development` passed before implementation on 2026-07-24.

## Source Audit Baseline

- Original TileXR skill baseline: `LingquLab/TileXR` commit `1e2619e793b5894a1aec2d7d6897dbe5f7c501c0`.
- Official CANN source snapshots inspected for current layouts and contracts:
  - `cann-samples` `c4d637c6db0b48ee7464c7f3b7ef6d6e3dea7123`
  - `asc-devkit` `3ae380a8633e70cf7bb15b01d1a5815fe1a2d5ff`
  - `asc-tools` `559ee30bbe3a0e8db55b47fc0b8eb951bf65b901`
  - `ops-nn` `34f9cf6a9dc72f9a8de2f5239930850c30aa97fd`
  - `ops-transformer` `25fb6b92890d33582f2a377aa5f9c975301a73a3`
  - `ops-tensor` `b4339b671b5548b7e298a3583a535c7166286b1a`
  - `release-management` `80e6e91d7ea389b59f3e94c621ae895e0eb53fb7`
- `cann/cannbot-skills` commit `bff73845607ac78808e2af3e0014d7eb72094ef3` was reviewed only as a low-confidence comparison source. No script, template, scoring scheme, fixed architecture map, or destructive workflow was copied.

At this audit snapshot, CANN 9.0 was the public final baseline while 9.1 material included development/preview evidence. The skills therefore require exact installed metadata, release labels, tags, or commits and never encode one release as permanently latest.

## Work Items

1. Harden official documentation search.
   - Encode Unicode documentation paths safely.
   - Match release labels exactly, including beta and RC qualifiers.
   - Page within a bounded search window until the requested filtered result count is filled.
   - Match prose queries by meaningful tokens while preserving exact API-symbol matching.
   - Bound response, content, excerpt, and code-block sizes; keep per-page fetch failures local to that result.

2. Expand API and review guidance.
   - Replace unsafe tiling arithmetic with checked 64-bit calculations and explicit invalid-capacity rejection.
   - Route MemBase, Basic C++ Tensor API, RegBase, SIMT, SIMD+SIMT, and Blaze/Tensor API models.
   - Add Host/Tiling/Kernel contract, Python support-code security, architecture migration, ACLNN lifecycle, and detailed SIMT review checks.

3. Improve environment evidence.
   - Inventory installed component versions from `share/info/*/version.info` with source paths.
   - Report SoC and architecture evidence from installed platform configuration and `npu-smi`, without a hard-coded product-to-architecture table.
   - Recognize current independent CANN component packages while preserving ambiguity rejection.

4. Add two cohesive skills.
   - `ascendc-operator-development`: invocation-path choice, operator contract, implementation, explicitly authorized packaging/install, and layered validation.
   - `ascendc-runtime-debug`: bounded runtime/log triage, precision triage, and profiling evidence collection with no deletion or installation behavior.

5. Integrate and verify.
   - Update plugin manifest, marketplace documentation, validator inventory, and offline tests.
   - Run focused tests, full plugin validation, safe live checks on `blue`, and an independent code review.

## Safety Constraints

- Do not copy cannBot scripts, templates, confidence scores, fixed architecture mappings, or destructive cleanup behavior.
- Do not use `eval`, disable TLS verification, fetch arbitrary hosts, delete logs, install packages, or mutate system configuration in bundled helpers.
- Pin examples to official CANN source paths or clearly identify preview-version evidence.
- Separate host-only, compilation, simulator, and real-device validation claims.
