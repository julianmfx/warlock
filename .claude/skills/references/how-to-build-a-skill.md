# How to Build a Skill for Warlock
> Consult this before creating or editing any skill in `.claude/skills/`.

---

## What a skill is

A folder containing a `SKILL.md` file (required) plus optional subdirectories:

```
your-skill-name/       ← kebab-case, no spaces, no capitals
├── SKILL.md           ← required, exact spelling, case-sensitive
├── scripts/           ← optional: Python, Bash scripts
├── references/        ← optional: docs loaded on demand
└── assets/            ← optional: templates, fonts, icons
```

**No `README.md` inside the skill folder.** All docs go in `SKILL.md` or `references/`.

---

## YAML frontmatter — the most important part

Claude decides whether to load your skill based on this block alone. Get it right.

```yaml
---
name: your-skill-name
description: What it does. Use when user says "[trigger phrase 1]", "[trigger phrase 2]", or asks to "[action phrase]".
---
```

### Rules

| Field | Rule |
|---|---|
| `name` | kebab-case only — no spaces, no capitals, no underscores |
| `description` | Must include WHAT it does AND WHEN to use it (trigger phrases). Under 1024 chars. No XML tags (`<` or `>`). |
| `license` | Optional. Use `MIT` or `Apache-2.0` for open skills. |
| `metadata` | Optional. Suggested keys: `author`, `version`. |

### Description formula

```
[What it does] + [When to use it] + [Key capabilities]
```

**Good:**
```yaml
description: End-of-session spec consolidation for Warlock. Reviews what was built,
  updates all .specs/ files, and prepares the project for the next session.
  Use when the user types /dream, says "wrap up", "close the session", or "end of session".
```

**Bad — missing triggers:**
```yaml
description: Creates sophisticated documentation systems.
```

**Bad — too vague:**
```yaml
description: Helps with projects.
```

### Security: forbidden in frontmatter
- XML angle brackets `< >`
- Skills named `claude-*` or `anthropic-*` (reserved)

---

## SKILL.md body structure

After the frontmatter, write instructions in Markdown. Use this template:

```markdown
# Skill Name

## Steps (or Instructions)

### 1. [First step]
Clear, specific description. Name exact files, commands, and expected outputs.

### 2. [Second step]
...

---

## Edge Cases

**[Scenario that could fail]:**
- What to do instead
- How to detect it

---

## Example

User says: "[typical invocation]"

Actions:
1. ...
2. ...

Result:
[what the user sees]
```

---

## Writing good instructions

### Be specific, not vague

```
# Bad
Validate the data before proceeding.

# Good
Run `python scripts/validate.py --input {filename}`.
If validation fails, common issues:
- Missing required fields (add them to the CSV)
- Invalid date formats (use YYYY-MM-DD)
```

### Put critical instructions at the top
Use `## CRITICAL` or `## Important` headers. Claude reads top-down; buried instructions get missed.

### Use progressive disclosure
Keep `SKILL.md` under ~5,000 words. Move detailed docs to `references/` and link to them:
```
Before proceeding, consult `references/api-patterns.md` for rate limiting guidance.
```

### Include error handling
Every non-trivial step should say what to do when it fails.

---

## Calling subagents from a skill

Skills can instruct Claude to spawn subagents via the Agent tool. Use this for:
- Independent parallel work (e.g. a safety scan while reading specs)
- Isolating risky operations (e.g. scanning for secrets before writing files)
- Work that should not pollute the main context window

Pattern:
```
Spawn a subagent with this prompt:
> [Self-contained prompt — include all context the subagent needs]

If the subagent reports [X]: [blocking action]
If the subagent reports [Y]: [continue action]
```

The subagent has no memory of the parent conversation — give it everything it needs inline.

---

## Checklist before saving a new skill

**Structure**
- [ ] Folder name is kebab-case
- [ ] File is named exactly `SKILL.md`
- [ ] YAML frontmatter has `---` delimiters top and bottom
- [ ] No `README.md` inside the folder

**Frontmatter**
- [ ] `name` matches folder name, kebab-case only
- [ ] `description` includes WHAT the skill does
- [ ] `description` includes WHEN to use it (trigger phrases users would actually say)
- [ ] No XML tags (`<` `>`) anywhere in frontmatter
- [ ] Under 1024 characters

**Body**
- [ ] Steps are numbered and specific
- [ ] Each step names exact files, commands, or outputs
- [ ] Edge cases section covers what can go wrong
- [ ] At least one Example section showing invocation → result

**Safety (if skill writes files or calls external tools)**
- [ ] Blocking safety check runs before any write operation
- [ ] CRITICAL findings stop execution; user must resolve before continuing
- [ ] WARNING findings are shown but do not block

---

## Patterns worth reusing

### Sequential workflow (steps depend on each other)
Number every step. Name what each step produces. Reference outputs by name in the next step.

### Safety gate (before writing or committing)
Spawn a read-only subagent to scan for secrets/vulnerabilities first. Block on CRITICAL, warn on WARNING, proceed silently on CLEAR.

### Iterative refinement (quality loop)
Define explicit done criteria. Cap the number of iterations. Always finalize — never leave in a draft state.

---

## What NOT to put in a skill

- README.md inside the skill folder
- Speculative instructions ("you might want to...")
- Instructions that duplicate what Claude already knows
- More than ~5,000 words in `SKILL.md` — move extras to `references/`

---

*Last updated: 2026-04-30 — synthesized from Anthropic's Complete Guide to Building Skills and Warlock session experience.*
