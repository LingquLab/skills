# Risk-Driven Testing

## Skill Under Test

- `superpowers-neo-testing-strategy`

## Request A: Alternative Validation

Fix a device-only timing problem that can be reproduced on specialized hardware but not in the local unit-test environment. A focused code change and hardware log demonstrate the failure boundary.

## Expected Behavior A

- Select validation based on regression risk and available evidence.
- Recommend a regression test if the existing framework can represent the behavior reliably.
- Otherwise use the strongest practical combination of reproduction, logs, compile checks, integration checks, or documented manual validation.
- Explain why an automated regression test is absent and state residual risk.
- Allow exploration or implementation before the final test strategy when necessary.

## Failure Signals A

- Requiring deletion of implementation because no failing test came first.
- Claiming full validation from a compile check alone.
- Treating unavailable hardware as permission to provide no evidence.

## Request B: TDD Is Useful

Add a deterministic parser rule with a clear public input/output contract and an existing fast unit-test suite. The new behavior has several boundary cases and a high regression risk.

## Expected Behavior B

- Recommend test-first development because the behavior is clear, cheap to test, and regression-sensitive.
- Use focused examples that express the desired contract rather than implementation details.
- Verify the test can detect the missing behavior when practical, then implement and broaden validation according to blast radius.

## Failure Signals B

- Rejecting TDD merely because Neo does not mandate it.
- Adding only tests that mirror internal implementation.
- Treating one focused test as proof of unrelated system behavior.

## Request C: Practical Bug Regression

Fix a stable input-validation bug that is reproducible in the current unit-test framework with no external dependencies.

## Expected Behavior C

- Add a regression test covering the reported behavior.
- Confirm the test meaningfully represents the original failure without recreating implementation just to enforce ordering.
- Report the regression check and any broader relevant checks before completion.

## Failure Signals C

- Substituting manual validation when inexpensive durable automation is available.
- Omitting the reported failure boundary from the test.
