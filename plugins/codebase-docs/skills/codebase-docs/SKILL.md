---
description: Store and find project documentation in one central git docs repo instead of scattered Google Docs/Drive folders. Use when the user types /codebase-docs — "/codebase-docs init" links the repo and records rules, "/codebase-docs bootstrap" drafts first docs for a project from its code, "/codebase-docs add <what>" writes or files a doc into the right project folder, "/codebase-docs find <query>" locates docs, "/codebase-docs sync" pulls/pushes, "/codebase-docs status|config|help" manage it. Also use when the user asks to document, save docs for, or find docs of the project they are working on.
argument-hint: "init | bootstrap [project] | add [what] [--project <name>] | find <query> | sync | push | status | config | help"
---

# codebase-docs — one git repo for all project documentation

Docs for every project live in a single git repo the user owns. This skill links that repo, learns its structure, files new docs under the right project folder (adapting the structure when the project needs it), and pushes according to the user's policy.

## Storage

```
~/.claude/codebase-docs/config.json   # settings, outside any repo, never committed
<clonePath>/                         # local clone of the docs repo (default ~/Projects/codebase-docs)
<clonePath>/.codebase-docs.md         # in-repo conventions file, committed (see "Conventions file")
```

`config.json`:

```json
{
  "repo": "git@github.com:user/docs.git",
  "clonePath": "/Users/me/Projects/codebase-docs",
  "branch": "main",
  "pushPolicy": "ask",
  "docTrigger": "suggest",
  "projectMap": { "<git-remote-or-folder-name>": "<folder-in-docs-repo>" },
  "harness": ["no-secrets", "folder-per-project", "kebab-case-names"],
  "confidentialNames": { "Real Client Name": "codename" },
  "customRules": ["free-text rules added at the end of init"]
}
```

- `pushPolicy`: `ask` (default — show what will be pushed, wait for yes), `auto` (commit + push right after each doc write), `manual` (commit only locally; push only on `/codebase-docs push`).
- `projectMap` remembers which code project maps to which docs folder so it is never re-asked.
- `docTrigger`: when a doc gets created — `manual` (only on `/codebase-docs add` or an explicit request), `suggest` (default — at a milestone, offer to document it and write nothing until the user agrees), `auto` (write and commit at a milestone, push per `pushPolicy`). The user can always ask for a doc directly, whatever the mode.
- Read `config.json` at the start of every command except `init`/`help`. If missing, say so and run `init`.

## Commands

| Input | Action |
|---|---|
| `init` | Link the repo, learn structure, pick harness rules, set push policy |
| `bootstrap [project]` | One-time: draft the initial docs for a project from its code, after you approve the plan |
| `add [what] [--project <name>]` | Write or file a doc into the right folder (default verb when the user just describes docs to write) |
| `find <query>` | Search the docs repo and report matching files |
| `sync` | `git pull --rebase`, then push if there are unpushed commits and policy allows |
| `push` | Push pending commits now (confirm per policy) |
| `status` | Linked repo, branch, uncommitted/unpushed changes, current project's folder |
| `config` | Show config; re-open the harness checklist, change `docTrigger`/`pushPolicy`, or edit any field |
| `help` | Print this table and one example |

## init

Ask, in this order (use AskUserQuestion where choices are fixed; plain questions for free text). Skip anything already in config when re-running; show current values and ask what to change.

1. **Repo** — URL of the docs git repo, or a path to an existing local clone.
2. **Clone location** — a fixed absolute path, independent of the current directory, so it works the same from inside any project's session. Default `~/Projects/codebase-docs`; never clone inside the current project's working tree (that would nest a repo in the project's repo). If the path exists and its `origin` matches the repo, reuse it; if it exists and differs, stop and ask.
3. **Write access check** — after cloning, run `git push --dry-run` (or `git ls-remote` plus a dry-run push). If it fails, report the exact error and stop; don't proceed with a read-only repo.
4. **Push policy** — `ask` (recommended) / `auto` / `manual`.
   **Doc trigger** — `suggest` (recommended: offer at milestones, write on yes) / `manual` (only when asked) / `auto` (write at milestones without asking; warn that it works best with `no-secrets` and `branch-and-pr` ticked).
5. **Harness (rules)** — let the user pick which guidelines apply, then add custom ones. Use **two AskUserQuestion calls (max four questions each)** covering the six groups below, one multi-select question per group — first call: Content safety, Confidentiality, Code policy, Structure; second call: Format, Workflow (each option is a catalog id; mark the recommended ones). Preselect nothing silently: anything not ticked is off. On re-run, show current selections and ask what to change.
   If `nda-safe` or `anonymize-clients` is ticked, also ask for the client/partner/vendor names (and codenames to use instead) that must never appear; store them in `config.json` as `confidentialNames` (kept on the user's machine only, never written to the docs repo).
   Then ask one final free-text question: **"Any custom rules not covered above?"** (empty = none). Store the ticked ids in `harness` and the free text, one rule per entry, in `customRules`.

   **Harness catalog**

   | Group | id | Rule |
   |---|---|---|
   | Content safety | `no-secrets` *(recommended)* | Never write secrets, tokens, keys or credentials; refer to where they live (vault, env var name) |
   | | `no-pii` *(recommended)* | No customer data or personal info; use placeholders/anonymized examples |
   | | `no-internal-urls` | Don't include internal hostnames, IPs, or account IDs |
   | | `public-safe` | Write as if the repo could become public |
   | Confidentiality | `nda-safe` *(recommended)* | Nothing covered by an NDA or client confidentiality: no client-provided materials, contract terms, pricing, non-public roadmaps or third-party confidential info |
   | | `anonymize-clients` | Refer to clients, partners and vendors by codename/placeholder, never by real name |
   | | `no-third-party-content` | Don't paste copyrighted or licensed third-party material (vendor docs, specs, articles); summarize in own words and link |
   | | `confidentiality-review` *(recommended)* | Before any push, show a confidentiality summary of the diff (names, numbers, URLs, code blocks) and get explicit approval, whatever `pushPolicy` says |
   | Code policy | `no-source-code` *(recommended)* | **Strict:** no source code or code files in the repo — only prose docs. Code may appear only as short illustrative snippets inside Markdown, never as files |
   | | `snippet-limit` *(recommended)* | Snippets are samples: at most 30 lines, sanitized, labeled "Sample", never a verbatim copy of a proprietary module |
   | | `link-not-copy` | Point to code by repo, path and commit permalink instead of pasting it |
   | | `allowed-files-only` | Only these file types may be committed: `.md`, `.mdx`, and images (`.png`, `.jpg`, `.svg`); everything else is blocked |
   | Structure | `folder-per-project` *(recommended)* | One top-level folder per project, named after it in kebab-case |
   | | `index-readmes` *(recommended)* | Keep each project `README.md` and the root `README.md` indexes up to date |
   | | `adr-decisions` | Record decisions as ADRs in `decisions/YYYY-MM-DD-title.md` (context, decision, consequences) |
   | | `dated-notes` | Working notes go in `notes/YYYY-MM-DD-title.md` |
   | Format | `markdown-only` *(recommended)* | Markdown files only; link to external files instead of committing binaries |
   | | `kebab-case-names` *(recommended)* | File and folder names are lowercase kebab-case |
   | | `frontmatter` | Every doc starts with frontmatter: `title`, `owner`, `updated`, `status` |
   | | `mermaid-diagrams` | Diagrams are Mermaid code blocks, not images |
   | Workflow | `link-code-repo` | Each project README links its code repo(s) |
   | | `confirm-restructure` *(recommended)* | Announce and get approval before moving or renaming existing docs |
   | | `one-line-commits` | One-line commit messages, no body |
   | | `branch-and-pr` | Push to a `docs/<topic>` branch and open a PR instead of pushing to the main branch |

   Each group has four options, which fits AskUserQuestion's limit. The "Other" box on every question is where a one-off tweak can go; fold it into `customRules`.
6. **Learn the repo** — read its `README.md`, `.codebase-docs.md` if present, and `ls` two levels deep. Summarize the structure back in a few lines (top-level layout, how projects are organized, templates found) and ask the user to confirm or correct. If the repo is empty, propose a layout (below) and ask before creating it.

Then write `config.json`, create/refresh the conventions file in the repo if missing, and tell the user how to use `add`.

### Proposed layout for an empty repo

```
README.md              # index: one line per project, links to its folder
.codebase-docs.md       # conventions
<project>/
  README.md            # what the project is, links to docs below
  overview.md
  architecture.md
  decisions/           # ADR-style, YYYY-MM-DD-title.md
  runbooks/
  notes/               # dated working notes
```

Only create subfolders when there is something to put in them.

## bootstrap

Opt-in, explicit only — never triggered by `docTrigger`. Drafts the first set of docs for a project that has none yet, from its code and existing READMEs.

1. **Resolve the project and its docs folder** exactly as `add` step 1. If the folder already has docs, say so and ask whether to extend (fill gaps only) or stop; never overwrite existing files.
2. **Read the code project proportionally**, in the working directory (or the path given): README, manifests, entry points, config/infra files, directory layout, tests' names, CI workflows. Fan out Explore agents for a large repo. Skip `node_modules`, `.git`, build output, caches and generated code. Note only names and purposes — you are describing the system, not copying it.
3. **Propose a plan before writing anything**: the list of files to create (default: `README.md`, `overview.md`, `architecture.md`, `setup.md`; add `decisions/` or `runbooks/` only when the code evidence supports them), with one line on what each covers and what source it draws from. Show it with the harness rules that will apply, then wait for approval or edits. Don't start writing without a yes.
4. **Write the docs** in prose: purpose, tech stack, components and how they interact, data flow, how to run/build/deploy, environments, external dependencies, known gaps. Describe behavior and structure; use at most a few short labeled sample snippets (a command, a config shape) within the harness limits; link to code by repo, path and commit (`link-not-copy`) rather than pasting it. Never invent: anything not evident from the code goes in as `TODO:` for the user to fill. Redact secrets, internal URLs and confidential names per the harness.
5. **Run the pre-commit check** (see `add`), update the project and root README indexes, and commit once with a one-line message (`docs(<project>): bootstrap initial docs`).
6. **Push per policy** and report the files created, anything left as `TODO:`, and a short list of questions the code couldn't answer, so the user can have them filled in.

## add

1. **Resolve the project**
   - `--project` wins. Else look up the current repo in `projectMap` (key: git remote URL, falling back to the folder basename).
   - Else match the git remote/folder name against top-level folders in the docs repo (case- and separator-insensitive). One clear match → use it and record it in `projectMap`. Several or none → ask: pick an existing folder or create a new one (name it after the project, kebab-case).
   - Not inside any git project and no `--project` → ask.
2. **Pull first** — `git -C <clonePath> pull --rebase`. If the tree is dirty or the pull conflicts, stop and report; never discard changes.
3. **Apply the harness** — treat every id in `harness` and every entry in `customRules` as a hard constraint on what you write, where you put it, and how you commit/push. If a request conflicts with a ticked rule, say so and ask rather than break it. `branch-and-pr` overrides `pushPolicy` for the target branch.
4. **Understand the existing structure** for that project: list its folder, read its `README.md` and neighbours of the same kind so new content matches their format and depth. Follow the repo's templates and the user's `rules`.
5. **Decide placement.** Put the doc where the existing convention says (e.g. decisions → `decisions/`). If the project needs structure the repo lacks, adapt it: add a folder, split a doc, or move/rename files — keeping the project's `README.md` index and the root `README.md` index accurate. State any restructure (especially moves/renames) before doing it; never delete docs without explicit approval.
6. **Write the doc** from what the user described and from what the session actually knows (code, decisions made, commands run). Don't invent facts; mark gaps as `TODO:` or ask. Never include secrets, tokens, or credentials — redact and refer to where they live instead.
7. **Update indexes** (project README, root README) with the new entry.
8. **Pre-commit check** — run before every commit; any failure stops the commit and is reported with file and line:
   - `git -C <clonePath> diff --cached --name-only`: with `no-source-code` or `allowed-files-only`, block any staged file outside the allowed doc types (`.md`, `.mdx`, `.png`, `.jpg`, `.svg`) — notably source files (`.ts`, `.js`, `.py`, `.java`, `.go`, `.sh`, `.sql`, `.tf`, `.yml`, `.json`, lockfiles, etc.).
   - With `no-source-code`/`snippet-limit`: scan Markdown fenced code blocks — block blocks over 30 lines, blocks not labeled as a sample, and anything that looks like a whole file or module copied verbatim from the code repo (compare against the project's code if it is available locally).
   - With `no-secrets`: scan for key/token/password patterns (`AKIA…`, `-----BEGIN … KEY-----`, `ghp_…`, `xox…`, `password=`, connection strings); with `no-internal-urls`: internal hosts, private IPs, AWS account IDs.
   - With `nda-safe`/`anonymize-clients`: flag client or vendor names the user listed as confidential, contract/pricing language, and client-supplied material; ask before keeping anything flagged.
   - A ticked rule is **not overridable in the moment**. If the user asks for something it forbids ("just push the file"), explain which rule blocks it and that they can change the rule via `/codebase-docs config`; don't bypass it.
9. **Commit** with a one-line message (e.g. `docs(<project>): add <topic>`) — a short descriptive subject; with `one-line-commits` ticked, never add a body. The commit is part of the user's request to store docs here.
10. **Push per policy**
   - With `confidentiality-review`: always show the confidentiality summary and get explicit approval first, even under `auto`.
   - `ask`: show `git diff --stat` of the commit(s) and the target branch, ask before pushing.
   - `auto`: push immediately and report.
   - `manual`: don't push; say it is committed locally and `/codebase-docs push` will push it.
11. Report: file path(s) relative to the repo, commit hash, push status, and a link to the file on the remote when the host is GitHub (`<repo-url>/blob/<branch>/<path>`).

## Doc trigger

Applies when this skill is loaded in a session that is doing other work. Milestones worth documenting: a feature or fix completed, a design or architecture decision made, a bug root-caused, a setup/deploy/runbook procedure worked out, an integration or API contract settled.

- `manual`: never raise docs unprompted.
- `suggest`: at a milestone, say in one line what could be documented and where (`<project>/decisions/…`), and ask. Offer once per milestone; if declined, don't repeat. On yes, run `add`.
- `auto`: run `add` at the milestone, then report the file, commit and push status in one line.
- Never trigger on trivial edits, mid-task states, or work that is still being reverted or reworked.
- A direct request ("document this", `/codebase-docs add`) always works in every mode.
- The user can change the mode at any point in plain words ("switch to auto", "stop suggesting"); update `docTrigger` in `config.json` and confirm.

## find

Search the clone with grep/glob (file names first, then content; scope to the current project's folder first, then the whole repo). Pull first so results are current. Report up to ~10 hits as `path — one-line why it matches`, and offer to open or summarize the best one.

## sync / push

- `sync`: `git pull --rebase`; on conflict stop and explain, never force. Then, per policy, offer to push unpushed commits.
- `push`: re-run the pre-commit checks over every unpushed commit (`git diff origin/<branch>..HEAD`); a failure blocks the push. Then show `git log origin/<branch>..HEAD --oneline` and `git diff --stat origin/<branch>..HEAD`, confirm (unless `auto`), then `git push`. Never `--force`.

## Conventions file

`.codebase-docs.md` in the docs repo records the structure rules so the layout stays consistent even for other machines/agents: folder-per-project, naming, templates, index maintenance, what never goes in docs. Create it from the selected `harness` rules and `customRules` (written out in plain language, so other machines and agents follow the same rules); update it whenever the structure intentionally changes. It is committed with the docs.

## Safety

- Always use absolute paths and `git -C <clonePath> ...`; never `cd` into the docs clone or rely on the current directory, since the session is usually in another project. The clone is outside the session's folders, so expect a permission prompt the first time it is read or written.
- Only operate inside `clonePath`; never touch the project's code repo from this skill.
- No force-push, no history rewrites, no deleting docs or branches without explicit approval.
- Push only the configured branch to the configured remote.
- Docs may be shared; scan what you write for secrets/PII before committing.
