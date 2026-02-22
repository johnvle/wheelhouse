# Ralph Agent Instructions

## Your Task

1. Read `.ralph/prd.json`
2. Read `.ralph/progress.txt`
   (check Codebase Patterns first)
3. Check you're on the correct branch
4. Run `git log --oneline` and collect every story ID
   that already has a commit matching `feat: US-XXX`
5. Pick the highest priority story whose ID is
   NOT in the completed set from step 4
6. Implement that ONE story
7. Run typecheck and tests
8. Update AGENTS.md files with learnings
9. **COMMIT** with EXACTLY this format: `feat: [ID] - [Title]`
   - This commit is HOW progress is tracked — if you
     don't commit, the story will be re-attempted
   - The commit message MUST start with `feat: US-XXX`
     (matching the story ID) for detection to work
10. Append learnings to progress.txt. If blocked, add tag and info to progress.txt as well.

## Progress Format

APPEND to progress.txt:

## [Date] - [Story ID]
- What was implemented
- Files changed
- **Learnings:**
  - Patterns discovered
  - Gotchas encountered

## Critical Rules
- Implement exactly ONE story, then STOP
- After committing, do NOT pick another story
- After committing, output a brief summary of what you did and EXIT
- Do NOT continue to the next story — the next iteration will handle it


---

## Codebase Patterns

Add reusable patterns to the TOP 
of progress.txt:

## Codebase Patterns
- Migrations: Use IF NOT EXISTS
- React: useRef<Timeout | null>(null)

## Stop Condition

If EVERY story ID in prd.json has a matching
`feat: US-XXX` commit in `git log --oneline`, reply:
<promise>COMPLETE</promise>

Otherwise end normally.