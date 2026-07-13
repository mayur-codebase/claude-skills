---
description: Load, build, and sync reusable project-context files stored in ~/.claude/context/. Use when the user types /ctx — "/ctx" or "/ctx <area>" loads (auto-builds if missing), "/ctx build [area]" re-explores from scratch, "/ctx save [area]" folds session learnings back in, "/ctx list" shows all saved contexts.
argument-hint: "[area] | build [area] | save [area] | list"
---

# ctx — portable project context

One command to prime any session with what a project looks like: layout, data model, what's real vs mock, gotchas, current work. Works in any repo or folder; context files live outside the repo and are never committed.

## Storage

```
~/.claude/context/<repo-slug>/<area>.md
```

- `<repo-slug>` = `basename $(git rev-parse --show-toplevel 2>/dev/null || pwd)`
- `<area>` = lowercase kebab name. **Default area** (when omitted): the area already loaded this session → else the repo's only saved area if exactly one exists → else the repo slug itself (a whole-repo context).

## Commands

Parse `$ARGUMENTS`; anything not matching `build`, `save`, or `list` is an area name to load.

### `/ctx` or `/ctx <area>` — load (auto-build if missing)

1. Resolve the area (default rule above). Read its file.
   - **File exists:** spot-check 2–3 load-bearing claims cheaply (ls a dir, grep a symbol). Reply with a compact briefing: one-paragraph overview, what's live vs in-progress, `Current state`, gotchas. Flag drift found by the spot-check and note the `verified:` date if old. Treat the file as working knowledge from here on.
   - **File missing:** say so in one line, then **build it** (below) — don't make the user re-type. If the area name doesn't obviously map to a path, ask which folder(s) it covers first.
   - If no area matches but the repo has saved areas, show them and ask.
2. Never dump the whole file at the user — brief them.

### `/ctx build [area]` — explore and (re)write

1. Scope = the area's matching top-level folder, or the whole repo for a repo-level area, or paths the user gave.
2. Explore thoroughly — prefer Explore agents for breadth (manifests, source layout, data model, API surface, auth, frontend state, infra, tests, dead code) plus recent git history and current branch state.
3. Write the file using the **Template**. 60–200 lines, dense, concrete file paths, facts over narration; mark mock/stub/dead code explicitly. Merge with any existing file — keep still-true facts.
4. Confirm with a short summary of what was captured.

### `/ctx save [area]` — sync the session back

Fold what this conversation learned into the file: new facts, corrected assumptions, decisions, in-flight work. While there, fix any claims the session showed to be stale. Update `verified:`. Report the delta in a few lines. (No full re-exploration — that's `build`.)

### `/ctx list` — what exists

Show `~/.claude/context/*/` as a small table: repo / area / `verified:` date / one-line overview (read only frontmatter + first lines). Note which repo matches the cwd.

## Template

Only three sections are required — **Overview**, **Current state**, and whatever the project actually has. Pick from these headings as they apply; invent others when the project calls for it:

```markdown
---
area: <area>
repo: <repo-slug>
scope: <paths covered>
verified: <YYYY-MM-DD>
---

# <Area> context

**Overview** — what this is, one short paragraph.

## Layout & packages      <!-- one-liners: name, role, stack; mark dead/legacy -->
## Data model             <!-- entities/tables/schemas, key patterns, where defined -->
## API & clients          <!-- surface, generated clients, where validation lives -->
## Frontend               <!-- framework, routing, state; real vs mock features -->
## Auth & access control  <!-- authn + authz, where enforced -->
## Infra & deploy         <!-- IaC, environments/accounts, deploy path -->
## Conventions & gotchas  <!-- build/regen recipes, footguns — the "bit me" list -->

## Current state (<YYYY-MM-DD>)
<branch, in-flight work, agreed next steps.>
```

Every claim should be checkable: name files and symbols, not vibes.

## Notes

- Never write context files inside a repo; never commit them.
- Independent of any auto-memory directory — don't move content between the two unless asked.
- If the cwd's slug has no contexts but another slug clearly matches (renamed checkout), say so and ask which to use.
