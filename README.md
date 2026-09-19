# Ministry Orchestration — Body/Orchestrator

A local-first church and ministry inventory, Scripture-analysis, and orchestration research application.

The goal is to make the wider Body more visible to itself: what organizations exist, what they believe and teach, what ministries they operate, what capabilities they possess, what needs they cannot meet, where referrals go, and what becomes possible through better coordination.

## Current MVP

- First-run administrator setup and login
- SQLite persistent database
- Multi-organization inventory
- Identity, history, leadership, governance, worship, discipleship, pastoral care, evangelism, outreach, missions, capabilities, needs, partnerships, referrals, communications, campaigns, outcomes, and institutional learning
- Dedicated sermon / teaching corpus
- Hermeneutical and theological tagging
- Passage-context and text-to-sermon analysis
- Grace / shame / restoration analysis
- Love-of-neighbor / enemy / outsider analysis
- Application-depth and agency analysis
- Scripture-to-practice analysis
- Dedicated ministry inventory
- Evidence provenance:
  - F — Verified fact
  - S — Self-description
  - O — Observation
  - A — Analysis
  - H — Hypothesis
- Live aggregate teaching analysis
- HTML5 analysis packet
- US Letter PDF-friendly export
- Per-organization JSON backup

The application deliberately does **not** create a single "church score." It exposes multidimensional evidence, gifts, needs, constraints, theological patterns, and relationships.

## Run on macOS

```bash
git clone git@github.com:danielwjohnston/ministry-orchestration.git
cd ministry-orchestration
./start.command
```

Or double-click `start.command` in Finder.

The application opens at:

```
http://127.0.0.1:5050
```

No pip install, Node.js, or third-party Python package is required. The MVP uses the Python standard library and SQLite.

## Windows

Run:

```
start.bat
```

## Data

The working database is created locally as:

```
body_orchestrator.db
```

It is intentionally ignored by Git. Back up that file separately.

You can override its location:

```bash
BODY_ORCH_DB="/path/to/body_orchestrator.db" python3 app.py
```

## Organization 001

The first intended full research profile is **Connection Christian Church in Odessa, Texas**.

The purpose of Organization 001 is not merely to document one church. It is to pressure-test the schema deeply enough that Organizations 002–200 can inherit a useful, repeatable structure.

## Security boundary

The MVP binds only to `127.0.0.1`, so it is local to the computer running it.

Do not store confidential pastoral-care case files, protected health information, abuse reports, or other sensitive personal records in this MVP.

Before public hosting, add at minimum:

- TLS
- CSRF protection
- persistent server-side sessions
- role-based permissions
- audit logging
- encrypted backups
- formal privacy and retention rules
- a separate protected case-management design if sensitive personal information is ever required

## Design thesis

**Inventory → Intelligence → Orchestration**

The central question is:

> What gift exists here, what need exists elsewhere, and what becomes possible when they can see one another?

No person discarded. No gift presumed useless. No congregation expected to be the whole Body by itself.
