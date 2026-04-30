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

### 2. Inspect what changed this session
Run `git diff HEAD~1 HEAD --stat` and `git log --oneline -10` to understand what was committed.
If there are uncommitted changes, run `git diff --stat` and `git status` as well.

### 3. Update `.specs/plan.md`
- Mark completed phase steps with `[x]`
- If any design decision changed during the session, update the relevant section
- Do not add speculative steps — only reflect what actually shipped or was explicitly decided

### 4. Update `.specs/agents.md`
- Update agent status column for any agent that was created, modified, or tested
- If new tools were added to an agent, add them to the tools section
- If the base Agent interface changed, update the interface section

### 5. Rewrite `.specs/warlock_session.md`
This file is the single source of truth for resuming work. Rewrite it completely with:

**What Warlock is** — keep this section unchanged unless the vision changed

**What we have built so far** — full list of every file that exists, with a one-line description and the key methods/classes in it. Include actual code snippets for the most recent additions.

**What we were about to build next** — the exact next step: filename, class/function name, and the code we were about to type. Make it specific enough that a cold session can start immediately without re-derivation.

**Project structure** — current file tree with `✓ done` or `← next` markers

**Principles** — keep as-is unless something changed

### 6. Print a session summary
After updating all files, output a short summary to the conversation:

```
Session closed.

Built:
- <bullet per thing shipped>

Specs updated:
- plan.md   — <what changed>
- agents.md — <what changed>
- warlock_session.md — <what changed>

Next session starts at:
→ <exact next step, file and action>
```

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

Next session starts at:
→ Create warlock/agent.py — Agent class with __init__ and describe()
```
