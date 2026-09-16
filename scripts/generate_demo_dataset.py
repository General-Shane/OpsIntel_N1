import os
import sys
import csv
import random
from datetime import datetime, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SMALL_DIR = os.path.join(PROJECT_ROOT, "demo_dataset_small")
LARGE_DIR = os.path.join(PROJECT_ROOT, "demo_dataset_large_5x")

SERVICES_SMALL = [
    {"service_id": "SVC_PAYMENT", "service_name": "Payment Gateway", "criticality": "CRITICAL"},
    {"service_id": "SVC_AUTH", "service_name": "Authentication Service", "criticality": "CRITICAL"},
    {"service_id": "SVC_WEB", "service_name": "Web Frontend", "criticality": "HIGH"},
    {"service_id": "SVC_DB", "service_name": "Core Database Cluster", "criticality": "CRITICAL"},
    {"service_id": "SVC_EMAIL", "service_name": "Email Service", "criticality": "MEDIUM"},
    {"service_id": "SVC_ECOM", "service_name": "E-Commerce Platform", "criticality": "HIGH"},
    {"service_id": "SVC_ORD", "service_name": "Order Management", "criticality": "HIGH"},
    {"service_id": "SVC_INV", "service_name": "Inventory Service", "criticality": "HIGH"},
    {"service_id": "SVC_REP", "service_name": "Reporting Service", "criticality": "MEDIUM"},
    {"service_id": "SVC_SHIP", "service_name": "Shipping Service", "criticality": "MEDIUM"},
]

SERVICES_LARGE = SERVICES_SMALL + [
    {"service_id": "SVC_NET", "service_name": "Core Network Switch", "criticality": "CRITICAL"},
    {"service_id": "SVC_SEC", "service_name": "Security Gateway", "criticality": "CRITICAL"},
    {"service_id": "SVC_CRM", "service_name": "CRM System", "criticality": "HIGH"},
    {"service_id": "SVC_ERP", "service_name": "ERP Enterprise Core", "criticality": "CRITICAL"},
    {"service_id": "SVC_NOTIF", "service_name": "Push Notification Engine", "criticality": "MEDIUM"},
    {"service_id": "SVC_SEARCH", "service_name": "Elastic Search Cluster", "criticality": "HIGH"},
    {"service_id": "SVC_LOG", "service_name": "Log Analytics Platform", "criticality": "MEDIUM"},
    {"service_id": "SVC_CACHE", "service_name": "Redis Distributed Cache", "criticality": "HIGH"},
    {"service_id": "SVC_API", "service_name": "API Gateway", "criticality": "CRITICAL"},
    {"service_id": "SVC_STORAGE", "service_name": "Blob Storage Cluster", "criticality": "HIGH"},
]

def generate_dataset_pack(out_dir, services_list, inc_count, prb_count, chg_count, sla_count, label, seed=42):
    random.seed(seed)
    now = datetime.utcnow()
    os.makedirs(out_dir, exist_ok=True)
    print(f"\n--- Generating {label} in '{os.path.basename(out_dir)}' ---")

    # 1. Services
    services_rows = services_list

    # 2. Incidents
    incidents_rows = []
    for i in range(1, inc_count + 1):
        days_back = int(random.triangular(0, 90, 0))
        created_at = now - timedelta(days=days_back, hours=random.randint(0, 23), minutes=random.randint(0, 59))
        if created_at > now:
            created_at = now - timedelta(minutes=random.randint(5, 120))

        svc = random.choice(services_list)
        priority = random.choices(["P1", "P2", "P3", "P4"], weights=[12, 28, 38, 22])[0]

        status_choice = random.random()
        if status_choice < 0.91:
            status = "RESOLVED"
        elif status_choice < 0.96:
            status = "INVESTIGATING"
        else:
            status = "OPEN"

        resolved_at = None
        res_hours = None
        if status == "RESOLVED":
            if priority == "P1":
                res_hours = round(random.uniform(0.5, 3.5), 2)
            elif priority == "P2":
                res_hours = round(random.uniform(1.0, 7.5), 2)
            elif priority == "P3":
                res_hours = round(random.uniform(2.0, 18.0), 2)
            else:
                res_hours = round(random.uniform(4.0, 36.0), 2)

            resolved_at = created_at + timedelta(hours=res_hours)
            if resolved_at > now:
                resolved_at = now

        incidents_rows.append({
            "incident_id": f"INC_{i:05d}",
            "service_id": svc["service_id"],
            "service_name": svc["service_name"],
            "priority": priority,
            "status": status,
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "resolved_at": resolved_at.strftime("%Y-%m-%d %H:%M:%S") if resolved_at else "",
            "resolution_time_hours": res_hours if res_hours else ""
        })

    # 3. Problems (with live timestamps starting from today Aug 10!)
    problems_rows = []
    for i in range(1, prb_count + 1):
        svc = random.choice(services_list)
        priority = random.choices(["P1", "P2", "P3", "P4"], weights=[10, 25, 45, 20])[0]
        status = "RESOLVED" if random.random() < 0.70 else random.choice(["OPEN", "INVESTIGATING"])

        age_tier = random.choices(["<7", "7-30", "30-60", ">60"], weights=[30, 35, 20, 15])[0]
        if age_tier == "<7":
            # Include very recent problems created today (0.01 - 6.5 days)
            age_days = round(random.uniform(0.01, 6.5), 2)
        elif age_tier == "7-30":
            age_days = round(random.uniform(7.0, 29.5), 1)
        elif age_tier == "30-60":
            age_days = round(random.uniform(30.0, 59.5), 1)
        else:
            age_days = round(random.uniform(60.0, 120.0), 1)

        created_at = now - timedelta(days=age_days)

        problems_rows.append({
            "problem_id": f"PRB_{i:05d}",
            "service_id": svc["service_id"],
            "service_name": svc["service_name"],
            "priority": priority,
            "status": status,
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "age_days": age_days
        })

    # 4. Changes
    changes_rows = []
    change_types = ["Standard", "Normal", "Emergency", "Major", "Minor"]
    change_weights = [40, 30, 15, 10, 5]
    risk_levels = ["LOW", "MEDIUM", "HIGH"]

    for i in range(1, chg_count + 1):
        days_back = int(random.triangular(0, 90, 5))
        created_at = now - timedelta(days=days_back, hours=random.randint(0, 23))
        svc = random.choice(services_list)
        c_type = random.choices(change_types, weights=change_weights)[0]
        risk = "HIGH" if c_type in ["Emergency", "Major"] else random.choice(risk_levels)

        status = "COMPLETED" if random.random() < 0.94 else "SCHEDULED"
        successful = True if status == "COMPLETED" and random.random() < 0.92 else False
        rollback = True if not successful and status == "COMPLETED" and random.random() < 0.60 else False

        completed_at = created_at + timedelta(hours=random.uniform(1.0, 6.0)) if status == "COMPLETED" else None

        changes_rows.append({
            "change_id": f"CHG_{i:05d}",
            "service_id": svc["service_id"],
            "service_name": svc["service_name"],
            "change_type": c_type,
            "status": status,
            "risk_level": risk,
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "completed_at": completed_at.strftime("%Y-%m-%d %H:%M:%S") if completed_at else "",
            "successful": "true" if successful else "false",
            "rollback_required": "true" if rollback else "false"
        })

    # 5. SLA Records
    sla_rows = []
    for i in range(1, sla_count + 1):
        svc = random.choice(services_list)
        target = random.choice([2.0, 4.0, 8.0, 24.0])
        if random.random() < 0.91:
            actual = round(random.uniform(0.2, target * 0.85), 2)
            breached = "false"
        else:
            actual = round(random.uniform(target * 1.1, target * 2.5), 2)
            breached = "true"

        sla_rows.append({
            "sla_id": f"SLA_{i:05d}",
            "service_id": svc["service_id"],
            "service_name": svc["service_name"],
            "target_hours": target,
            "actual_hours": actual,
            "breached": breached
        })

    # Write files
    write_csv(os.path.join(out_dir, "services.csv"), services_rows, ["service_id", "service_name", "criticality"])
    write_csv(os.path.join(out_dir, "incidents.csv"), incidents_rows, ["incident_id", "service_id", "service_name", "priority", "status", "created_at", "resolved_at", "resolution_time_hours"])
    write_csv(os.path.join(out_dir, "problems.csv"), problems_rows, ["problem_id", "service_id", "service_name", "priority", "status", "created_at", "age_days"])
    write_csv(os.path.join(out_dir, "changes.csv"), changes_rows, ["change_id", "service_id", "service_name", "change_type", "status", "risk_level", "created_at", "completed_at", "successful", "rollback_required"])
    write_csv(os.path.join(out_dir, "slas.csv"), sla_rows, ["sla_id", "service_id", "service_name", "target_hours", "actual_hours", "breached"])

    print(f"SUCCESS: {label} generated in '{os.path.basename(out_dir)}/'")

def generate_demo_dataset():
    # 1. Generate Small Dataset
    generate_dataset_pack(SMALL_DIR, SERVICES_SMALL, 6000, 500, 1500, 2500, "Small Standard Dataset")
    # 2. Generate Large 5x Dataset
    generate_dataset_pack(LARGE_DIR, SERVICES_LARGE, 30000, 2500, 7500, 12500, "Large 5x Dataset")

def write_csv(filepath, data, fieldnames):
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"  Generated: {os.path.basename(filepath)} ({len(data)} rows)")

if __name__ == "__main__":
    generate_demo_dataset()
