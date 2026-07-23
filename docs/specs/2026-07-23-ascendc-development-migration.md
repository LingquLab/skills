# Ascend C Development Skill Migration

## Source

- Repository: `https://github.com/LingquLab/TileXR`
- Source directory: `.claude/skills`
- Audited commit: `1e2619e793b5894a1aec2d7d6897dbe5f7c501c0`
- Source snapshot date: 2026-07-21

The source contained six skills and 11,132 lines across skill instructions, references, scripts, styles, and scenarios.

## Decisions

| Source skill | Decision | Main issues found | Migration changes |
|---|---|---|---|
| `ascendc-api-best-practices` | Migrated and calibrated | Several version-, product-, API-family-, and overload-specific rules were written as universal rules. Examples included an obsolete Reduce helper signature, fixed temporary-buffer sizing, one Cast rounding shortcut, a blanket `Gather<uint8_t>` prohibition, mandatory `VECOUT depth >= 2`, and an undocumented `aclrtSetDevice` prerequisite | Added source precedence and version/SoC/overload discovery; checked disputed rules against CANN 9.0 official pages and CANN 9.1 installed headers; corrected the Reduce signature and runtime lifecycle; rewrote precision, queue, transpose, buffer, and performance guidance as evidence-scoped decisions; fixed broken links |
| `ascendc-code-review` | Migrated and calibrated | Required users to repeat code and a rule even when available in the workspace; used arbitrary additive confidence scores; required unavailable LSP/tool workflows; referenced a missing `agents/...` style path; mixed useful GitCode acquisition with a full bare clone, a duplicate source-clone helper, and broad generic rulebooks | Replaced the review method with findings-first, call-path-based analysis; retained concise Ascend-specific checks; delegated API facts to the API and docs skills; restored one dependency-free GitCode PR diff client using canonical URL checks and bounded shallow fetches; removed the duplicate clone helper and generic duplicated guidance |
| `ascendc-docs-search` | Migrated and redesigned | Hard-coded one A3/CANN 8.5 environment, repository paths, and file counts; used Claude `Task`/`Explore`; split online search and page extraction across three scripts with `requests` and Beautiful Soup dependencies; one copied cleaner referenced a license file absent from TileXR | Added dynamic root/version discovery and reusable local search patterns; consolidated official endpoint search and page fetching into one standard-library script with public-URL validation and bounded excerpts; removed the unrelated cleaner and dependency file |
| `ascendc-env-check` | Migrated and calibrated | Parsed one assumed `npu-smi` table format, treated warnings as available devices, conflated command presence with usable hardware, contained fixed path/tool assumptions, and documented process release and device mutation commands inside a diagnostic skill | Reworked scripts to preserve command exit status, report bounded raw diagnostics and component version sources, and remain read-only; removed destructive guidance; added offline fixture coverage and live checks on `blue` |
| `cann-env-setup` | Migrated and calibrated | Embedded time-sensitive Python ranges and installation commands, used unverified repository URLs, installed broad Python dependencies unconditionally, and appended to `.bashrc` without a change boundary | Replaced fixed installation recipes with host/package inventory, official release-matrix verification, explicit approval before downloads or persistent changes, component-level version checks, and separate package, environment, compile, and real-hardware verification layers |
| `commit-push-pr` | Not migrated | Duplicates the marketplace's Git-delivery workflow and the installed skill namespace; instructs the agent to stage, push, and open a PR in one response with unsafe parallelism | Continue to use `superpowers-neo-finishing-a-development-branch`; no duplicate skill is published |

## Packaging

The five migrated skills ship as the independent `ascendc-development` plugin. Each skill has Codex `agents/openai.yaml` metadata and is independently discoverable. Detailed reference material is loaded only when relevant. Scripted online access is retained where it removes repeated manual work: official Ascend documentation search/page extraction and public GitCode PR diff acquisition.

The plugin is licensed separately under CANN Open Software License Agreement Version 2.0. TileXR's source tree declared that license but did not contain the referenced root `LICENSE`; the plugin includes the agreement recovered from the official Ascend SHMEM repository and records the source in `THIRD_PARTY_NOTICES.md`.

## Validation Contract

Repository validation checks:

- plugin and marketplace identities, paths, policies, versions, and licenses;
- the exact five-skill inventory and required Codex UI metadata;
- valid skill frontmatter and relative Markdown links;
- absence of Claude-specific task instructions, initializer placeholders, legacy split online-search dependencies, and the duplicate `commit-push-pr` skill;
- presence and Python syntax validation of both dependency-free online clients;
- required calibration evidence for the corrected Reduce, Cast, Gather, TQue, and Runtime rules;
- shell syntax, read-only command policy, toolkit discovery, and invalid-active-path failure behavior for the environment scripts;
- offline regression tests for official documentation search, GitCode PR diff acquisition, and environment parsing.

## Live Calibration Evidence

The online clients were exercised against Huawei's official documentation service and a public `cann/ops-transformer` GitCode pull request. On `blue`, the existing CANN 9.1 tree was inspected without installation or persistent changes: `set_env.sh` resolved matching toolkit and OPP 9.1.0 metadata, a minimal ACL source passed `bisheng` syntax compilation, eight 910B3 devices were visible, the installed `GetReduceMaxMaxMinTmpSize` declaration matched the corrected seven-parameter signature, and `SetAtomicType` was present with product-specific implementations. The offline package inspector also classified the existing CANN 8.2.RC1 toolkit, kernels, and NNAL run packages correctly. These observations validate the discovery and inspection workflows; they do not make CANN 9.1, CANN 8.2, or 910B3 a plugin-wide default.
