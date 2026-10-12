---
name: codebase-docs
description: Store and find project documentation in central git docs repos instead of scattered Google Docs/Drive folders — one or several repos, each holding many projects (a folder each) or a single project (organized by document type). Use when the user types /codebase-docs — "/codebase-docs init" links the repo and records rules, "/codebase-docs bootstrap" drafts first docs for a project from its code, "/codebase-docs add <what>" writes or files a doc into the right project folder (or `add --from <file|artifact link>` converts an existing Word/PDF/HTML/Claude-artifact into one), "/codebase-docs find <query>" locates docs, "/codebase-docs sync" pulls/pushes, "/codebase-docs status|config|help" manage it. Also use when the user asks to document, save docs for, or find docs of the project they are working on.
argument-hint: "init | repos | bootstrap [project] | add [what | --from <file|link> [--keep-original]] [--project <name>] | find <query> [--all] | sync | push | status | config | help   (any command: --repo <name>)"
---

# codebase-docs — git repos for all project documentation

Docs live in one or more git repos. Each repo holds either many projects (one folder each, `layout: multi`) or one project organized by document type (`layout: single`). This skill links those repos, maps each code project to its repo, learns its structure, files new docs under the right project folder (adapting the structure when the project needs it), enforces the team's rules with a script, and pushes according to the user's policy.

Requires `git` and `python3`.

## Storage

```
$HOME/.claude/codebase-docs/config.json   # settings, outside any repo, never committed
<clonePath>/                              # one local clone per docs repo (default $HOME/Projects/<repo-name>)
<clonePath>/.codebase-docs.md             # in-repo conventions file, committed
<this skill's dir>/scripts/precommit.py   # the rule checker (see "Pre-commit check")
```

`config.json` (all paths absolute — expand `~` before writing):

```json
{
  "docTrigger": "suggest",
  "defaultRepo": "scm",
  "repos": {
    "scm": {
      "repo": "git@github.com:org/scm-docs.git",
      "clonePath": "/Users/me/Projects/scm-docs",
      "branch": "main",
      "layout": "single",
      "pushPolicy": "ask",
      "harness": ["no-secrets", "no-source-code", "kebab-case-names"],
      "confidentialNames": { "Real Client Name": "codename" },
      "attachmentMaxMB": 10,
      "customRules": ["free-text rules added at the end of init"]
    },
    "platform": { "repo": "git@github.com:org/platform-docs.git", "clonePath": "/Users/me/Projects/platform-docs", "branch": "main", "layout": "multi", "pushPolicy": "manual", "harness": [], "customRules": [] }
  },
  "projectMap": {
    "github.com/org/scm-connect": { "repo": "scm", "folder": "." },
    "github.com/org/orders-api": { "repo": "platform", "folder": "orders-api" }
  }
}
```

- **Several repos.** `repos` is a map of short names (kebab-case, e.g. `scm`, `platform`) to repo entries. Each repo has **its own** settings — `repo`, `clonePath`, `branch`, `layout`, `pushPolicy`, `harness`, `confidentialNames`, `attachmentMaxMB`, `customRules` — so a client repo can be strict and an internal one relaxed. Global keys are `docTrigger`, `defaultRepo` and `projectMap`.
- **Active repo.** Every setting named below (`clonePath`, `layout`, `harness`, `pushPolicy`, …) means the entry of the repo chosen by "Choosing the repo". Pass its name to the checker as `--repo <name>`.
- **Older flat configs** (no `repos` key, with `repo`/`clonePath`/`harness` at the top level) are one repo: read them as `repos.<name>` where `<name>` is the repo URL's basename; rewrite them in the new shape at the next config change, never silently mid-command. Old `projectMap` values are strings (a folder, or `"."`) → `{ "repo": <that repo>, "folder": <string> }`.
- `pushPolicy`: `ask` (default — show what will be pushed, wait for yes), `auto` (push right after each doc write), `manual` (commit only; push on `/codebase-docs push`).
- `layout`: `multi` (default — one top-level folder per project) or `single` (the repo documents one project; docs are filed by type in the existing top-level folders such as `requirements/`, `architecture/`, `meetings/`; its `projectMap` folder is `"."`). If `layout` is missing, treat it as `single` when the repo's mapped folder is `"."`, else `multi`.
- `docTrigger` (global): `manual` (only on `/codebase-docs add` or an explicit request), `suggest` (default — at a milestone, offer to document it and write nothing until the user agrees), `auto` (write and commit at a milestone, push per the repo's `pushPolicy`). The user can always ask for a doc directly, whatever the mode.
- `projectMap`: code project → `{repo, folder}`, so neither is re-asked. The skill writes an entry whenever it resolves a project. Key = the code repo's normalized remote (`host/owner/repo`, no `.git`, no scheme; a path key goes stale if the project directory moves — re-resolve then); with no remote, the project's absolute path. A project maps to exactly one repo.
- `attachmentMaxMB` (per repo, default 10) caps each attachment when `allow-attachments` is ticked.
- `confidentialNames` stays on the user's machine; never write it (or any real name from it) into the docs repo, including `.codebase-docs.md`.
- Read `config.json` at the start of every command except `init`/`help`. If missing, say so and run `init`.
- Locating the script: it sits in `scripts/` next to this `SKILL.md` (the skill's base directory is shown when the skill loads). If that path is missing, look in `$HOME/.claude/skills/codebase-docs/scripts/` then `find $HOME/.claude/plugins -path '*codebase-docs/scripts/precommit.py'`.

## Commands

| Input | Action |
|---|---|
| `init` | Link a docs repo (the first, or another one), check access, pick its settings and harness rules, push the starter files |
| `repos` | List the configured repos: name, layout, clone path, which code projects use each |
| `bootstrap [project]` | One-time: draft the initial docs for a project from its code, after you approve the plan |
| `add [what] [--project <name>]` | Write or file a doc into the right folder (default verb when the user just describes docs to write) |
| `add --from <file\|link> [--keep-original]` | Convert an existing Word/PDF/HTML/Excel/PowerPoint file or a Claude artifact link into a Markdown doc; optionally keep the original as an attachment |
| `find <query> [--all]` | Search the active repo (`--all`: every configured repo) and report matching files |
| `sync [--all]` | `git pull --rebase`, then offer to push unpushed commits |
| `push` | Check and push pending commits |
| `status` | For the active repo (or `--all`): branch, uncommitted/unpushed changes, current project's folder |
| `config [--repo <name>]` | Show config; re-open a repo's harness checklist, change `docTrigger`/`pushPolicy`, or edit any field. `config remove-repo <name>` drops a repo from the config (asks first; never deletes the clone or the remote) |
| (any command) | `--repo <name>` overrides the repo choice for that command |
| `help` | Print this table plus: `Example: /codebase-docs add "how we deploy the orders API"` |

## init

Use AskUserQuestion where choices are fixed, plain questions for free text. `init` links **one repo per run**. If repos are already configured, list them and ask: add another repo, or change one (then show its current values and ask only what to change). Run `init` again any time to add more.

1. **Repo** — URL of the docs git repo, or a path to an existing local clone, then a short **name** for it (kebab-case; default the URL's basename minus `-docs`/`.git`; must be unique in `repos`).
2. **Clone location** — a fixed absolute path independent of the current directory, so it works from inside any project's session, and different for every repo. Default `$HOME/Projects/<repo URL basename>`; never inside the current project's working tree. If the path exists and its `origin` matches, reuse it; if it exists and differs, stop and ask. Clone it.
3. **Git identity** — `git -C <clone> config user.email` must resolve (global or local). If it doesn't, ask the user for name and email and set them in the clone's local config only; if no one can be asked, stop and say identity is missing rather than inventing one.
4. **Learn the repo and choose the layout** — read its `README.md`, `.codebase-docs.md` if present, and list two levels deep; summarize the structure in a few lines and ask the user to confirm or correct. Then set `layout`: if top-level folders are document types (requirements, architecture, reports, meetings, contracts, …) or the user says the repo covers one project, propose `single`; if they are project names, or the repo is empty and will hold several projects, propose `multi`. Confirm with the user (AskUserQuestion: multi-project / single-project). For an empty `single` repo, ask which type folders to create (default: `requirements`, `architecture`, `reports`, `meetings`, `estimates`, `contracts`, `references`, `templates`).
5. **Settings and harness — two AskUserQuestion calls of four questions each:**
   - Call A: **Push policy** (`ask` recommended / `auto` / `manual`); **Doc trigger** (global — ask only on the first repo or when the user wants to change it: `suggest` recommended / `manual` / `auto`, warning that `auto` works best with `no-secrets` and `branch-and-pr` ticked); if that leaves a slot free, offer to copy the harness from an existing repo as the starting selection; then the multi-select groups **Content safety** and **Confidentiality**.
   - Call B: multi-select groups **Code policy**, **Structure**, **Format**, **Workflow**. In `single` layout leave `folder-per-project` and `dated-notes` out of **Structure** (they assume per-project folders).
   - Each option is a catalog id (below), recommended ones marked. Nothing is on unless ticked. An "Other" entry on any question is folded into `customRules`.
   - Only if `anonymize-clients` is ticked, ask for the client/partner/vendor names that must never appear and a codename for each → `confidentialNames`. Client-name scanning exists only under this rule; leaving it unticked means names are never checked. Whenever `anonymize-clients` is unticked (at `init` or `config`), tell the user the saved `confidentialNames` will stop being checked and ask whether to delete them, so the config never holds names that look protected but aren't.
   - Finally ask free text: **"Any custom rules not covered above?"** (empty = none) → `customRules`, one rule per entry (e.g. a file-naming pattern).
6. **Write config.json** (add or update `repos.<name>`; set `defaultRepo` if this is the first repo or the user says so; ask which code projects, if any, should map to it now — otherwise they are mapped at first use), then create/refresh the starter files if missing: root `README.md` (title, one-line purpose, and an index table `| Project | Summary |` with no rows yet) and `.codebase-docs.md` (the chosen rules in plain language, per "Conventions file"). In `multi`, project folders are **not** created here — they appear at the first `add`/`bootstrap`; the root index is a `| Project | Summary |` table. In `single`, create the chosen type folders (each with a `.gitkeep`) and make the root `README.md` a short project description plus a `Structure` list of those folders. Never overwrite existing starter files.
7. **Check and commit the starter files** — `git add` them, run the pre-commit check (staged, no `--code`) and fix any BLOCK, then commit (`docs: initialize docs repo`).
8. **Write-access check** — only possible once the clone has a commit, which is why it comes after step 7. Run `git -C <clone> push --dry-run origin HEAD:<branch>`. If it fails, report the exact error and stop; don't continue with a read-only repo.
9. **Push the starter commit.** It is the one push `confidentiality-review` does not apply to (it holds no project content). With `branch-and-pr` and a non-empty repo, follow "Branch and PR" instead.
10. Tell the user the next steps: `bootstrap` for an existing project, `add` for a single doc, `init` again to link another repo.

### Harness catalog

| Group | id | Rule |
|---|---|---|
| Content safety | `no-secrets` ★ | Never write secrets, tokens, keys or credentials; refer to where they live (vault, env var name) |
| | `no-pii` ★ | No customer data or personal info; use placeholders |
| | `no-internal-urls` | No internal hostnames, private IPs, or AWS account IDs |
| | `public-safe` | Write as if the repo could become public |
| Confidentiality | `nda-safe` ★ | Nothing covered by an NDA or client confidentiality: no client-provided materials, contract terms, pricing, non-public roadmaps or third-party confidential info |
| | `anonymize-clients` | Clients, partners and vendors appear by codename only |
| | `no-third-party-content` | No pasted copyrighted/licensed material; summarize in own words and link |
| | `confidentiality-review` ★ | Before any push, show a confidentiality summary and get explicit approval, whatever `pushPolicy` says |
| Code policy | `no-source-code` ★ | **Strict:** no code files in the repo — only `.md`/`.mdx` and images (plus attachments, if `allow-attachments` is ticked). Code appears only as short snippets inside Markdown |
| | `snippet-limit` ★ | Snippets are samples: at most 30 lines, labeled "Sample", never a verbatim copy of code from the project |
| | `link-not-copy` | Point to code by repo, path and commit permalink instead of pasting it |
| | `allow-attachments` | Opt-in: original files (`.pdf`, `.docx`, `.xlsx`, `.pptx`, `.csv`, `.html`, images) may be kept in `<project>/attachments/`, each linked from a Markdown page, under `attachmentMaxMB`. The checker scans their text; anything it can't read is flagged for your review |
| Structure | `folder-per-project` ★ | `multi` layout only: one top-level folder per project, named in kebab-case |
| | `index-readmes` ★ | Keep each project `README.md` and the root `README.md` index up to date |
| | `adr-decisions` | Decisions are ADRs in `decisions/YYYY-MM-DD-title.md` (context, decision, consequences) |
| | `dated-notes` | `multi` layout only: working notes in `notes/YYYY-MM-DD-title.md` |
| Format | `markdown-only` ★ | Markdown only (no images either); link to external files instead of committing binaries. Narrows `no-source-code`'s image allowance |
| | `kebab-case-names` ★ | File and folder names are lowercase kebab-case (`README.md` excepted) |
| | `frontmatter` | Every content doc starts with frontmatter: `title`, `owner`, `updated`, `status` |
| | `mermaid-diagrams` | Diagrams are Mermaid code blocks, not images |
| Workflow | `link-code-repo` | Each project README links its code repo(s) |
| | `confirm-restructure` ★ | Announce and get approval before moving or renaming existing docs |
| | `one-line-commits` | One-line commit messages, no body |
| | `branch-and-pr` | Push to a `docs/<topic>` branch and open a PR instead of pushing to the main branch |

★ = recommended. The script enforces what can be checked mechanically (file types, names, frontmatter, secrets, internal addresses, confidential names, code blocks, commit bodies) and prints `MANUAL` reminders for the rest.

## Pre-commit check

One script, used by `init`, `add`, `bootstrap` and `push`. Run it **before every commit** (staged mode) and **before every push** (range mode):

```
python3 <skill dir>/scripts/precommit.py --clone <clonePath> --config $HOME/.claude/codebase-docs/config.json --repo <name> \
  [--mode staged|range] [--range origin/<branch>..HEAD | ALL] [--code <project path> ...] [--message "<commit msg>"] [--summary]
```

- `staged` (default): checks what is staged, reading content from the index. `range`: checks the files and commit messages in the range (`ALL` for a first push when the remote branch doesn't exist yet).
- `--code`: the code project(s) being documented (the session's working directory, or the path given to `bootstrap`). Needed to catch verbatim copies; skip it only when no code project is known.
- Output: `BLOCK` lines (stop), `FLAG` lines (show the user, keep or reword, proceed only on an explicit answer), `MANUAL` lines (rules the script can't judge — you must verify each one against what you wrote and fix violations), then `RESULT PASS|FLAGS|FAIL`. Exit 0 / 2 / 1.
- Thresholds, so results are reproducible: code blocks over 30 lines blocked; a block is "labeled" if the word *Sample* is on the fence line or the nearest non-blank line above (`mermaid` blocks exempt); a block is a "verbatim copy" if at least 3 non-trivial lines match a project file and they are at least 50% of the block, or the doc contains a whole project file; contract/pricing language is a FLAG, everything else listed is a BLOCK.
- **Attachments** (`allow-attachments`): files in `<project>/attachments/` (in `single` layout: anywhere inside a type folder, e.g. `contracts/signed-msa.pdf`) are exempt from the file-type rule but must be an allowed type, under the size limit, kebab-case named, and linked from a Markdown page in the same project (`single`: in the same type folder). The script extracts and scans the text of `.docx/.pptx/.xlsx`, `.html`, `.csv` and (when `pdftotext` is installed) `.pdf` with the same secret/internal-address/confidential-name checks; unreadable content (scanned PDFs, images excluded) gets a `FLAG` — open it yourself, check it, and ask the user before keeping it. HTML containing scripts is flagged too.
- `--summary` prints the confidentiality summary (files and line counts, attachments, code blocks, URLs, amounts/percentages, confidential names found) — show it verbatim for `confidentiality-review`.
- A ticked rule is **not overridable in the moment**. If the user asks for something it forbids ("just push the file"), name the rule that blocks it and say they can change it via `/codebase-docs config`; don't bypass the check.
- On BLOCK: don't commit. Report each line, **unstage** the offending paths (`git -C <clone> reset -q -- <path>`) without deleting them, then fix the content and re-run. Files this run created that were never committed may be edited or removed to fix them; existing committed docs are never deleted (see Safety).
- **Bad commit already made** (a range-mode BLOCK): if it is unpushed, `git -C <clone> reset --soft HEAD~<n>`, fix, and re-commit — allowed, since nothing was published. If it is already pushed, don't rewrite history; explain and ask the user.
- **Custom rules** (`customRules`) are checked by you, not the script (it only prints them as `MANUAL`) — verify each against what you wrote. They apply to content docs, not to index files (root/project `README.md`) or `.codebase-docs.md`, unless a rule says otherwise. When updating an index, insert new rows inside its table/list and keep any trailer line last. If a rule needs a value you don't have (e.g. an owner name), write `TODO:` rather than inventing it.

## Choosing the repo

Used by every command that touches docs (`add`, `bootstrap`, `find`, `sync`, `push`, `status`, the doc trigger). The result is the **active repo**.

1. `--repo <name>` wins. If the current code project is mapped to a *different* repo, say so and ask before using the override.
2. Else the current code project's `projectMap` entry → its repo (and folder).
3. Else only one repo configured → it.
4. Else several repos and the project is unmapped → ask which repo (AskUserQuestion; list name, layout and clone path; mark `defaultRepo`), then record `{repo, folder}` in `projectMap` once the folder is resolved. Never guess between repos, and never file one project's docs in two repos.
5. Not inside any code project (`find`, `sync`, `status`, `push`) → `defaultRepo`, or ask if there isn't one; `--all` runs the command over every repo in turn and reports per repo.

Each repo is independent: its own clone, layout, harness, push policy and conventions file. Run the pre-commit check with that repo's `--repo <name>` and never apply one repo's rules to another.

## Resolving the project

Used by `add` and `bootstrap`, within the active repo.

**`layout: single`** — there is no project folder to pick; docs go in the repo's type folders (see "Placement in a single-project repo"). The repo was chosen by "Choosing the repo", so the code project is mapped to it or the user just picked it; record `{ "repo": "<name>", "folder": "." }`. If the repo was chosen only because it is the sole or default repo and the code project is unmapped, say this repo documents one project and confirm it is the right one before filing. Skip steps 1–6 below.

**`layout: multi`:**

1. `--project <name>` wins.
2. Else the current code project's `projectMap` folder in this repo (key as defined above).
3. Else match its name against top-level folders in the docs repo (case- and separator-insensitive). Exactly one match → use it. Several or none → ask: pick an existing folder or create a new one.
4. A new folder's name comes from, in order: what the user says; the project's manifest name (`package.json` `name`, `pyproject.toml`, `Cargo.toml`, `go.mod`); the code README's first `#` heading; the working directory's basename. Kebab-case it and confirm with the user.
5. Not inside any project and no `--project` → ask.
6. Record `{ "repo": "<name>", "folder": "<folder>" }` in `projectMap`.

## bootstrap

Opt-in, explicit only — never triggered by `docTrigger`. Drafts the first docs for a project that has none yet, from its code.

1. **Resolve the project** (above). If its folder already has docs, say so and ask whether to extend (fill gaps only) or stop; never overwrite existing files.
2. **Pull** — `git -C <clonePath> pull --rebase`; on a dirty tree or conflict, stop and report.
3. **Read the code project proportionally**, in the working directory or the path given: README, manifests, entry points, config/infra files, layout, test names, CI workflows. Fan out Explore agents for a large repo. Skip `node_modules`, `.git`, build output, caches and generated code. Note names and purposes — you are describing the system, not copying it.
4. **Propose a plan before writing anything**: files to create (`multi` default: `README.md`, `overview.md`, `architecture.md`, `setup.md`; add `decisions/` or `runbooks/` only when the code supports them; `single`: the root `README.md` description plus an architecture doc in `architecture/`, setup/run notes in `references/` or the best-fitting folder, named per the repo's naming rule), one line each on what it covers and its source, and the harness rules that apply. Wait for approval or edits; don't write without a yes.
5. **Write the docs** in prose: purpose, tech stack, components and how they interact, data flow, how to run/build/deploy, environments, external dependencies, known gaps. At most a few short labeled sample snippets; link to code by repo, path and commit instead of pasting. Never invent: anything not evident from the code is `TODO:`. Use codenames from `confidentialNames` wherever the real name would appear.
6. **Update indexes** (`multi`: project `README.md` and the root index; `single`: the root `README.md`).
7. **Pre-commit check** (staged, with `--code <project path>`), passing `--message "docs(<project>): bootstrap initial docs"`, then **commit** once with that message.
8. **Push and report** — follow `add` steps 9–10. The report also lists anything left as `TODO:` and the questions the code couldn't answer.

## add

1. **Resolve the project** (above; in `single` layout just confirm the code project is mapped).
2. **Pull first** — `git -C <clonePath> pull --rebase`. If the tree is dirty or the pull conflicts, stop and report; never discard changes.
3. **Apply the harness** — treat every id in `harness` and every `customRules` entry as a hard constraint on what you write, where you put it, and how you commit and push. If a request conflicts with a ticked rule, say so rather than break it.
4. **Understand the existing structure** for that project: list its folder, read its `README.md` and neighbouring docs of the same kind so new content matches their format and depth; follow templates found in the repo.
5. **Decide placement.** In `single` layout use "Placement in a single-project repo". In `multi`, put the doc where the existing convention says (decisions → `decisions/`). If the project needs structure the repo lacks, adapt it: add a folder, split a doc, or move/rename files — keeping both README indexes accurate. State any restructure, especially moves and renames, before doing it (`confirm-restructure` makes approval mandatory); never delete docs without explicit approval.
6. **Write the doc** from what the user described and what the session actually knows (code, decisions made, commands run). Don't invent facts; mark gaps `TODO:` or ask. Never include secrets, tokens or credentials — refer to where they live instead.
7. **Update indexes** — in `multi`, the project and root `README.md`; in `single`, the root `README.md` Structure list (and a type folder's `README.md` if it has one), only when a folder was added or its purpose changed.
8. **Pre-commit check** (staged, `--code <project path>`, `--message "<subject>"`), then **commit** with a short descriptive one-line subject (`docs(<project>): add <topic>`); with `one-line-commits` never add a body. Committing is part of the user's request to store docs here.
9. **Push per policy**
   - Run the pre-commit check in range mode (`--range origin/<branch>..HEAD`, or `ALL` if the remote branch doesn't exist).
   - `confidentiality-review` ticked: show the `--summary` output plus `git diff --stat`; **one** explicit approval covers the push — even under `auto`, and it replaces the `ask` prompt.
   - Else `ask`: show `git log origin/<branch>..HEAD --oneline` and `git diff --stat origin/<branch>..HEAD`, ask before pushing.
   - Else `auto`: push and report. `manual`: don't push; say it is committed locally and `/codebase-docs push` will push it.
   - `branch-and-pr` ticked: use "Branch and PR" below instead of pushing the main branch.
10. **Report:** file path(s) relative to the repo, commit hash, push status, and — when the host is GitHub — a link (`<repo-url>/blob/<branch>/<path>`).

### Placement in a single-project repo

Choose the type folder by what the doc is: requirements/specs → `requirements/`, design and decisions (ADRs) → `architecture/`, status/analysis → `reports/`, calls and minutes → `meetings/`, quotes and effort → `estimates/`, agreements → `contracts/`, external or imported material → `references/`, reusable forms → `templates/`. Map to whichever of the repo's actual folders fits best; if none fits, ask — new folders need approval (`confirm-restructure`) and an update to the root `README.md` Structure list. Follow the file-naming pattern in `customRules` or `.codebase-docs.md`, and match neighbouring files in that folder. If a doc with the same subject exists, update it in place with the next version instead of adding a copy.

### Branch and PR

For `branch-and-pr`: create `docs/<topic>` (kebab-case, from the doc topic) before committing, push it with `git push -u origin docs/<topic>`, then open a PR with `gh pr create` if `gh` is available (title = the commit subject), otherwise print the branch's compare URL. Never merge it.

## add --from (import an existing file or artifact)

Brings documents that already exist (Word, PDF, HTML, Excel, PowerPoint, a Claude artifact) into the docs repo. Follows `add`'s steps 1–2 and 4–10; only the source of the content differs.

1. **Read the source.**
   - `.docx`/`.pptx`/`.xlsx`: `pandoc -t gfm` if installed, otherwise the available docx/pptx/xlsx skills or a plain text extraction.
   - `.pdf`: the Read tool with `pages`, or `pdftotext -layout`.
   - `.html`/`.md`/`.txt`: read directly (HTML → structure the content as Markdown).
   - **Claude artifact link** (`claude.ai/.../artifact/...`): the Artifact tool's `read` action returns its page; convert the content to Markdown. Never fetch it with a web tool.
   - Google Doc/Drive link: use a Drive/Docs connector if one is attached; otherwise ask the user to export the file and pass the path.
   - Unreadable or empty source → say so; never fabricate content.
2. **Convert faithfully** to a Markdown doc: keep headings, lists and tables; describe charts/images in a line instead of embedding them (or note `TODO: diagram — see original`); replace real client names with codenames and redact secrets per the harness. Open the doc with a line `Imported from <file name or artifact title>, <YYYY-MM-DD>` — no private URLs.
3. **Placement and naming** as `add` (project folder, kebab-case name from the source's title).
4. **Original file** — not committed by default. Keep it only when the user passes `--keep-original` (or asks) **and** `allow-attachments` is ticked: copy it to `<project>/attachments/<kebab-name>.<ext>` (`single`: into the matching type folder, named per the repo's naming rule) and link it from the Markdown page ("Original: [name](attachments/name.ext)"). If the rule isn't ticked, say attachments are off, offer to enable it via `config`, and commit only the Markdown. A Claude artifact kept as `.html` loses nothing but must be downloaded to view — mention that.
5. **The original defeats redaction.** If step 2 codenamed or redacted anything, the untouched original still contains it, and the checker will BLOCK it. Explain this rather than working around it; the Markdown conversion is the shareable version.
6. Continue with `add` steps 7–10 (indexes, pre-commit check, commit, push). The pre-commit check covers the Markdown and any attachment.

## Doc trigger

Applies when this skill is loaded in a session doing other work. The target repo comes from "Choosing the repo"; if the project is unmapped and several repos exist, ask which one when making the suggestion. Milestones worth documenting: a feature or fix completed, a design or architecture decision made, a bug root-caused, a setup/deploy/runbook procedure worked out, an integration or API contract settled.

- `manual`: never raise docs unprompted.
- `suggest`: at a milestone, say in one line what could be documented and where (`<project>/decisions/…`), and ask. Offer once per milestone; if declined, don't repeat. On yes, run `add`.
- `auto`: run `add` at the milestone, then report file, commit and push status in one line.
- Never trigger on trivial edits, mid-task states, or work that is still being reverted or reworked.
- A direct request ("document this", `/codebase-docs add`) always works in every mode.
- The user can change the mode in plain words ("switch to auto", "stop suggesting"); update `docTrigger` in `config.json` and confirm.

## find

Search the active repo (every configured repo with `--all`, labelling hits by repo). Pull first (`git -C <clonePath> pull --rebase`); if the pull fails or there is no network, continue on the local copy and say the results may be stale. Search file names first, then content (`git -C <clonePath> ls-files | grep -i`, then `grep -rniI`), scoped to the current project's folder first, then the whole repo. Report up to ~10 hits as `path — one-line why it matches`, and offer to open or summarize the best one.

## sync / push / status / repos

- `repos`: list each configured repo as `name — layout — clonePath — remote — code projects mapped to it`, marking `defaultRepo`. Read-only.
- `status`: for the active repo (every repo with `--all`) show branch, uncommitted changes, unpushed commits and the current project's folder.
- `config remove-repo <name>`: ask first, then delete only its `repos` entry and its `projectMap` mappings; never touch the clone or the remote. If it was `defaultRepo`, ask for a new default.

- `sync`: `git -C <clonePath> pull --rebase`; on conflict stop and explain, never force. Then, if there are unpushed commits, continue as `push`.
- `push`: if nothing is unpushed, say so. Otherwise follow `add` step 9 (range-mode check, confidentiality summary or push confirmation per policy, `branch-and-pr` handling), then `git push`. A BLOCK anywhere in the range stops the push and is reported. Never `--force`.

## Conventions file

`.codebase-docs.md` in the docs repo states the layout (`multi` or `single`) and rules in plain language so other machines and agents follow the same structure: folder-per-project (`multi`) or the type folders (`single`), naming, templates, index maintenance, what never goes in docs, plus the selected `harness` rules and `customRules`. Never include `confidentialNames`. Update it whenever the structure or rules intentionally change; it is committed with the docs.

## Safety

- Always use absolute paths and `git -C <clonePath> ...`; never `cd` into the docs clone or rely on the current directory — the session is usually in another project. The clone is outside the session's folders, so expect a permission prompt the first time it is read or written.
- Only operate inside the active repo's `clonePath`; never modify the project's code repo from this skill (reading it is fine).
- No force-push, no history rewrites, no deleting committed docs or branches without explicit approval.
- Push only the active repo's configured branch (or the `docs/<topic>` branch under `branch-and-pr`) to its configured remote. A command never pushes, pulls or writes in a repo other than the active one (`--all` visits them one at a time).
- Docs may be shared; the pre-commit check is mandatory before every commit and push.
