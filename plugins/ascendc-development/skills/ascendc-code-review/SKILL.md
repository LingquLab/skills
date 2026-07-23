---
name: ascendc-code-review
description: Review Ascend C Host, Tiling, Kernel, SIMT, build, and supporting Python changes for correctness, security, compatibility, and performance risks. Use for code snippets, local diffs, pull requests, operator implementations, or focused rule checks where findings must be evidence-based and tied to the actual call path and target CANN/SoC version.
---

# Ascend C Code Review

Prioritize defects that can change behavior, corrupt memory, break compatibility, or invalidate performance claims. Treat bundled rule documents as review aids; version-matched source, headers, tests, and official documentation take precedence.

## Establish Scope

1. Identify the code or diff, target SoC, CANN version, and requested review focus.
2. Inspect repository instructions and the surrounding call path before judging an isolated line.
3. Classify each changed area as Host/Tiling, Kernel, SIMT, build configuration, or supporting Python.
4. Select only the relevant references:
   - Host, Tiling, Kernel, and operator checks: `references/review-checklist.md`
   - SIMT API style migrations: `references/simt-review.md`
   - Build hardening: `references/build-hardening.md`

Do not require the user to restate code already available in the workspace or a rule already implied by the review request.

## Acquire a GitCode PR Diff

When the review target is a public `https://gitcode.com` pull request and its diff is not already available, resolve `<skill-dir>` as the directory containing this `SKILL.md` and run the bundled script. Start with the stat, then fetch the relevant diff:

```bash
python3 <skill-dir>/scripts/get_gitcode_pr_diff.py --repo https://gitcode.com/owner/repository --pr 123 --stat
python3 <skill-dir>/scripts/get_gitcode_pr_diff.py --repo https://gitcode.com/owner/repository --pr 123 --file-filter '**/*.asc'
```

The script writes to stdout by default; use `--output <path>` only when a file artifact is useful. It accepts only canonical GitCode HTTPS repository or matching pull-request URLs, runs Git noninteractively, and cleans its temporary bare repository. If the merge ref is unavailable, it stops instead of guessing a target branch; confirm the PR target and rerun with `--base <target-branch>`. A diff does not replace call-path context: inspect the available local checkout or request the missing source when definitions or guards outside the patch affect a finding.

## Review Method

1. Trace inputs, shapes, tiling values, offsets, buffer sizes, synchronization, and cleanup through the real call path.
2. For each suspected defect, construct the concrete failing condition and check whether another guard or invariant excludes it.
3. Verify Ascend C API semantics against the target version. Use `$ascendc-api-best-practices` for established patterns and `$ascendc-docs-search` for ambiguous overloads, SoC restrictions, or changed APIs.
4. Run the narrowest useful static check, compile, unit test, simulator check, or hardware test available. Keep unavailable evidence explicit.
5. Report only actionable findings. Do not manufacture a numeric confidence score by adding arbitrary evidence weights.

## Required Review Boundaries

- Separate Host/Tiling rules from Kernel rules; a rule for one side is not automatically valid for the other.
- Confirm arithmetic bounds with concrete ranges before reporting overflow or underflow.
- Confirm array and GM/UB accesses against both logical sizes and allocated/aligned sizes.
- Check resource and queue operations as pairs, including error exits.
- Treat precision and performance guidance as target-specific unless the official source establishes a general requirement.
- Do not require C-style SIMT APIs unless the target toolchain, headers, or project policy actually requires that migration.
- Keep compatibility findings tied to a public interface, serialized layout, kernel signature, or supported version contract.

## Output

Lead with findings ordered by severity. For each finding include a precise file and line, the triggering condition, user-visible or runtime impact, evidence, and the smallest credible fix. Then list open questions or validation gaps. If no findings remain after checking the call path, say so and state the residual test or hardware risk.

Do not create a separate report file unless the user requests an artifact.
