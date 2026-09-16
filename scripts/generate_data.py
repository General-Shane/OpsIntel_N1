import os
import sys
import argparse
import random
import json
from datetime import datetime, timedelta

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.database import engine, SessionLocal, Base
from backend.core.security import bootstrap_security
from backend.core.models import (
    Service,
    Incident,
    Problem,
    Change,
    SLARecord,
    DatasetVersion,
    User,
    AuditEvent
)

def init_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        bootstrap_security(db)
    finally:
        db.close()

def generate_data(seed: int):
    random.seed(seed)
    db = SessionLocal()
    bootstrap_security(db)
    
    try:
        # Fetch seeded users for ownership & assignment
        users = db.query(User).all()
        user_ids = [u.id for u in users] if users else [None]
        analyst_user = next((u for u in users if "analyst" in u.username.lower()), users[0] if users else None)
        admin_user = next((u for u in users if "admin" in u.username.lower()), users[0] if users else None)
        analyst_id = analyst_user.id if analyst_user else None
        admin_id = admin_user.id if admin_user else None

        # 1. Create Enterprise Services
        services = [
            Service(
                service_id="SVC_PAYMENT",
                external_id="SYS_SVC_001",
                service_name="Payment Gateway",
                description="Core PCI-DSS transaction processing engine and merchant settlement APIs",
                criticality="CRITICAL",
                owner_user_id=admin_id,
                support_group="Tier-3 Payments SRE",
                status="OPERATIONAL"
            ),
            Service(
                service_id="SVC_AUTH",
                external_id="SYS_SVC_002",
                service_name="Authentication",
                description="Central OAuth2, OIDC & SAML SSO Identity Provider service",
                criticality="CRITICAL",
                owner_user_id=admin_id,
                support_group="IAM Security Operations",
                status="OPERATIONAL"
            ),
            Service(
                service_id="SVC_WEB",
                external_id="SYS_SVC_003",
                service_name="Web Frontend",
                description="Enterprise client web application portal & CDN edge routing layer",
                criticality="HIGH",
                owner_user_id=analyst_id,
                support_group="Frontend Web Engineering",
                status="OPERATIONAL"
            ),
            Service(
                service_id="SVC_DB",
                external_id="SYS_SVC_004",
                service_name="Core Database",
                description="High-availability PostgreSQL relational cluster and read-replicas",
                criticality="CRITICAL",
                owner_user_id=admin_id,
                support_group="Database Reliability Team",
                status="OPERATIONAL"
            ),
            Service(
                service_id="SVC_EMAIL",
                external_id="SYS_SVC_005",
                service_name="Email Service",
                description="Asynchronous SMTP transaction dispatch & customer notification gateway",
                criticality="LOW",
                owner_user_id=analyst_id,
                support_group="Messaging Operations",
                status="OPERATIONAL"
            )
        ]
        db.add_all(services)
        db.commit()

        # Audit event for services creation
        audit_events = [
            AuditEvent(
                actor_user_id=admin_id,
                actor_username="admin",
                entity_type="Service",
                entity_id="SVC_PAYMENT",
                action="CREATE",
                new_state_json=json.dumps({"service_name": "Payment Gateway", "criticality": "CRITICAL"}),
                correlation_id="INIT_SVC_001"
            )
        ]

        # Timeframe covering 6 months of historical operational data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        def random_date(start, end):
            delta = end - start
            int_delta = int(delta.total_seconds())
            random_second = random.randint(0, max(0, int_delta))
            return start + timedelta(seconds=random_second)

        # 2. Generate Problems First (to allow Incident & Change foreign key linkage)
        problem_categories = ["Software Bug", "Hardware Failure", "Configuration Drift", "Capacity Exhaustion", "Network Latency"]
        root_causes = [
            ("Connection Pool Exhaustion", "HikariCP pool limit set too low during peak traffic surges"),
            ("Memory Leak in JVM", "Unbounded cache growth in transaction deserializer"),
            ("BGP Route Flapping", "Transatlantic transit provider routing table instability"),
            ("Database Lock Contention", "Unindexed foreign key queries causing table-level lock escalation"),
            ("Stale DNS Records", "DNS TTL configured to 86400s during multi-region failover event")
        ]

        problems = []
        for i in range(2500):
            created_at = random_date(start_date, end_date)
            status = random.choice(["OPEN", "INVESTIGATING", "KNOWN_ERROR", "RESOLVED"])
            svc = random.choice(services)
            priority = random.choice(["P1", "P2", "P3"])
            rc_cat, rc_text = random.choice(root_causes)
            resolved_at = None
            age_days = (end_date - created_at).total_seconds() / 86400

            if status == "RESOLVED":
                resolved_at = created_at + timedelta(days=random.uniform(2, 10))
                age_days = (resolved_at - created_at).total_seconds() / 86400
            
            problems.append(
                Problem(
                    problem_id=f"PRB{1000 + i}",
                    external_id=f"SYS_PRB_{1000 + i}",
                    title=f"Recurring {rc_cat} on {svc.service_name}",
                    description=f"Underlying defect causing intermittent performance degradation and errors on {svc.service_name}.",
                    priority=priority,
                    status=status,
                    category=random.choice(problem_categories),
                    root_cause_category=rc_cat,
                    root_cause_text=rc_text,
                    workaround="Restart application pods and scale read replicas during peak load windows.",
                    resolution="Applied kernel parameter tuning and updated connection pool limits in v2.4.1 release." if status == "RESOLVED" else None,
                    kedb_status="PUBLISHED" if status in ["KNOWN_ERROR", "RESOLVED"] else "DRAFT",
                    service_id=svc.service_id,
                    owner_user_id=random.choice([analyst_id, admin_id]),
                    assignment_group=svc.support_group,
                    opened_at=created_at,
                    target_resolution_at=created_at + timedelta(days=14),
                    resolved_at=resolved_at,
                    closed_at=resolved_at + timedelta(days=2) if resolved_at else None,
                    created_at=created_at,
                    age_days=age_days
                )
            )

        # High-aging problem backlog on Core Database
        for i in range(400):
            created_at = random_date(start_date, start_date + timedelta(days=5))
            problems.append(
                Problem(
                    problem_id=f"PRB90000{i}",
                    external_id=f"SYS_PRB_90000{i}",
                    title=f"Core Database Replication Lag & I/O Spikes #{i+1}",
                    description="Chronic storage I/O bottleneck observed during nightly backup window and ETL batch execution.",
                    priority="P2",
                    status="OPEN",
                    category="Capacity Exhaustion",
                    root_cause_category="Database Lock Contention",
                    root_cause_text="High lock wait timeout on ledger settlement table.",
                    workaround="Throttle bulk ingestion jobs to off-peak hours.",
                    kedb_status="DRAFT",
                    service_id="SVC_DB",
                    owner_user_id=admin_id,
                    assignment_group="Database Reliability Team",
                    opened_at=created_at,
                    created_at=created_at,
                    resolved_at=None,
                    age_days=(end_date - created_at).total_seconds() / 86400
                )
            )

        db.add_all(problems)
        db.commit()

        # Map problems by service for incident/change correlation
        problems_by_svc = {}
        for p in problems:
            problems_by_svc.setdefault(p.service_id, []).append(p)

        # 3. Generate Changes
        changes = []
        for i in range(5000):
            created_at = random_date(start_date, end_date)
            svc = random.choice(services)
            status = random.choice(["COMPLETED", "FAILED"])
            completed_at = created_at + timedelta(hours=random.uniform(1, 5))
            successful = (status == "COMPLETED")
            rollback = not successful
            chg_type = random.choice(["NORMAL", "STANDARD", "EMERGENCY"])
            risk = random.choice(["LOW", "MEDIUM", "HIGH"])
            
            # Associate to a problem on the same service with 25% probability
            linked_prb = random.choice(problems_by_svc.get(svc.service_id, [None])) if random.random() < 0.25 else None

            changes.append(
                Change(
                    change_id=f"CHG{5000 + i}",
                    external_id=f"SYS_CHG_{5000 + i}",
                    title=f"{chg_type} Release Deployment: {svc.service_name} Patch {random.randint(10, 99)}",
                    description=f"Standard deployment of application updates, configuration patches, and infrastructure provisioning for {svc.service_name}.",
                    change_type=chg_type,
                    risk_level=risk,
                    impact="HIGH" if risk == "HIGH" else "MEDIUM",
                    status=status,
                    cab_status="APPROVED" if chg_type in ["NORMAL", "EMERGENCY"] else "PRE_APPROVED",
                    approval_status="APPROVED",
                    implementation_plan="1. Drain traffic 2. Deploy blue-green containers 3. Run automated smoke tests 4. Shift DNS traffic",
                    implementation_start=created_at + timedelta(minutes=30),
                    implementation_end=completed_at,
                    rollback_plan="Revert DNS traffic to previous active target cluster and restart warm fallback instances.",
                    rollback_required=rollback,
                    successful=successful,
                    service_id=svc.service_id,
                    requester_user_id=analyst_id,
                    implementer_user_id=admin_id,
                    assignment_group=svc.support_group,
                    problem_id=linked_prb.problem_id if linked_prb else None,
                    created_at=created_at,
                    completed_at=completed_at
                )
            )

        # Failed deployment change preceding incident spike on SVC_PAYMENT
        spike_start = start_date + timedelta(days=45)
        for i in range(3):
            created_at = spike_start - timedelta(hours=random.uniform(1, 4))
            completed_at = created_at + timedelta(hours=1)
            changes.append(
                Change(
                    change_id=f"CHG90000{i}",
                    external_id=f"SYS_CHG_90000{i}",
                    title=f"Emergency Hotfix: Payment Routing Middleware v3.{i}",
                    description="Urgent deployment of updated payment gateway routing rules.",
                    change_type="EMERGENCY",
                    status="FAILED",
                    risk_level="HIGH",
                    impact="HIGH",
                    cab_status="APPROVED",
                    approval_status="APPROVED",
                    implementation_plan="Deploy payment routing binary updates across all payment nodes.",
                    rollback_plan="Execute rollback script and restore previous stable configuration.",
                    created_at=created_at,
                    completed_at=completed_at,
                    successful=False,
                    rollback_required=True,
                    service_id="SVC_PAYMENT",
                    requester_user_id=analyst_id,
                    implementer_user_id=admin_id,
                    assignment_group="Tier-3 Payments SRE"
                )
            )

        db.add_all(changes)
        db.commit()

        # Map changes by service for incident correlation
        changes_by_svc = {}
        for c in changes:
            changes_by_svc.setdefault(c.service_id, []).append(c)

        # 4. Generate Incidents with Relationships
        incident_titles = {
            "SVC_PAYMENT": ["Payment Gateway Timeout", "Credit Card Authorization Failure", "Settlement Batch Dropped", "Merchant Webhook Delay"],
            "SVC_AUTH": ["SSO Token Verification Failure", "High Latency on Token Endpoint", "MFA SMS Delivery Outage", "LDAP Sync Stalled"],
            "SVC_WEB": ["HTTP 502 Bad Gateway Spike", "Static Asset CDN Cache Miss Rate High", "Session Drop During Checkout", "Slow First Byte Time"],
            "SVC_DB": ["Database Connection Timeout", "PostgreSQL Replication Lag Breached", "Read Replica High CPU Utilization", "Vacuum Worker Lock Timeout"],
            "SVC_EMAIL": ["Customer Receipt Email Queue Jam", "SMTP Relay Connection Rejected", "Bounce Rate Exceeded Threshold", "Template Rendering Error"]
        }

        incidents = []
        for i in range(25000):
            created_at = random_date(start_date, end_date)
            svc = random.choice(services)
            priority = random.choice(["P1", "P2", "P3", "P4"])
            status = "RESOLVED" if random.random() < 0.88 else "IN_PROGRESS" if random.random() < 0.5 else "NEW"
            resolved_at = None
            resolution_time_hours = None
            
            if status == "RESOLVED":
                if priority == "P1":
                    res_time = random.uniform(0.5, 4.0)
                elif priority == "P2":
                    res_time = random.uniform(1.0, 12.0)
                else:
                    res_time = random.uniform(2.0, 48.0)
                
                resolved_at = created_at + timedelta(hours=res_time)
                resolution_time_hours = res_time

            # Deterministic relationship links
            linked_prb = random.choice(problems_by_svc.get(svc.service_id, [None])) if random.random() < 0.35 else None
            
            # Find change completed shortly before incident on same service
            svc_changes = changes_by_svc.get(svc.service_id, [])
            recent_chg = next((c for c in svc_changes if c.completed_at and timedelta(0) <= (created_at - c.completed_at) <= timedelta(hours=24)), None)

            title_choice = random.choice(incident_titles.get(svc.service_id, ["Service Disruption Detected"]))

            incidents.append(
                Incident(
                    incident_id=f"INC{10000 + i}",
                    external_id=f"SYS_INC_{10000 + i}",
                    title=f"{title_choice} (#{10000 + i})",
                    description=f"Automated alert detected operational telemetry anomaly on {svc.service_name}. Error rate spiked above standard operational baseline.",
                    priority=priority,
                    urgency="HIGH" if priority in ["P1", "P2"] else "MEDIUM" if priority == "P3" else "LOW",
                    impact="HIGH" if priority == "P1" else "MEDIUM" if priority in ["P2", "P3"] else "LOW",
                    status=status,
                    category="Application",
                    subcategory="API Endpoint",
                    service_id=svc.service_id,
                    assignment_group=svc.support_group,
                    assigned_user_id=analyst_id if status in ["IN_PROGRESS", "RESOLVED"] else None,
                    reporter_user_id=admin_id,
                    problem_id=linked_prb.problem_id if linked_prb else None,
                    related_change_id=recent_chg.change_id if recent_chg else None,
                    resolution_code="Solved (Permanently)" if status == "RESOLVED" else None,
                    resolution_notes="Restarted degraded service instances and rerouted active traffic to healthy cluster pods." if status == "RESOLVED" else None,
                    opened_at=created_at,
                    acknowledged_at=created_at + timedelta(minutes=random.randint(2, 15)),
                    resolved_at=resolved_at,
                    closed_at=resolved_at + timedelta(hours=24) if resolved_at else None,
                    created_at=created_at,
                    resolution_time_hours=resolution_time_hours
                )
            )

        # Incident spikes on SVC_PAYMENT
        for i in range(500):
            created_at = random_date(spike_start, spike_start + timedelta(days=2))
            resolved_at = created_at + timedelta(hours=random.uniform(0.1, 2.0))
            incidents.append(
                Incident(
                    incident_id=f"INC80000{i}",
                    external_id=f"SYS_INC_80000{i}",
                    title=f"Payment Gateway Transaction Rejections #{i+1}",
                    description="Customer checkout failures caused by payment routing change CHG900000 rollback failure.",
                    priority="P2",
                    urgency="HIGH",
                    impact="HIGH",
                    status="RESOLVED",
                    category="Application",
                    subcategory="Payment Processing",
                    service_id="SVC_PAYMENT",
                    assignment_group="Tier-3 Payments SRE",
                    assigned_user_id=analyst_id,
                    reporter_user_id=admin_id,
                    problem_id="PRB900000" if "PRB900000" in [p.problem_id for p in problems] else None,
                    related_change_id="CHG900000",
                    resolution_code="Rolled Back Change",
                    resolution_notes="Reverted payment routing rules to pre-release build.",
                    opened_at=created_at,
                    acknowledged_at=created_at + timedelta(minutes=3),
                    created_at=created_at,
                    resolved_at=resolved_at,
                    closed_at=resolved_at + timedelta(hours=12),
                    resolution_time_hours=(resolved_at - created_at).total_seconds() / 3600
                )
            )
        
        db.add_all(incidents)
        db.commit()

        # 5. Generate SLAs with Incident Linkages
        slas = []
        for inc in incidents:
            if inc.priority in ["P1", "P2"] and inc.resolution_time_hours:
                target_hrs = 2.0 if inc.priority == "P1" else 8.0
                actual_hrs = inc.resolution_time_hours
                breached = actual_hrs > target_hrs
                slas.append(
                    SLARecord(
                        sla_id=f"SLA_{inc.incident_id}",
                        external_id=f"SYS_SLA_{inc.incident_id}",
                        name=f"{inc.priority} Resolution SLA ({inc.service_id})",
                        service_id=inc.service_id,
                        incident_id=inc.incident_id,
                        target_hours=target_hrs,
                        actual_hours=actual_hrs,
                        target_minutes=int(target_hrs * 60),
                        response_target_minutes=15 if inc.priority == "P1" else 30,
                        resolution_target_minutes=int(target_hrs * 60),
                        started_at=inc.created_at,
                        response_due_at=inc.created_at + timedelta(minutes=15),
                        resolution_due_at=inc.created_at + timedelta(hours=target_hrs),
                        responded_at=inc.acknowledged_at or (inc.created_at + timedelta(minutes=5)),
                        resolved_at=inc.resolved_at,
                        status="BREACHED" if breached else "MET",
                        breached=breached,
                        created_at=inc.created_at
                    )
                )
        db.add_all(slas)
        db.add_all(audit_events)
        db.commit()

        print(f"Enterprise Data Generation Complete! Seed: {seed}")
        print(f"Total Services: {len(services)}")
        print(f"Total Incidents: {len(incidents)}")
        print(f"Total Problems: {len(problems)}")
        print(f"Total Changes: {len(changes)}")
        print(f"Total SLAs: {len(slas)}")
        print(f"Total Audit Events: {len(audit_events)}")

    except Exception as e:
        db.rollback()
        print(f"Error generating data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic enterprise ITSM operational data.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic generation")
    args = parser.parse_args()

    print("Initializing database schema...")
    init_db()
    print("Generating synthetic enterprise operational data...")
    generate_data(args.seed)
