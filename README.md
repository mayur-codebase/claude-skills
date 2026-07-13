# claude-skills

A collection of reusable [Claude Code](https://claude.com/claude-code) skills, packaged as installable plugins.

## Skills

### `/ctx` — portable project context

Prime any Claude Code session with what a project looks like: layout, data model, what's real vs mock, gotchas, and current work. Context files are stored in `~/.claude/context/<repo>/<area>.md` on your machine — never inside the repo, never committed.

| Command | What it does |
|---|---|
| `/ctx` or `/ctx <area>` | Load the saved context (auto-builds it if missing) and get a compact briefing |
| `/ctx build [area]` | Explore the project from scratch and (re)write the context file |
| `/ctx save [area]` | Fold what the current session learned back into the file |
| `/ctx list` | Show all saved contexts with their verified dates |

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
