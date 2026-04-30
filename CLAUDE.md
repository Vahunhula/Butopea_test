# CLAUDE.md

Operating instructions for any AI assistant (Claude, Copilot, Cursor, etc.) working in this repository.

This file is loaded at the start of every session. The rules below override any instinct, default, or training data the AI has. If a rule conflicts with what the AI "wants" to suggest, the rule wins.

---

## Project

This repo is a take-home case study for a Backend Python (Odoo) Developer Intern role at Butopêa, a Hungarian furniture e-commerce company that runs on Odoo ERP. The work is evaluated on three dimensions, in this order:

1. **Working code** that meets the acceptance criteria.
2. **Correct Odoo idioms** (not "Python that happens to compile inside Odoo").
3. **AI context discipline** — the reviewer explicitly cares how the human directs the AI, and rewards moments where the AI's first suggestion was wrong and the human caught it.

The human (Vakho) is a CS student at ELTE Budapest. Strong in Python (FastAPI), PostgreSQL, Celery, Docker, and REST APIs. Production projects: ValuBet (football betting analytics), UFCEdge (UFC predictions), SignVision (sign language thesis). New to Odoo specifically — has read tutorials, has no production Odoo experience. This matters for how you (the AI) explain things: don't assume Odoo conventions are obvious, but don't condescend on Python or architecture.

---

## Deliverables in this repo

- `addons/estate/` — Foundation module, built by following the official Odoo 16 "Getting Started" tutorial.
- `addons/estate_account/` — Task A. Separate addon that wires `estate` into `account` (invoicing on sale).
- `addons/course_catalog/` — Task B. Provided buggy module with 5 planted defects to fix.
- `NOTES.md` — workflow log, AI decisions, accepted/rejected suggestions. **This is the primary graded artifact.**
- `README.md` — how to run the project and tests.

---

## Hard constraints (non-negotiable)

These come directly from the brief. Violating any of them is a failed submission.

1. **Target is Odoo 16 Community Edition.** Not 15, not 17, not 18, not Enterprise. If a suggested API was added in 17 or removed before 16, reject it.
2. **`estate` must not depend on `account`.** No accounting fields, imports, or references in the `estate` module. All accounting integration lives in `estate_account` via model inheritance.
3. **Uninstalling `estate_account` must leave `estate` working.** Test this mentally before adding anything to `estate`.
4. **No hard-coded account codes or journal IDs.** Resolve via Odoo's defaults (`account.move` line defaults, `with_company` context).
5. **Multi-company correctness.** Use `property.company_id` to resolve journal and accounts. Never `self.env.company` for record-bound logic.
6. **Lean code.** No new modules, wizards, reports, or fields beyond what the brief asks for. "Every line you add, you have to maintain" — this is a stated value of the team.
7. **No modifying the tutorial-built `estate` module to make Task A easier.** Task A's whole point is clean separation.

---

## Verification rules (the AI's most important job)

The #1 failure mode for AI-assisted Odoo work is **version drift**: the AI confidently suggests v17 or v18 syntax that doesn't exist in v16, or hallucinates a method that was never in Odoo at all.

Therefore:

- **Every Odoo API claim must be verifiable in v16 source or the v16 docs.** Model methods, field types, ORM helpers, decorators, view tag attributes — all of it. If you can't cite `addons/<module>/models/<file>.py` in Odoo 16, treat the suggestion as unverified.
- When uncertain, the correct response is **"I need to verify this against v16 source"**, not "this should work."
- Prefer citing exact source paths over paraphrasing behavior. Example: "`account.move._onchange_partner_id` in `addons/account/models/account_move.py` resolves the journal from `company_id` context" — not "Odoo automatically figures out the journal."
- If the human asks "does X work in v16?" and you don't actually know, say so. Do not pattern-match from v17 examples.
- Reject these specific anti-patterns even if they look right:
  - `models.Model` methods that take `cr, uid` (v7-era API, dead in v16)
  - `@api.one` (deprecated, gone)
  - `SavepointCase` (replaced by `TransactionCase` in v16+; verify the exact name in v16)
  - `fields.Char(size=N)` as the way to limit length (use SQL constraint instead)
  - View `<tree>` vs `<list>` — v16 uses `<tree>`, v17+ moves toward `<list>`. Use `<tree>`.

---

## Odoo idioms to follow

- Inheritance: `_inherit = "model.name"` to extend an existing model (Task A pattern). Don't use `_inherits` (different mechanism, not what we want here).
- Computed fields: declare with `@api.depends(...)`. Always include the dependency. The Total Revenue bug in Task B is almost certainly a missing or wrong `@api.depends`.
- Constraints: `@api.constrains` for Python-level checks, `_sql_constraints` for DB-level uniqueness/range.
- Errors raised to the user: `from odoo.exceptions import UserError`. Use `UserError` for expected failure paths (no buyer, already sold, no journal). Use `ValidationError` for constraint violations.
- Multi-company: when creating records, use `.with_company(company)` to set the active company so default field resolution picks the right values.
- Smart buttons: view inheritance into the form's `oe_button_box` div. Action returns an `ir.actions.act_window` dict with a domain filtering the target records.
- Tests: subclass `odoo.tests.common.TransactionCase`. Use `@tagged('post_install', '-at_install')` for tests that need other modules installed (most of ours).

---

## Code style

- Small functions with descriptive names. If a method is over ~20 lines, ask whether it should split.
- No dead code. No commented-out blocks. No `print()` left behind. No `# TODO` markers in submitted code unless the brief explicitly leaves something open.
- Imports ordered: stdlib, then `odoo`, then relative. Match Odoo's own style.
- Error messages in English, even though Butopêa is Hungarian. Their codebase will be English; introducing Hungarian strings looks unprofessional.
- Commit history is part of the grade. One logical change per commit. Messages in imperative mood ("Add invoice creation on property sale", not "added stuff"). Don't squash everything to a single "final" commit at the end.

---

## What is OUT of scope

- New features beyond the brief.
- Cosmetic improvements to the Foundation `estate` views (kanban polish, custom CSS, etc.) unless required by the tutorial.
- Refactoring `course_catalog` beyond fixing the 5 planted defects. The brief says "Only fix what is broken."
- Performance optimization unless the brief asks for it.
- Internationalization, translations, demo data beyond what's needed for tests.
- Wizards, reports, or scheduled actions in `estate_account`. The smart button + override is the entire UI surface.

---

## How decisions are recorded

Every meaningful AI exchange that changes the code or the plan goes into the **Decisions log** at the bottom of this file as I work. Format:

```
- [timestamp] AI suggested X. I checked Y (source path / doc link). Decision: accepted / rejected / modified to Z. Reason: ...
```

At the end of the project, the most useful entries get promoted into `NOTES.md`. The raw log stays here as evidence.

---

## Communication style with the human

- Be direct. Skip filler ("Great question!", "Absolutely!", "Here's a comprehensive overview...").
- When the human asks for a quick answer, give a quick answer.
- Push back when the human is about to do something that violates a rule above. Don't be agreeable for its own sake.
- When making a recommendation, state the recommendation, then the reason. Not the other way around.
- Tell the human when you're uncertain. Calibration matters more than confidence.

---

## Decisions log

(filled as work progresses)

- [setup] Repo layout uses `addons/` wrapper folder rather than modules at root. Reason: cleaner Docker mount, idiomatic Odoo convention. Brief lists modules at root but doesn't require it; one-line note in NOTES.md.
- [setup] Idempotency for `action_sold`: chose to **raise UserError** rather than no-op when property is already sold. Reason: explicit failure is easier to test and shows defensive thinking; silent no-op masks real bugs in caller code.

- [foundation/ch4] Used `-i estate` for first install (module wasn't yet in DB), then switched to `-u estate` for subsequent runs. Tutorial assumes module is already installed and only documents `-u`. Worth noting: `-u` only works on already-installed modules; `-i` is for first install.
- [foundation/ch4] Added `'license': 'LGPL-3'` to manifest in chapter 4 to silence the "Missing `license` key" default warning. Tutorial omits this until later but it's idiomatic on every Odoo core module manifest.
- [foundation/ch6] `default=lambda self: fields.Date.add(fields.Date.today(), months=3)` for `date_availability`. The lambda defers evaluation to record-creation time. Without it, the default would freeze to module-load date. Verified pattern in Odoo 16 core (e.g., `addons/sale/models/sale_order.py` uses similar lambda defaults for date defaults).
- [foundation/ch9] Added `default=0.0` keyword to `max(record.offer_ids.mapped("price"), default=0.0)`. AI's first suggestion omitted it; would crash with `ValueError: max() arg is an empty sequence` when a property has zero offers. The `default=` is critical for empty-recordset safety.
- [foundation/ch9] Used `record.create_date.date() if record.create_date else fields.Date.today()` as a fallback for `date_deadline` compute on offers. The chapter explicitly flags this: `create_date` is `False` until a record is saved, and computing fields on unsaved form values would crash without the fallback.
- [foundation/ch10] `action_sold` is intentionally minimal — only handles state transition, no invoice creation. Task A's `estate_account` module will inherit this method via `_inherit = "estate.property"` and add accounting logic via `super().action_sold()`. Keeping `estate.action_sold` clean is what preserves the brief's "uninstall estate_account, estate keeps working" constraint.
- [foundation/ch11] Imported `float_compare` and `float_is_zero` from `odoo.tools.float_utils` for the 90% selling-price constraint, instead of using Python's `<` and `==` operators. Floating-point arithmetic in Python is unreliable at scale (`0.1 + 0.2 != 0.3`). Odoo's helpers handle precision_digits explicitly. Verified usage in `addons/account/models/account_move.py`.
- [foundation/ch11] Used `ValidationError` for the 90% Python constraint, not `UserError`. Convention: `@api.constrains` raises `ValidationError`; button actions raise `UserError`. They render slightly differently in the UI and the convention matters for code review.
- [foundation/ch12] Manifest data file order matters when XML records cross-reference. Stat button on `estate.property.type` form references `estate_property_offer_action` defined in the offer views file. Initial manifest order placed type-views before offer-views → ParseError on upgrade. Rule: a file that defines an XML ID must load before any file referencing it. Reordered manifest data list to fix.
- [foundation/ch12] Used v16 `attrs="{'invisible': [(...)]}"` and `states="..."` syntax for conditional UI. Confirmed v17+ replaces these with bare `invisible=` taking a domain. Stayed with v16 idiom per CLAUDE.md verification rule.