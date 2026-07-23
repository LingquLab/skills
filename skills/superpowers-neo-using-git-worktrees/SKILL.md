---
name: superpowers-neo-using-git-worktrees
description: Use when a user requests isolation, parallel writes may conflict, the current Git workspace is unsafe, or staged, unstaged, or untracked files may belong to another task
---

# Using Git Worktrees

## Overview

Default to the current workspace. Add isolation only when it solves a concrete conflict or protects work that already exists.

## Evaluate the Workspace

1. Read repository guidance and any approved spec or plan requirements.
2. Inspect staged, unstaged, and untracked files with `git status --short --branch`, and inspect existing worktrees with `git worktree list`.
3. Determine whether those files overlap the planned work or may belong to another task.
4. If ownership is uncertain, explain the conflict and ask whether to create a worktree. Do not mutate existing changes to make room.

If the user declines isolation and the scopes are disjoint, continue carefully in the current workspace.

If isolation was not already requested by the user or approved in the plan, explain the concrete conflict and get the user's direction before creating a worktree.

## Choose the Execution Shape

| Situation | Choice |
|---|---|
| Small, coupled, or shared-file work | Current workspace, main agent |
| Independent tasks that still share files or state | Current workspace, serialized work |
| Read-only tasks or writes with clearly disjoint ownership | Parallel agents may share the workspace |
| Conflicting parallel writes, unsafe workspace, explicit isolation, or plan requirement | Separate worktree |

Same-workspace parallel writers must have explicit, disjoint file ownership. Serialize changes to shared files, generated artifacts, repository state, or ordered dependencies.

## Preserve Existing Work

Never automatically stash, move, commit, clean, overwrite, or discard existing changes. Do not assume an untracked file is disposable or that a staged change belongs to the current task.

Creating a worktree grants no extra delivery authority. In a shared workspace, delegated agents may edit and verify but must not commit, push, or open a pull request. In an isolated worktree, a local integration commit is allowed only when the user explicitly authorizes that commit, including by explicitly approving a named plan step. A generated plan alone is not authorization. Pushes and pull requests always require separate user authorization.

After setup, verify the original workspace is unchanged and the selected workspace is on the intended branch and path.
