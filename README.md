# claude-skills

A collection of reusable [Claude Code](https://claude.com/claude-code) skills, packaged as installable plugins.

## Skills

### `/ctx` — portable context for any folder

Prime any Claude Code session with what a project or folder contains: layout, stack, data model, what's real vs mock, gotchas, and current work. Works with code in any language, monorepos, infra, data/ML, docs sites — and plain file directories, where it builds an organized inventory instead. Context files are stored in `~/.claude/context/<repo>/<area>.md` on your machine — never inside the repo, never committed, and never containing secret values.

| Command | What it does |
|---|---|
| `/ctx` or `/ctx <area\|path>` | Load the saved context (auto-builds it if missing) and get a compact briefing |
| `/ctx build [target …]` | Explore from scratch and (re)write the context file — targets can be names or paths |
| `/ctx save [area]` | Fold what the current session learned back into the file |
| `/ctx show [area]` | Print the raw context file |
| `/ctx rm <area>` | Delete a context (asks first) |
| `/ctx list` | Show all saved contexts with their verified dates |
| `/ctx help` | Show the command table |

## Install

### As a plugin (recommended)

In Claude Code:

```
/plugin marketplace add <your-github-username>/claude-skills
/plugin install ctx@claude-skills
```

### Manual copy

Copy the skill file to your personal skills directory:

```sh
mkdir -p ~/.claude/skills/ctx
curl -o ~/.claude/skills/ctx/SKILL.md \
  https://raw.githubusercontent.com/<your-github-username>/claude-skills/main/plugins/ctx/skills/ctx/SKILL.md
```

It is picked up automatically in your next session.

## Repo layout

```
.claude-plugin/marketplace.json   # marketplace manifest (lists all plugins)
plugins/
  ctx/
    .claude-plugin/plugin.json    # plugin manifest
    skills/ctx/SKILL.md           # the skill itself
```

To add a new skill, create `plugins/<name>/` with the same shape and add an entry to `marketplace.json`.
