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
| `ascendc-api-best-practices` | Migrated | Several overload-specific alignment rules were written as universal rules; performance guidance was framed as a production blacklist; six relative links were broken | Added version/SoC discovery, source precedence, overload checks, provisional-result labeling, fixed links, and narrowed absolute claims |
| `ascendc-code-review` | Migrated and condensed | Required users to repeat code and a rule even when available in the workspace; used arbitrary additive confidence scores; required unavailable LSP/tool workflows; referenced a missing `agents/...` style path; bundled unused GitCode scripts and broad generic rulebooks | Replaced with findings-first, call-path-based review; retained concise Ascend-specific checklists; delegated API facts to the API and docs skills; removed unused scripts and generic duplicated guidance |
| `ascendc-docs-search` | Migrated and redesigned | Hard-coded one A3/CANN 8.5 environment, repository paths, and file counts; used Claude `Task`/`Explore`; split online search and page extraction across three scripts with `requests` and Beautiful Soup dependencies; one copied cleaner referenced a license file absent from TileXR | Added dynamic root/version discovery and reusable local search patterns; consolidated official endpoint search and page fetching into one standard-library script with public-URL validation and bounded excerpts; removed the unrelated cleaner and dependency file |
| `ascendc-env-check` | Migrated | Parsed one assumed `npu-smi` table format, treated warnings as available devices, contained fixed path/tool assumptions, and documented process release and device mutation commands inside a diagnostic skill | Reworked scripts to report raw bounded tool output and real path/version evidence; kept default behavior read-only; removed destructive diagnostic guidance |
| `cann-env-setup` | Migrated and redesigned | Embedded time-sensitive Python ranges and installation commands, used unverified repository URLs, and appended to `.bashrc` without a change boundary | Added platform/version inventory, official release-matrix verification, explicit approval before privileged or persistent changes, and layered verification |
| `commit-push-pr` | Not migrated | Duplicates the marketplace's Git-delivery workflow and the installed skill namespace; instructs the agent to stage, push, and open a PR in one response with unsafe parallelism | Continue to use `superpowers-neo-finishing-a-development-branch`; no duplicate skill is published |

## Packaging

The five migrated skills ship as the independent `ascendc-development` plugin. Each skill has Codex `agents/openai.yaml` metadata and is independently discoverable. Detailed reference material is loaded only when relevant.

The plugin is licensed separately under CANN Open Software License Agreement Version 2.0. TileXR's source tree declared that license but did not contain the referenced root `LICENSE`; the plugin includes the agreement recovered from the official Ascend SHMEM repository and records the source in `THIRD_PARTY_NOTICES.md`.

## Validation Contract

Repository validation checks:

- plugin and marketplace identities, paths, policies, versions, and licenses;
- the exact five-skill inventory and required Codex UI metadata;
- valid skill frontmatter and relative Markdown links;
- absence of Claude-specific task instructions, initializer placeholders, legacy split online-search dependencies, and the duplicate `commit-push-pr` skill;
- presence and Python syntax validation of the dependency-free official documentation search script;
- shell syntax and read-only failure behavior for the environment scripts.
