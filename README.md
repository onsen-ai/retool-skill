# retool-app-builder-skill

An agent skill for building, editing, and improving importable [Retool](https://retool.com) apps using ToolScript (RSX format). Compatible with [Claude Code](https://docs.anthropic.com/en/docs/claude-code), [Cursor](https://cursor.com), [Cline](https://cline.bot), [OpenCode](https://github.com/opencode-ai/opencode), and any coding agent that supports the [skills standard](https://github.com/vercel-labs/skills).

## What it does

This skill enables your coding agent to generate complete, importable Retool applications from natural language descriptions. It handles the mechanical and error-prone parts of ToolScript — validation, scaffolding, position math, query wiring — so the LLM focuses on creative and structural decisions.

### Three modes

- **NEW** — "Build me a Retool app for managing expenses" → scaffolds from template, customizes, validates, zips
- **EDIT** — "Add a search bar and status filter to my app" → understands existing structure, adds components, fixes positions
- **IMPROVE** — "Make this app production-ready" → audits against best practices, adds loading states, confirmation dialogs, event chains

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
├── SKILL.md                    # Skill definition (~260 lines)
├── references/
│   ├── TOOLSCRIPT-CHEATSHEET.md  # Condensed rules (~310 lines)
│   └── TOOLSCRIPT-SPEC.md        # Full ToolScript spec (2541 lines)
├── scripts/
│   ├── validate_app.py          # Validate app against all import rules
│   ├── scaffold_app.py          # Create app from 6 templates
│   ├── list_components.py       # Parse app → structured component tree
│   ├── add_component.py         # Add component + update positions atomically
│   ├── add_query.py             # Add query with event chains
│   ├── extract_component.py     # Move subtree to src/ + add Include
│   ├── fix_positions.py         # Recalculate vertical layout positions
│   └── zip_app.sh               # Zip for Retool import (validates first)
├── assets/examples/             # 6 importable example apps
│   ├── Minimal App/
│   ├── CRUD Table App/
│   ├── Master-Detail App/
│   ├── Search Filter App/
│   ├── AI Chat App/
│   └── Advanced CRUD App/
└── evals/
    └── evals.json               # 3 test cases with assertions
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

## Benchmark

Tested against 3 eval scenarios (with-skill vs baseline without skill):

| Eval | With Skill | Baseline | Delta |
|------|-----------|----------|-------|
| Build expense manager from scratch | 10/10 (100%) | 6/10 (60%) | **+40%** |
| Add search + filter to existing app | 8/8 (100%) | 8/8 (100%) | 0% |
| Improve master-detail app | 6/6 (100%) | 5/6 (83%) | **+17%** |
| **Overall** | **24/24 (100%)** | **19/24 (81%)** | **+19%** |

The skill costs ~39s extra and ~14K more tokens per run but produces structurally correct, importable apps every time.

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

1. Bundles a condensed cheatsheet of all rules so the agent doesn't need to memorize the 2541-line spec
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
