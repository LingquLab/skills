---
name: superpowers-neo-validation-strategy
description: Use when deciding what tests or other evidence a code, configuration, or documentation change needs, especially for bug fixes, risky behavior, unavailable hardware, or costly automation.
---

# Neo Validation Strategy

## Principle

Choose validation by failure risk, affected boundaries, and available environments. Test order is a tool, not a quality gate; completion still requires credible evidence that the intended behavior works and important regressions were not introduced.

## Choose the Approach

1. Define the behavior being changed, likely failure modes, impact, and regression surface.
2. Prefer TDD (test-first development) when behavior is clear, regression risk is high, or a stable bug reproduction can demonstrate the failure before the fix.
3. Explore or implement first when uncertainty, prototyping, legacy structure, or setup cost makes that more effective. Add useful tests during or after implementation. Never discard valid implementation solely because tests were not written first.
4. Select evidence proportional to risk:
   - Narrow, low-risk changes may need focused tests, a parser or linter, compile checks, or direct inspection.
   - Behavioral logic usually merits targeted unit or component tests.
   - Cross-component changes merit integration or end-to-end checks at the affected boundaries.
   - High-impact changes merit broader regression coverage and realistic failure-path checks.

## Bug Fixes

When the cause is uncertain, use `superpowers-neo-systematic-debugging` first.

Add a practical regression test when the symptom is stable and the existing framework can express it without disproportionate setup. Make the test cover the reported failure, not incidental implementation details. When practical, confirm it detects the uncorrected behavior using a safe reproduction or prior revision; do not recreate the implementation merely to satisfy test ordering.

If automation depends on unavailable hardware, external services, timing, credentials, or excessive setup, use the strongest feasible alternative: a minimal reproduction, captured logs, compile or static checks, a focused integration check, or documented manual validation.

## Completion Evidence

Record:

- the checks run and their results;
- the behavior and boundaries they establish;
- why an automated regression test was omitted, when applicable;
- any untested boundary and its residual risk.

An explanation for missing automation is not itself validation. Pair it with concrete alternative evidence, and never claim more coverage than the evidence supports.
