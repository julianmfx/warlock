---
name: dream
description: End-of-session spec consolidation for Warlock. Reviews what was built, updates all .specs/ files, and prepares the project for the next session. Use when the user types /dream, says "wrap up", "close the session", "update the specs", or "end of session".
---

# /dream — End-of-Session Spec Consolidation

Run this at the end of every coding session. It reviews what was built, reconciles the `.specs/` folder, and prepares the project for the next session.

## Steps

### 1. Read the current specs
Read all three files in `.specs/`:
- `.specs/plan.md`
- `.specs/agents.md`
- `.specs/warlock_session.md`

### 2. Run the safety scan (blocking gate)
Spawn a subagent to scan `.specs/` and `.claude/` for security issues before any spec file is written or committed.

Use the Agent tool with this prompt:

> You are a security scanner. Search the directories `.specs/` and `.claude/` (excluding `.claude/skills/`) for any content that should never be committed. Report findings grouped by severity: CRITICAL (stop immediately) and WARNING (review before committing).
>
> Scan for:
> - API keys, tokens, secrets (patterns: `sk-`, `key =`, `token =`, `secret =`, `password =`, `Bearer `, `AIza`, `AKIA`, any 40+ character hex/base64 strings)
> - Hardcoded credentials or connection strings (database URLs with passwords, `postgresql://user:pass@`, etc.)
> - Private keys or certificate content (`-----BEGIN`, `-----END`)
> - Email addresses in unexpected places (outside of known author fields)
> - Absolute local file paths that expose directory structure (e.g. `/home/username/`)
> - Any line containing the word `PRIVATE`, `SECRET`, or `CONFIDENTIAL` in a value context
>
> For each finding report: file, line number, the offending content (redacted to first 20 chars), and severity.
> If nothing is found, output: `SCAN CLEAR — no sensitive content detected.`

**If the subagent reports any CRITICAL findings:** stop the dream sequence, do not update any spec files, and show the findings to the user with: `Safety scan blocked the dream. Fix the following before closing the session:`

**If only WARNINGs:** show them to the user, then continue the dream sequence.

**If SCAN CLEAR:** continue without comment.

### 3. Inspect what changed this session
Run `git diff HEAD~1 HEAD --stat` and `git log --oneline -10` to understand what was committed.
If there are uncommitted changes, run `git diff --stat` and `git status` as well.

### 4. Update `.specs/plan.md`
- Mark completed phase steps with `[x]`
- If any design decision changed during the session, update the relevant section
- Do not add speculative steps — only reflect what actually shipped or was explicitly decided

### 5. Update `.specs/agents.md`
- Update agent status column for any agent that was created, modified, or tested
- If new tools were added to an agent, add them to the tools section
- If the base Agent interface changed, update the interface section

### 6. Rewrite `.specs/warlock_session.md`
This file is the single source of truth for resuming work. Rewrite it with:

**What Warlock is** — keep this section unchanged unless the vision changed

**What we have built so far** — full list of every file that exists. **Critical rule: for files that existed before this session, copy their description verbatim from the previous `warlock_session.md` — do not summarize, compress, or reword them.** Only write new descriptions for files that were added or significantly changed this session. Include actual code snippets for the most recent additions.

**What we were about to build next** — the exact next step: filename, class/function name, and the code we were about to type. Make it specific enough that a cold session can start immediately without re-derivation.

**Project structure** — current file tree with `✓ done` or `← next` markers

**Principles** — keep as-is unless something changed

### 7. Print a session summary
After updating all files, output a short summary to the conversation:

```
Session closed.

Built:
- <bullet per thing shipped>

Specs updated:
- plan.md   — <what changed>
- agents.md — <what changed>
- warlock_session.md — <what changed>

Removed from warlock_session.md:
- <section name> — <one line reason why it was removed or where the info now lives>

Next session starts at:
→ <exact next step, file and action>
```

**Rule:** only include the `Removed` section if something was actually removed. If nothing was removed, omit it entirely — do not print "Removed: nothing."

That's it. Warlock now dreams.

---

## Edge Cases

**No previous commit** (`HEAD~1` fails — first commit in repo):
- Skip `git diff HEAD~1 HEAD --stat`
- Use `git log --oneline -5` and `git show --stat HEAD` instead
- Describe what the first commit introduced

**No uncommitted changes and no new commits**:
- Still rewrite `warlock_session.md` to reflect current state accurately
- Note in the summary: "No new commits this session — specs verified and refreshed"

**`.specs/` directory doesn't exist yet**:
- Create all three files from scratch based on `CLAUDE.md` and current git state
- Do not fail silently — create the files

---

## Example

User says: `/dream`

Actions:
1. Read `.specs/plan.md`, `.specs/agents.md`, `.specs/warlock_session.md`
2. Run `git log --oneline -10` and `git diff HEAD~1 HEAD --stat`
3. Mark any completed steps `[x]` in `plan.md`
4. Update agent statuses in `agents.md`
5. Rewrite `warlock_session.md` with current state and exact next step

Result:
```
Session closed.

Built:
- warlock/memory.py — WarlockMemory class with dict/list backing

Specs updated:
- plan.md   — Memory marked [x] done
- agents.md — Base Agent status updated to "next"
- warlock_session.md — Full rewrite with memory.py code and next step pinned

Removed from warlock_session.md:
- "What an Agent needs" section — content folded into agent.py key concepts block
- "The 6 specialist agents" table — already covered in full in agents.md and plan.md

Next session starts at:
→ Create warlock/agent.py — Agent class with __init__ and describe()
```
