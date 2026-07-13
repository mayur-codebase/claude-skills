---
description: Load, build, and sync reusable context files for any project or folder — code in any language, monorepos, infra, data, docs, or plain file directories. Stored in ~/.claude/context/, never in the repo. Use when the user types /ctx — "/ctx" or "/ctx <area-or-path>" loads (auto-builds if missing), "/ctx build [target…]" re-explores, "/ctx save" folds session learnings back in, "/ctx list" shows everything, "/ctx show|rm <area>" prints or deletes one.
argument-hint: "[area|path] | build [area|path …] | save [area] | show [area] | rm <area> | list | help"
---

# ctx — portable context for any folder

One command to prime a session with what a project or folder contains: layout, stack, data model, what's real vs mock, gotchas, current work — or, for non-code folders, an organized inventory. Works anywhere; context files live outside the target and are never committed.

## Storage & naming

```
~/.claude/context/<slug>/<area>.md
```

- `<slug>` = `basename $(git rev-parse --show-toplevel 2>/dev/null || pwd)`. If the cwd is `$HOME` or `/`, don't guess — ask for an explicit target path and use that path's basename as the slug.
- `<area>` = a name the user gives, or derived from a path (its basename). Sanitize: lowercase, spaces/slashes/underscores → `-`, strip other punctuation. The full path always goes in the file's `scope:` frontmatter so the name never has to encode it.
- **Default area** (when omitted): the area already loaded this session → else the slug's only saved area → else the slug itself (whole-repo context).
- A target may be a bare name (`audravera`), a relative path (`src/api`), or an absolute path anywhere on disk (`~/Downloads/specs`). Paths win over name-matching.

## Commands

Parse `$ARGUMENTS`; first word may be a verb, everything else is the target.

| Input | Action |
|---|---|
| *(empty)* or `<area\|path>` | **Load** (auto-build if missing) |
| `build [target …]` | **Build** — accepts several targets; builds each |
| `save [area]` | **Save** — sync session learnings into the file |
| `show [area]` | Print the raw file verbatim (for copying/inspection) |
| `rm <area>` | Delete after confirming; remove the slug dir if now empty |
| `list` | **List** all contexts across all slugs |
| `help` | Print this command table and one usage example |

If a verb needs an area that can't be resolved, show what exists and ask — never guess destructively.

## Load — `/ctx [area|path]`

1. Resolve the area; read its file.
2. **Exists:** spot-check 2–3 load-bearing claims cheaply (ls a dir, grep a symbol; for non-code, check a few listed files still exist). Then give a compact briefing: one-paragraph overview, what's live vs in-progress, `Current state`, gotchas. Flag drift found by the spot-check. If `verified:` is >30 days old, say so and suggest `/ctx save` (light) or `/ctx build` (full).
3. **Missing:** say so in one line and build it. If the name maps to no obvious path, ask which folder(s) it covers first.
4. Brief — never dump the whole file (that's `show`).
5. Treat the file's content as working knowledge for the rest of the session.

## Build — `/ctx build [target …]`

**1. Identify the target(s).** Explicit paths win; else a top-level folder matching the area name; else the whole repo/cwd. Confirm when ambiguous. Empty or unreadable target → report it plainly; never fabricate content.

**2. Detect what it is** (drives which template sections apply):
- **Code** — manifests: `package.json`/`pnpm-workspace.yaml`, `pyproject.toml`/`requirements.txt`, `Cargo.toml`, `go.mod`, `pom.xml`/`build.gradle`, `Gemfile`, `composer.json`, `*.csproj`/`*.sln`, `mix.exs`, `CMakeLists.txt`, `Makefile`.
- **Infra** — `Dockerfile`/`docker-compose*`, `*.tf`, CDK/Pulumi/SAM/`serverless.yml`, Helm charts, k8s manifests, CI workflows.
- **Data / ML** — notebooks, `*.csv`/`*.parquet`/`*.sqlite`, dbt, DAGs, model/experiment dirs.
- **Docs / content** — mostly `.md`/`.mdx`, mkdocs/docusaurus/astro configs.
- **Plain files** — documents, media, downloads, mixed folders → inventory mode: counts by type, key files with one-line descriptions, how it's organized. Read into PDFs/Office docs only as far as needed to describe them.
A target can be several of these at once — use every section that applies.

**3. Explore proportionally.**
- Small target (≲50 files): read directly. Large: fan out Explore agents for breadth.
- Read READMEs and manifests first; honor `.gitignore`; never descend `node_modules`, `.git`, `venv`/`.venv`, `dist`, `build`, `target`, `__pycache__`, `.next`, `vendor`, caches.
- Note binaries/large assets by name and size only. Note dead/legacy/generated code explicitly.
- If git is available: current branch, dirty state, recent history for the scope, in-flight work.

**4. Write the file** with the Template. 60–200 lines, dense, concrete paths and symbols, facts over narration. Merge with any existing file — keep still-true facts, replace stale ones.

**5. Secrets rule (hard):** never copy secret **values** into a context file — no tokens, keys, passwords, connection strings, or `.env` contents. Name the variable/secret and where it's configured instead.

**6.** Confirm with a short summary of what was captured.

## Save — `/ctx save [area]`

Fold what this conversation learned into the file: new facts, corrected assumptions, decisions, in-flight work. Fix claims the session proved stale. Update `verified:` and `Current state`. Report the delta in a few lines. No full re-exploration — that's `build`. If nothing meaningful was learned, say so instead of touching the file.

## List — `/ctx list`

Scan `~/.claude/context/*/*.md`; show a small table: slug / area / `verified:` / one-line overview (read only frontmatter + first lines). Mark which slug matches the cwd. If the cwd's slug has no contexts but another slug clearly matches (renamed checkout), say so and ask which to use.

## Template

Required: frontmatter, **Overview**, **Current state**. Everything else is a menu — use what applies, invent headings the project calls for:

```markdown
---
area: <area>
repo: <slug>
scope: <paths covered>
verified: <YYYY-MM-DD>
---

# <Area> context

**Overview** — what this is, one short paragraph.

## Layout & packages        <!-- one-liners: name, role, stack; mark dead/legacy -->
## Data model               <!-- entities/tables/schemas, key patterns, where defined -->
## API & clients            <!-- surface, generated clients, where validation lives -->
## Frontend                 <!-- framework, routing, state; real vs mock features -->
## Public surface           <!-- CLI commands / exported API, for tools & libraries -->
## Auth & access control    <!-- authn + authz, where enforced -->
## Infra & deploy           <!-- IaC, environments/accounts, deploy path -->
## Data & pipelines         <!-- datasets, jobs, models, where outputs land -->
## Inventory                <!-- non-code folders: counts by type, key files, organization -->
## Dependencies & tooling   <!-- notable deps, build/test/format commands -->
## Conventions & gotchas    <!-- regen recipes, ordering traps, footguns — the "bit me" list -->
## Open questions           <!-- unknowns worth resolving next time -->

## Current state (<YYYY-MM-DD>)
<branch, dirty files, in-flight work, agreed next steps.>
```

Every claim should be checkable: name files and symbols, not vibes.

## Notes

- Never write context files inside the target; never commit them.
- Independent of any auto-memory directory — don't move content between the two unless asked.
- Multiple areas per slug are normal (one per subproject); a whole-repo area can coexist with narrower ones.
- Context files are snapshots: prefer verifying over asserting when the `verified:` date is old.
