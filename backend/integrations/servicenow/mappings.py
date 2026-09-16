from datetime import datetime, timezone
from typing import Optional, Dict, Any, Union

def extract_reference_value(val: Any) -> Optional[str]:
    """
    Extracts the string identifier from ServiceNow reference fields,
    which can be a string, dict with 'value'/'display_value', or None.
    """
    if val is None:
        return None
    if isinstance(val, str):
        cleaned = val.strip()
        return cleaned if cleaned else None
    if isinstance(val, dict):
        if "value" in val and val["value"]:
            return str(val["value"]).strip()
        if "display_value" in val and val["display_value"]:
            return str(val["display_value"]).strip()
    return str(val).strip() if val else None


def extract_reference_display(val: Any) -> Optional[str]:
    """Extracts human-readable display label from a reference field if present."""
    if isinstance(val, dict) and "display_value" in val and val["display_value"]:
        return str(val["display_value"]).strip()
    return extract_reference_value(val)


def parse_sn_datetime(val: Any) -> Optional[datetime]:
    """
    Parses ServiceNow datetime strings (e.g. '2026-08-22 14:30:00' or ISO format)
    into a timezone-naive UTC datetime object.
    """
    if not val:
        return None
    if isinstance(val, datetime):
        return val.replace(tzinfo=None)
    val_str = str(val).strip()
    if not val_str:
        return None

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(val_str, fmt)
            return dt
        except ValueError:
            continue
    try:
        # Fallback to fromisoformat
        dt = datetime.fromisoformat(val_str.replace("Z", "+00:00"))
        return dt.replace(tzinfo=None)
    except (ValueError, TypeError):
        return None


# ============================================================================
# 1. Incident Mapping
# ============================================================================

SN_INCIDENT_STATE_MAP = {
    "1": "NEW",
    "2": "IN_PROGRESS",
    "3": "ON_HOLD",
    "6": "RESOLVED",
    "7": "CLOSED",
    "8": "CANCELED"
}

OPSINTEL_INCIDENT_STATE_TO_SN = {
    "NEW": "1",
    "OPEN": "1",
    "IN_PROGRESS": "2",
    "ON_HOLD": "3",
    "RESOLVED": "6",
    "CLOSED": "7"
}

SN_PRIORITY_MAP = {
    "1": "P1",
    "2": "P2",
    "3": "P3",
    "4": "P4",
    "5": "P4"
}

def sn_to_opsintel_incident(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalizes a raw ServiceNow incident record into an OPSINTEL Incident dictionary."""
    sys_id = extract_reference_value(raw.get("sys_id"))
    number = raw.get("number") or (f"INC-{sys_id[:8]}" if sys_id else "INC-UNKNOWN")
    
    state_raw = str(raw.get("incident_state") or raw.get("state") or "1")
    status = SN_INCIDENT_STATE_MAP.get(state_raw, "OPEN")
    
    priority_raw = str(raw.get("priority") or "3")
    priority = SN_PRIORITY_MAP.get(priority_raw, "P3")
    
    service_ref = extract_reference_value(raw.get("cmdb_ci") or raw.get("business_service") or raw.get("service_id"))
    service_id = service_ref or "SVC_GENERAL"
    if not service_id.startswith("SVC_") and len(service_id) < 20:
        service_id = f"SVC_{service_id.upper()}"
        
    problem_ref = extract_reference_value(raw.get("problem_id"))
    related_change_ref = extract_reference_value(raw.get("rfc") or raw.get("caused_by_change"))

    opened_at = parse_sn_datetime(raw.get("opened_at") or raw.get("sys_created_on"))
    resolved_at = parse_sn_datetime(raw.get("resolved_at"))
    closed_at = parse_sn_datetime(raw.get("closed_at"))
    acknowledged_at = parse_sn_datetime(raw.get("work_start"))

    return {
        "external_id": sys_id,
        "incident_id": number,
        "title": raw.get("short_description") or "ServiceNow Incident",
        "description": raw.get("description") or raw.get("short_description") or "",
        "priority": priority,
        "urgency": str(raw.get("urgency") or "HIGH" if priority in ("P1", "P2") else "MEDIUM"),
        "impact": str(raw.get("impact") or "HIGH" if priority == "P1" else "MEDIUM"),
        "status": status,
        "category": raw.get("category") or "Infrastructure",
        "subcategory": raw.get("subcategory") or "Compute",
        "service_id": service_id,
        "assignment_group": extract_reference_display(raw.get("assignment_group")) or "Service Desk",
        "problem_id": problem_ref,
        "related_change_id": related_change_ref,
        "resolution_code": raw.get("close_code") or raw.get("resolution_code"),
        "resolution_notes": raw.get("close_notes") or raw.get("resolution_notes"),
        "opened_at": opened_at or datetime.now(),
        "acknowledged_at": acknowledged_at,
        "resolved_at": resolved_at,
        "closed_at": closed_at,
    }


def opsintel_to_sn_incident(update_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Translates OPSINTEL incident updates to ServiceNow Table API payload format."""
    payload = {}
    if "status" in update_dict:
        sn_state = OPSINTEL_INCIDENT_STATE_TO_SN.get(update_dict["status"])
        if sn_state:
            payload["state"] = sn_state
            payload["incident_state"] = sn_state
    if "resolution_notes" in update_dict:
        payload["close_notes"] = update_dict["resolution_notes"]
    if "resolution_code" in update_dict:
        payload["close_code"] = update_dict["resolution_code"]
    if "assignment_group" in update_dict:
        payload["assignment_group"] = update_dict["assignment_group"]
    if "work_notes" in update_dict:
        payload["work_notes"] = update_dict["work_notes"]
    return payload


# ============================================================================
# 2. Problem Mapping
# ============================================================================

SN_PROBLEM_STATE_MAP = {
    "101": "OPEN",
    "102": "INVESTIGATING",
    "103": "KNOWN_ERROR",
    "104": "RESOLVED",
    "105": "CLOSED",
    "1": "OPEN",
    "2": "INVESTIGATING",
    "3": "KNOWN_ERROR",
    "4": "RESOLVED",
    "5": "CLOSED"
}

OPSINTEL_PROBLEM_STATE_TO_SN = {
    "OPEN": "101",
    "INVESTIGATING": "102",
    "KNOWN_ERROR": "103",
    "RESOLVED": "104",
    "CLOSED": "105"
}

def sn_to_opsintel_problem(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalizes a raw ServiceNow problem record into an OPSINTEL Problem dictionary."""
    sys_id = extract_reference_value(raw.get("sys_id"))
    number = raw.get("number") or (f"PRB-{sys_id[:8]}" if sys_id else "PRB-UNKNOWN")
    
    state_raw = str(raw.get("problem_state") or raw.get("state") or "101")
    status = SN_PROBLEM_STATE_MAP.get(state_raw, "OPEN")
    
    priority_raw = str(raw.get("priority") or "3")
    priority = SN_PRIORITY_MAP.get(priority_raw, "P3")
    
    service_ref = extract_reference_value(raw.get("cmdb_ci") or raw.get("business_service") or raw.get("service_id"))
    service_id = service_ref or "SVC_GENERAL"
    if not service_id.startswith("SVC_") and len(service_id) < 20:
        service_id = f"SVC_{service_id.upper()}"

    opened_at = parse_sn_datetime(raw.get("opened_at") or raw.get("sys_created_on"))
    resolved_at = parse_sn_datetime(raw.get("resolved_at"))
    closed_at = parse_sn_datetime(raw.get("closed_at"))

    return {
        "external_id": sys_id,
        "problem_id": number,
        "title": raw.get("short_description") or "ServiceNow Problem",
        "description": raw.get("description") or raw.get("short_description") or "",
        "priority": priority,
        "status": status,
        "category": raw.get("category") or "Infrastructure",
        "root_cause_category": raw.get("u_root_cause_category") or raw.get("root_cause_category") or "Software Defect",
        "root_cause_text": raw.get("cause_notes") or raw.get("root_cause") or "",
        "workaround": raw.get("work_around") or raw.get("workaround") or "",
        "resolution": raw.get("fix_notes") or raw.get("resolution") or "",
        "kedb_status": "PUBLISHED" if raw.get("known_error") in (True, "true", "1") else "DRAFT",
        "service_id": service_id,
        "assignment_group": extract_reference_display(raw.get("assignment_group")) or "Problem Management",
        "opened_at": opened_at or datetime.now(),
        "resolved_at": resolved_at,
        "closed_at": closed_at,
    }


def opsintel_to_sn_problem(update_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Translates OPSINTEL problem updates to ServiceNow Table API payload format."""
    payload = {}
    if "status" in update_dict:
        sn_state = OPSINTEL_PROBLEM_STATE_TO_SN.get(update_dict["status"])
        if sn_state:
            payload["problem_state"] = sn_state
            payload["state"] = sn_state
    if "workaround" in update_dict:
        payload["work_around"] = update_dict["workaround"]
    if "resolution" in update_dict:
        payload["fix_notes"] = update_dict["resolution"]
    if "root_cause_text" in update_dict:
        payload["cause_notes"] = update_dict["root_cause_text"]
    if "kedb_status" in update_dict:
        payload["known_error"] = "true" if update_dict["kedb_status"] == "PUBLISHED" else "false"
    return payload


# ============================================================================
# 3. Change Request Mapping
# ============================================================================

SN_CHANGE_STATE_MAP = {
    "-5": "DRAFT",
    "-4": "REQUESTED",
    "-3": "APPROVED",
    "-2": "IN_PROGRESS",
    "-1": "REVIEW",
    "0": "COMPLETED",
    "3": "COMPLETED",
    "4": "FAILED",
    "7": "CANCELLED"
}

OPSINTEL_CHANGE_STATE_TO_SN = {
    "DRAFT": "-5",
    "REQUESTED": "-4",
    "APPROVED": "-3",
    "IN_PROGRESS": "-2",
    "COMPLETED": "3",
    "FAILED": "4",
    "CANCELLED": "7"
}

def sn_to_opsintel_change(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalizes a raw ServiceNow change_request record into an OPSINTEL Change dictionary."""
    sys_id = extract_reference_value(raw.get("sys_id"))
    number = raw.get("number") or (f"CHG-{sys_id[:8]}" if sys_id else "CHG-UNKNOWN")
    
    state_raw = str(raw.get("state") or "-4")
    status = SN_CHANGE_STATE_MAP.get(state_raw, "REQUESTED")
    
    type_raw = str(raw.get("type") or "normal").upper()
    change_type = type_raw if type_raw in ("STANDARD", "NORMAL", "EMERGENCY") else "NORMAL"
    
    risk_raw = str(raw.get("risk") or "2")
    risk_map = {"1": "HIGH", "2": "MEDIUM", "3": "LOW", "4": "LOW"}
    risk_level = risk_map.get(risk_raw, "MEDIUM")
    
    service_ref = extract_reference_value(raw.get("cmdb_ci") or raw.get("business_service") or raw.get("service_id"))
    service_id = service_ref or "SVC_GENERAL"
    if not service_id.startswith("SVC_") and len(service_id) < 20:
        service_id = f"SVC_{service_id.upper()}"
        
    problem_ref = extract_reference_value(raw.get("parent") or raw.get("problem_id"))

    start_time = parse_sn_datetime(raw.get("start_date") or raw.get("work_start"))
    end_time = parse_sn_datetime(raw.get("end_date") or raw.get("work_end"))
    completed_time = parse_sn_datetime(raw.get("closed_at") or raw.get("end_date"))

    return {
        "external_id": sys_id,
        "change_id": number,
        "title": raw.get("short_description") or "ServiceNow Change Request",
        "description": raw.get("description") or raw.get("short_description") or "",
        "change_type": change_type,
        "risk_level": risk_level,
        "impact": "HIGH" if risk_level == "HIGH" else "MEDIUM",
        "status": status,
        "cab_status": "APPROVED" if raw.get("cab_approval") in ("approved", "APPROVED") else "PENDING",
        "approval_status": str(raw.get("approval") or "pending").upper(),
        "implementation_plan": raw.get("change_plan") or raw.get("implementation_plan") or "Automated ServiceNow Deployment",
        "implementation_start": start_time,
        "implementation_end": end_time,
        "rollback_plan": raw.get("backout_plan") or raw.get("rollback_plan") or "Execute rollback runbook",
        "rollback_required": bool(raw.get("u_rollback_required") or False),
        "successful": status == "COMPLETED",
        "service_id": service_id,
        "assignment_group": extract_reference_display(raw.get("assignment_group")) or "Release Management",
        "problem_id": problem_ref,
        "completed_at": completed_time,
    }


def opsintel_to_sn_change(update_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Translates OPSINTEL change updates to ServiceNow Table API payload format."""
    payload = {}
    if "status" in update_dict:
        sn_state = OPSINTEL_CHANGE_STATE_TO_SN.get(update_dict["status"])
        if sn_state:
            payload["state"] = sn_state
    if "rollback_plan" in update_dict:
        payload["backout_plan"] = update_dict["rollback_plan"]
    if "implementation_plan" in update_dict:
        payload["change_plan"] = update_dict["implementation_plan"]
    if "close_notes" in update_dict:
        payload["close_notes"] = update_dict["close_notes"]
    return payload


# ============================================================================
# 4. Service / CMDB Mapping
# ============================================================================

def sn_to_opsintel_service(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalizes a raw ServiceNow cmdb_ci_service record into an OPSINTEL Service dictionary."""
    sys_id = extract_reference_value(raw.get("sys_id"))
    service_id_raw = raw.get("u_service_id") or raw.get("name") or sys_id or "SVC_GENERAL"
    service_id = str(service_id_raw).upper().replace(" ", "_")
    if not service_id.startswith("SVC_"):
        service_id = f"SVC_{service_id}"
        
    crit_raw = str(raw.get("busines_criticality") or raw.get("criticality") or "2").lower()
    crit_map = {
        "1": "CRITICAL", "critical": "CRITICAL", "1 - most critical": "CRITICAL",
        "2": "HIGH", "somewhat critical": "HIGH", "2 - somewhat critical": "HIGH",
        "3": "MEDIUM", "medium": "MEDIUM", "3 - less critical": "MEDIUM",
        "4": "LOW", "low": "LOW"
    }
    criticality = crit_map.get(crit_raw, "HIGH")

    return {
        "external_id": sys_id,
        "service_id": service_id,
        "service_name": raw.get("name") or service_id,
        "description": raw.get("short_description") or raw.get("comments") or "Enterprise Service Monitored via ServiceNow CMDB",
        "criticality": criticality,
        "support_group": extract_reference_display(raw.get("support_group")) or "Tier-3 Operations",
        "status": "OPERATIONAL" if str(raw.get("operational_status") or "1") == "1" else "DEGRADED"
    }


# ============================================================================
# 5. SLA Mapping
# ============================================================================

def sn_to_opsintel_sla(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalizes a raw ServiceNow task_sla record into an OPSINTEL SLARecord dictionary."""
    sys_id = extract_reference_value(raw.get("sys_id"))
    sla_id = raw.get("u_sla_id") or (f"SLA_{sys_id[:8]}" if sys_id else "SLA_UNKNOWN")
    
    stage_raw = str(raw.get("stage") or "in_progress").lower()
    has_breached = bool(raw.get("has_breached") in (True, "true", "1", 1))
    
    status = "BREACHED" if has_breached else ("MET" if stage_raw in ("achieved", "completed") else "IN_PROGRESS")
    
    # SLA Durations (in seconds / minutes / hours)
    duration_sec = float(raw.get("duration") or 3600)
    target_hours = round(duration_sec / 3600.0, 2)
    target_minutes = int(duration_sec / 60.0)
    
    elapsed_sec = float(raw.get("business_duration") or raw.get("percentage") or 1800)
    actual_hours = round(elapsed_sec / 3600.0, 2)

    incident_ref = extract_reference_value(raw.get("task"))
    
    service_ref = extract_reference_value(raw.get("cmdb_ci") or raw.get("service"))
    service_id = service_ref or "SVC_PAYMENT"
    if not service_id.startswith("SVC_") and len(service_id) < 20:
        service_id = f"SVC_{service_id.upper()}"

    start_time = parse_sn_datetime(raw.get("start_time") or raw.get("sys_created_on"))
    end_time = parse_sn_datetime(raw.get("end_time"))
    planned_end = parse_sn_datetime(raw.get("planned_end_time"))

    return {
        "external_id": sys_id,
        "sla_id": sla_id,
        "name": raw.get("sla_name") or extract_reference_display(raw.get("sla")) or "Service Resolution SLA",
        "service_id": service_id,
        "incident_id": incident_ref,
        "target_hours": max(0.5, target_hours),
        "actual_hours": max(0.0, actual_hours),
        "target_minutes": target_minutes,
        "response_target_minutes": int(target_minutes * 0.25),
        "resolution_target_minutes": target_minutes,
        "started_at": start_time or datetime.now(),
        "response_due_at": start_time,
        "resolution_due_at": planned_end,
        "resolved_at": end_time,
        "breached": has_breached,
        "status": status
    }
