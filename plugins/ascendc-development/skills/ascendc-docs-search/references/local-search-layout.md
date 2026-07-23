# Local Ascend C Search Layouts

Use these as candidate locations, then verify them against the actual repository and CANN version.

## Discover Roots

```bash
printf '%s\n' "${ASCEND_HOME_PATH:-}"
rg --files -g 'version.info' -g 'version.cfg' -g 'version.cmake' .
find "${ASCEND_HOME_PATH:-/nonexistent}" -maxdepth 3 \
  \( -name version.info -o -name version.cfg \) -print 2>/dev/null
```

Common source-tree candidates include:

- `asc-devkit/docs/`
- `asc-devkit/examples/`
- `asc-devkit/impl/`
- CANN headers under the selected toolkit's `include/` and compiler directories
- operator-specific source and tests in the current repository

Do not assume these directories exist or belong to the selected installation.

## Find an API and Its Variants

```bash
rg --files <root> | rg '(^|/)(APIName)(-[0-9]+)?\.(md|h|hpp)$'
rg -n --glob '*.{md,h,hpp,cpp,asc}' '\bAPIName\b' <root>
```

For every candidate, compare:

- namespace and full function signature
- template parameters and overloads
- parameter units and legal ranges
- supported data types and SoCs
- alignment, stride, repeat, and temporary-buffer restrictions
- examples that call the same overload

## Match the Version

Inspect the version metadata shipped with the selected toolkit or source checkout. Do not infer compatibility from a directory named `latest`, and do not mix a source-tree version with an unrelated runtime installation without labeling the mismatch.

## Search Online

From the skill directory, query and fetch official Huawei documentation with:

```bash
python3 scripts/search_ascend_docs.py 'APIName' --fetch --max-results 5
python3 scripts/search_ascend_docs.py 'APIName' --fetch --version 8.3.RC1
```

Check `document.keyword_found` and the extracted excerpts before citing a result. Use `--full-content` only when the excerpts do not contain enough context. If the endpoint is unavailable, search the official site for the API name, target CANN version, SoC family, and one distinctive parameter or error.
