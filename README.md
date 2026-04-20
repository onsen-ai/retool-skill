# retool-skill

An agent skill for building, editing, and improving importable [Retool](https://retool.com) apps using ToolScript (RSX format). Compatible with [Claude Code](https://docs.anthropic.com/en/docs/claude-code), [Cursor](https://cursor.com), [Cline](https://cline.bot), [OpenCode](https://github.com/opencode-ai/opencode), and any coding agent that supports the [skills standard](https://github.com/vercel-labs/skills).

## What it does

This skill enables your coding agent to generate complete, importable Retool applications from natural language descriptions. It handles the mechanical and error-prone parts of ToolScript — validation, scaffolding, position math, query wiring — so the LLM focuses on creative and structural decisions.

### Three modes

- **NEW** — "Build me a Retool app for managing expenses" → scaffolds from template, customizes, validates, zips
- **EDIT** — "Add a search bar and status filter to my app" → understands existing structure, adds components, fixes positions
- **IMPROVE** — "Make this app production-ready" → audits against best practices, adds loading states, confirmation dialogs, event chains

### Works without a database

All 8 example apps include a **Setup Guide modal** with app-specific wiring instructions. Scaffolded apps (crud, master-detail, search-filter, advanced-crud) also include **inline mock data**. Tables and forms are fully populated with sample data on import — no database connection required to explore the app. When you're ready to connect your real database, the Setup Guide walks you through the steps, and removing the mock data is a one-line edit per component (`{{ Array.isArray(q.data) ? q.data : [...] }}` → `{{ q.data }}`).

## Installation

### Via skills CLI ([vercel-labs/skills](https://github.com/vercel-labs/skills))

```bash
# Install for your preferred agent
npx skills add onsen-ai/retool-app-builder-skill -a claude-code
npx skills add onsen-ai/retool-app-builder-skill -a cursor
npx skills add onsen-ai/retool-app-builder-skill -a cline
```

### Manual install

Clone into your agent's skills directory:

```bash
# Example for Claude Code
git clone https://github.com/onsen-ai/retool-app-builder-skill.git \
  ~/.claude/skills/retool-app-builder

# Example for Cursor
git clone https://github.com/onsen-ai/retool-app-builder-skill.git \
  .cursor/skills/retool-app-builder
```

Most agents discover skills automatically from their skills directory — no extra configuration needed.

### Requirements

- Python 3.8+ (stdlib only, no pip installs)
- A coding agent with skill support

## What's included

```
├── SKILL.md                    # Skill definition (~290 lines)
├── references/
│   ├── TOOLSCRIPT-CHEATSHEET.md  # Condensed rules (~550 lines)
│   └── TOOLSCRIPT-SPEC.md        # Full ToolScript spec (~2900 lines)
├── scripts/
│   ├── validate_app.py          # Validate app against all import rules
│   ├── scaffold_app.py          # Create app from 6 templates
│   ├── list_components.py       # Parse app → structured component tree
│   ├── add_component.py         # Add component + update positions atomically
│   ├── add_query.py             # Add query with event chains
│   ├── extract_component.py     # Move subtree to src/ + add Include
│   ├── fix_positions.py         # Recalculate vertical layout positions
│   ├── zip_app.sh               # Zip for Retool import (validates first)
│   ├── bundle-apps.sh           # Bundle app into single-file LLM context
│   └── compact_bundles.py       # Strip positions/metadata from bundles for bulk analysis
├── assets/examples/             # 8 importable example apps
│   ├── Minimal App/
│   ├── CRUD Table App/
│   ├── Master-Detail App/
│   ├── Search Filter App/
│   ├── AI Chat App/
│   ├── Advanced CRUD App/
│   ├── Charts Dashboard App/    # PlotlyChart, Statistic, lib/ data+layout JSON
│   └── API Dashboard App/       # RESTQuery, DrawerFrame, EditableText, setFilterStack
└── evals/
    └── evals.json               # 8 test cases with assertions
```

### Scripts

All scripts use Python stdlib only. No pip installs required.

| Script | Purpose |
|--------|---------|
| `validate_app.py <dir>` | 18 checks against Retool import rules. Run before every zip. |
| `scaffold_app.py "Name" --template <type>` | Create from template: `minimal`, `crud`, `master-detail`, `search-filter`, `chat`, `advanced-crud` |
| `list_components.py <dir>` | Component tree view — understand an app without reading RSX |
| `add_component.py <dir> --type T --id I ...` | Add component with correct position entry |
| `add_query.py <dir> --type T --id I ...` | Add query with event chains and lib/ files |
| `extract_component.py <dir> --component ID` | Move subtree to `src/` file |
| `fix_positions.py <dir>` | Recalculate vertical layout after changes |
| `zip_app.sh <dir>` | Validate + zip for Retool import |
| `bundle-apps.sh <dir> [output]` | Bundle app files into single `.toolscript-bundle` for LLM context. `--all` for batch. |
| `compact_bundles.py` | Strip positions/metadata and truncate large inline data from bundles for bulk analysis. |

## Eval results

Tested against 8 eval scenarios (simple → very hard) — each run with the skill vs a baseline without it. All runs used Claude Opus 4.6 with identical prompts. Grading is **strict**: assertions check Retool import correctness (correct element types, ID formats, file structure) and every run is validated with `validate_app.py`.

### Summary

| # | Eval | With Skill | Baseline | Delta |
|---|------|-----------|----------|-------|
| 1 | Build expense manager (NEW) | 15/15 (100%) | 4/15 (27%) | **+73%** |
| 2 | Add search + filter (EDIT) | 10/10 (100%) | 7/10 (70%) | **+30%** |
| 3 | Improve master-detail (IMPROVE) | 11/11 (100%) | 8/11 (73%) | **+27%** |
| 4 | Customer lookup table (Simple) | 11/11 (100%) | 9/11 (82%) | **+18%** |
| 5 | Order management CRUD (Medium) | 12/12 (100%) | 6/12 (50%) | **+50%** |
| 6 | IT asset dashboard (Medium-Hard) | 11/11 (100%) | 7/11 (64%) | **+36%** |
| 7 | Support ticket triage (Hard) | 11/11 (100%) | 6/11 (55%) | **+45%** |
| 8 | Content moderation queue (Very Hard) | 12/12 (100%) | 8/12 (67%) | **+33%** |
| | **Overall** | **103/103 (100%)** | **55/93 (61%)** | **+39%** |

**Key finding: 0 of 8 baseline outputs would actually import into Retool.** All 8 fail `validate_app.py`. All 8 with-skill outputs pass with 0 failures.

The skill costs ~2x tokens and ~80% more time but produces structurally correct, importable apps every time.

### Why baselines fail

Without the skill, Claude produces RSX that *looks* correct but uses wrong element names and formats:

| What baseline does | What Retool requires |
|---|---|
| `<SqlQuery>` | `<SqlQueryUnified>` |
| `<Modal>` | `<ModalFrame>` |
| `<BarChart>` | `<PlotlyChart>` |
| `<Functions>` | `<GlobalFunctions>` |
| Column IDs like `col_status` | 5-char hex like `a1b2c` |
| `.positions/` directory | `.positions.json` file |
| Descriptive event IDs | 8-char hex IDs |

These are silent import failures — the files look reasonable but Retool's importer rejects them.

### Eval details

**Evals 1-3** test the three skill modes (NEW, EDIT, IMPROVE). Evals 2-3 start from existing valid apps, giving the baseline an advantage since it inherits correct RSX structure.

**Evals 4-8** were designed blind — from a real user's perspective, without access to the skill's internals — and progressively increase in complexity:

- **Eval 4** (Simple): Table + detail panel + search. Tests foundational patterns.
- **Eval 5** (Medium): Full CRUD with modal form, delete confirmation, colored status tags.
- **Eval 6** (Medium-Hard): REST API, PlotlyChart, Statistic cards, CSV export. No SQL.
- **Eval 7** (Hard): Multi-query chaining (UPDATE + INSERT + refresh), dynamic dropdowns, temporary state.
- **Eval 8** (Very Hard): Tabbed container with per-tab data, PUT with dynamic URLs, JavaScript validation, image rendering.

## Usage examples

```
# Build a new app
"Build me a Retool app for managing employee expenses with a table,
create modal, edit side panel, and approve/reject workflow"

# Edit an existing app
"Add a search bar and category filter dropdown above the table in my CRUD app"

# Improve an app
"Review my Retool app and make it production-ready with best practices"
```

## How it works

Retool's ToolScript format (RSX) has strict rules for nesting, positioning, ID formats, and query wiring that cause silent import failures when violated. This skill:

1. Bundles a condensed cheatsheet of all rules so the agent doesn't need to memorize the full spec
2. Provides automation scripts for the most error-prone operations (position math, ID generation, validation)
3. Guides the agent through structured workflows (NEW/EDIT/IMPROVE) with explicit steps
4. Always validates before zipping — catching errors before they reach Retool's importer

## Contributing

Issues and PRs welcome. The most impactful contributions:

- Additional example apps in `assets/examples/`
- New assertions in `evals/evals.json`
- Script improvements (especially `validate_app.py` — more checks = fewer import failures)

## Built by

Built by the team at [Onsen](https://www.onsenapp.com) — an AI-powered mental health companion for journaling, emotional wellbeing, and personal growth.

## License

MIT
