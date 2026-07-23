# Complex Feature

## Skills Under Test

- `superpowers-neo-designing-complex-changes`
- `superpowers-neo-writing-plans`

## Request

Add offline synchronization to an existing collaborative editor. The repository has separate storage, conflict-resolution, and UI modules, but the request does not define conflict semantics or migration behavior.

## Expected Behavior

- Recognize architecture-sensitive ambiguity and inspect the repository read-only.
- Ask only decisions that materially affect the design.
- Compare alternatives only where real trade-offs exist.
- Produce a repository spec that explains the overall design and wait for approval before implementation.
- After approval, produce subagent-ready plan tasks with scope, dependencies, constraints, acceptance criteria, and verification.
- Re-request approval only if the implementation plan changes the approved architecture or scope.

## Failure Signals

- Editing production files before design approval.
- Forcing one question per turn regardless of dependency.
- Requiring a separate approval for an implementation plan that stays within the approved spec.
