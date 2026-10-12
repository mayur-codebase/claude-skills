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

Stop hunting through Google Docs and Drive folders. Point the skill at one or several git repos you own (each with its own layout, rules and push policy; every code project is mapped to one of them) and it keeps your project docs there — one repo for many projects (a folder each) or for a single project (organized by document type: requirements, architecture, meetings, contracts, …): it learns the repo's structure, files each new doc under the right project folder (creating or reshaping folders when a project needs it), keeps the README indexes current, and commits. Run `init` once to link the repo (it checks write access), tick which harness rules apply from a built-in checklist (content safety, NDA/confidentiality, code policy, structure, format, workflow), add any custom rules, and choose when to push. Settings live in `~/.claude/codebase-docs/config.json` on your machine — never in the repo.

| Command | What it does |
|---|---|
| `/codebase-docs init` | Link a docs repo (run again to add more), verify write access, learn its structure, record its rules and push policy |
| `/codebase-docs repos` | List your configured docs repos and which code projects use each |
| `/codebase-docs bootstrap [project]` | One-time: draft a project's initial docs from its code, after you approve the plan |
| `/codebase-docs add --from <file\|link> [--keep-original]` | Import an existing Word/PDF/HTML/Excel/PowerPoint file or Claude artifact as a Markdown doc; optionally keep the original as an attachment |
| `/codebase-docs add [what]` | Write or file a doc into the right project folder, update indexes, commit, push per policy |
| `/codebase-docs find <query>` | Search the docs repo and report matches |
| `/codebase-docs sync` / `push` | Pull with rebase / push pending commits (never force) |
| `/codebase-docs status` / `config` | Show repo state / view and edit settings |

Existing documents come in as Markdown by default (`add --from`). Keeping originals (PDF, Word, Excel, PowerPoint, HTML, Claude artifacts) is an opt-in `allow-attachments` rule: files live in `<project>/attachments/`, each linked from a Markdown page, size-capped (10 MB by default), and the checker scans their text for secrets, internal addresses and client names.

The repo is docs-only by design: with the strict `no-source-code` rule, code files are blocked and only short labeled sample snippets are allowed inside Markdown. A bundled script (`scripts/precommit.py`, needs `python3`) runs before every commit and push: it blocks code files, oversized or copied code blocks, secrets, internal IPs/hosts, confidential client names and multi-line commit messages, and lists the rules it can't check for Claude to verify.

Doc trigger is `suggest` (default: Claude offers to document milestones, you say yes), `manual` (only when you ask), or `auto` (writes at milestones itself); change it any time by saying so.

Push policy is `ask` (confirm each time, default), `auto` (push right after each write), or `manual` (commit locally, push on request).

### Getting started with `/codebase-docs`

1. **Install** it (any method below; the quick install gets all skills) and start a new Claude Code session.
2. **Run `/codebase-docs init`** (once per docs repo; run it again to link more). It asks for your docs repo URL (you need write access) and where to clone it (default `~/Projects/codebase-docs`). Then pick the harness rules that apply from the checklist (content safety, NDA/confidentiality, code policy, structure, format, workflow), add any custom rules, and choose the doc trigger and push policy.
3. **Optional: `/codebase-docs bootstrap`** from inside a project to draft its first docs from the code. It shows the plan and waits for your approval before writing.
4. **Work normally.** In `suggest` mode Claude offers to document milestones (a finished feature, a decision, a root-caused bug); say yes and it files the doc in the right project folder. Or run `/codebase-docs add <what>` any time.
5. **Find and sync:** `/codebase-docs find <query>` searches the docs; `/codebase-docs sync` pulls, and `/codebase-docs push` pushes pending commits.

The docs clone lives outside your projects, so you can run this from any project's session. Change any setting later with `/codebase-docs config`, or just say it ("switch to auto", "stop suggesting").

## Install

### Quick install (one command)

Works for every Claude Code environment (terminal, desktop, IDE):

```sh
curl -fsSL https://raw.githubusercontent.com/mayur-codebase/claude-skills/main/install.sh | sh
```

To install only specific skills, pass their names (`ctx`, `meeting-notes`, `codebase-docs`):

```sh
curl -fsSL https://raw.githubusercontent.com/mayur-codebase/claude-skills/main/install.sh | sh -s -- codebase-docs
```

With no names, installs all skills in this repo to `~/.claude/skills/` — available in your next session, in every project. Re-run it any time to update.

### Other install options

Pick whichever matches how you run Claude Code:

### Terminal (CLI)

From any shell (no interactive session needed):

```sh
claude plugin marketplace add mayur-codebase/claude-skills
claude plugin install ctx@claude-skills --scope user
claude plugin install meeting-notes@claude-skills --scope user
claude plugin install codebase-docs@claude-skills --scope user
```

Or inside an interactive `claude` session:

```
/plugin marketplace add mayur-codebase/claude-skills
/plugin install ctx@claude-skills
/plugin install meeting-notes@claude-skills
/plugin install codebase-docs@claude-skills
```

> `/plugin` slash commands only exist in the terminal app — the desktop app, web, and IDE extensions use the options below instead.

### Desktop app

Click the **+** button next to the prompt box → **Plugins**, add the marketplace `mayur-codebase/claude-skills`, then install the plugins you want (**ctx**, **meeting-notes**, **codebase-docs**).

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
    { "name": "ctx", "marketplace": "claude-skills", "scope": "user" },
    { "name": "meeting-notes", "marketplace": "claude-skills", "scope": "user" },
    { "name": "codebase-docs", "marketplace": "claude-skills", "scope": "user" }
  ]
}
```

### Manual copy (simplest, no plugin system)

Copy a skill file to your personal skills directory (replace `ctx` with `meeting-notes` or `codebase-docs` for the others):

```sh
mkdir -p ~/.claude/skills/ctx
curl -o ~/.claude/skills/ctx/SKILL.md \
  https://raw.githubusercontent.com/mayur-codebase/claude-skills/main/plugins/ctx/skills/ctx/SKILL.md
```

`codebase-docs` also needs its checker script, so copy that folder's `scripts/` too:

```sh
mkdir -p ~/.claude/skills/codebase-docs/scripts
B=https://raw.githubusercontent.com/mayur-codebase/claude-skills/main/plugins/codebase-docs/skills/codebase-docs
curl -o ~/.claude/skills/codebase-docs/SKILL.md $B/SKILL.md
curl -o ~/.claude/skills/codebase-docs/scripts/precommit.py $B/scripts/precommit.py
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
