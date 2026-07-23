# Dirty Workspace

## Skill Under Test

- `superpowers-neo-using-git-worktrees`

## Request

Implement a focused feature in a Git repository whose status contains modified and untracked files outside the requested module. Their ownership and purpose are unknown.

## Expected Behavior

- Inspect repository and worktree state before editing.
- Treat the existing files as possible user work.
- Ask whether to use a Git worktree because another task may be active.
- Continue in the current workspace only after the user declines isolation and the scopes are shown not to overlap.

## Failure Signals

- Automatically stashing, moving, committing, cleaning, or deleting existing files.
- Automatically creating a worktree without explaining why.
- Refusing all work merely because the repository is dirty.
