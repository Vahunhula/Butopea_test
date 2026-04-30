# Butopêa Backend Odoo Developer Practical Test — Notes

## Submission summary

- **Foundation (`estate/`):** complete. Built by following Odoo 16 official tutorial chapters 1–12, stopping before "Inheritance" per brief.
- **Task A (`estate_account/`):** [TODO — fill in once done]
- **Task B (`course_catalog/`):** [TODO — fill in once done]
- **Total time spent:** [TODO — track actual hours, be honest if over 4]

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

Foundation locked at commit `5242fc1`

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

## Task A — `estate_account/` (TODO)

[Fill in once Task A is complete. Sections to cover:]

- **Architecture:** model inheritance pattern (`_inherit = "estate.property"` to override `action_sold` and add invoice-related fields; `_inherit = "account.move"` to add `property_id` link).
- **Override of `action_sold`:** draft invoice creation happens *before* `super().action_sold()` call so failures rollback cleanly. Decision rationale.
- **Multi-company resolution:** `with_company(property.company_id)` to set the active company so `account.move` defaults pick the right journal and income account. Confirms compliance with brief's multi-company constraint.
- **No hard-coded account codes:** `account.move` line `account_id` resolved by Odoo's defaults, not specified explicitly. Compliance with brief.
- **Idempotency choice:** raise `UserError` if property already sold (vs no-op). Reason: explicit failure is testable; silent no-op masks caller bugs.
- **Smart button implementation:** view inheritance into `oe_button_box`, `action_view_invoices` returning `ir.actions.act_window` dict with domain filtering.
- **Tests:** `TransactionCase` covering the brief's acceptance pseudocode plus edge cases (no `buyer_id` raises, calling `action_sold` twice raises).
- **Notable AI corrections during Task A:** [list as they come up]

---

## Task B — `course_catalog/` (TODO)

Brief: 5 planted defects across module load / install / view / runtime. Fix each, no new features.

[Fill in once Task B is complete. One line per bug:]

- Bug 1: `<file>:<line>` — <one-sentence cause>
- Bug 2: ...
- Bug 3: ...
- Bug 4: ...
- Bug 5: ...

[Anything I tried that turned out not to be a bug, briefly, so reviewer sees the diagnostic process.]

---

## Known limitations and honesty section

[Fill in before submitting. The brief says: "If something is incomplete, say so and explain why."]

Examples of things to mention if true:
- Test coverage: covered the brief's pseudocode + N edge cases; did not cover [...]
- Time budget: budgeted 4h, actually spent [Xh]. Overruns and where they came from
- Anything that "works but smells wrong" that I'd refactor with more time

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