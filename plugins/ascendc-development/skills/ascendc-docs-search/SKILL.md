---
name: ascendc-docs-search
description: Locate authoritative, version-matched Ascend C and CANN API documentation, headers, implementation examples, compatibility notes, and source references. Use when answering API questions, checking overloads or SoC restrictions, finding operator examples, validating review claims, or resolving differences between local CANN installations and online documentation.
---

# Ascend C Documentation Search

Return the best source for the user's actual CANN version and target SoC. Do not assume a fixed server model, repository layout, document count, or CANN release.

## Source Priority

1. The target repository's checked-in documentation, headers, examples, and build metadata.
2. The installed CANN tree selected by `ASCEND_HOME_PATH`, including its `version.info` and headers.
3. A nearby `asc-devkit` checkout whose version matches the target environment.
4. Current official Huawei Ascend documentation and official CANN source repositories.

Prefer primary sources. When searching online, restrict technical conclusions to official Huawei Ascend documentation or official CANN repositories and provide direct links.

## Local Search

1. Determine likely roots from the workspace, `ASCEND_HOME_PATH`, build configuration, and user-provided paths.
2. Search filenames and symbols with `rg` or `rg --files`; do not depend on a single hard-coded directory.
3. For an API name, enumerate all same-name and suffixed variants before selecting a document.
4. Compare signatures, parameter units, supported types, restrictions, examples, and version markers.
5. Search examples and implementations for the exact overload, not only the base API name.

Read `references/local-search-layout.md` for common locations and query patterns when the repository layout is unfamiliar.

## Version Matching

- Record the installed or requested CANN version and target SoC before making compatibility claims.
- Prefer documentation shipped with the selected installation over a newer unrelated checkout.
- If only a newer or older source is available, label the mismatch and identify what must be verified on the target.
- Treat filename suffixes as opaque variant identifiers. Infer semantics from content, not the suffix number.

## Online Fallback

Use online search only when local sources are absent, incomplete, or mismatched. Search for the API plus the CANN version, SoC family, and relevant parameter or error. Open the source page and verify it actually contains the claimed signature or restriction.

## Output

Provide the exact source path or official URL, the version/SoC context, the relevant signature or restriction in concise form, and any mismatch with the user's environment. If no authoritative match is found, say what was searched and keep the conclusion provisional.
