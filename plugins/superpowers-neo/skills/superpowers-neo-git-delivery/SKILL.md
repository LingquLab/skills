---
name: superpowers-neo-git-delivery
description: Use after completing feature or bug-fix work in a Git repository; when the user requests a commit, push, pull request, merge, history rewrite, or cleanup; or when manually invoked to authorize current-task branch selection, a scoped commit when needed, normal push, and pull request creation
---

# Git Delivery

## Authority

Enter automatically after completed feature or bug-fix work in a Git repository and on explicit delivery requests. Ask when the task category is unclear. Respect any opt-out or narrower instruction; for non-Git work, provide only a result summary.

- **Automatic entry:** Commit task-owned uncommitted changes after checks. Push only an established, task-owned non-default branch. Do not infer branch-choice or PR authority.
- **Named request:** Perform exactly the requested Git actions without redundant confirmation. A first normal push includes setting upstream. Infer no unnamed action.
- **Manual invocation:** `$superpowers-neo-git-delivery` or an equivalent explicit attachment authorizes selecting or creating and switching to a task branch, a scoped commit when needed, normal push, and PR creation. A quoted name, discussion, or automatic trigger is not manual invocation.

Automatic entry and the manual bundle do not authorize merge, history rewrite, force push, hook bypass, cleanup, discarding changes, or bypassing repository protections. Apply the separate boundaries below even when a protected action is named.

## Deliver

1. Read repository guidance. Inspect the current and default branches, history and tracking, PR template, status, staged and unstaged diffs, untracked files, generated artifacts, and sensitive content.
2. Select the branch according to the authority source. Establish task ownership from repository guidance, history, tracking, and workspace scope, not the branch name alone. Under automatic entry, ask for a branch decision before creating, switching, or committing on the default branch; uncertain ownership of the current non-default branch limits automatic push, not the scoped commit. Under a named request, create or switch only when requested. Under manual invocation, prefer a suitable task branch or create and switch to one without another prompt, following repository conventions or otherwise using `codex/<topic>`; treat a new branch as task-owned after verifying its base and scope. Never move, stash, overwrite, or discard unrelated work to switch branches; stop and ask when safe isolation is impossible.
3. Define the exact task-owned scope. Include relevant code, tests, documentation, approved specs, and durable plans; exclude unrelated changes, accidental generated files, and temporary plans. Stop and ask when task and user changes in one file cannot be separated.
4. Verify the exact content being delivered after the final edit. Fix task-caused failures only when a commit is authorized; otherwise preserve the workspace and stop if the failure blocks the requested action. Report unavailable checks, unrelated failures, and residual risk; stop and ask when they block delivery.
5. When a commit is authorized and task-owned uncommitted changes exist, stage exact paths and recheck the cached diff, status, scope, generated files, and sensitive content before committing. When no commit is authorized or needed, do not alter the index or create an empty commit; continue only with authorized actions from the existing head. Follow repository commit style, add no generated authorship, and do not bypass hooks. After a successful implementation commit, delete only its uncommitted temporary plan; retain the plan if the commit fails.
6. Push only the selected branch. Automatic push requires an established, task-owned non-default branch. A named push applies to the exact requested branch after identity and scope checks. Manual invocation applies to the selected task branch. Set upstream on first push; stop if a force push would be required.
7. Before creating a PR, query open PRs for the exact head branch and reuse one when present. Automatic entry requires explicit PR authority; a named PR request authorizes only PR creation; manual invocation includes it. Follow the PR template and report actual verification, gaps, and risks. Readiness evidence must apply to the committed head, not uncommitted working-tree content; use clean-head or CI evidence, or stop and disclose the gap. Create a ready PR only when complete and verified, otherwise a draft.

## Protected Actions

- **Merge:** Require an explicit merge request, then check CI, review status, branch currency, and repository policy.
- **History rewrite:** Require the specific operation and affected commits after explaining collaboration impact.
- **Force push:** Require separate risk confirmation for `--force-with-lease`; never use bare `--force` or bypass protections.
- **Hook bypass:** Require separate authorization after explaining the cause, validation gap, and risk. Never bypass a task-caused failure.
- **Cleanup:** Require an explicit target. Confirm integration, a clean worktree, and that the target is not the current working directory. Never discard changes implicitly.

Never fabricate results or treat a failed remote action as permission for a riskier workaround.
