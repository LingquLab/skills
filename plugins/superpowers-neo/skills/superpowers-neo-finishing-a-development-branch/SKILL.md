---
name: superpowers-neo-finishing-a-development-branch
description: Use when feature or bug-fix work is complete in a Git repository, or when the user explicitly requests Git delivery such as a commit, push, pull request, merge, or cleanup
---

# Finishing a Development Branch

## Enter the Delivery Flow

Enter automatically after completed feature or bug-fix work in a Git repository, and when the user explicitly requests delivery. If the user opts out, stop after the result summary. If the task category is unclear, ask whether to enter delivery. For non-Git work, provide only a result summary.

Entering this flow authorizes no Git mutation. Commit, push, pull request, merge, force-with-lease, and cleanup are independent decisions; do not infer authorization for one from another.

## Prepare the Commit

1. Read repository guidance. Determine the current and default branches, existing development branches, recent branch and commit conventions, and any pull request template.
2. Inspect `git status`, staged and unstaged diffs, untracked files, task ownership, generated artifacts, and possible secrets or sensitive content.
3. If on the default branch, ask before either creating a feature branch or committing there. Prefer an appropriate existing development branch. For a new branch, follow user or repository conventions; only otherwise use `codex/<topic>` with lowercase hyphenated words.
4. Define the exact commit scope: task-owned code, tests, and documentation, approved specs, and durable plans. Exclude unrelated changes, accidental generated files, and temporary plans. If task changes cannot be separated from user changes in a file, stop and ask.
5. Confirm relevant verification is fresh after the final edit. If a check is unavailable or failing, report the exact gap and residual risk before asking whether to commit.
6. Present the proposed branch, file scope, commit message, verification evidence, and known risks. If the original request explicitly authorized a commit, continue after these checks; otherwise ask for commit confirmation.
7. Stage exact task paths only, then inspect `git diff --cached` and status again for scope, generated files, and sensitive content. Do not bypass commit or push hooks with `--no-verify` by default. Fix task-caused hook failures. If an unrelated external hook remains unavailable, disclose the gap and require separate explicit user authorization before any bypass. Follow recent commit-message style, or use a concise imperative outcome when none exists. Add no generated authorship or unrelated metadata.

After the implementation commit succeeds, delete its uncommitted temporary plan and inspect the remaining workspace. Never stage that plan or delete it before a successful commit; retain it if the commit fails.

## Authorize Each Next Action

| Action | Required boundary |
|---|---|
| Commit | Explicitly included in the original request or confirmed after the scope proposal. |
| Push | Explicitly requested, or explicitly user-approved as a named plan action. Push only the task branch and set upstream on its first push. |
| Pull request | Explicitly requested, or explicitly user-approved as a named plan action. Do not treat push authorization as PR authorization. |
| Merge | Explicit user request after checking CI, review status, branch currency, and repository merge policy. |
| `--force-with-lease` | Separate, explicit confirmation after explaining the concrete overwrite risk. |
| Cleanup | Explicit request, or explicit user approval of a named cleanup step in a plan covering the specific local branch, remote branch, or worktree. |

Follow the repository PR template. Without one, include the summary, actual verification, known risks, and relevant spec. Create a ready PR only when implementation and required verification are complete; use a draft when work is incomplete, blocked, or explicitly requested as draft. Never fabricate results or hide unverified scope.

Never force push automatically or use bare `--force`. Never bypass branch protections. A hook bypass requires its own explicit authorization after the cause, validation gap, and risk are explained; never bypass a task-caused failure instead of fixing it. A failed remote action does not authorize a force push, protection bypass, or another high-risk workaround.

Before cleanup, confirm the work is integrated, the worktree is clean, and the target is not the current working directory. Never discard uncommitted changes or perform destructive cleanup implicitly.
