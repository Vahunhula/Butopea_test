# Butopêa Backend Odoo Developer Practical Test

Take-home case study for the Backend Python (Odoo) Developer Intern role at Butopêa. Three Odoo 16 Community modules:

- **`addons/estate/`** — Real Estate module built from the official Odoo 16 tutorial (Foundation).
- **`addons/estate_account/`** — Accounting integration: creates a draft invoice when a property is sold (Task A).
- **`addons/course_catalog/`** — Bug-fix exercise for a provided buggy module (Task B).

The full workflow log, decisions, and AI-assistance notes live in [`NOTES.md`](./NOTES.md). The AI operating instructions used during development are in [`CLAUDE.md`](./CLAUDE.md).

---

## Prerequisites

- Docker and Docker Compose v2 (`docker compose ...`, not `docker-compose ...`)
- Port `8069` and `8072` available on the host
- ~1 GB free disk for the Odoo and Postgres images

Tested on Windows 11 with Docker Desktop. Linux and macOS should work identically.

---

## Repo layout

```
.
├── CLAUDE.md                ← AI operating instructions
├── NOTES.md                 ← workflow, decisions, AI moments — primary submission artifact
├── README.md                ← this file
├── docker-compose.yml       ← Odoo 16 + Postgres 15
├── config/
│   └── odoo.conf            ← addons_path, dev_mode, db credentials
└── addons/
    ├── estate/              ← Foundation
    ├── estate_account/      ← Task A
    └── course_catalog/      ← Task B
```

---

## Run

### 1. Start the stack

From the repo root:

```bash
docker compose up -d
```

First boot pulls the images (~600 MB) and takes 1–2 minutes. Subsequent boots are seconds.

### 2. Create the database

Open `http://localhost:8069`. The Odoo database manager prompts for setup:

- **Master Password:** the auto-generated one shown, or set your own (must match `admin_passwd` in `config/odoo.conf` if you want to manage DBs via UI later)
- **Database Name:** `butopea`
- **Email:** any (becomes login; e.g. `admin@example.com`)
- **Password:** any (your user login password)
- **Language:** English (US)
- **Country:** Hungary
- **Demo data:** ✅ check this

Click **Create database**. Takes ~30 seconds.

### 3. Install the modules

```bash
docker compose exec odoo odoo -c /etc/odoo/odoo.conf \
    -i estate,estate_account,course_catalog \
    -d butopea --stop-after-init
```

The `-i` flag installs the modules. Use `-u` instead for subsequent code changes.

### 4. Open the UI

`http://localhost:8069` — log in with the email/password from step 2. The **Real Estate** app appears in the apps menu.

---

## Run tests

```bash
docker compose exec odoo odoo -c /etc/odoo/odoo.conf \
    -d butopea --test-enable --stop-after-init \
    -i estate_account
```

Test results print to stdout. Look for `tests/test_*: OK` lines and a `Modules loaded.` confirmation at the end.

---

## Common operations

**Re-apply code changes after editing a Python or XML file:**

```bash
docker compose exec odoo odoo -c /etc/odoo/odoo.conf \
    -u estate_account -d butopea --stop-after-init
```

`dev_mode = reload,qweb,xml` is set in `config/odoo.conf` so most changes (Python edits, view tweaks) reload automatically. New fields, new models, or new XML files still require an explicit `-u` to migrate the schema and load data files.

**Tail logs in real time:**

```bash
docker compose logs -f odoo
```

**Reset everything (wipe DB + filestore):**

```bash
docker compose down -v
```

The `-v` flag deletes named volumes. After this, you must re-do steps 2 and 3 above.

**Inspect the database directly:**

```bash
docker compose exec db psql -U odoo butopea
```

---

## Module overview

### `estate/` — Foundation

Real Estate listing module with properties, types, tags, and offers. Key features:

- Properties with state machine: `New` → `Offer Received` → `Offer Accepted` → `Sold` / `Canceled`
- Computed fields: `total_area`, `best_price`
- SQL constraints (positive prices, unique type/tag names) and Python `@api.constrains` (selling price ≥ 90% of expected)
- Custom tree, form, and search views with decorations and conditional UI
- Stat button on Property Types showing related offer count

No dependency on `account` — accounting integration is in `estate_account`.

### `estate_account/` — Task A

Wires the `estate` module into Odoo's `account` module:

- Inherits `estate.property` to override `action_sold`. When a property is sold, creates a draft customer invoice (`account.move` with `move_type='out_invoice'`) for the buyer.
- Two invoice lines: 6% commission on selling price + flat 100.00 administrative fee.
- Inherits `account.move` to add a `property_id` link.
- Smart button on the property form opens related invoices.
- Multi-company correct: invoice's company, journal, and default income account resolve via `property.company_id` and `with_company()` context. No hard-coded account codes.
- Idempotency: raises `UserError` if `action_sold` is called on an already-sold property.
- Tests in `tests/test_invoice.py` cover the brief's pseudocode plus two edge cases (missing buyer, double-sell).

Uninstalling `estate_account` leaves `estate` fully functional.

### `course_catalog/` — Task B

Provided buggy module with 5 planted defects across module load, install, view rendering, and runtime stages. Fixed in place; no new features added. See `NOTES.md` for the per-bug breakdown.

---

## Submission checklist

- [x] All three modules install cleanly on a fresh DB via `-i estate,estate_account,course_catalog`
- [x] `estate_account` tests pass via `--test-enable`
- [x] `NOTES.md` documents the workflow, AI moments, and known limitations
- [x] Commit history shows progressive work, not a single dump
- [x] No hard-coded account IDs or company assumptions in `estate_account`
- [x] `estate` has no dependency on `account`

---

## Contact

Vakhtang — ELTE Budapest, CS BSc.
Repo: https://github.com/Vahunhula/Butopea_test