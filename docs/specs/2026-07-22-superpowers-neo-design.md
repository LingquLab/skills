# Superpowers Neo Skill Series Design

Date: 2026-07-22

Status: Approved design, pending written-spec review

## 1. Context

The existing Superpowers plugin provides a broad development methodology, but it also introduces a global entry skill and several absolute workflow requirements. Those requirements cause lightweight tasks to enter heavyweight design, TDD, worktree, subagent, review, and branch-finishing flows even when the task does not justify them.

Superpowers Neo will be a separate personal skill series. It keeps the useful planning, execution, quality, and delivery disciplines while making their triggers proportional to task complexity and risk.

## 2. Goals

- Provide independently triggered development workflow skills without a global entry skill.
- Preserve design planning for tasks with meaningful ambiguity or architectural impact.
- Preserve plan-driven execution and subagent collaboration without requiring a subagent for every task.
- Replace absolute TDD with risk-driven testing and evidence-based verification.
- Preserve disciplined Git delivery while requiring authorization for state-changing and remote actions.
- Keep each skill concise, independently understandable, and free from dependencies on the original Superpowers plugin.

## 3. Non-Goals

- Do not ship a `using-superpowers` or equivalent global entry skill.
- Do not ship a skill for creating, editing, or testing skills.
- Do not require test-first development for every implementation change.
- Do not require a design document, worktree, subagent, review, commit, push, or PR for every task.
- Do not modify the installed original Superpowers plugin in place.
- Do not embed repository-specific TileXR implementation guidance in the reusable skill series.

## 4. Shared Principles

1. User instructions and repository guidance have priority over Neo workflow defaults.
2. Workflow rigor scales with ambiguity, risk, blast radius, and collaboration needs.
3. Read-only investigation and diagnostics are allowed before an implementation decision.
4. Persistent implementation changes require the appropriate design approval when a design gate has triggered.
5. Claims of completion must be supported by current evidence.
6. Existing user changes are preserved. Neo must not stash, move, commit, overwrite, or discard them without authorization.
7. Git commits, pushes, PRs, merges, history rewrites, and cleanup are separate actions with separate authorization boundaries.
8. Skills cross-reference only other `superpowers-neo-*` skills, never the original `superpowers:*` names.

## 5. Skill Inventory

| Skill | Trigger | Primary responsibility |
|---|---|---|
| `superpowers-neo-brainstorming` | Complex, ambiguous, cross-component, or architecture-sensitive work | Clarify intent, compare real alternatives, produce an approved design |
| `superpowers-neo-writing-plans` | Multi-step, cross-module, risky, multi-session, or handoff-oriented work | Produce an executable, subagent-friendly implementation plan |
| `superpowers-neo-using-git-worktrees` | Explicit isolation request, parallel conflict, unsafe current workspace, or dirty workspace that may belong to other work | Decide whether and how to isolate work safely |
| `superpowers-neo-executing-plans` | An in-scope plan is ready for implementation | Execute continuously using the main agent and appropriately scoped subagents |
| `superpowers-neo-testing-strategy` | A feature, fix, refactor, or behavior change needs a validation strategy | Select tests and other evidence in proportion to risk |
| `superpowers-neo-systematic-debugging` | A bug, failure, or unexpected behavior needs diagnosis | Establish evidence and root cause before applying a fix |
| `superpowers-neo-requesting-code-review` | A change has enough risk or breadth to benefit from an independent review | Obtain focused, evidence-based review findings |
| `superpowers-neo-receiving-code-review` | Review feedback must be evaluated or implemented | Verify feedback technically before accepting, clarifying, or rejecting it |
| `superpowers-neo-verification-before-completion` | The agent is about to claim work is complete, fixed, or passing | Require current relevant evidence and disclose validation gaps |
| `superpowers-neo-finishing-a-development-branch` | Git-backed feature or fix work is complete, or the user requests Git delivery | Prepare and perform authorized commit, push, PR, merge, and cleanup actions |

There is no umbrella or startup skill. Discovery depends on each skill's own precise description and trigger conditions.

## 6. Workflow Composition

### 6.1 Clear, small change

1. Inspect the relevant repository guidance and code.
2. Implement directly without invoking brainstorming or a persistent plan.
3. Apply risk-driven testing.
4. Verify before claiming completion.
5. If this is feature or fix work in a Git repository, enter the delivery decision flow.

### 6.2 Complex feature

1. Use `superpowers-neo-brainstorming`.
2. Write and obtain approval for a spec when the design helps explain the overall system.
3. Use `superpowers-neo-writing-plans` when execution is multi-step, risky, cross-module, multi-session, or intended for handoff.
4. Evaluate the current workspace with `superpowers-neo-using-git-worktrees` when isolation may be useful.
5. Execute with `superpowers-neo-executing-plans`.
6. Apply testing, debugging, review, and final verification skills when their individual triggers match.
7. Enter the delivery flow for Git-backed feature work.

### 6.3 Bug fix

1. Use `superpowers-neo-systematic-debugging` when the root cause is not already established.
2. Select a suitable regression or alternative validation strategy with `superpowers-neo-testing-strategy`.
3. Implement the fix without an absolute test-first requirement.
4. Verify the result and disclose any untested boundary.
5. Enter the Git delivery flow when applicable.

## 7. Detailed Skill Behavior

### 7.1 `superpowers-neo-brainstorming`

Trigger only when the task is complex, has key ambiguity, spans components, or requires an architectural decision. Clear small edits, fixes, and configuration changes proceed directly.

When triggered:

- Permit read-only inspection and diagnostics.
- Do not modify project files until the user approves a concise design.
- Allow the user to explicitly waive the design gate.
- Ask only questions that materially affect the design.
- Ask dependent questions sequentially; independent questions may be grouped.
- Present multiple approaches only when real trade-offs exist. Otherwise present one recommendation with reasons.
- Write a persistent spec for complex designs that improve understanding of architecture, module relationships, interfaces, or long-term decisions.
- Require user approval of a complex-task spec before implementation.
- Prefer an existing repository documentation convention that is not tied to the original Superpowers product name. If the only convention is under `docs/superpowers/`, or no convention exists, use `docs/specs/YYYY-MM-DD-<topic>-design.md`.
- Write the spec into the repository without a separate spec-only commit. Include it in a later implementation commit.

### 7.2 `superpowers-neo-writing-plans`

Trigger only for cross-module, multi-step, high-risk, multi-session, or handoff-oriented execution.

A plan contains:

- Goal and scope.
- Relevant components or files.
- Ordered implementation work.
- Dependencies and key risks.
- Verification strategy.
- Tasks that can be assigned independently to a subagent.

Each subagent-ready task contains:

- The task objective and its role in the overall design.
- Required background and prerequisites.
- Modification scope and target files or modules.
- Constraints and explicit non-goals.
- Acceptance criteria and verification commands.
- Expected artifacts and downstream interfaces.

The plan must contain enough context that a subagent does not depend on the original conversation, but it must not duplicate unrelated repository material or lock in unnecessary implementation detail. Code blocks, line-by-line implementation instructions, zero-context assumptions, and per-step Git commits are not mandatory.

Plan storage rules:

- Follow an existing repository convention when it is compatible with Neo and is not tied to the original Superpowers product name.
- If the only convention is under `docs/superpowers/`, or no convention exists, use `docs/plans/YYYY-MM-DD-<topic>.md`.
- A durable plan with long-term handoff or maintenance value is committed with the implementation.
- A temporary plan is still written under `docs/plans/` for current agents and subagents, but it is not staged.
- After implementation has been completed and successfully committed, delete the uncommitted temporary plan.
- An implementation plan that remains within an approved spec or settled request does not require separate user approval.
- Request approval again if the plan expands scope, changes architecture, changes interfaces, changes acceptance criteria, or introduces major risk.
- A generated plan does not authorize Git mutation by itself. Push, PR, or cleanup steps count as authorized only when the user explicitly approves those named actions; commit, merge, history rewrite, and other protected actions retain their documented separate boundaries.

### 7.3 `superpowers-neo-using-git-worktrees`

Default to the current workspace. Do not create a worktree merely because feature development has started.

Create or propose a worktree when:

- The user requests isolation.
- Parallel work may conflict.
- The current workspace cannot safely host the planned change.
- The approved plan requires isolation.
- Uncommitted, staged, or untracked files may belong to another development task.

When the workspace is dirty, inspect the status and ask whether to use a worktree if the files may represent other work. Do not automatically stash, move, commit, clean, or discard existing changes. If the user declines a worktree and the scopes do not overlap, continue carefully in the current workspace.

### 7.4 `superpowers-neo-executing-plans`

Choose the execution mode based on task boundaries and coordination value:

- Use the main agent for small, tightly coupled, or shared-file work.
- Use a subagent for a bounded workstream where context isolation or specialization helps.
- Use parallel subagents only for read-only work or clearly disjoint write ownership.
- Serialize tasks that share files, generated artifacts, state, or ordering dependencies.
- Use separate worktrees when parallel write isolation is necessary.

Subagent dispatch rules:

- Provide the task goal, boundaries, dependencies, acceptance criteria, and authoritative file paths. Include the approved spec path when one exists; otherwise include the settled request as the scope authority.
- Instruct the subagent to read repository guidance and its plan task directly, plus the approved spec when one exists or the settled request when it does not.
- Do not copy the complete conversation or pre-bias the subagent with an expected conclusion.
- In a shared workspace, subagents modify and verify but do not commit, push, or open a PR.
- In an isolated worktree, a subagent may create a local integration commit only when the user explicitly authorizes that commit, including by explicitly approving a named plan step. A generated plan alone is not authorization.
- Subagents never push or create a PR without separate user authorization.
- Do not hard-code model names. Subagents inherit the current model and reasoning settings unless the user or a supported environment-specific policy says otherwise.

Execution behavior:

- After any required design or spec approval, or from a settled request that does not require a spec, execute continuously within the approved scope.
- Give concise progress updates without asking whether to continue after every task.
- Pause only for scope change, major risk, irreversible action, unsafe workspace conflict, genuine ambiguity, or a blocker that cannot be resolved safely.
- Treat the plan as a guide rather than an immutable script. Adjust files, ordering, and implementation details when the governing spec or settled request and its acceptance criteria remain unchanged.
- Pause when a core plan assumption is false or architecture, scope, interface, or acceptance criteria must change.

Every subagent reports:

- Completion status: complete, partial, needs clarification, or blocked.
- Modified files and artifacts.
- Key decisions.
- Verification commands and results.
- Remaining risks or unresolved work.

The main agent reviews the evidence and does not blindly retry an unchanged prompt. It may add context, narrow the task, take over directly, or reassign the work.

### 7.5 `superpowers-neo-testing-strategy`

Testing is risk-driven rather than universally test-first.

- Prefer TDD when behavior is clear, regression risk is high, or a bug can be reproduced reliably before the fix.
- Allow exploration or implementation before tests when that is the more effective path.
- Never require deletion of already written implementation solely because tests were not written first.
- Require validation evidence proportional to the change before completion.
- For a bug fix, add a regression test when reproduction is stable and the existing framework is suitable.
- When automation depends on unavailable hardware, external systems, timing, or disproportionate setup cost, use a minimal reproduction, logs, compile checks, integration checks, or documented manual validation.
- State why an automated regression test was not added and describe the residual risk.

### 7.6 `superpowers-neo-systematic-debugging`

Preserve the principle of evidence before fixes without forcing a fixed four-phase ceremony.

- Reproduce or otherwise establish the symptom.
- Inspect relevant logs, boundaries, recent changes, and environment state.
- Form a falsifiable root-cause hypothesis.
- Perform the smallest useful check to validate or reject it.
- Fix directly once evidence is sufficient.
- If a fix fails, revisit the hypothesis instead of stacking speculative changes.

The amount of investigation scales with the problem. An obvious, well-evidenced failure does not need artificial process expansion.

### 7.7 `superpowers-neo-requesting-code-review`

Use independent review based on risk rather than after every task.

Independent review is expected for broad, cross-module, public-interface, concurrent, security-sensitive, or data-consistency changes. Small and clear changes may use main-agent diff review plus testing.

A review subagent receives:

- The approved spec when one exists, otherwise the settled request or acceptance criteria.
- The relevant plan when one exists.
- The actual diff.
- Test and verification results.

It does not receive the implementer's desired conclusion. Findings are ordered by severity and include file locations, technical reasoning, and actionable consequences. A no-finding review still identifies test gaps and residual risk.

### 7.8 `superpowers-neo-receiving-code-review`

Evaluate feedback against code, the governing spec or settled request, relevant plan when one exists, and actual behavior.

- Implement and verify correct feedback.
- Clarify ambiguous feedback before acting.
- Reject technically incorrect or scope-expanding feedback with evidence.
- Avoid performative agreement and blind implementation.
- The main agent remains responsible for the final integration decision.

### 7.9 `superpowers-neo-verification-before-completion`

Before claiming work is complete, fixed, or passing:

- Run current verification relevant to the final state of the change.
- Start with focused tests and expand based on shared dependencies and blast radius.
- Re-run checks invalidated by later edits.
- Distinguish failures caused by the current change from pre-existing baseline failures.
- Fix current-change failures before completion.
- Record unrelated baseline failures without expanding scope unless the user requests it.
- If environment, hardware, permission, or external-system constraints prevent verification, state what was verified, what was not, why, and the residual risk.
- Never present inference as a confirmed passing result.

### 7.10 `superpowers-neo-finishing-a-development-branch`

Enter the delivery flow automatically when feature or bug-fix work completes in a Git repository. Do not enter when the user explicitly opts out. Ask when the task category is unclear. Non-Git work only receives a result summary.

#### Commit boundary

- Entering the flow does not itself authorize a commit.
- If the original request explicitly includes a commit, proceed after checks.
- Otherwise inspect status, diff, verification, and unrelated changes; present the intended commit scope and ask for confirmation.
- Stage only task code, tests, documentation, the approved spec, and durable plans.
- Exclude unrelated changes and temporary plans.
- If a file contains inseparable user changes, stop and ask.
- Follow the repository's recent commit-message style. If there is no convention, use a concise imperative message describing the outcome.
- Do not add generated authorship or unrelated metadata.
- After a successful implementation commit, delete the uncommitted temporary plan and inspect the remaining workspace state.

#### Branch boundary

- If the current branch is the default branch, ask before creating a feature branch or committing there.
- Use an existing development branch when appropriate.
- For a new branch, follow user and repository conventions first; otherwise use `codex/<topic>` with lowercase hyphenated words.

#### Pre-commit checks

- Confirm relevant verification is current after the final edit.
- Inspect the staged diff, file scope, accidental generated files, and sensitive information.
- If verification cannot be completed, disclose the gap and risk before asking whether to commit.
- Do not bypass commit or push hooks with `--no-verify` by default.

#### Push and PR boundary

- Push only the task branch and set upstream on first push.
- Never force push automatically.
- Allow only explicit, risk-confirmed `--force-with-lease`; never use bare `--force`.
- Push and PR creation require explicit user instruction or explicit user approval of those named actions in a plan. Merely generating an in-scope plan is not authorization.
- Follow the repository PR template.
- Without a template, include summary, verification, known risks, and the relevant spec.
- Create a ready PR when implementation and verification are complete.
- Create a draft PR when work is incomplete, blocked, or explicitly requested as draft.
- Never fabricate test results or hide unverified scope.

#### Merge and cleanup boundary

- Merge only on explicit user request.
- Check CI, review status, branch currency, and repository merge policy first.
- Do not bypass branch protections.
- Delete local branches, remote branches, or worktrees only when explicitly requested or explicitly user-approved as named cleanup steps in a plan.
- Before cleanup, confirm the work is integrated, the worktree is clean, and the target is not the current working directory.
- Never discard uncommitted changes as part of cleanup.
- A failed remote action must not trigger force push, protection bypass, or another high-risk workaround without authorization.

## 8. Artifact Lifecycle

| Artifact | Created when | User approval | Git behavior | Cleanup |
|---|---|---|---|---|
| Complex design spec | The design materially improves overall understanding | Required before implementation | Committed with implementation | Retained |
| Durable implementation plan | Cross-session or long-term handoff value exists | Only if it changes approved scope or architecture | Committed with implementation | Retained |
| Temporary implementation plan | Multi-step execution needs a working plan but no long-term value | Only if it changes approved scope or architecture | Never staged | Deleted after successful implementation commit |
| Review report | Independent review is risk-justified | Not separately required | Normally not persisted | Kept in task output unless repository policy requires otherwise |

## 9. Packaging and Discovery

- Ship ten flat personal skill directories using the exact names in the inventory.
- Each directory contains a concise `SKILL.md` and recommended `agents/openai.yaml` metadata.
- Add scripts or references only when they remove meaningful duplication or support deterministic behavior.
- Keep trigger descriptions precise and limited to when the skill should load.
- Do not add a global entry, umbrella router, startup hook, or skill-development module.
- Do not cross-reference the original Superpowers plugin.
- Default personal installation root is `${CODEX_HOME:-$HOME/.codex}/skills`; the user may select a version-controlled source directory before initialization.
- Validate Neo before removing the original plugin. Removing the existing plugin is a separate, explicitly authorized cutover action.

## 10. Acceptance Criteria

1. A clear small edit does not trigger brainstorming or a persistent plan.
2. A complex architectural task produces a repository spec and waits for user approval before implementation.
3. A multi-step task can produce subagent-ready tasks with sufficient authoritative context.
4. A dirty workspace that may represent other work causes a worktree question, not an automatic stash or cleanup.
5. Parallel agents never write overlapping shared state without isolation.
6. A change can be validly implemented without test-first ordering, while completion still requires proportionate evidence.
7. A bug fix adds a regression test when practical or documents a justified alternative and residual risk.
8. Review is required by risk, not by task count, and feedback is verified rather than blindly accepted.
9. Completion claims distinguish confirmed checks, unavailable checks, and unrelated baseline failures.
10. Feature or fix work in a Git repository enters a delivery decision flow but does not commit without authorization.
11. Push, PR, merge, force-with-lease, and cleanup remain separately authorized actions.
12. No Neo skill requires `using-superpowers`, `writing-skills`, or absolute TDD behavior.

## 11. Validation Strategy

Implementation validation will include:

- Structural validation of every skill directory and frontmatter.
- Trigger checks for clear small changes versus complex design work.
- Scenario checks for spec approval gates and plan re-approval boundaries.
- Dirty-workspace and default-branch delivery scenarios.
- Shared-workspace and isolated-worktree subagent scenarios.
- Risk-driven testing scenarios where TDD is useful and where it is intentionally not used.
- Bug-fix scenarios with both automated regression and justified alternative validation.
- Review scenarios with valid, ambiguous, incorrect, and scope-expanding feedback.
- Completion scenarios with passing tests, unavailable hardware, and unrelated baseline failures.
- Delivery scenarios covering commit confirmation, push, PR, merge, hooks, and cleanup boundaries.

The original Superpowers plugin remains installed during Neo development and validation. Cutover occurs only after the user reviews the implemented skills and explicitly authorizes removal of the original plugin.
