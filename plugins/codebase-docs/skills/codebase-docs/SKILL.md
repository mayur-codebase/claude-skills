---
name: codebase-docs
description: Store and find project documentation in one central git docs repo instead of scattered Google Docs/Drive folders. Use when the user types /codebase-docs — "/codebase-docs init" links the repo and records rules, "/codebase-docs bootstrap" drafts first docs for a project from its code, "/codebase-docs add <what>" writes or files a doc into the right project folder (or `add --from <file|artifact link>` converts an existing Word/PDF/HTML/Claude-artifact into one), "/codebase-docs find <query>" locates docs, "/codebase-docs sync" pulls/pushes, "/codebase-docs status|config|help" manage it. Also use when the user asks to document, save docs for, or find docs of the project they are working on.
argument-hint: "init | bootstrap [project] | add [what | --from <file|link> [--keep-original]] [--project <name>] | find <query> | sync | push | status | config | help"
---

# codebase-docs — one git repo for all project documentation

Docs for every project live in a single git repo. This skill links that repo, learns its structure, files new docs under the right project folder (adapting the structure when the project needs it), enforces the team's rules with a script, and pushes according to the user's policy.

Requires `git` and `python3`.

## Storage

```
$HOME/.claude/codebase-docs/config.json   # settings, outside any repo, never committed
<clonePath>/                              # local clone of the docs repo (default $HOME/Projects/codebase-docs)
<clonePath>/.codebase-docs.md             # in-repo conventions file, committed
<this skill's dir>/scripts/precommit.py   # the rule checker (see "Pre-commit check")
```

`config.json` (all paths absolute — expand `~` before writing):

```json
{
  "repo": "git@github.com:org/docs.git",
  "clonePath": "/Users/me/Projects/codebase-docs",
  "branch": "main",
  "pushPolicy": "ask",
  "docTrigger": "suggest",
  "projectMap": { "github.com/org/orders-api": "orders-api" },
  "harness": ["no-secrets", "folder-per-project", "kebab-case-names"],
  "confidentialNames": { "Real Client Name": "codename" },
  "attachmentMaxMB": 10,
  "customRules": ["free-text rules added at the end of init"]
}
```

- `pushPolicy`: `ask` (default — show what will be pushed, wait for yes), `auto` (push right after each doc write), `manual` (commit only; push on `/codebase-docs push`).
- `docTrigger`: `manual` (only on `/codebase-docs add` or an explicit request), `suggest` (default — at a milestone, offer to document it and write nothing until the user agrees), `auto` (write and commit at a milestone, push per `pushPolicy`). The user can always ask for a doc directly, whatever the mode.
- `projectMap`: code project → docs folder, so it is never re-asked. The skill writes an entry whenever it resolves a project. Key = the code repo's normalized remote (`host/owner/repo`, no `.git`, no scheme); with no remote, the project's absolute path.
- `attachmentMaxMB` (default 10) caps each attachment when `allow-attachments` is ticked.
- `confidentialNames` stays on the user's machine; never write it (or any real name from it) into the docs repo, including `.codebase-docs.md`.
- Read `config.json` at the start of every command except `init`/`help`. If missing, say so and run `init`.
- Locating the script: it sits in `scripts/` next to this `SKILL.md` (the skill's base directory is shown when the skill loads). If that path is missing, look in `$HOME/.claude/skills/codebase-docs/scripts/` then `find $HOME/.claude/plugins -path '*codebase-docs/scripts/precommit.py'`.

## Commands

| Input | Action |
|---|---|
| `init` | Link the repo, check access, pick settings and harness rules, push the starter files |
| `bootstrap [project]` | One-time: draft the initial docs for a project from its code, after you approve the plan |
| `add [what] [--project <name>]` | Write or file a doc into the right folder (default verb when the user just describes docs to write) |
| `add --from <file\|link> [--keep-original]` | Convert an existing Word/PDF/HTML/Excel/PowerPoint file or a Claude artifact link into a Markdown doc; optionally keep the original as an attachment |
| `find <query>` | Search the docs repo and report matching files |
| `sync` | `git pull --rebase`, then offer to push unpushed commits |
| `push` | Check and push pending commits |
| `status` | Linked repo, branch, uncommitted/unpushed changes, current project's folder |
| `config` | Show config; re-open the harness checklist, change `docTrigger`/`pushPolicy`, or edit any field |
| `help` | Print this table plus: `Example: /codebase-docs add "how we deploy the orders API"` |

## init

Use AskUserQuestion where choices are fixed, plain questions for free text. On re-run, show current values and ask only what to change.

1. **Repo** — URL of the docs git repo, or a path to an existing local clone.
2. **Clone location** — a fixed absolute path independent of the current directory, so it works from inside any project's session. Default `$HOME/Projects/codebase-docs`; never inside the current project's working tree. If the path exists and its `origin` matches, reuse it; if it exists and differs, stop and ask. Clone it.
3. **Git identity** — `git -C <clone> config user.email` must resolve (global or local). If it doesn't, ask the user for name and email and set them in the clone's local config only; if no one can be asked, stop and say identity is missing rather than inventing one.
4. **Settings and harness — two AskUserQuestion calls of four questions each:**
   - Call A: **Push policy** (`ask` recommended / `auto` / `manual`); **Doc trigger** (`suggest` recommended / `manual` / `auto` — warn that `auto` works best with `no-secrets` and `branch-and-pr` ticked); then the multi-select groups **Content safety** and **Confidentiality**.
   - Call B: multi-select groups **Code policy**, **Structure**, **Format**, **Workflow**.
   - Each option is a catalog id (below), recommended ones marked. Nothing is on unless ticked. An "Other" entry on any question is folded into `customRules`.
   - If `nda-safe` or `anonymize-clients` is ticked, ask for the client/partner/vendor names that must never appear and a codename for each → `confidentialNames`.
   - Finally ask free text: **"Any custom rules not covered above?"** (empty = none) → `customRules`, one rule per entry.
5. **Learn the repo** — read its `README.md`, `.codebase-docs.md` if present, and list two levels deep. Summarize the structure in a few lines and ask the user to confirm or correct.
6. **Write config.json**, then create/refresh the starter files if missing: root `README.md` (title, one-line purpose, and an index table `| Project | Summary |` with no rows yet) and `.codebase-docs.md` (the chosen rules in plain language, per "Conventions file"). Project folders are **not** created here — they appear at the first `add`/`bootstrap`.
7. **Check and commit the starter files** — `git add` them, run the pre-commit check (staged, no `--code`) and fix any BLOCK, then commit (`docs: initialize docs repo`).
8. **Write-access check** — only possible once the clone has a commit, which is why it comes after step 7. Run `git -C <clone> push --dry-run origin HEAD:<branch>`. If it fails, report the exact error and stop; don't continue with a read-only repo.
9. **Push the starter commit.** It is the one push `confidentiality-review` does not apply to (it holds no project content). With `branch-and-pr` and a non-empty repo, follow "Branch and PR" instead.
10. Tell the user the next steps: `bootstrap` for an existing project, `add` for a single doc.

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
| Structure | `folder-per-project` ★ | One top-level folder per project, named in kebab-case |
| | `index-readmes` ★ | Keep each project `README.md` and the root `README.md` index up to date |
| | `adr-decisions` | Decisions are ADRs in `decisions/YYYY-MM-DD-title.md` (context, decision, consequences) |
| | `dated-notes` | Working notes in `notes/YYYY-MM-DD-title.md` |
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
python3 <skill dir>/scripts/precommit.py --clone <clonePath> --config $HOME/.claude/codebase-docs/config.json \
  [--mode staged|range] [--range origin/<branch>..HEAD | ALL] [--code <project path> ...] [--message "<commit msg>"] [--summary]
```

- `staged` (default): checks what is staged, reading content from the index. `range`: checks the files and commit messages in the range (`ALL` for a first push when the remote branch doesn't exist yet).
- `--code`: the code project(s) being documented (the session's working directory, or the path given to `bootstrap`). Needed to catch verbatim copies; skip it only when no code project is known.
- Output: `BLOCK` lines (stop), `FLAG` lines (show the user, keep or reword, proceed only on an explicit answer), `MANUAL` lines (rules the script can't judge — you must verify each one against what you wrote and fix violations), then `RESULT PASS|FLAGS|FAIL`. Exit 0 / 2 / 1.
- Thresholds, so results are reproducible: code blocks over 30 lines blocked; a block is "labeled" if the word *Sample* is on the fence line or the nearest non-blank line above (`mermaid` blocks exempt); a block is a "verbatim copy" if at least 3 non-trivial lines match a project file and they are at least 50% of the block, or the doc contains a whole project file; contract/pricing language is a FLAG, everything else listed is a BLOCK.
- **Attachments** (`allow-attachments`): files in `<project>/attachments/` are exempt from the file-type rule but must be an allowed type, under the size limit, kebab-case named, and linked from a Markdown page in the same project. The script extracts and scans the text of `.docx/.pptx/.xlsx`, `.html`, `.csv` and (when `pdftotext` is installed) `.pdf` with the same secret/internal-address/confidential-name checks; unreadable content (scanned PDFs, images excluded) gets a `FLAG` — open it yourself, check it, and ask the user before keeping it. HTML containing scripts is flagged too.
- `--summary` prints the confidentiality summary (files and line counts, attachments, code blocks, URLs, amounts/percentages, confidential names found) — show it verbatim for `confidentiality-review`.
- A ticked rule is **not overridable in the moment**. If the user asks for something it forbids ("just push the file"), name the rule that blocks it and say they can change it via `/codebase-docs config`; don't bypass the check.
- On BLOCK: don't commit. Report each line, **unstage** the offending paths (`git -C <clone> reset -q -- <path>`) without deleting them, then fix the content and re-run. Files this run created that were never committed may be edited or removed to fix them; existing committed docs are never deleted (see Safety).
- **Bad commit already made** (a range-mode BLOCK): if it is unpushed, `git -C <clone> reset --soft HEAD~<n>`, fix, and re-commit — allowed, since nothing was published. If it is already pushed, don't rewrite history; explain and ask the user.
- **Custom rules** (`customRules`) are checked by you, not the script (it only prints them as `MANUAL`) — verify each against what you wrote. They apply to content docs, not to index files (root/project `README.md`) or `.codebase-docs.md`, unless a rule says otherwise. When updating an index, insert new rows inside its table/list and keep any trailer line last. If a rule needs a value you don't have (e.g. an owner name), write `TODO:` rather than inventing it.

## Resolving the project

Used by `add` and `bootstrap`.

1. `--project <name>` wins.
2. Else look the current code project up in `projectMap` (key as defined above).
3. Else match its name against top-level folders in the docs repo (case- and separator-insensitive). Exactly one match → use it. Several or none → ask: pick an existing folder or create a new one.
4. A new folder's name comes from, in order: what the user says; the project's manifest name (`package.json` `name`, `pyproject.toml`, `Cargo.toml`, `go.mod`); the code README's first `#` heading; the working directory's basename. Kebab-case it and confirm with the user.
5. Not inside any project and no `--project` → ask.
6. Record the resolved pairing in `projectMap` (a path key is stale if the project directory moves — re-resolve then).

## bootstrap

Opt-in, explicit only — never triggered by `docTrigger`. Drafts the first docs for a project that has none yet, from its code.

1. **Resolve the project** (above). If its folder already has docs, say so and ask whether to extend (fill gaps only) or stop; never overwrite existing files.
2. **Pull** — `git -C <clonePath> pull --rebase`; on a dirty tree or conflict, stop and report.
3. **Read the code project proportionally**, in the working directory or the path given: README, manifests, entry points, config/infra files, layout, test names, CI workflows. Fan out Explore agents for a large repo. Skip `node_modules`, `.git`, build output, caches and generated code. Note names and purposes — you are describing the system, not copying it.
4. **Propose a plan before writing anything**: files to create (default `README.md`, `overview.md`, `architecture.md`, `setup.md`; add `decisions/` or `runbooks/` only when the code supports them), one line each on what it covers and its source, and the harness rules that apply. Wait for approval or edits; don't write without a yes.
5. **Write the docs** in prose: purpose, tech stack, components and how they interact, data flow, how to run/build/deploy, environments, external dependencies, known gaps. At most a few short labeled sample snippets; link to code by repo, path and commit instead of pasting. Never invent: anything not evident from the code is `TODO:`. Use codenames from `confidentialNames` wherever the real name would appear.
6. **Update indexes** (project `README.md` and the root index).
7. **Pre-commit check** (staged, with `--code <project path>`), passing `--message "docs(<project>): bootstrap initial docs"`, then **commit** once with that message.
8. **Push and report** — follow `add` steps 9–10. The report also lists anything left as `TODO:` and the questions the code couldn't answer.

## add

1. **Resolve the project** (above).
2. **Pull first** — `git -C <clonePath> pull --rebase`. If the tree is dirty or the pull conflicts, stop and report; never discard changes.
3. **Apply the harness** — treat every id in `harness` and every `customRules` entry as a hard constraint on what you write, where you put it, and how you commit and push. If a request conflicts with a ticked rule, say so rather than break it.
4. **Understand the existing structure** for that project: list its folder, read its `README.md` and neighbouring docs of the same kind so new content matches their format and depth; follow templates found in the repo.
5. **Decide placement.** Put the doc where the existing convention says (decisions → `decisions/`). If the project needs structure the repo lacks, adapt it: add a folder, split a doc, or move/rename files — keeping both README indexes accurate. State any restructure, especially moves and renames, before doing it (`confirm-restructure` makes approval mandatory); never delete docs without explicit approval.
6. **Write the doc** from what the user described and what the session actually knows (code, decisions made, commands run). Don't invent facts; mark gaps `TODO:` or ask. Never include secrets, tokens or credentials — refer to where they live instead.
7. **Update indexes** (project and root `README.md`).
8. **Pre-commit check** (staged, `--code <project path>`, `--message "<subject>"`), then **commit** with a short descriptive one-line subject (`docs(<project>): add <topic>`); with `one-line-commits` never add a body. Committing is part of the user's request to store docs here.
9. **Push per policy**
   - Run the pre-commit check in range mode (`--range origin/<branch>..HEAD`, or `ALL` if the remote branch doesn't exist).
   - `confidentiality-review` ticked: show the `--summary` output plus `git diff --stat`; **one** explicit approval covers the push — even under `auto`, and it replaces the `ask` prompt.
   - Else `ask`: show `git log origin/<branch>..HEAD --oneline` and `git diff --stat origin/<branch>..HEAD`, ask before pushing.
   - Else `auto`: push and report. `manual`: don't push; say it is committed locally and `/codebase-docs push` will push it.
   - `branch-and-pr` ticked: use "Branch and PR" below instead of pushing the main branch.
10. **Report:** file path(s) relative to the repo, commit hash, push status, and — when the host is GitHub — a link (`<repo-url>/blob/<branch>/<path>`).

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
4. **Original file** — not committed by default. Keep it only when the user passes `--keep-original` (or asks) **and** `allow-attachments` is ticked: copy it to `<project>/attachments/<kebab-name>.<ext>` and link it from the Markdown page ("Original: [name](attachments/name.ext)"). If the rule isn't ticked, say attachments are off, offer to enable it via `config`, and commit only the Markdown. A Claude artifact kept as `.html` loses nothing but must be downloaded to view — mention that.
5. **The original defeats redaction.** If step 2 codenamed or redacted anything, the untouched original still contains it, and the checker will BLOCK it. Explain this rather than working around it; the Markdown conversion is the shareable version.
6. Continue with `add` steps 7–10 (indexes, pre-commit check, commit, push). The pre-commit check covers the Markdown and any attachment.

## Doc trigger

Applies when this skill is loaded in a session doing other work. Milestones worth documenting: a feature or fix completed, a design or architecture decision made, a bug root-caused, a setup/deploy/runbook procedure worked out, an integration or API contract settled.

- `manual`: never raise docs unprompted.
- `suggest`: at a milestone, say in one line what could be documented and where (`<project>/decisions/…`), and ask. Offer once per milestone; if declined, don't repeat. On yes, run `add`.
- `auto`: run `add` at the milestone, then report file, commit and push status in one line.
- Never trigger on trivial edits, mid-task states, or work that is still being reverted or reworked.
- A direct request ("document this", `/codebase-docs add`) always works in every mode.
- The user can change the mode in plain words ("switch to auto", "stop suggesting"); update `docTrigger` in `config.json` and confirm.

## find

Pull first (`git -C <clonePath> pull --rebase`); if the pull fails or there is no network, continue on the local copy and say the results may be stale. Search file names first, then content (`git -C <clonePath> ls-files | grep -i`, then `grep -rniI`), scoped to the current project's folder first, then the whole repo. Report up to ~10 hits as `path — one-line why it matches`, and offer to open or summarize the best one.

## sync / push

- `sync`: `git -C <clonePath> pull --rebase`; on conflict stop and explain, never force. Then, if there are unpushed commits, continue as `push`.
- `push`: if nothing is unpushed, say so. Otherwise follow `add` step 9 (range-mode check, confidentiality summary or push confirmation per policy, `branch-and-pr` handling), then `git push`. A BLOCK anywhere in the range stops the push and is reported. Never `--force`.

## Conventions file

`.codebase-docs.md` in the docs repo states the rules in plain language so other machines and agents follow the same layout: folder-per-project, naming, templates, index maintenance, what never goes in docs, plus the selected `harness` rules and `customRules`. Never include `confidentialNames`. Update it whenever the structure or rules intentionally change; it is committed with the docs.

## Safety

- Always use absolute paths and `git -C <clonePath> ...`; never `cd` into the docs clone or rely on the current directory — the session is usually in another project. The clone is outside the session's folders, so expect a permission prompt the first time it is read or written.
- Only operate inside `clonePath`; never modify the project's code repo from this skill (reading it is fine).
- No force-push, no history rewrites, no deleting committed docs or branches without explicit approval.
- Push only the configured branch (or the `docs/<topic>` branch under `branch-and-pr`) to the configured remote.
- Docs may be shared; the pre-commit check is mandatory before every commit and push.
