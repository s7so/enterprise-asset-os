"""Enterprise Accounting & Invoicing Engine (ERP / Odoo / Daftra Architecture).

Provides realistic schema, SQLite benchmark data, and query engines for
accounts receivable, unpaid invoices, aging buckets, and cash flow analysis.
"""

from __future__ import annotations

import datetime
import sqlite3
from pathlib import Path
from typing import Any

# Default path for persistent SQLite database
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "tests" / "data" / "erp_accounting.db"

# Seed Data representing realistic SME & Enterprise Invoicing
SEED_CLIENTS = [
    ("CLI-101", "شركة الأهرام للتوزيع والتوكيلات", "TAX-912840-EG", "finance@ahram-dist.com", "+201001234567", "القاهرة", 500000.0, "EGP"),
    ("CLI-102", "مجموعة النيل للتوريدات الطبية", "TAX-849201-EG", "accounts@nile-medical.eg", "+201012345678", "الجيزة", 750000.0, "EGP"),
    ("CLI-103", "الشركة الهندسية للتصنيع المتطور", "TAX-772910-EG", "billing@eng-adv.com", "+201023456789", "العاشر من رمضان", 1200000.0, "EGP"),
    ("CLI-104", "مؤسسة الدلتا للخدمات اللوجستية", "TAX-661029-EG", "invoicing@delta-logistics.net", "+201034567890", "الإسكندرية", 400000.0, "EGP"),
    ("CLI-105", "الريادة للحلول البرمجية والنظم", "TAX-552918-EG", "pay@reyada-tech.com", "+201045678901", "القرية الذكية", 300000.0, "EGP"),
    ("CLI-106", "Apex Global Trading FZE", "TAX-AE-840192", "treasury@apex-global.ae", "+97148192000", "Dubai", 150000.0, "USD"),
    ("CLI-107", "North Star Cloud Logistics", "TAX-US-992144", "ap@northstarcloud.io", "+14155552671", "San Francisco", 250000.0, "USD"),
]

# Baseline reference date for deterministic test calculations: 2026-09-18
BASE_DATE = datetime.date(2026, 9, 18)

SEED_INVOICES = [
    # Overdue > 90 days (Critical)
    ("INV-2026-0041", "CLI-101", "شركة الأهرام للتوزيع والتوكيلات", "2026-05-10", "2026-06-10", 185000.0, 35000.0, 150000.0, "EGP", "PARTIALLY_PAID", "توريد مواد خام - تشغيل مصنع بدر"),
    ("INV-2026-0055", "CLI-103", "الشركة الهندسية للتصنيع المتطور", "2026-05-20", "2026-06-20", 320000.0, 0.0, 320000.0, "EGP", "UNPAID", "عقد صيانة خطوط إنتاج نصف سنوي"),
    
    # Overdue 60-90 days (High Risk)
    ("INV-2026-0082", "CLI-102", "مجموعة النيل للتوريدات الطبية", "2026-06-25", "2026-07-25", 95000.0, 0.0, 95000.0, "EGP", "UNPAID", "توريد أجهزة فحص ومستلزمات معملية"),
    ("INV-2026-0089", "CLI-104", "مؤسسة الدلتا للخدمات اللوجستية", "2026-07-01", "2026-07-31", 140000.0, 40000.0, 100000.0, "EGP", "PARTIALLY_PAID", "شحن وتفريغ حاويات ميناء الإسكندرية"),

    # Overdue 30-60 days (Warning)
    ("INV-2026-0110", "CLI-101", "شركة الأهرام للتوزيع والتوكيلات", "2026-07-15", "2026-08-15", 85000.0, 0.0, 85000.0, "EGP", "UNPAID", "دفعة توريدات إضافية لمستودع أكتوبر"),
    ("INV-2026-0125", "CLI-105", "الريادة للحلول البرمجية والنظم", "2026-07-28", "2026-08-28", 65000.0, 20000.0, 45000.0, "EGP", "PARTIALLY_PAID", "تراخيص منصة إدارة الأصول السحابية"),
    ("INV-2026-0130", "CLI-103", "الشركة الهندسية للتصنيع المتطور", "2026-08-01", "2026-08-31", 110000.0, 0.0, 110000.0, "EGP", "UNPAID", "قطع غيار لمحطات التوليد"),

    # Overdue 1-30 days (Recent Due)
    ("INV-2026-0152", "CLI-102", "مجموعة النيل للتوريدات الطبية", "2026-08-10", "2026-09-10", 120000.0, 50000.0, 70000.0, "EGP", "PARTIALLY_PAID", "أجهزة رعاية مركزة - مستشفى النيل"),
    ("INV-2026-0160", "CLI-104", "مؤسسة الدلتا للخدمات اللوجستية", "2026-08-15", "2026-09-15", 48000.0, 0.0, 48000.0, "EGP", "UNPAID", "نقل بضائع خط القاهرة - السويس"),

    # Not Due Yet / Current (Healthy)
    ("INV-2026-0180", "CLI-101", "شركة الأهرام للتوزيع والتوكيلات", "2026-09-01", "2026-10-01", 90000.0, 0.0, 90000.0, "EGP", "UNPAID", "شحنة دورية شهر سبتمبر"),
    ("INV-2026-0185", "CLI-105", "الريادة للحلول البرمجية والنظم", "2026-09-05", "2026-10-05", 55000.0, 0.0, 55000.0, "EGP", "UNPAID", "خدمات دعم فني واستشارات سنوية"),

    # Fully Paid Invoices (Historical record)
    ("INV-2026-0010", "CLI-101", "شركة الأهرام للتوزيع والتوكيلات", "2026-03-01", "2026-04-01", 200000.0, 200000.0, 0.0, "EGP", "PAID", "سداد بالكامل بشيك رقم 9410"),
    ("INV-2026-0022", "CLI-102", "مجموعة النيل للتوريدات الطبية", "2026-03-15", "2026-04-15", 150000.0, 150000.0, 0.0, "EGP", "PAID", "تحويل بنكي فوري"),

    # USD International Transactions
    ("INV-2026-0070", "CLI-106", "Apex Global Trading FZE", "2026-06-15", "2026-07-15", 35000.0, 10000.0, 25000.0, "USD", "PARTIALLY_PAID", "International freight shipment to Jebel Ali"),
    ("INV-2026-0145", "CLI-107", "North Star Cloud Logistics", "2026-08-01", "2026-08-31", 42000.0, 0.0, 42000.0, "USD", "UNPAID", "Cloud Enterprise infrastructure subscription"),
]


def init_accounting_db(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Initialize SQLite database with clients and invoices tables and populate with seed data if empty."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            tax_id TEXT,
            email TEXT,
            phone TEXT,
            city TEXT,
            credit_limit REAL DEFAULT 0.0,
            currency TEXT DEFAULT 'EGP'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_number TEXT PRIMARY KEY,
            client_id TEXT NOT NULL,
            client_name TEXT NOT NULL,
            issue_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            amount_total REAL NOT NULL,
            amount_paid REAL NOT NULL DEFAULT 0.0,
            amount_due REAL NOT NULL,
            currency TEXT DEFAULT 'EGP',
            status TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)

    # Seed if tables are empty
    cursor.execute("SELECT COUNT(*) FROM clients")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO clients (id, name, tax_id, email, phone, city, credit_limit, currency) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            SEED_CLIENTS,
        )

    cursor.execute("SELECT COUNT(*) FROM invoices")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            """INSERT INTO invoices 
               (invoice_number, client_id, client_name, issue_date, due_date, amount_total, amount_paid, amount_due, currency, status, notes) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            SEED_INVOICES,
        )

    conn.commit()
    return conn


def calculate_days_overdue(due_date_str: str, as_of_date: datetime.date | None = None) -> int:
    """Compute days overdue relative to reference date. Negative or 0 means not overdue."""
    ref_date = as_of_date or datetime.date.today()
    try:
        due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d").date()
        diff = (ref_date - due_date).days
        return max(0, diff)
    except Exception:
        return 0


def get_unpaid_invoices_sync(
    client_name: str = "",
    min_days_overdue: int = 0,
    limit: int = 10,
    db_path: Path | str = DEFAULT_DB_PATH,
    as_of_date: datetime.date | None = None,
) -> dict[str, Any]:
    """Query unpaid/partially-paid invoices with aging breakdown and client filtering."""
    conn = init_accounting_db(db_path)
    ref_date = as_of_date or BASE_DATE
    cursor = conn.cursor()

    query = """
        SELECT invoice_number, client_id, client_name, issue_date, due_date, 
               amount_total, amount_paid, amount_due, currency, status, notes
        FROM invoices
        WHERE status IN ('UNPAID', 'PARTIALLY_PAID') AND amount_due > 0
    """
    params: list[Any] = []

    if client_name.strip():
        query += " AND client_name LIKE ?"
        params.append(f"%{client_name.strip()}%")

    query += " ORDER BY due_date ASC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    results = []
    total_outstanding = 0.0
    for row in rows:
        days_od = calculate_days_overdue(row["due_date"], as_of_date=ref_date)
        if days_od < min_days_overdue:
            continue

        if days_od >= 60:
            urgency = "CRITICAL"
        elif days_od >= 30:
            urgency = "WARNING"
        elif days_od > 0:
            urgency = "ATTENTION"
        else:
            urgency = "CURRENT"

        results.append({
            "invoice_number": row["invoice_number"],
            "client_name": row["client_name"],
            "due_date": row["due_date"],
            "days_overdue": days_od,
            "amount_total": float(row["amount_total"]),
            "amount_paid": float(row["amount_paid"]),
            "amount_due": float(row["amount_due"]),
            "currency": row["currency"],
            "status": row["status"],
            "urgency": urgency,
            "notes": row["notes"],
        })
        total_outstanding += float(row["amount_due"])

    # Sort descending by days overdue then amount due
    results.sort(key=lambda x: (x["days_overdue"], x["amount_due"]), reverse=True)
    paginated_results = results[:limit]

    return {
        "status": "success",
        "as_of_date": ref_date.isoformat(),
        "total_unpaid_found": len(results),
        "displayed_count": len(paginated_results),
        "total_outstanding_sum": total_outstanding,
        "filter_applied": {
            "client_name": client_name if client_name else "ALL",
            "min_days_overdue": min_days_overdue,
            "limit": limit,
        },
        "invoices": paginated_results,
    }


def get_cash_flow_summary_sync(
    currency: str = "EGP",
    db_path: Path | str = DEFAULT_DB_PATH,
    as_of_date: datetime.date | None = None,
) -> dict[str, Any]:
    """Generate consolidated Cash Flow & Accounts Receivable summary with aging buckets."""
    conn = init_accounting_db(db_path)
    ref_date = as_of_date or BASE_DATE
    cursor = conn.cursor()

    curr_clean = currency.strip().upper() or "EGP"

    cursor.execute("""
        SELECT invoice_number, client_name, due_date, amount_total, amount_paid, amount_due, status
        FROM invoices
        WHERE currency = ?
    """, (curr_clean,))
    rows = cursor.fetchall()
    conn.close()

    total_invoiced = 0.0
    total_collected = 0.0
    total_receivable = 0.0

    aging_buckets = {
        "current_0_to_30_days": 0.0,
        "overdue_31_to_60_days": 0.0,
        "overdue_61_to_90_days": 0.0,
        "overdue_over_90_days": 0.0,
    }

    client_balances: dict[str, float] = {}

    for r in rows:
        amt_total = float(r["amount_total"])
        amt_paid = float(r["amount_paid"])
        amt_due = float(r["amount_due"])
        c_name = str(r["client_name"])

        total_invoiced += amt_total
        total_collected += amt_paid
        total_receivable += amt_due

        if amt_due > 0:
            client_balances[c_name] = client_balances.get(c_name, 0.0) + amt_due
            days_od = calculate_days_overdue(r["due_date"], as_of_date=ref_date)

            if days_od <= 30:
                aging_buckets["current_0_to_30_days"] += amt_due
            elif 31 <= days_od <= 60:
                aging_buckets["overdue_31_to_60_days"] += amt_due
            elif 61 <= days_od <= 90:
                aging_buckets["overdue_61_to_90_days"] += amt_due
            else:
                aging_buckets["overdue_over_90_days"] += amt_due

    # Top debtors
    sorted_debtors = sorted(client_balances.items(), key=lambda x: x[1], reverse=True)
    top_debtors = [{"client_name": name, "total_debt": round(amt, 2)} for name, amt in sorted_debtors[:5]]

    # Cash flow risk evaluation
    critical_overdue = aging_buckets["overdue_61_to_90_days"] + aging_buckets["overdue_over_90_days"]
    overdue_ratio = (critical_overdue / total_receivable) if total_receivable > 0 else 0.0

    if overdue_ratio > 0.40:
        health = "HIGH_RISK"
        action = "تتطلب استدعاء عاجل لفريق التحصيل: أكثر من 40% من المستحقات متأخرة لأكثر من 60 يوماً."
    elif overdue_ratio > 0.20:
        health = "MODERATE_WARNING"
        action = "متابعة دورية: توجد مبالغ متأخرة تحتاج لجدولة مع كبار العملاء."
    else:
        health = "HEALTHY"
        action = "التدفق النقدي سليم وتوقيتات السداد ضمن الحدود المسموح بها."

    collection_rate_pct = round((total_collected / total_invoiced * 100), 1) if total_invoiced > 0 else 0.0

    return {
        "status": "success",
        "currency": curr_clean,
        "as_of_date": ref_date.isoformat(),
        "total_invoiced": round(total_invoiced, 2),
        "total_collected": round(total_collected, 2),
        "total_receivables_outstanding": round(total_receivable, 2),
        "collection_rate_pct": collection_rate_pct,
        "aging_buckets": {k: round(v, 2) for k, v in aging_buckets.items()},
        "top_5_debtor_clients": top_debtors,
        "portfolio_health": {
            "status": health,
            "critical_overdue_sum": round(critical_overdue, 2),
            "critical_overdue_ratio_pct": round(overdue_ratio * 100, 1),
            "recommended_action": action,
        },
    }
