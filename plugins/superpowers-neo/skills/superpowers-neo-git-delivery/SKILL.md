---
name: superpowers-neo-git-delivery
description: Use when feature or bug-fix work is complete in a Git repository, when the user requests Git delivery such as commit, push, pull request, merge, or cleanup, or when the user explicitly invokes this skill to authorize branch creation, scoped commit, normal push, and pull request creation for the current task
---

# Git Delivery

## Enter the Delivery Flow

Enter automatically after completed feature or bug-fix work in a Git repository, and when the user explicitly requests delivery. If the user opts out, stop after the result summary. If the task category is unclear, ask whether to enter delivery. For non-Git work, provide only a result summary.

Distinguish three authority sources:

- **Automatic entry:** Authorize a scoped commit after the required checks. Authorize a normal push only from an established, task-owned non-default branch. Do not infer branch-choice or pull-request authority.
- **Explicit named request:** When the user directly requests one or more Git actions, authorize exactly those named actions without a redundant confirmation. Treat this narrower request as overriding automatic delivery defaults for unnamed actions. Do not expand `push this branch`, for example, into commit or PR authority. Ordinary mechanics within the named action, such as setting upstream on its first normal push, are included.
- **Manual invocation:** When the user invokes this skill through `$superpowers-neo-git-delivery` syntax or an equivalent explicit skill attachment, treat that invocation as one bundled authorization to select or create and switch to a task branch, commit the exact task scope, push that branch normally, and create a pull request. Do not ask separately for those four actions. A mere automatic trigger, quoted skill name, or discussion of the skill is not manual invocation.

An explicit opt-out or narrower instruction overrides any authority source. Automatic entry and the manual-invocation bundle do not authorize merge, history rewrite, force push, hook bypass, cleanup, discarding changes, or bypassing repository protections. Those actions require their own specific request and documented safety checks.

## Prepare the Commit

1. Read repository guidance. Determine the current and default branches, existing development branches, recent branch and commit conventions, and any pull request template. Before creating a PR, look up any open PR whose head is the selected task branch.
2. Inspect `git status`, staged and unstaged diffs, untracked files, task ownership, generated artifacts, and possible secrets or sensitive content.
3. Prefer an appropriate existing task branch. Under manual invocation, create and switch to a new task branch without another prompt when no appropriate branch exists; follow user or repository conventions, otherwise use `codex/<topic>` with lowercase hyphenated words. Under an explicit named request, create or switch branches only when that action was requested. Under automatic entry, ask before creating or switching branches when on the default branch. Never carry unrelated commits or move, stash, or discard user changes to make a branch switch work; stop and ask if isolation cannot be achieved safely.
4. Define the exact commit scope: task-owned code, tests, and documentation, approved specs, and durable plans. Exclude unrelated changes, accidental generated files, and temporary plans. If task changes cannot be separated from user changes in a file, stop and ask.
5. Confirm relevant verification is fresh after the final edit. Fix failures caused by the task. If a check is unavailable or an unrelated failure remains, report the exact gap and residual risk before committing or pushing.
6. Determine and report the branch, file scope, commit message, verification evidence, and known risks. Under automatic entry or manual invocation, proceed with the scoped commit unless the user opted out. Under automatic entry on the default branch, first obtain the branch decision required above. Under an explicit named request, commit only when commit was named; otherwise leave staged, unstaged, and untracked changes intact while performing the requested actions. Under manual invocation, make the branch decision within the bundled authority and continue without redundant authorization prompts.
7. When a commit is authorized, stage exact task paths only, then inspect `git diff --cached` and status again for scope, generated files, and sensitive content. When commit is not authorized, do not alter the index. Do not bypass commit or push hooks with `--no-verify` by default. Fix task-caused hook failures. If an unrelated external hook remains unavailable, disclose the gap and require separate explicit user authorization before any bypass. Follow recent commit-message style, or use a concise imperative outcome when none exists. Add no generated authorship or unrelated metadata.

After the implementation commit succeeds, delete its uncommitted temporary plan and inspect the remaining workspace. Never stage that plan or delete it before a successful commit; retain it if the commit fails.

## Apply Delivery Authority

| Action | Automatic entry | Explicit named request | Manual invocation |
|---|---|---|---|
| Branch create/switch | Ask on the default branch or when branch ownership is unresolved. | Create or switch only when requested, using the named target or repository conventions. | Select an appropriate task branch or create and switch to one without another prompt. |
| Commit | Commit the exact completed task scope after checks. | Commit the exact requested scope after checks; infer no push or PR. | Commit the exact completed task scope after checks. |
| Push | Push only an established, task-owned non-default branch; otherwise ask. | Normally push the exact requested branch after verifying its identity and scope; infer no commit or PR. | Normally push only the selected task branch and set upstream on its first push. |
| Pull request | Require explicit instruction or approval of a named plan action. | Reuse an open PR for the exact head branch; otherwise create the requested PR after readiness checks. Infer no branch creation, commit, or merge. | Reuse an open PR for the selected head branch; otherwise create one after the task branch is pushed. |
| Merge | Require a separate explicit request after checking CI, review status, branch currency, and repository policy. | Perform the requested merge only after those checks. | Require a separate explicit merge request. |
| Local history rewrite | Require a separate explicit request after identifying affected commits and collaboration impact. | Rewrite only when the specific operation and affected commits were requested after impact disclosure. | Require the same separate explicit request. |
| `--force-with-lease` | Require separate explicit confirmation after explaining overwrite risk. | Use only when the request is separately risk-confirmed; never use bare `--force`. | Require the same separate confirmation. |
| Cleanup | Require an explicit request or approval of a named cleanup step covering the specific branch or worktree. | Clean up only the specifically requested, verified target. | Require a separate explicit cleanup request. |

Treat a branch as established and task-owned only after repository guidance, branch history, tracking state, and workspace scope show that it belongs to the current task. A non-default branch name alone is not enough. A new branch created specifically for the current task under manual invocation is task-owned once its base and workspace scope are verified.

Before creating a PR, query open PRs for the exact selected head branch. If one exists, reuse it: update its branch, description, or status only as the task requires, then report its URL. Do not attempt a duplicate PR. Otherwise follow the repository PR template. Without one, include the summary, actual verification, known risks, and relevant spec. Create a ready PR only when implementation and required verification are complete; use a draft when work is incomplete, blocked, or explicitly requested as draft. Manual invocation authorizes PR creation, not a false readiness claim. Never fabricate results or hide unverified scope.

Never force push automatically or use bare `--force`. Never bypass branch protections. A hook bypass requires its own explicit authorization after the cause, validation gap, and risk are explained; never bypass a task-caused failure instead of fixing it. A failed remote action does not authorize a force push, protection bypass, or another high-risk workaround.

Before cleanup, confirm the work is integrated, the worktree is clean, and the target is not the current working directory. Never discard uncommitted changes or perform destructive cleanup implicitly.
