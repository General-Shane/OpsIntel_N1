import csv
from io import StringIO
from datetime import datetime
import structlog
from sqlalchemy.orm import Session
from backend.core.models import Incident, Problem, Change, SLARecord, Service

logger = structlog.get_logger(__name__)

class IngestionService:
    def __init__(self, db: Session):
        self.db = db

    def _parse_date(self, date_str: str) -> datetime:
        if not date_str:
            return datetime.now()
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            try:
                return datetime.strptime(date_str, "%b %d, %Y %I:%M %p")
            except ValueError:
                return datetime.now()

    def _normalize_priority(self, raw_priority: str) -> str:
        if not raw_priority:
            return "P3"
        p = str(raw_priority).strip().upper()
        if p in ["P1", "CRITICAL", "1"]:
            return "P1"
        elif p in ["P2", "HIGH", "2"]:
            return "P2"
        elif p in ["P3", "MEDIUM", "3"]:
            return "P3"
        elif p in ["P4", "LOW", "4"]:
            return "P4"
        return p

    SERVICE_NAME_MAP = {
        'SVC_ECOM': 'E-Commerce Platform',
        'SVC_SVC_EC': 'E-Commerce Platform',
        'SVC_SHIP': 'Shipping Service',
        'SVC_SVC_SH': 'Shipping Service',
        'SVC_REP': 'Reporting Service',
        'SVC_SVC_RE': 'Reporting Service',
        'SVC_EMAIL': 'Email Service',
        'SVC_SVC_EM': 'Email Service',
        'SVC_NET': 'Core Network Switch',
        'SVC_SVC_NE': 'Core Network Switch',
        'SVC_DB': 'Core Database Cluster',
        'SVC_SVC_DB': 'Core Database Cluster',
        'SVC_AUTH': 'Authentication Service',
        'SVC_SVC_AU': 'Authentication Service',
        'SVC_PAY': 'Payment Gateway',
        'SVC_SVC_PA': 'Payment Gateway',
        'SVC_ORD': 'Order Management',
        'SVC_SVC_OR': 'Order Management',
        'SVC_INV': 'Inventory Service',
        'SVC_SVC_IN': 'Inventory Service',
    }

    def _resolve_service_id(self, service_val: str) -> str:
        if not service_val:
            return None
        clean_name = self.SERVICE_NAME_MAP.get(service_val, service_val)
        svc = self.db.query(Service).filter(Service.service_id == service_val).first()
        if svc:
            if svc.service_name in self.SERVICE_NAME_MAP:
                svc.service_name = self.SERVICE_NAME_MAP[svc.service_name]
                self.db.commit()
            return svc.service_id
        svc = self.db.query(Service).filter(Service.service_name == clean_name).first()
        if svc:
            return svc.service_id
        if service_val.startswith("SVC_"):
            new_svc_id = service_val
        else:
            new_svc_id = f"SVC_{service_val.replace(' ', '').upper()}"
        new_svc = Service(service_id=new_svc_id, service_name=clean_name, criticality="HIGH")
        self.db.add(new_svc)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            existing = self.db.query(Service).filter(Service.service_id == new_svc_id).first()
            if existing:
                return existing.service_id
        return new_svc_id

    def process_csv(self, file_contents: str) -> dict:
        """
        Auto-detects CSV entity type based on header columns and ingests into SQLite.
        """
        reader = csv.DictReader(StringIO(file_contents))
        headers = set(reader.fieldnames or [])

        if "incident_id" in headers or "id" in headers and "priority" in headers and "status" in headers:
            return self.process_incident_csv(file_contents)
        elif "problem_id" in headers or "age_days" in headers:
            return self.process_problem_csv(file_contents)
        elif "change_id" in headers or "type" in headers and "risk" in headers:
            return self.process_change_csv(file_contents)
        elif "sla_id" in headers or "target_hours" in headers:
            return self.process_sla_csv(file_contents)
        elif "service_id" in headers and "service_name" in headers:
            return self.process_service_csv(file_contents)
        else:
            # Fallback to incident processing
            return self.process_incident_csv(file_contents)

    def process_incident_csv(self, file_contents: str) -> dict:
        reader = csv.DictReader(StringIO(file_contents))
        success_count = 0
        error_count = 0
        errors = []

        for row_idx, row in enumerate(reader, start=2):
            try:
                incident_id = row.get("incident_id", "").strip() or row.get("id", "").strip()
                raw_service = row.get("service_id", "").strip() or row.get("service", "").strip()
                service_id = self._resolve_service_id(raw_service)
                
                if not incident_id or not service_id:
                    continue

                created_at_str = row.get("created_at", "").strip() or row.get("created", "").strip()
                created_at = self._parse_date(created_at_str)

                resolved_at_str = row.get("resolved_at", "").strip()
                resolved_at = self._parse_date(resolved_at_str) if resolved_at_str else None

                res_hours = float(row.get("resolution_time_hours")) if row.get("resolution_time_hours") else None

                inc = self.db.query(Incident).filter(Incident.incident_id == incident_id).first()
                if not inc:
                    inc = Incident(incident_id=incident_id)
                    self.db.add(inc)

                inc.service_id = service_id
                inc.priority = self._normalize_priority(row.get("priority", "P3"))
                inc.status = row.get("status", "OPEN")
                inc.created_at = created_at
                inc.resolved_at = resolved_at
                inc.resolution_time_hours = res_hours

                success_count += 1
            except Exception as e:
                error_count += 1
                errors.append(f"Row {row_idx}: {str(e)}")

        self.db.commit()
        return {"type": "Incidents", "processed": success_count + error_count, "success": success_count, "errors": error_count}

    def process_problem_csv(self, file_contents: str) -> dict:
        reader = csv.DictReader(StringIO(file_contents))
        success_count = 0
        error_count = 0

        for row_idx, row in enumerate(reader, start=2):
            try:
                problem_id = row.get("problem_id", "").strip() or row.get("id", "").strip()
                raw_service = row.get("service_id", "").strip() or row.get("service", "").strip()
                service_id = self._resolve_service_id(raw_service)
                if not problem_id or not service_id:
                    continue

                created_at_str = row.get("created_at", "").strip() or row.get("created", "").strip()
                created_at = self._parse_date(created_at_str)

                prb = self.db.query(Problem).filter(Problem.problem_id == problem_id).first()
                if not prb:
                    prb = Problem(problem_id=problem_id)
                    self.db.add(prb)

                prb.service_id = service_id
                prb.status = row.get("status", "OPEN")
                prb.created_at = created_at
                prb.priority = self._normalize_priority(row.get("priority", "P2"))

                success_count += 1
            except Exception as e:
                error_count += 1

        self.db.commit()
        return {"type": "Problems", "processed": success_count + error_count, "success": success_count, "errors": error_count}

    def process_change_csv(self, file_contents: str) -> dict:
        reader = csv.DictReader(StringIO(file_contents))
        success_count = 0
        error_count = 0

        for row_idx, row in enumerate(reader, start=2):
            try:
                change_id = row.get("change_id", "").strip() or row.get("id", "").strip()
                raw_service = row.get("service_id", "").strip() or row.get("service", "").strip()
                service_id = self._resolve_service_id(raw_service)
                if not change_id or not service_id:
                    continue

                created_at_str = row.get("created_at", "").strip() or row.get("created", "").strip()
                created_at = self._parse_date(created_at_str)

                successful = row.get("successful", "").lower() in ["true", "1", "yes"]

                chg = self.db.query(Change).filter(Change.change_id == change_id).first()
                if not chg:
                    chg = Change(change_id=change_id)
                    self.db.add(chg)

                chg.service_id = service_id
                chg.change_type = row.get("change_type", "Standard")
                chg.status = row.get("status", "COMPLETED")
                chg.risk_level = row.get("risk_level", "LOW")
                chg.created_at = created_at
                chg.successful = successful

                success_count += 1
            except Exception as e:
                error_count += 1

        self.db.commit()
        return {"type": "Changes", "processed": success_count + error_count, "success": success_count, "errors": error_count}

    def process_sla_csv(self, file_contents: str) -> dict:
        reader = csv.DictReader(StringIO(file_contents))
        success_count = 0
        error_count = 0

        for row_idx, row in enumerate(reader, start=2):
            try:
                sla_id = row.get("sla_id", "").strip() or row.get("id", "").strip()
                raw_service = row.get("service_id", "").strip() or row.get("service", "").strip()
                service_id = self._resolve_service_id(raw_service)
                if not sla_id or not service_id:
                    continue

                target = float(row.get("target_hours", 2.0))
                actual = float(row.get("actual_hours", 2.0))
                breached = row.get("breached", "").lower() in ["true", "1", "yes"]

                sla = self.db.query(SLARecord).filter(SLARecord.sla_id == sla_id).first()
                if not sla:
                    sla = SLARecord(sla_id=sla_id)
                    self.db.add(sla)

                sla.service_id = service_id
                sla.target_hours = target
                sla.actual_hours = actual
                sla.breached = breached

                success_count += 1
            except Exception as e:
                error_count += 1

        self.db.commit()
        return {"type": "SLA Records", "processed": success_count + error_count, "success": success_count, "errors": error_count}

    def process_service_csv(self, file_contents: str) -> dict:
        reader = csv.DictReader(StringIO(file_contents))
        success_count = 0
        error_count = 0

        for row_idx, row in enumerate(reader, start=2):
            try:
                service_id = row.get("service_id", "").strip()
                service_name = row.get("service_name", "").strip()
                if not service_id or not service_name:
                    continue

                svc = self.db.query(Service).filter(Service.service_id == service_id).first()
                if not svc:
                    svc = Service(service_id=service_id)
                    self.db.add(svc)

                svc.service_name = service_name
                svc.criticality = row.get("criticality", "HIGH")

                success_count += 1
            except Exception as e:
                error_count += 1

        self.db.commit()
        return {"type": "Services", "processed": success_count + error_count, "success": success_count, "errors": error_count}
