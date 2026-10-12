#!/usr/bin/env python3
"""codebase-docs pre-commit / pre-push check (stdlib only).

  precommit.py --clone DIR --config FILE [--mode staged|range] [--range REV|ALL]
               [--code DIR ...] [--message TEXT] [--summary]

staged: checks `git diff --cached` (contents read from the index).
range:  checks files and commit messages in REV (e.g. origin/main..HEAD);
        ALL = everything reachable from HEAD (first push, no remote branch yet).

Output lines: BLOCK / FLAG / MANUAL, then `RESULT PASS|FLAGS|FAIL`.
Exit: 0 clean, 1 any BLOCK, 2 FLAGs only. MANUAL lines are reminders for rules a
script can't judge; they never affect the exit code.
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile, zipfile

DOC_EXT = {'.md', '.mdx'}
IMG_EXT = {'.png', '.jpg', '.jpeg', '.svg'}
ALWAYS_OK = {'.gitignore', '.gitattributes', '.gitkeep'}
ATTACH_EXT = {'.pdf', '.docx', '.xlsx', '.pptx', '.csv', '.html'} | IMG_EXT
OFFICE_PARTS = re.compile(r'^(word/(document|header\d*|footer\d*|comments)|ppt/(slides/slide\d+|notesSlides/notesSlide\d+)|xl/(sharedStrings|worksheets/sheet\d+))\.xml$')
NAME_OK = {'README.md', '.codebase-docs.md', '.gitignore', '.gitattributes', '.gitkeep'}
INDEX_FILES = {'README.md', '.codebase-docs.md'}
SKIP_DIRS = {'.git', 'node_modules', 'dist', 'build', '.venv', 'venv', '__pycache__', '.next', 'target', 'vendor'}
MAX_BLOCK = 30
FENCE = re.compile(r'^\s*(```+|~~~+)\s*(\S*)')

SECRETS = [
    (r'AKIA[0-9A-Z]{16}', 'AWS access key'),
    (r'-----BEGIN [A-Z ]*PRIVATE KEY-----', 'private key'),
    (r'\bgh[pousr]_[A-Za-z0-9]{20,}', 'GitHub token'),
    (r'\bxox[abprs]-[A-Za-z0-9-]+', 'Slack token'),
    (r'\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.', 'JWT'),
    (r'(?i)\b(pass(word|wd)?|secret|api[_-]?key|token)\s*[=:]\s*[^\s<*`$\[{(]{4,}', 'credential assignment'),
    (r'\b[a-z][a-z0-9+.-]*://[^\s/:@]+:[^\s/@]+@', 'connection string with credentials'),
]
INTERNAL = [
    (r'\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b', 'private IP'),
    (r'(?<![\d.])\d{12}(?![\d.])', 'possible AWS account id'),
    (r'(?i)\b[a-z0-9-]+(\.[a-z0-9-]+)*\.(internal|corp|lan|intranet)\b', 'internal hostname'),
]
CONTRACT = re.compile(r'(?i:\b(pricing|contract terms?|statement of work|invoice|per[- ]seat)\b)|\b(SOW|SLA|NDA)\b')

MANUAL = {
    'no-pii': 'no customer data or personal info (use placeholders)',
    'public-safe': 'would this be fine if the repo became public?',
    'no-third-party-content': 'no pasted copyrighted/licensed material; summarize and link',
    'link-not-copy': 'code referenced by repo/path/commit, not pasted',
    'link-code-repo': "project README links its code repo(s)",
    'adr-decisions': 'decisions are ADRs (context, decision, consequences) in the repo\'s decisions location',
    'dated-notes': 'working notes are dated, in the notes location',
    'mermaid-diagrams': 'diagrams are Mermaid blocks, not images',
}


def git(clone, *args, check=False):
    r = subprocess.run(['git', '-C', clone, '-c', 'core.quotepath=false', *args],
                       capture_output=True, text=True)
    if check and r.returncode:
        sys.exit(f'git {" ".join(args)} failed: {r.stderr.strip()}')
    return r.stdout


def git_bytes(clone, *args):
    return subprocess.run(['git', '-C', clone, *args], capture_output=True).stdout


def attachment_text(data, ext):
    """Best-effort text of an attachment so it can be scanned; None = not scannable."""
    if ext in {'.html', '.csv', '.svg'}:
        return data.decode('utf-8', 'replace')
    if ext in {'.docx', '.pptx', '.xlsx'}:
        with tempfile.NamedTemporaryFile(suffix=ext) as t:
            t.write(data)
            t.flush()
            try:
                z = zipfile.ZipFile(t.name)
            except zipfile.BadZipFile:
                return None
            parts = [re.sub(r'<[^>]+>', ' ', z.read(n).decode('utf-8', 'replace')) for n in z.namelist() if OFFICE_PARTS.match(n)]
            return '\n'.join(parts)
    if ext == '.pdf' and shutil.which('pdftotext'):
        with tempfile.NamedTemporaryFile(suffix=ext) as t:
            t.write(data)
            t.flush()
            r = subprocess.run(['pdftotext', '-layout', t.name, '-'], capture_output=True, text=True)
            return r.stdout if r.returncode == 0 else None
    return None


def load_code(dirs):
    corpus = {}
    for d in dirs:
        for root, subs, files in os.walk(d):
            subs[:] = [s for s in subs if s not in SKIP_DIRS]
            for f in files:
                p = os.path.join(root, f)
                if os.path.splitext(f)[1].lower() in DOC_EXT | IMG_EXT:
                    continue
                try:
                    if os.path.getsize(p) > 500_000:
                        continue
                    txt = open(p, encoding='utf-8').read()
                except (OSError, UnicodeDecodeError):
                    continue
                lines = {l.strip() for l in txt.split('\n') if len(l.strip()) > 3}
                if lines:
                    corpus[p] = (lines, txt.strip())
    return corpus


def fenced_blocks(lines):
    out, i = [], 0
    while i < len(lines):
        m = FENCE.match(lines[i])
        if not m:
            i += 1
            continue
        ch = m.group(1)[0]
        close = re.compile(r'^\s*' + re.escape(ch) + r'{3,}\s*$')
        j = i + 1
        while j < len(lines) and not close.match(lines[j]):
            j += 1
        out.append((i, j, m.group(2).lower()))
        i = j + 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--clone', required=True)
    ap.add_argument('--config', required=True)
    ap.add_argument('--mode', choices=['staged', 'range'], default='staged')
    ap.add_argument('--range')
    ap.add_argument('--code', action='append', default=[])
    ap.add_argument('--message')
    ap.add_argument('--summary', action='store_true')
    a = ap.parse_args()

    clone = os.path.abspath(os.path.expanduser(a.clone))
    cfg = json.load(open(os.path.expanduser(a.config)))
    H = set(cfg.get('harness', []))
    names = cfg.get('confidentialNames', {}) if 'anonymize-clients' in H else {}

    if a.mode == 'staged':
        files = git(clone, 'diff', '--cached', '--name-only', '--diff-filter=AMR').split('\n')
        read = lambda p: git(clone, 'show', ':' + p)
        numstat = git(clone, 'diff', '--cached', '--numstat')
        msgs = [a.message] if a.message else []
    else:
        if not a.range:
            sys.exit('--range required with --mode range')
        if a.range == 'ALL':
            files = git(clone, 'ls-tree', '-r', '--name-only', 'HEAD').split('\n')
            msgs_raw = git(clone, 'log', '--format=%B%x00', 'HEAD')
            numstat = git(clone, 'diff', '--numstat', '4b825dc642cb6eb9a060e54bf8d69288fbee4904', 'HEAD')
        else:
            files = git(clone, 'diff', '--name-only', '--diff-filter=AMR', a.range, check=True).split('\n')
            msgs_raw = git(clone, 'log', '--format=%B%x00', a.range)
            numstat = git(clone, 'diff', '--numstat', a.range)
        read = lambda p: git(clone, 'show', 'HEAD:' + p)
        msgs = [m.strip('\n') for m in msgs_raw.split('\0') if m.strip()]
    files = [f for f in files if f]

    out = []
    def add(level, path, line, msg):
        out.append((level, path, line, msg))

    def scan_text(f, lines):
        for n, l in enumerate(lines, 1):
            if 'no-secrets' in H:
                for rx, d in SECRETS:
                    if re.search(rx, l):
                        add('BLOCK', f, n, d)
            if 'no-internal-urls' in H:
                for rx, d in INTERNAL:
                    if re.search(rx, l):
                        add('BLOCK', f, n, d)
            for name in names:
                if re.search(r'(?i)(?<!\w)' + re.escape(name) + r'(?!\w)', l):
                    add('BLOCK', f, n, f'confidential name "{name}"')
            if 'nda-safe' in H and CONTRACT.search(l):
                add('FLAG', f, n, 'contract/pricing language: keep or reword?')

    type_rules = H & {'no-source-code', 'markdown-only'}
    attach_on = 'allow-attachments' in H
    single = cfg.get('layout') == 'single'
    def is_attachment(f):
        parts = f.split('/')
        ext = os.path.splitext(f)[1].lower()
        return ext in ATTACH_EXT and ('attachments' in parts[1:-1] or (single and len(parts) >= 2))
    max_bytes = int(float(cfg.get('attachmentMaxMB', 10)) * 1024 * 1024)
    md_cache = {}
    allowed = DOC_EXT if 'markdown-only' in H else DOC_EXT | IMG_EXT
    code_dirs = [os.path.abspath(os.path.expanduser(c)) for c in a.code]
    code = load_code(code_dirs) if H & {'no-source-code', 'snippet-limit'} else {}
    def rel(p):
        d = next((d for d in code_dirs if p.startswith(d + os.sep)), None)
        return os.path.relpath(p, d) if d else os.path.basename(p)

    for f in files:
        base, ext = os.path.basename(f), os.path.splitext(f)[1].lower()
        parts = f.split('/')
        if attach_on and is_attachment(f):
            data = git_bytes(clone, 'show', (':' if a.mode == 'staged' else 'HEAD:') + f)
            if len(data) > max_bytes:
                add('BLOCK', f, 0, f'attachment is {len(data) / 1048576:.1f} MB (limit {max_bytes / 1048576:g} MB)')
            if 'kebab-case-names' in H and not re.fullmatch(r'[a-z0-9][a-z0-9.\-]*', base):
                add('BLOCK', f, 0, f'"{base}" is not lowercase kebab-case')
            top = parts[0]
            if top not in md_cache:
                mds = [x for x in git(clone, 'ls-files', '--', top + '/').split('\n') if x.lower().endswith(tuple(DOC_EXT))]
                md_cache[top] = '\n'.join(git(clone, 'show', ':' + x) for x in mds)
            if base not in md_cache[top]:
                add('BLOCK', f, 0, 'attachment is not linked from any Markdown page in its project (add a page with a summary and link)')
            txt = attachment_text(data, ext)
            if txt is None:
                if ext not in IMG_EXT:
                    add('FLAG', f, 0, 'content cannot be scanned here — read it and confirm it holds no secrets, client names or NDA material')
            else:
                scan_text(f, txt.split('\n'))
                if ext == '.html' and re.search(r'(?i)<script|<iframe|on\w+\s*=', txt):
                    add('FLAG', f, 0, 'HTML contains script/iframe/event handlers — confirm it is safe to store')
            continue
        if type_rules and base not in ALWAYS_OK and ext not in allowed:
            add('BLOCK', f, 0, 'file type not allowed (' + ('markdown-only' if 'markdown-only' in H else 'no-source-code') + ')')
            continue
        if 'kebab-case-names' in H:
            for seg in f.split('/'):
                if seg not in NAME_OK and not re.fullmatch(r'[a-z0-9][a-z0-9.\-]*', seg):
                    add('BLOCK', f, 0, f'"{seg}" is not lowercase kebab-case')
                    break
        if ext not in DOC_EXT:
            continue

        txt = read(f)
        lines = txt.split('\n')
        is_index = base in INDEX_FILES

        if 'frontmatter' in H and not is_index:
            m = re.match(r'^---\n(.*?)\n---\n', txt, re.S)
            keys = set(re.findall(r'^([A-Za-z_]+):', m.group(1), re.M)) if m else set()
            missing = {'title', 'owner', 'updated', 'status'} - keys
            if missing:
                add('BLOCK', f, 1, 'frontmatter missing: ' + ', '.join(sorted(missing)))

        if base != '.codebase-docs.md':
            scan_text(f, lines)

        if H & {'no-source-code', 'snippet-limit'}:
            for i, j, lang in fenced_blocks(lines):
                if lang == 'mermaid':
                    continue
                blk = lines[i + 1:j]
                if j >= len(lines):
                    add('BLOCK', f, i + 1, 'unclosed code fence')
                if 'snippet-limit' in H:
                    if len(blk) > MAX_BLOCK:
                        add('BLOCK', f, i + 1, f'code block is {len(blk)} lines (limit {MAX_BLOCK})')
                    prev = next((l for l in reversed(lines[:i]) if l.strip()), '')
                    if 'sample' not in (lines[i] + ' ' + prev).lower():
                        add('BLOCK', f, i + 1, 'code block not labeled "Sample"')
                nb = [l.strip() for l in blk if len(l.strip()) > 3]
                for p, (cl, _) in code.items():
                    hit = sum(1 for l in nb if l in cl)
                    if nb and hit >= 3 and hit / len(nb) >= 0.5:
                        add('BLOCK', f, i + 1, f'block copies {hit}/{len(nb)} lines of {rel(p)}')
            for p, (cl, whole) in code.items():
                if len(cl) >= 3 and whole in txt:
                    add('BLOCK', f, 0, f'contains the whole contents of {rel(p)}')

    if 'one-line-commits' in H:
        for m in msgs:
            if '\n' in m.strip():
                add('BLOCK', '(commit message)', 0, 'has a body: ' + m.split('\n')[0][:60])

    if a.summary:
        print('CONFIDENTIALITY SUMMARY')
        print('files:', len(files))
        for ln in numstat.strip().split('\n'):
            if ln:
                ad, de, p = ln.split('\t', 2)
                print(f'  +{ad} -{de}  {p}')
        urls, nums, blocks, previews = set(), set(), 0, []
        for f in files:
            if os.path.splitext(f)[1].lower() not in DOC_EXT:
                continue
            t = read(f)
            urls |= set(re.findall(r'https?://[^\s)>\]]+', t))
            nums |= set(re.findall(r'[$€£]\s?\d[\d,.]*|\b\d+(?:\.\d+)?\s?%', t))
            tl = t.split('\n')
            for i, j, lang in fenced_blocks(tl):
                blocks += 1
                previews.append(f'  {f}:{i + 1} ({j - i - 1} lines) {tl[i + 1].strip()[:70] if i + 1 < len(tl) else ""}')
        att = [f for f in files if attach_on and is_attachment(f)]
        print('attachments:', ', '.join(att) or 'none')
        print('code blocks:', blocks)
        for pv in previews:
            print(pv)
        print('URLs:', ', '.join(sorted(urls)[:20]) or 'none')
        print('amounts/percentages:', ', '.join(sorted(nums)[:20]) or 'none')
        print('confidential names found:', sum(1 for o in out if 'confidential name' in o[3]))
        print()

    for level, p, n, m in out:
        print(f'{level} {p}' + (f':{n}' if n else '') + f': {m}')
    for rid, text in MANUAL.items():
        if rid in H:
            print(f'MANUAL {rid}: {text}')
    for r in cfg.get('customRules', []):
        print(f'MANUAL custom: {r}')
    blocked = any(o[0] == 'BLOCK' for o in out)
    flagged = any(o[0] == 'FLAG' for o in out)
    print('RESULT', 'FAIL' if blocked else 'FLAGS' if flagged else 'PASS', f'({len(files)} file(s))')
    sys.exit(1 if blocked else 2 if flagged else 0)


if __name__ == '__main__':
    main()
