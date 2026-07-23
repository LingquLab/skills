# Systematic Debugging

## Skill Under Test

- `superpowers-neo-systematic-debugging`

## Request

A previously passing integration test now times out after several dependency and configuration changes. One attempted timeout increase did not help.

## Expected Behavior

- Establish the symptom and inspect logs, boundaries, environment, and relevant recent changes.
- Form a falsifiable hypothesis and run the smallest discriminating check.
- Revisit the hypothesis after the failed workaround instead of adding another guess.
- Scale the investigation to the uncertainty without performing a ceremonial fixed sequence.

## Failure Signals

- Suggesting multiple speculative fixes before collecting evidence.
- Increasing the timeout again without explaining the cause.
- Continuing to stack changes after a hypothesis fails.
