"""Handles the seeded company checklist and delegation SQLite database."""

import os
import pathlib
import sqlite3
from datetime import date, timedelta

_DEFAULT_DB_PATH = pathlib.Path(__file__).parent.parent / "data" / "CompanyTasks.db"
DB_PATH = pathlib.Path(os.getenv("DB_PATH", str(_DEFAULT_DB_PATH)))

_SCHEMA_AND_SEED = """
CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    role TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE
);

CREATE TABLE checklists (
    checklist_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    department TEXT NOT NULL,
    owner_id INTEGER NOT NULL REFERENCES employees(employee_id),
    due_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('Not started', 'In progress', 'Completed'))
);

CREATE TABLE checklist_items (
    item_id INTEGER PRIMARY KEY,
    checklist_id INTEGER NOT NULL REFERENCES checklists(checklist_id),
    task TEXT NOT NULL,
    assigned_to INTEGER NOT NULL REFERENCES employees(employee_id),
    due_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('Pending', 'In progress', 'Completed', 'Blocked')),
    priority TEXT NOT NULL CHECK (priority IN ('Low', 'Medium', 'High', 'Critical')),
    completed_at TEXT
);

CREATE TABLE delegations (
    delegation_id INTEGER PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES checklist_items(item_id),
    delegated_by INTEGER NOT NULL REFERENCES employees(employee_id),
    delegated_to INTEGER NOT NULL REFERENCES employees(employee_id),
    delegated_on TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('Assigned', 'Accepted', 'In progress', 'Completed', 'Declined')),
    notes TEXT
);

INSERT INTO employees VALUES
    (1, 'Maya Patel', 'Operations', 'Operations Manager', 'maya.patel@northstar.example'),
    (2, 'Daniel Kim', 'Finance', 'Finance Analyst', 'daniel.kim@northstar.example'),
    (3, 'Sofia Garcia', 'Human Resources', 'HR Specialist', 'sofia.garcia@northstar.example'),
    (4, 'Liam Chen', 'IT', 'Systems Administrator', 'liam.chen@northstar.example'),
    (5, 'Ava Thompson', 'Sales', 'Account Executive', 'ava.thompson@northstar.example'),
    (6, 'Noah Williams', 'Operations', 'Facilities Coordinator', 'noah.williams@northstar.example');

INSERT INTO checklists VALUES
    (1, 'Monthly office safety review', 'Operations', 1, '2026-09-30', 'In progress'),
    (2, 'September payroll close', 'Finance', 2, '2026-09-25', 'In progress'),
    (3, 'New starter onboarding - Priya Shah', 'Human Resources', 3, '2026-09-27', 'Not started'),
    (4, 'Quarterly access review', 'IT', 4, '2026-09-29', 'In progress');

INSERT INTO checklist_items VALUES
    (1, 1, 'Inspect emergency exits', 6, '2026-09-23', 'Completed', 'High', '2026-09-22'),
    (2, 1, 'Verify first-aid kit supplies', 6, '2026-09-26', 'In progress', 'Medium', NULL),
    (3, 1, 'Upload signed inspection report', 1, '2026-09-30', 'Pending', 'High', NULL),
    (4, 2, 'Reconcile contractor invoices', 2, '2026-09-24', 'Completed', 'High', '2026-09-23'),
    (5, 2, 'Approve payroll variance report', 1, '2026-09-25', 'Pending', 'Critical', NULL),
    (6, 3, 'Create accounts and equipment request', 4, '2026-09-26', 'Blocked', 'High', NULL),
    (7, 3, 'Schedule orientation meeting', 3, '2026-09-27', 'Pending', 'Medium', NULL),
    (8, 4, 'Export inactive user list', 4, '2026-09-22', 'Completed', 'Medium', '2026-09-21'),
    (9, 4, 'Confirm manager access approvals', 5, '2026-09-28', 'In progress', 'High', NULL);

INSERT INTO delegations VALUES
    (1, 1, 1, 6, '2026-09-20', 'Completed', 'Photo evidence uploaded to the safety folder.'),
    (2, 2, 1, 6, '2026-09-21', 'In progress', 'Waiting for the replacement fire extinguisher.'),
    (3, 4, 1, 2, '2026-09-19', 'Completed', 'Matched all invoices to purchase orders.'),
    (4, 6, 3, 4, '2026-09-18', 'Assigned', 'Blocked until the laptop inventory is confirmed.'),
    (5, 9, 4, 5, '2026-09-22', 'Accepted', 'Sales manager review requested.'),
    (6, 5, 1, 2, '2026-09-23', 'Assigned', 'Please approve before payroll cutoff.');
"""


def _seed_additional_data(con: sqlite3.Connection) -> None:
    tables = {
        row[0]
        for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    required_tables = {"employees", "checklists", "checklist_items", "delegations"}
    if not required_tables.issubset(tables):
        return

    employee_ids = [row[0] for row in con.execute("SELECT employee_id FROM employees ORDER BY employee_id")]
    if not employee_ids:
        return

    checklist_count = con.execute("SELECT COUNT(*) FROM checklists").fetchone()[0]
    if checklist_count < 50:
        next_checklist_id = con.execute("SELECT COALESCE(MAX(checklist_id), 0) + 1 FROM checklists").fetchone()[0]
        checklist_rows = []
        departments = ["Operations", "Finance", "Human Resources", "IT", "Sales"]
        for offset in range(50):
            department = departments[offset % len(departments)]
            due_date = date(2026, 10, 1) + timedelta(days=offset % 28)
            checklist_rows.append(
                (
                    next_checklist_id + offset,
                    f"{department} weekly action review {offset + 1:02d}",
                    department,
                    employee_ids[offset % len(employee_ids)],
                    due_date.isoformat(),
                    ("Not started", "In progress", "Completed")[offset % 3],
                )
            )
        con.executemany(
            "INSERT OR IGNORE INTO checklists VALUES (?, ?, ?, ?, ?, ?)",
            checklist_rows,
        )

    item_count = con.execute("SELECT COUNT(*) FROM checklist_items").fetchone()[0]
    if item_count < 200:
        checklist_ids = [row[0] for row in con.execute("SELECT checklist_id FROM checklists ORDER BY checklist_id")]
        next_item_id = con.execute("SELECT COALESCE(MAX(item_id), 0) + 1 FROM checklist_items").fetchone()[0]
        item_rows = []
        statuses = ["Pending", "In progress", "Completed", "Blocked"]
        priorities = ["Low", "Medium", "High", "Critical"]
        for offset in range(200):
            status = statuses[offset % len(statuses)]
            due_date = date(2026, 9, 1) + timedelta(days=offset % 45)
            item_rows.append(
                (
                    next_item_id + offset,
                    checklist_ids[offset % len(checklist_ids)],
                    f"Complete delegated company task {offset + 1:03d}",
                    employee_ids[(offset + 1) % len(employee_ids)],
                    due_date.isoformat(),
                    status,
                    priorities[offset % len(priorities)],
                    due_date.isoformat() if status == "Completed" else None,
                )
            )
        con.executemany(
            "INSERT OR IGNORE INTO checklist_items VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            item_rows,
        )

    delegation_count = con.execute("SELECT COUNT(*) FROM delegations").fetchone()[0]
    if delegation_count < 200:
        item_ids = [row[0] for row in con.execute("SELECT item_id FROM checklist_items ORDER BY item_id")]
        next_delegation_id = con.execute("SELECT COALESCE(MAX(delegation_id), 0) + 1 FROM delegations").fetchone()[0]
        delegation_rows = []
        delegation_statuses = ["Assigned", "Accepted", "In progress", "Completed", "Declined"]
        for offset in range(200):
            delegation_rows.append(
                (
                    next_delegation_id + offset,
                    item_ids[offset % len(item_ids)],
                    employee_ids[offset % len(employee_ids)],
                    employee_ids[(offset + 2) % len(employee_ids)],
                    (date(2026, 8, 1) + timedelta(days=offset % 55)).isoformat(),
                    delegation_statuses[offset % len(delegation_statuses)],
                    f"Delegation update {offset + 1:03d}",
                )
            )
        con.executemany(
            "INSERT OR IGNORE INTO delegations VALUES (?, ?, ?, ?, ?, ?, ?)",
            delegation_rows,
        )


def ensure_database() -> pathlib.Path:
    """Create the local company task database the first time it is needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    database_exists = DB_PATH.exists()
    with sqlite3.connect(DB_PATH) as con:
        if not database_exists:
            con.executescript(_SCHEMA_AND_SEED)
        _seed_additional_data(con)
    return DB_PATH


def get_connection() -> sqlite3.Connection:
    ensure_database()
    return sqlite3.connect(DB_PATH)
