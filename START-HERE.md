# Starting Diyneco in Claude Code

## What is in this folder

| Path | What it is |
| --- | --- |
| `CLAUDE.md` | Project memory. Claude Code reads it automatically at the start of every session in this folder. |
| `PHASE-1-PROMPT.md` | The kickoff instructions for Phase 1 (foundation). |
| `docs/00-build-spec.md` | Your original 82-section brief. |
| `docs/01-platform-foundation.txt` | Architecture decisions and the phase plan. |
| `docs/02-api-specification.md` | Every endpoint, permission and error code. |
| `docs/03-database-specification.md` | The full PostgreSQL schema. |
| `docs/04-security-and-compliance.md` | Security design, role matrix, POPIA, VAT, PCI. |
| `docs/05-operations-runbooks.txt` | Environments, config, incidents, backups, daily close. |
| `docs/reference/prototype.html` | The clickable prototype, for reference only. |
| `brand/` | Logo and icon drafts. |

## Steps

1. Unzip this folder where you keep code, for example `~/code/diyneco`.
2. In a terminal inside it, run `git init` and make a first commit so every change Claude makes is reviewable.
3. Make sure Docker Desktop (or Docker Engine), Python 3.12 and Node 20+ with pnpm are installed.
4. Start Claude Code in the folder: `claude`.
5. Switch to plan mode (press Shift+Tab until it shows plan mode), then paste:

```
Read CLAUDE.md and PHASE-1-PROMPT.md, then follow PHASE-1-PROMPT.md. Start with Step 1: give me the plan and wait for my approval.
```

6. Review the plan. Approve it, or ask for changes.
7. Let it build. When it stops at the end of Phase 1, check the results it reports, run the tests yourself, and commit.
8. For each later phase, start a fresh session and say, for example: "Read CLAUDE.md and docs/PROGRESS.md. Plan Phase 2 from the phase table in docs/01-platform-foundation.txt, then wait for my approval."

## Before production

- Have an SA attorney review the POPIA sections and a registered tax practitioner review the VAT and invoicing rules in `docs/04-security-and-compliance.md`.
- Commission a clean SVG logo master and exact brand colours.
- Choose the hosting provider and Supabase region.
