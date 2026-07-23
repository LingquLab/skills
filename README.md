# Superpowers Neo

Superpowers Neo is a pragmatic, modular software-development workflow for coding agents. It keeps explicit design, plan execution, debugging, review, verification, and Git delivery practices while scaling ceremony to the ambiguity and risk of the task.

Neo has no global entry skill. Each skill is independently discoverable and loads only when its own trigger matches.

## Skills

| Skill | Use when |
|---|---|
| `superpowers-neo-brainstorming` | A change is complex, ambiguous, cross-component, or architecture-sensitive |
| `superpowers-neo-writing-plans` | Approved work needs a multi-step or subagent-ready implementation plan |
| `superpowers-neo-using-git-worktrees` | Workspace isolation may be needed for dirty or parallel work |
| `superpowers-neo-executing-plans` | An in-scope plan is ready for main-agent and scoped-subagent execution |
| `superpowers-neo-testing-strategy` | A change needs validation proportional to its risk |
| `superpowers-neo-systematic-debugging` | A bug or unexpected failure needs evidence-based diagnosis |
| `superpowers-neo-requesting-code-review` | A substantial or risky change benefits from independent review |
| `superpowers-neo-receiving-code-review` | Review feedback needs technical evaluation |
| `superpowers-neo-verification-before-completion` | Work is about to be described as complete, fixed, or passing |
| `superpowers-neo-finishing-a-development-branch` | Completed Git work needs an authorized delivery decision |

## What Changes from Superpowers

- No `using-superpowers` startup or umbrella skill.
- Brainstorming and persistent plans trigger only when complexity justifies them.
- Worktrees and subagents are selected by isolation and coordination value.
- Testing is risk-driven; test-first development is useful but not universal.
- Independent review is selected by risk rather than required after every task.
- Git commit, push, PR, merge, history rewrite, and cleanup remain separate authorization boundaries.
- Skill-authoring methodology is not part of the shipped series.

See the [approved design](docs/specs/2026-07-22-superpowers-neo-design.md) for the complete behavior contract.

## Validate

The validator uses Ruby's standard YAML library and needs no Python packages:

```bash
ruby scripts/validate-skills.rb
bash -n scripts/install.sh
```

The Ruby validator checks the ten skill packages and the structure of all nine behavior scenario definitions. Behavioral validation itself is a fresh-agent evaluation: give a new agent only the relevant `SKILL.md` files and the request section from one file in `tests/scenarios/`, then compare the response with its expected behaviors and failure signals. Do not include the expected result in the agent prompt.

## Install

Preview installation first:

```bash
scripts/install.sh --dry-run
```

Install to `${CODEX_HOME:-$HOME/.codex}/skills`:

```bash
scripts/install.sh
```

Use `--target PATH` to install elsewhere. The installer copies exactly the ten Neo skill directories, refuses to overwrite existing targets, and never disables or removes the original Superpowers plugin.

For an update, validate the new checkout, review the differences against the installed Neo directories, remove or archive the old Neo directories deliberately, and run the installer again. Refusing in-place overwrite prevents a partial update from mixing versions.

## Cutover

Neo and the original plugin may coexist during validation. Remove `superpowers@openai-api-curated` only after Neo has been reviewed in real tasks and the user explicitly authorizes cutover. Installing Neo does not imply permission to remove the original plugin.

## Attribution

Superpowers Neo is an independent adaptation inspired by [Superpowers](https://github.com/obra/superpowers) by Jesse Vincent. Superpowers is available under the MIT License. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the upstream notice. This project is not affiliated with or endorsed by the upstream project.

## License

Superpowers Neo is licensed under the [MIT License](LICENSE).
