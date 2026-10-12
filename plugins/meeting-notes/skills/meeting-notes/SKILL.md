---
description: Persistent memory for client meeting notes during project discovery. Ingests pasted notes into a standard format, answers questions with exact citations, and maintains a dated history of feature asks, decisions, and open questions per project. Stored in ~/.claude/meeting-notes/, never in the repo. Use whenever the user invokes /meeting-notes, shares meeting/call notes or a transcript to save, or asks what a client said, asked for, or decided — e.g. "save these notes", "what did the client say about X", "what's still open with <client>", "when did we decide Y".
argument-hint: "save [project] | ask <question> | history [topic] | open [project] | list | help"
---

# meeting-notes — durable memory for client meetings

Queryable memory for client meetings — built for the discovery phase, where
feature asks, decisions, and open questions accumulate across many calls and
must be answerable later with exact sources.

The skill has no memory of its own. All knowledge lives in plain markdown files
under the notes root; every operation reads from or writes to those files.

## Storage layout

Notes root: `~/.claude/meeting-notes/<project>/` where `<project>` is a short
kebab-case slug (e.g. `belina`, `acme-crm`).

```
~/.claude/meeting-notes/
└── <project>/
    ├── INDEX.md            # one line per meeting: date, title, key topics
    ├── OPEN-QUESTIONS.md   # rolling tracker of unanswered questions
    ├── DECISIONS.md        # decision log, append-only, supersessions linked
    └── meetings/
        └── YYYY-MM-DD-<slug>.md   # one file per meeting, raw notes preserved
```

Create the project directory and tracker files on first save. If the user
doesn't name a project and more than one exists, list the projects under the
notes root and ask which one — never guess.

## Operations

Parse the user's intent into one of these. `/meeting-notes` with no arguments →
show the project list and a one-line usage summary.

### save — ingest pasted notes

1. Determine the project and the meeting date. If the notes don't state a date,
   ask (don't default to today — notes are often saved days after the call).
2. Read `INDEX.md`, `OPEN-QUESTIONS.md`, and `DECISIONS.md` first. You need the
   current ID counters and open items to link new content correctly.
3. Normalize the raw notes into the meeting template below. Extraction rules:
   - **Feature asks** are things the client wants built or changed. Capture each
     as its own item, in the client's terms, even if vague — vagueness is itself
     information during discovery.
   - **Decisions** are anything agreed or concluded. If a decision reverses or
     narrows an earlier one, do NOT edit the old entry — add the new one and
     mark the old one `superseded by D-<n> (YYYY-MM-DD)`. The evolution of a
     requirement is exactly what this skill exists to preserve.
   - **Open questions** are things raised but not answered. If this meeting
     answers a previously open question, close it in `OPEN-QUESTIONS.md` with
     the answer and a reference to this meeting, and record the answer as a
     decision if it is one.
   - When something is ambiguous (an aside vs. a real ask), keep it — file it
     under the closest section with a `(?)` marker rather than dropping it.
4. Write the meeting file, then update `INDEX.md`, `OPEN-QUESTIONS.md`, and
   `DECISIONS.md` in the same pass.
5. Confirm to the user with a short digest: N feature asks, N decisions,
   N new open questions, N questions closed — with their IDs.

### ask — answer a question from stored notes

1. Search the project's files (grep across `meetings/`, plus the trackers).
2. Answer from what's written, and cite every claim: meeting date + section,
   e.g. `(2026-07-14, Feature Asks FA-12)`. The user relies on these citations
   with the client — an uncited or inferred answer is worse than "not recorded".
3. If the notes contradict across meetings, present both with dates — the later
   one is current, the earlier one is history worth surfacing.
4. If nothing matches, say so plainly and suggest the nearest related items.

### history — timeline

Render `INDEX.md` as a timeline: date, title, and the key decisions/asks per
meeting. For "history of X", trace one topic across meetings chronologically,
including supersessions.

### open — outstanding items

List unresolved entries from `OPEN-QUESTIONS.md` (and unchecked action items if
asked), grouped by meeting of origin, oldest first — stale questions are the
ones about to fall through.

## IDs

Sequential per project, never reused: `FA-<n>` feature asks, `D-<n>` decisions,
`Q-<n>` open questions. Continue numbering from the highest existing ID (scan
the trackers before assigning). IDs make cross-references stable: "Q-3 answered
→ D-9" survives any rewording.

## Meeting file template

```markdown
# <Short title> — YYYY-MM-DD

**Project:** <project> · **Attendees:** <names, client vs. our side if known>

## Summary
2–4 sentences: what the call was about and what moved.

## Feature Asks
- **FA-<n>:** <ask, in the client's terms> — <context/constraints if given>

## Decisions
- **D-<n>:** <what was agreed> <(supersedes D-<m>) if applicable>

## Open Questions
- **Q-<n>:** <question> — waiting on <who, if known>

## Action Items
- [ ] <owner> — <item>

## Raw Notes
<the pasted notes, verbatim>
```

Keep the raw notes verbatim at the bottom of every meeting file. The structured
sections are an interpretation; the raw text is the evidence when a citation is
challenged.

## Tracker formats

`INDEX.md` — one row per meeting, newest last:

```markdown
| Date | Meeting | Key topics | File |
|------|---------|-----------|------|
| 2026-07-14 | Discovery call #3 | payments, onboarding | meetings/2026-07-14-discovery-3.md |
```

`OPEN-QUESTIONS.md` — open items on top, closed below:

```markdown
## Open
- **Q-7** (2026-07-14): Which payment providers must v1 support? — waiting on client
## Closed
- **Q-3** (2026-07-01 → 2026-07-14): SSO required? → Yes, Google only → D-9
```

`DECISIONS.md` — append-only:

```markdown
- **D-9** (2026-07-14): SSO in v1 is Google-only. (answers Q-3)
- **D-4** (2026-07-01): ~~Invoicing out of scope for v1.~~ superseded by D-11 (2026-07-21)
```
