# Decision records

One short note per meaningful choice: what was chosen, what else was considered, and why.
This is the learning log, and it shows reviewers how the project was reasoned about.

Name files `NNNN-short-title.md` and copy the template below.

## The build loop (run it for every step)

1. **Explain before building.** Ask: "Explain [concept] like I'm a junior data engineer.
   What problem does it solve, and what goes wrong without it?"
2. **Build with AI.** Let the assistant write it.
3. **Explain it back.** Say in your own words what the code does and why, and ask to be corrected.
4. **Break it on purpose.** Duplicate an event, delete a row, make a test fail.
5. **Write a decision record** here.

## Template

```markdown
# NNNN. Title

- Status: Proposed | Accepted | Superseded by NNNN
- Date: YYYY-MM-DD

## Context
What problem are we solving? What constraints matter?

## Decision
What we chose.

## Alternatives considered
- Option A: why not
- Option B: why not

## Consequences
What gets easier, what gets harder, what we'd revisit.
```
