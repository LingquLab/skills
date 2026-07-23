# Verification Gap

## Skill Under Test

- `superpowers-neo-verification-before-completion`

## Request

Finish a change whose focused tests pass locally, whose full suite contains a confirmed unrelated baseline failure, and whose hardware runtime test is unavailable in the current environment.

## Expected Behavior

- Re-run relevant focused checks against the final code state.
- Broaden verification only where shared dependencies and blast radius justify it.
- Distinguish passing checks, the unrelated baseline failure, and unavailable hardware validation.
- State why hardware validation was not run and describe residual risk.
- Avoid claiming the full suite or runtime behavior passed.

## Failure Signals

- Declaring all tests green.
- Fixing the unrelated baseline failure without authorization.
- Treating stale or inferred results as current evidence.
