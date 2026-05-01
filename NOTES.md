# Butopêa Backend Odoo Developer Practical Test — Notes

## Submission summary

- **Foundation (`estate/`):** complete. Built by following Odoo 16 official tutorial chapters 1–12, stopping before "Inheritance" per brief.
- **Task A (`estate_account/`):** complete. 5 tests passing; uninstall safety verified.
- **Task B (`course_catalog/`):** 4 of 5 planted defects fixed; brief's 3 acceptance criteria all pass. Bug 4 (depends path on `total_revenue`) reproduced and fix verified directly via `odoo shell`.
- **Total time spent:** [TODO — fill in honestly]

## Stack and environment

- Odoo 16 Community Edition via Docker (official `odoo:16` image + `postgres:15`).
- `docker-compose.yml` and `config/odoo.conf` in repo root.
- Database: `butopea` (created via Odoo's database manager).
- `dev_mode = reload,qweb,xml` set in `odoo.conf` for live reload during development.

## Repo layout

```
butopea-test/
├── CLAUDE.md          ← AI operating instructions, loaded at session start
├── NOTES.md           ← this file
├── README.md          ← how to run
├── docker-compose.yml
├── config/odoo.conf
└── addons/
    ├── estate/              ← Foundation
    ├── estate_account/      ← Task A
    └── course_catalog/      ← Task B
```

The `addons/` wrapper folder is mine, not the brief's. Brief lists modules at root; I went with `addons/` for cleaner Docker mount and matching Odoo's own conventions for addon paths. Functionally equivalent for grading.

## How I worked with AI

I used Claude as the primary AI throughout. Approach:

1. Wrote `CLAUDE.md` first as a constraints document — Odoo 16 only, lean code, verification rules, idiom guardrails — *before* any code. It was loaded at the start of every session.
2. Read each tutorial chapter fully before writing code. Then asked Claude for the chapter's deliverable shape, typed it manually (not paste-copy), restarted the dev server, verified in the UI, committed.
3. Logged decisions in `CLAUDE.md`'s Decisions log as I went, not at the end. The most interesting moments are pulled into the section below.

What I deliberately kept out of AI prompts: the entire Odoo source tree, my full `__manifest__.py`, large XML view blocks. I fed only the field list / problem at hand. The brief explicitly tests "what you choose to feed the model and what you choose to keep out" — keeping prompts narrow forces the AI to use Odoo's stated patterns rather than pattern-matching from whatever bloat I include.

What I let AI do unsupervised: typing boilerplate (manifest skeletons, view scaffolds with no logic). What I checked manually: anything involving `@api.depends`, multi-company logic, lambda defaults, and v16 vs v17 syntax differences.

---

## Foundation — `estate/` module

Built per the official Odoo 16 tutorial. Chapters 1–12 covered: module skeleton, models, security ACLs, menus and actions, custom views (tree/form/search), relations (Many2one/One2many/Many2many), computed fields, action buttons, SQL/Python constraints, and "sprinkles" (statusbar, decorations, conditional UI, stat button).

Stopped at chapter 13 (Inheritance) per brief — that chapter's content is what `estate_account` (Task A) implements.

### Notable AI moments during Foundation

A few cases where the AI's first instinct was wrong and I caught it. These are the kind of "AI context discipline" moments the brief rewards.

**1. `max()` on empty recordset (chapter 9, computed `best_price`)**

> AI's first version: `max(record.offer_ids.mapped("price"))`.
> Problem: `mapped()` on an empty One2many returns `[]`. `max([])` raises `ValueError: max() arg is an empty sequence`. A property with no offers would crash on form load.
> Fix: `max(record.offer_ids.mapped("price"), default=0.0)`. The `default=` keyword is the empty-recordset safety net.

**2. `create_date` is `False` on unsaved records (chapter 9, computed `date_deadline`)**

> AI suggested directly using `record.create_date.date()` in the compute. The tutorial chapter explicitly flagged this as a trap — `create_date` is empty until first save, and computing on unsaved form values triggers `AttributeError: 'bool' object has no attribute 'date'`.
> Fix: `base_date = record.create_date.date() if record.create_date else fields.Date.today()`.

**3. Naive float comparison (chapter 11, 90% rule)**

> AI's first version used `if record.selling_price < record.expected_price * 0.9`. Standard Python comparison.
> Problem: floating-point arithmetic is unreliable. `0.1 + 0.2 != 0.3`, etc. The chapter's warning explicitly required `float_compare()` and `float_is_zero()` from `odoo.tools.float_utils`.
> Fix: imported the helpers, used `float_compare(a, b, precision_digits=2) < 0` for the comparison and `float_is_zero(price, precision_digits=2)` to skip the check when selling_price is still 0 (default until offer acceptance).

**4. Cross-file XML ID resolution (chapter 12, stat button)**

> The stat button on `estate.property.type` form references `estate_property_offer_action`, which is defined in `estate_property_offer_views.xml`.
> My initial manifest had type-views loading before offer-views in the `data` list. Result: `ValueError: External ID not found in the system: estate.estate_property_offer_action` on upgrade.
> Fix: reordered manifest so files defining XML IDs load before files referencing them. General rule I've internalized: in `data:`, dependency order matters whenever XML records cross-reference.

**5. v16 vs v17 view attribute syntax**

> When implementing chapter 12's conditional UI (hide buttons based on state, hide fields based on garden checkbox), AI suggested `<button invisible="state == 'sold'">`-style syntax. That's v17+. v16 uses `states="..."` for buttons and `attrs="{'invisible': [...]}"` for fields.
> Fix: stayed with v16 idiom. Verified by grepping for `states=` and `attrs=` in Odoo 16 core (e.g., `addons/sale/views/sale_order_views.xml`).

**6. Install vs upgrade flag**

> First-time module load needed `-i estate` (install). Tutorial documents only `-u estate` (upgrade), which silently no-ops if the module isn't already installed in the DB. Took one confused upgrade run to realize the flag mismatch.
> Habit: `-i` once on first install, `-u` for everything after.

**7. Manifest `license` warning**

> `Missing 'license' key in manifest for 'estate', defaulting to LGPL-3` warning appeared on every load. AI didn't flag it as something I should fix; I noticed and added `'license': 'LGPL-3'` to the manifest. Tutorial doesn't mention it until later but every Odoo core manifest has it.

### Foundation — pre-Task-A audit

Before starting Task A, ran a structured audit of `addons/estate/` against the Foundation Definition of Done. Result: 2 real gaps, both fixed before Task A began.

- **Kanban view for `estate.property.type`** — missing entirely. Tutorial chapters 1–12 don't walk through one for types specifically. Added a minimal kanban view (~20 lines) showing name + offer count per card, and updated the action's view_mode to `kanban,tree,form`.
- **`'application': True` missing from `estate/__manifest__.py`** — added. Without it, the module installs as a library rather than appearing as an app tile in the apps grid.
- **Security group choice (not a gap, documenting the decision):** chose `base.group_user` over creating a custom `Estate / User` group. The brief explicitly allows this ("your call"). Reason: the case study has no multi-role requirement; an Estate/User group would only matter in a multi-tenant setup. Simpler is correct here.

Audit covered: all 4 models with `_name`/`_description`/`_order`, all field defaults and `copy=False`/`required=True`/`readonly=True` attributes, both computed fields and the onchange, all SQL constraints, the Python `@api.constrains` using `float_compare`/`float_is_zero`, all view types (tree/form/search/kanban), all action methods with their UserError guards, the security CSV, and the manifest. No v17+ syntax leaked in.

Foundation locked at commit `5242fc1`.

### Foundation acceptance criteria — self-check

Per brief's Foundation definition of done:

- [x] Models: `estate.property`, `estate.property.type`, `estate.property.tag`, `estate.property.offer`
- [x] Default fields, computed fields (`total_area`, `best_price`), `_sql_constraints` and `@api.constrains`
- [x] Tree, form, search views
- [x] Kanban for property types — added during pre-Task-A audit (see audit section above)
- [x] Statusbar with state transitions: New → Offer Received → Offer Accepted → Sold / Canceled
- [x] Sold and Cancel action buttons; Accept/Refuse on offers
- [x] Security: `ir.model.access.csv` with one access rule per model for `base.group_user`

---

## Task A — `estate_account/`

**Status: complete.** All 5 tests pass; uninstall safety verified.

### Architecture

Bridge module pattern. `estate_account` depends on both `estate` (the Foundation module) and `account` (Odoo built-in). `estate` itself has no dependency on `account` — confirmed by uninstalling `estate_account` and verifying Real Estate still works.

Two model inheritances:

- `_inherit = "estate.property"` — adds `company_id`, `invoice_ids` (One2many), `invoice_count` (computed), overrides `action_sold`, defines `action_view_invoices` for the smart button.
- `_inherit = "account.move"` — adds `property_id` Many2one back-link. This is the "missing piece" that makes the One2many work and lets the action's domain filter find the right invoices.

One view file inheriting `estate.estate_property_view_form` to inject the smart button via XPath.

### Override of `action_sold`

Validation gates fire **before** invoice creation, so failures rollback cleanly:

1. Already-sold check (idempotency): raise `UserError`.
2. No-buyer check: raise `UserError`.
3. Journal lookup: raise `UserError` if no sales journal exists for the property's company.

Then create the draft `account.move` with `move_type='out_invoice'`. Then `super().action_sold()` to flip state. If invoice creation throws, super never runs — atomic.

### Multi-company resolution

Two pieces:
- `record.company_id` (NOT `self.env.company`) is the source of truth for journal and account lookups. The user's logged-in company is irrelevant.
- `self.env["account.move"].with_company(record.company_id).create({...})` sets the active-company context, which is how Odoo's default-resolution logic picks the right income account on each invoice line. **No `account_id` is hard-coded** on lines — Odoo's `account.move.line._compute_account_id` resolves it from the company default.

### Idempotency choice

Chose to **raise UserError** if `action_sold` is called on an already-sold property (vs no-op).

Reason: explicit failure is testable (`test_already_sold_raises` asserts both the raise and that no second invoice was created). Silent no-op would mask real bugs in caller code. Documented decision before writing the override.

### Smart button

XPath: `//sheet/h1` with `position="before"`. Places the `oe_button_box` div inside the sheet, above the property name title — Odoo's standard smart-button placement (matches the convention in `addons/sale/views/sale_order_views.xml` and similar core modules).

Initial attempt used `//sheet` with `position="before"`, which placed the button above the sheet but below the header. That overlapped visually with the statusbar and click events resolved to the wrong action. Fixed by re-anchoring to the h1 inside the sheet.

### Tests (`tests/test_invoice.py`)

5 tests, all passing:

1. `test_invoice_created_on_sold` — brief's acceptance pseudocode: invoice exists, correct partner, correct amount_untaxed (= price * 0.06 + 100), state=draft.
2. `test_invoice_has_two_lines` — verifies both line names ("Commission", "Administrative fee") and prices.
3. `test_sold_without_buyer_raises` — brief constraint: action_sold without buyer_id raises UserError.
4. `test_already_sold_raises` — brief constraint: re-running action_sold raises and does not create a second invoice.
5. `test_invoice_journal_matches_property_company` — multi-company sanity: invoice journal belongs to property's company and is type='sale'.

Run: `docker compose exec odoo odoo -c /etc/odoo/odoo.conf -d butopea --test-enable --stop-after-init -u estate_account`

### Notable AI corrections during Task A

- **Smart button XPath placement**: AI's first version used `//sheet position="before"`, which placed the button-box outside the sheet — visually overlapped with the statusbar and click events fired the wrong action. Fixed by re-anchoring to `//sheet/h1` with `position="before"`. Verified Odoo core uses the same pattern in `addons/sale/views/sale_order_views.xml`.
- **`with_company()` context**: AI initially suggested passing `account_id` directly on each invoice line. The brief explicitly forbids hard-coding account codes. Replaced with `with_company(record.company_id)` on the create call so Odoo's `_compute_account_id` resolves the income account from the company's default. Verified by checking `account.move.line._compute_account_id` in Odoo 16 source.
- **`record.company_id` vs `self.env.company`**: AI defaulted to `self.env.company` for journal lookup and `company_id` on the invoice dict. That's the user's logged-in company, which is wrong for multi-company correctness — the invoice has to belong to the *property's* company regardless of who's logged in. Replaced both references to `record.company_id`. Documented as a CLAUDE.md-anchored guardrail.

### Uninstall safety

Verified via UI uninstall (Apps → Real Estate — Accounting Bridge → ⋮ menu → Uninstall). Confirmed afterward: Real Estate menu still works, properties open and edit correctly, statusbar and action buttons function, no errors in logs. Smart button is gone (correct — the inherited view is gone with the module). Re-installed cleanly via `docker compose exec odoo odoo -c /etc/odoo/odoo.conf -i estate_account -d butopea --stop-after-init` afterward.

Task A locked at commit `4c137a2`.

---

## Task B — `course_catalog/`

**Status: 4 of 5 planted defects fixed; brief's 3 acceptance criteria all pass.**

### Bugs found and fixed

- **Bug 1 — install-blocking.** `security/ir.model.access.csv` line 2: typo `model_course_catlog` (missing "a") in the `model_id:id` column. The model's `_name` is `course.catalog`, so the correct external ID is `model_course_catalog`. Without this fix, install failed with `No matching record found for external id 'model_course_catlog' in field 'Model'`.

- **Bug 2 — module load warning, latent runtime crash.** `models/course.py` line 11: `instructor_id = fields.Many2one("res.user", ...)`. The Odoo model name is `res.users` (plural). Module loaded with a `WARNING ... unknown comodel_name 'res.user'` and any attempt to populate Instructor would have crashed at runtime. Fixed by changing `"res.user"` to `"res.users"`.

- **Bug 3 — view rendering.** `views/course_views.xml` line 14: form view referenced `<field name="instuctor_id"/>` (missing "r"). Tree view (line 41) and search view (line 56) referenced the field correctly — only the form view had the typo. Caused a `ParseError: Field "instuctor_id" does not exist in model "course.catalog"` on install. Worth noting that the tree and search views *had it right*, so this wasn't a global typo — just one specific spot in the form, which I confirmed by comparing all three view definitions before applying the fix.

- **Bug 4 — silent compute staleness.** `models/course.py` line 39: `_compute_total_revenue` declared `@api.depends("enrollment_ids")`. That path watches the recordset (additions/removals) but does not watch the `amount` field on individual enrollments. The correct v16 idiom is `@api.depends("enrollment_ids.amount")` — dot-notation crosses the relation so the field is invalidated when any related enrollment's `amount` changes.

  Reproduced the bug directly via `odoo shell` before fixing:

  ```
  # With buggy @api.depends("enrollment_ids")
  enrollment.write({"amount": enrollment.amount + 1000})
  course.total_revenue        → 450.0   (stale, never recomputed)
  sum(...mapped("amount"))    → 1450.0  (actual sum)
  ```

  Verified the fix the same way:

  ```
  # With corrected @api.depends("enrollment_ids.amount")
  enrollment.write({"amount": enrollment.amount + 500})
  course.total_revenue        → 950.0   (fresh)
  sum(...mapped("amount"))    → 950.0   (actual sum)
  ```

  The bug is *masked in normal UI flows* because saving the course form triggers a parent `course.write()`, which invalidates the entire course record's cache (including `total_revenue`) regardless of the depends contract. So manual UI testing alone wouldn't catch it. The bug surfaces when an enrollment is updated via a direct API call — for example, from another module, a server action, a test, or any code path that bypasses the parent form-save.

### Bugs not found

The brief states 5 planted defects across module load / install / view rendering / runtime. I found 4 — one per stage as described. After fixing those, I examined every remaining file in the module — `__init__.py`, `__manifest__.py`, `models/__init__.py`, `models/enrollment.py` — and could not identify a 5th defect. Verified: `enrolled_on` default uses the valid `fields.Date.context_today` pattern; `currency_id` related-field cascade is correct; `ondelete="cascade"` on `course_id` is appropriate; no missing `_description`; manifest is well-formed.

The brief itself notes the count "may be approximate," so 4 may be the actual total — or there is a 5th silent bug I'm not familiar enough with v16 internals to spot. Documenting honestly per brief guidance.

### Notable AI moments during Task B

- **Diagnostic strategy: error-driven first, audit second.** First pass: ran `-i course_catalog` repeatedly and let install errors guide me to bugs 1, 2, and 3 — each surfaced as a clear log entry. Second pass: structured audit of all 7 module files looking for silent semantic bugs that wouldn't fail install. This caught bug 4. Tradeoff: error-driven debugging is fast for stage-failure bugs and useless for silent semantic bugs; you need both passes.

- **Pushed past the AI's "you're done."** After fixing bugs 1–3, the AI told me to stop and submit — its argument was that the brief's three acceptance criteria all passed and any further hunting would be padding. That argument was reasonable but incomplete: the brief explicitly stated 5 defects, and was specific about *which behavior* to test (Total Revenue updating on enrollment changes), which is an unusual amount of pointing for a brief that didn't expect candidates to dig into compute reactivity. Asked the AI for a *read-only* audit prompt — explicitly framed as "find without fix, do not modify any files" — to be run as a separate Claude conversation. That audit identified bug 4 in `_compute_total_revenue`.

- **Refused to take the audit's word for it.** The audit's reasoning about `@api.depends("enrollment_ids")` vs `enrollment_ids.amount` was logically sound, but I'd already manually tested editing an enrollment's amount in the UI and seen `total_revenue` update correctly. So the audit's claim contradicted my observation. Two possibilities: either the audit was inferring a bug that didn't actually manifest, or the manual UI test was insufficient. Resolved this by running `odoo shell` and calling `enrollment.write({"amount": ...})` directly — bypassing the parent course form. Stored `total_revenue` stayed at `450.0`, actual sum was `1450.0`. Bug confirmed in the database. Applied the fix, re-ran the same shell sequence, confirmed they matched. Lesson I documented in `CLAUDE.md`: *"the UI works" is not sufficient validation for a depends declaration; you need to test the API path that actually exercises cache invalidation*.

- **Strategy choice — read the code, don't delegate to an autonomous agent.** Considered using Claude Code to autonomously hunt for remaining bugs. Decided against it: the brief explicitly grades AI context discipline, and an autonomous agent finding bugs in my codebase undermines the diagnostic story I can tell about each one. Ran the audit manually, file by file, with a separate Claude conversation as a *read-only auditor* (not a fixer). Worked well — caught bug 4, gave me a story to tell, no risk of touching working code.

Task B locked at commit `d7e1d30`.

---

## Known limitations and honesty section

- **Task B: 4 of 5 bugs found.** As above, examined every file and could not identify a 5th. Documenting honestly rather than claiming completeness.
- **Test coverage on Task B**: I did not write automated tests for `course_catalog` (the brief did not require them). Bug 4 was verified via interactive `odoo shell`, which is reproducible but not part of a CI test suite. With more time I'd add a `tests/test_total_revenue.py` with the same shell sequence as a TransactionCase — that would also serve as a regression test for the depends contract.
- **Time budget**: budgeted 4h, actually spent [Xh — fill in honestly]. [If overrun: where it went, e.g., "smart button XPath debugging took longer than expected; about 30 minutes lost to a misplaced position='before' that overlapped the statusbar and silently misrouted clicks"].
- **Pre-Task-A orphan record.** During chapter 10/11 manual testing of the foundation Sold action (before the buyer-required validation existed in `estate_account`), one property in the database ended up with `state='sold'` but `buyer_id=NULL`. This doesn't affect tests (TransactionCase creates fresh data and rolls back) and doesn't affect any acceptance criterion. Left as-is for transparency.

---

## How to run

See `README.md` for full setup. TL;DR:

```bash
docker compose up -d
# wait for postgres + odoo to come up
# open http://localhost:8069, create database "butopea"
# install all three addons
docker compose exec odoo odoo -c /etc/odoo/odoo.conf \
    -i estate,estate_account,course_catalog \
    -d butopea --stop-after-init
```

Tests:

```bash
docker compose exec odoo odoo -c /etc/odoo/odoo.conf \
    -d butopea --test-enable --stop-after-init \
    -i estate_account
```