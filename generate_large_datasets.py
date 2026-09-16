import os
import csv
import random
from datetime import datetime, timedelta

def generate_large_datasets():
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)

    services = [
        ("SVC_PAY", "Payment Gateway", "CRITICAL"),
        ("SVC_AUTH", "Authentication Service", "CRITICAL"),
        ("SVC_ECOM", "E-Commerce Platform", "HIGH"),
        ("SVC_ORD", "Order Management", "HIGH"),
        ("SVC_INV", "Inventory Service", "HIGH"),
        ("SVC_EMAIL", "Email Service", "MEDIUM"),
        ("SVC_REP", "Reporting Service", "MEDIUM"),
        ("SVC_SHIP", "Shipping Service", "MEDIUM"),
        ("SVC_DB", "Core Database Cluster", "CRITICAL"),
        ("SVC_NET", "Core Network Switch", "HIGH"),
    ]

    end_date = datetime(2026, 8, 9, 12, 0, 0)
    start_date = datetime(2026, 7, 20, 0, 0, 0)

    def random_date(start, end):
        delta = end - start
        int_delta = int(delta.total_seconds())
        random_second = random.randint(0, max(0, int_delta))
        return start + timedelta(seconds=random_second)

    # 1. Services CSV
    svc_file = os.path.join(data_dir, "large_services_data.csv")
    with open(svc_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["service_id", "service_name", "criticality"])
        for s_id, s_name, crit in services:
            writer.writerow([s_id, s_name, crit])

    # 2. Large Incidents CSV (5,000 rows)
    inc_file = os.path.join(data_dir, "large_incidents_data.csv")
    priorities = ["P1", "P2", "P3", "P4"]
    statuses = ["RESOLVED", "RESOLVED", "RESOLVED", "OPEN", "INVESTIGATING"]
    with open(inc_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["incident_id", "service_id", "priority", "status", "created_at", "resolved_at"])
        for i in range(1, 5001):
            s_id = random.choice(services)[0]
            prio = random.choice(priorities)
            stat = random.choice(statuses)
            created_dt = random_date(start_date, end_date)
            resolved_dt = created_dt + timedelta(hours=random.uniform(0.5, 8.0)) if stat == "RESOLVED" else None
            writer.writerow([
                f"INC_{i:05d}",
                s_id,
                prio,
                stat,
                created_dt.strftime("%Y-%m-%d %H:%M:%S"),
                resolved_dt.strftime("%Y-%m-%d %H:%M:%S") if resolved_dt else ""
            ])

    # 3. Large Problems CSV (500 rows)
    prb_file = os.path.join(data_dir, "large_problems_data.csv")
    with open(prb_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["problem_id", "service_id", "status", "created_at", "resolved_at"])
        for i in range(1, 501):
            s_id = random.choice(services)[0]
            stat = random.choice(["OPEN", "OPEN", "UNDER_INVESTIGATION", "RESOLVED"])
            created_dt = random_date(start_date - timedelta(days=30), end_date)
            resolved_dt = created_dt + timedelta(days=random.randint(2, 20)) if stat == "RESOLVED" else None
            writer.writerow([
                f"PRB_{i:04d}",
                s_id,
                stat,
                created_dt.strftime("%Y-%m-%d %H:%M:%S"),
                resolved_dt.strftime("%Y-%m-%d %H:%M:%S") if resolved_dt else ""
            ])

    # 4. Large Changes CSV (1,500 rows)
    chg_file = os.path.join(data_dir, "large_changes_data.csv")
    types = ["Standard", "Normal", "Emergency", "Minor", "Major"]
    risk_levels = ["LOW", "MEDIUM", "HIGH"]
    with open(chg_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["change_id", "service_id", "change_type", "status", "risk_level", "created_at", "completed_at", "successful", "rollback_required"])
        for i in range(1, 1501):
            s_id = random.choice(services)[0]
            ctype = random.choice(types)
            stat = "COMPLETED"
            risk = random.choice(risk_levels)
            success = random.random() > 0.08
            rollback = not success if random.random() > 0.5 else False
            created_dt = random_date(start_date, end_date)
            comp_dt = created_dt + timedelta(hours=random.randint(1, 4))
            writer.writerow([
                f"CHG_{i:04d}",
                s_id,
                ctype,
                stat,
                risk,
                created_dt.strftime("%Y-%m-%d %H:%M:%S"),
                comp_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "true" if success else "false",
                "true" if rollback else "false"
            ])

    # 5. Large SLA CSV (2,500 rows)
    sla_file = os.path.join(data_dir, "large_sla_data.csv")
    with open(sla_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["sla_id", "service_id", "target_hours", "actual_hours", "breached"])
        for i in range(1, 2501):
            s_id = random.choice(services)[0]
            target = random.choice([2.0, 4.0, 8.0])
            actual = target + random.uniform(-1.0, 3.0)
            breached = actual > target
            writer.writerow([
                f"SLA_{i:04d}",
                s_id,
                target,
                round(actual, 2),
                "true" if breached else "false"
            ])

    print("Large CSV datasets (5,000 Incidents, 500 Problems, 1,500 Changes, 2,500 SLAs) generated successfully in data/ directory!")

if __name__ == "__main__":
    generate_large_datasets()
