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

Use online search only when local sources are absent, incomplete, or mismatched. Run the bundled script first; resolve its path relative to this `SKILL.md`, not the user's working directory:

```bash
python3 scripts/search_ascend_docs.py 'APIName' --fetch --max-results 5
```

The script queries Huawei's official Ascend documentation search endpoint, converts results to public documentation URLs, fetches matching pages, and returns structured JSON with keyword excerpts and matching code blocks. It has no third-party Python dependencies. Useful options include `--version 8.3.RC1`, `--lang en`, `--doc-type API`, and `--full-content` when the complete extracted page text is required.

Inspect more than the result title: confirm `document.keyword_found`, then read the returned excerpts or full content for the exact signature, restrictions, and version context. If the official endpoint is unavailable or returns no authoritative match, use an official-site web search as the final fallback. Restrict technical conclusions to Huawei Ascend documentation or official CANN repositories and provide direct links.

## Output

Provide the exact source path or official URL, the version/SoC context, the relevant signature or restriction in concise form, and any mismatch with the user's environment. State whether the bundled online search script found and fetched the page. If no authoritative match is found, say what was searched and keep the conclusion provisional.
