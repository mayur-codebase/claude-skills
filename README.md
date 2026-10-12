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

### `/meeting-notes` — durable memory for client meetings

Persistent, queryable memory for client meeting notes — built for the project discovery phase, where feature asks, decisions, and open questions accumulate across many calls and must be answerable later with exact sources. Paste raw notes and the skill normalizes them into a standard format (feature asks, decisions, open questions, action items, raw notes preserved verbatim), assigns stable IDs (`FA-n`, `D-n`, `Q-n`), and tracks how requirements evolve — superseded decisions are linked, never overwritten. Notes are stored in `~/.claude/meeting-notes/<project>/` on your machine — never inside the repo, never committed.

| Command | What it does |
|---|---|
| `/meeting-notes save [project]` | Paste raw notes; normalizes and files them, updates the index and trackers |
| `/meeting-notes ask <question>` | Answer from stored notes with exact citations (meeting date + item ID) |
| `/meeting-notes history [topic]` | Timeline of meetings, or trace one topic's evolution across calls |
| `/meeting-notes open [project]` | List unresolved questions and action items, oldest first |
| `/meeting-notes list` | Show all projects with saved notes |

### `/codebase-docs` — one git repo for all project documentation

Stop hunting through Google Docs and Drive folders. Point the skill at a git repo you own and it keeps every project's docs there: it learns the repo's structure, files each new doc under the right project folder (creating or reshaping folders when a project needs it), keeps the README indexes current, and commits. Run `init` once to link the repo (it checks write access), tick which harness rules apply from a built-in checklist (content safety, NDA/confidentiality, code policy, structure, format, workflow), add any custom rules, and choose when to push. Settings live in `~/.claude/codebase-docs/config.json` on your machine — never in the repo.

| Command | What it does |
|---|---|
| `/codebase-docs init` | Link the docs repo, verify write access, learn its structure, record rules and push policy |
| `/codebase-docs bootstrap [project]` | One-time: draft a project's initial docs from its code, after you approve the plan |
| `/codebase-docs add [what]` | Write or file a doc into the right project folder, update indexes, commit, push per policy |
| `/codebase-docs find <query>` | Search the docs repo and report matches |
| `/codebase-docs sync` / `push` | Pull with rebase / push pending commits (never force) |
| `/codebase-docs status` / `config` | Show repo state / view and edit settings |

The repo is docs-only by design: with the strict `no-source-code` rule, code files are blocked before every commit and only short labeled sample snippets are allowed inside Markdown. Every commit and push is also scanned for secrets and NDA/client-confidential content.

Doc trigger is `suggest` (default: Claude offers to document milestones, you say yes), `manual` (only when you ask), or `auto` (writes at milestones itself); change it any time by saying so.

Push policy is `ask` (confirm each time, default), `auto` (push right after each write), or `manual` (commit locally, push on request).

## Install

### Quick install (one command)

Works for every Claude Code environment (terminal, desktop, IDE):

```sh
curl -fsSL https://raw.githubusercontent.com/mayur-codebase/claude-skills/main/install.sh | sh
```

Installs all skills in this repo to `~/.claude/skills/` — available in your next session, in every project. Re-run it any time to update.

### Other install options

Pick whichever matches how you run Claude Code:

### Terminal (CLI)

From any shell (no interactive session needed):

```sh
claude plugin marketplace add mayur-codebase/claude-skills
claude plugin install ctx@claude-skills --scope user
```

Or inside an interactive `claude` session:

```
/plugin marketplace add mayur-codebase/claude-skills
/plugin install ctx@claude-skills
```

> `/plugin` slash commands only exist in the terminal app — the desktop app, web, and IDE extensions use the options below instead.

### Desktop app

Click the **+** button next to the prompt box → **Plugins**, add the marketplace `mayur-codebase/claude-skills`, then install **ctx**.

### settings.json (works everywhere, no UI)

Add to `~/.claude/settings.json` (personal) or a repo's `.claude/settings.json` (whole team — plugins auto-install for collaborators on next session):

```json
{
  "extraKnownMarketplaces": {
    "claude-skills": {
      "source": {
        "source": "github",
        "repo": "mayur-codebase/claude-skills"
      }
    }
  },
  "enabledPlugins": [
    {
      "name": "ctx",
      "marketplace": "claude-skills",
      "scope": "user"
    }
  ]
}
```

### Manual copy (simplest, no plugin system)

Copy the skill file to your personal skills directory:

```sh
mkdir -p ~/.claude/skills/ctx
curl -o ~/.claude/skills/ctx/SKILL.md \
  https://raw.githubusercontent.com/mayur-codebase/claude-skills/main/plugins/ctx/skills/ctx/SKILL.md
```

It is picked up automatically in your next session.

## Repo layout

```
.claude-plugin/marketplace.json   # marketplace manifest (lists all plugins)
plugins/
  ctx/
    .claude-plugin/plugin.json    # plugin manifest
    skills/ctx/SKILL.md           # the skill itself
  meeting-notes/
    .claude-plugin/plugin.json
    skills/meeting-notes/SKILL.md
  codebase-docs/
    .claude-plugin/plugin.json
    skills/codebase-docs/SKILL.md
```

To add a new skill, create `plugins/<name>/` with the same shape and add an entry to `marketplace.json`.
