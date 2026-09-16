import uuid
from sqlalchemy import (
    Column,
    String,
    Float,
    DateTime,
    Boolean,
    ForeignKey,
    Integer,
    Table,
    Text,
    Index
)
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.core.database import Base

def _utcnow():
    return datetime.now()

def _generate_uuid():
    return str(uuid.uuid4())

# ============================================================================
# Identity, RBAC & Security Association Tables
# ============================================================================

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", String, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime, default=_utcnow)
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", String, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", String, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime, default=_utcnow)
)

# ============================================================================
# Identity & RBAC Entity Models
# ============================================================================

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(String, primary_key=True, default=_generate_uuid, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

    def __repr__(self):
        return f"<Permission {self.name}>"


class Role(Base):
    __tablename__ = "roles"

    id = Column(String, primary_key=True, default=_generate_uuid, index=True)
    name = Column(String, unique=True, nullable=False, index=True)  # ADMIN | ANALYST | VIEWER
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles", lazy="joined")

    def __repr__(self):
        return f"<Role {self.name}>"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_generate_uuid, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=True, index=True)
    password_hash = Column(String, nullable=False)
    display_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    token_version = Column(Integer, default=1, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    roles = relationship("Role", secondary=user_roles, back_populates="users", lazy="joined")
    assigned_incidents = relationship("Incident", back_populates="assigned_user", foreign_keys="Incident.assigned_user_id")
    reported_incidents = relationship("Incident", back_populates="reporter_user", foreign_keys="Incident.reporter_user_id")
    owned_problems = relationship("Problem", back_populates="owner", foreign_keys="Problem.owner_user_id")
    requested_changes = relationship("Change", back_populates="requester", foreign_keys="Change.requester_user_id")
    implemented_changes = relationship("Change", back_populates="implementer", foreign_keys="Change.implementer_user_id")
    owned_services = relationship("Service", back_populates="owner", foreign_keys="Service.owner_user_id")
    audit_events = relationship("AuditEvent", back_populates="actor", foreign_keys="AuditEvent.actor_user_id")

    @property
    def role_names(self):
        return [r.name for r in self.roles]

    @property
    def permission_names(self):
        perms = set()
        for r in self.roles:
            for p in r.permissions:
                perms.add(p.name)
        return list(perms)

    def __repr__(self):
        return f"<User {self.username}>"


# ============================================================================
# Enterprise ITSM Operational Data Models
# ============================================================================

class Service(Base):
    __tablename__ = "services"

    id = Column(String, primary_key=True, default=_generate_uuid, index=True)
    service_id = Column(String, unique=True, index=True, nullable=False)  # e.g. SVC_PAYMENT
    external_id = Column(String, unique=True, index=True, nullable=True)
    service_name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    criticality = Column(String, nullable=False, index=True)  # CRITICAL, HIGH, MEDIUM, LOW
    owner_user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    support_group = Column(String, nullable=True)
    status = Column(String, default="OPERATIONAL", nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    owner = relationship("User", back_populates="owned_services", foreign_keys=[owner_user_id])
    incidents = relationship("Incident", back_populates="service", foreign_keys="Incident.service_id")
    problems = relationship("Problem", back_populates="service", foreign_keys="Problem.service_id")
    changes = relationship("Change", back_populates="service", foreign_keys="Change.service_id")
    sla_records = relationship("SLARecord", back_populates="service", foreign_keys="SLARecord.service_id")

    def __repr__(self):
        return f"<Service {self.service_id}: {self.service_name}>"


class Problem(Base):
    __tablename__ = "problems"

    id = Column(String, primary_key=True, default=_generate_uuid, index=True)
    problem_id = Column(String, unique=True, index=True, nullable=False)  # e.g. PRB001001
    external_id = Column(String, unique=True, index=True, nullable=True)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    priority = Column(String, nullable=True, index=True)  # P1, P2, P3, P4
    status = Column(String, nullable=False, index=True)    # OPEN, INVESTIGATING, KNOWN_ERROR, RESOLVED, CLOSED
    category = Column(String, nullable=True)
    root_cause_category = Column(String, nullable=True)
    root_cause_text = Column(Text, nullable=True)
    workaround = Column(Text, nullable=True)
    resolution = Column(Text, nullable=True)
    kedb_status = Column(String, nullable=True)           # PUBLISHED, DRAFT, NONE
    service_id = Column(String, ForeignKey("services.service_id", ondelete="RESTRICT"), nullable=False, index=True)
    owner_user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    assignment_group = Column(String, nullable=True, index=True)
    age_days = Column(Float, nullable=True)
    opened_at = Column(DateTime, default=_utcnow, nullable=True, index=True)
    target_resolution_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    service = relationship("Service", back_populates="problems", foreign_keys=[service_id])
    owner = relationship("User", back_populates="owned_problems", foreign_keys=[owner_user_id])
    incidents = relationship("Incident", back_populates="problem", foreign_keys="Incident.problem_id")
    changes = relationship("Change", back_populates="problem", foreign_keys="Change.problem_id")

    def __repr__(self):
        return f"<Problem {self.problem_id}: {self.status}>"


class Change(Base):
    __tablename__ = "changes"

    id = Column(String, primary_key=True, default=_generate_uuid, index=True)
    change_id = Column(String, unique=True, index=True, nullable=False)  # e.g. CHG001001
    external_id = Column(String, unique=True, index=True, nullable=True)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    change_type = Column(String, nullable=False, index=True)  # STANDARD, NORMAL, EMERGENCY
    risk_level = Column(String, nullable=False, index=True)   # HIGH, MEDIUM, LOW
    impact = Column(String, nullable=True)                   # HIGH, MEDIUM, LOW
    status = Column(String, nullable=False, index=True)       # DRAFT, REQUESTED, APPROVED, IN_PROGRESS, COMPLETED, FAILED, CANCELLED
    cab_status = Column(String, nullable=True)               # APPROVED, REJECTED, PENDING
    approval_status = Column(String, nullable=True)          # APPROVED, PENDING, REJECTED
    implementation_plan = Column(Text, nullable=True)
    implementation_start = Column(DateTime, nullable=True)
    implementation_end = Column(DateTime, nullable=True)
    rollback_plan = Column(Text, nullable=True)
    rollback_required = Column(Boolean, default=False, nullable=True)
    successful = Column(Boolean, default=True, nullable=True)
    service_id = Column(String, ForeignKey("services.service_id", ondelete="RESTRICT"), nullable=False, index=True)
    requester_user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    implementer_user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    assignment_group = Column(String, nullable=True, index=True)
    problem_id = Column(String, ForeignKey("problems.problem_id", ondelete="SET NULL"), nullable=True, index=True)
    completed_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    service = relationship("Service", back_populates="changes", foreign_keys=[service_id])
    problem = relationship("Problem", back_populates="changes", foreign_keys=[problem_id])
    requester = relationship("User", back_populates="requested_changes", foreign_keys=[requester_user_id])
    implementer = relationship("User", back_populates="implemented_changes", foreign_keys=[implementer_user_id])
    correlated_incidents = relationship("Incident", back_populates="related_change", foreign_keys="Incident.related_change_id")

    def __repr__(self):
        return f"<Change {self.change_id}: {self.change_type} - {self.status}>"


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, default=_generate_uuid, index=True)
    incident_id = Column(String, unique=True, index=True, nullable=False)  # e.g. INC001001
    external_id = Column(String, unique=True, index=True, nullable=True)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    priority = Column(String, nullable=False, index=True)  # P1, P2, P3, P4
    urgency = Column(String, nullable=True)               # HIGH, MEDIUM, LOW
    impact = Column(String, nullable=True)                # HIGH, MEDIUM, LOW
    status = Column(String, nullable=False, index=True)    # NEW, IN_PROGRESS, ON_HOLD, RESOLVED, CLOSED
    category = Column(String, nullable=True)
    subcategory = Column(String, nullable=True)
    service_id = Column(String, ForeignKey("services.service_id", ondelete="RESTRICT"), nullable=False, index=True)
    assignment_group = Column(String, nullable=True, index=True)
    assigned_user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    reporter_user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    problem_id = Column(String, ForeignKey("problems.problem_id", ondelete="SET NULL"), nullable=True, index=True)
    related_change_id = Column(String, ForeignKey("changes.change_id", ondelete="SET NULL"), nullable=True, index=True)
    resolution_code = Column(String, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    resolution_time_hours = Column(Float, nullable=True)
    opened_at = Column(DateTime, default=_utcnow, nullable=True, index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    service = relationship("Service", back_populates="incidents", foreign_keys=[service_id])
    problem = relationship("Problem", back_populates="incidents", foreign_keys=[problem_id])
    related_change = relationship("Change", back_populates="correlated_incidents", foreign_keys=[related_change_id])
    assigned_user = relationship("User", back_populates="assigned_incidents", foreign_keys=[assigned_user_id])
    reporter_user = relationship("User", back_populates="reported_incidents", foreign_keys=[reporter_user_id])
    sla_records = relationship("SLARecord", back_populates="incident", foreign_keys="SLARecord.incident_id")

    def __repr__(self):
        return f"<Incident {self.incident_id}: {self.priority} - {self.status}>"


class SLARecord(Base):
    __tablename__ = "sla_records"

    id = Column(String, primary_key=True, default=_generate_uuid, index=True)
    sla_id = Column(String, unique=True, index=True, nullable=False)
    external_id = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, nullable=True)
    service_id = Column(String, ForeignKey("services.service_id", ondelete="RESTRICT"), nullable=False, index=True)
    incident_id = Column(String, ForeignKey("incidents.incident_id", ondelete="SET NULL"), nullable=True, index=True)
    target_hours = Column(Float, nullable=False)
    actual_hours = Column(Float, nullable=False)
    target_minutes = Column(Integer, nullable=True)
    response_target_minutes = Column(Integer, nullable=True)
    resolution_target_minutes = Column(Integer, nullable=True)
    started_at = Column(DateTime, default=_utcnow, nullable=True)
    response_due_at = Column(DateTime, nullable=True)
    resolution_due_at = Column(DateTime, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    status = Column(String, default="IN_PROGRESS", nullable=True)  # IN_PROGRESS, MET, BREACHED
    breached = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    service = relationship("Service", back_populates="sla_records", foreign_keys=[service_id])
    incident = relationship("Incident", back_populates="sla_records", foreign_keys=[incident_id])

    def __repr__(self):
        return f"<SLARecord {self.sla_id}: breached={self.breached}>"


# ============================================================================
# Enterprise Audit & Event Model
# ============================================================================

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True, default=_generate_uuid, index=True)
    actor_user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    actor_username = Column(String, nullable=True)
    entity_type = Column(String, nullable=False, index=True)  # Incident, Problem, Change, Service, SLA, User
    entity_id = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False, index=True)       # CREATE, UPDATE, DELETE, ESCALATE, APPROVE, RESOLVE, CLOSE
    old_state_json = Column(Text, nullable=True)
    new_state_json = Column(Text, nullable=True)
    correlation_id = Column(String, nullable=True, index=True)
    timestamp_utc = Column(DateTime, default=_utcnow, nullable=False, index=True)

    actor = relationship("User", back_populates="audit_events", foreign_keys=[actor_user_id])

    def __repr__(self):
        return f"<AuditEvent {self.action} on {self.entity_type}:{self.entity_id}>"


# ============================================================================
# Ingestion, Dataset & Scheduler Pipeline Models
# ============================================================================

class DatasetVersion(Base):
    __tablename__ = "dataset_versions"
    version_id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime, default=_utcnow)


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"
    job_id = Column(String, primary_key=True, index=True)
    status = Column(String, index=True)
    filename = Column(String, nullable=True)
    entity_type = Column(String, nullable=True)
    records_processed = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utcnow)


class SchedulerRun(Base):
    __tablename__ = "scheduler_runs"
    run_id = Column(String, primary_key=True, index=True)
    period = Column(String, nullable=False)
    triggered_at = Column(DateTime, default=_utcnow)
    status = Column(String, nullable=False)
    filepath = Column(String, nullable=True)
    channels_json = Column(String, nullable=True)


# ============================================================================
# Stage 8: Live Integration & ServiceNow Sync Infrastructure Models
# ============================================================================

class IntegrationConfig(Base):
    __tablename__ = "integration_configs"

    id = Column(String, primary_key=True, default=_generate_uuid, index=True)
    connector_name = Column(String, unique=True, index=True, nullable=False, default="servicenow")
    is_enabled = Column(Boolean, default=True, nullable=False)
    instance_url = Column(String, nullable=True)
    auth_mode = Column(String, default="basic", nullable=False)  # basic | oauth2 | token
    conflict_policy = Column(String, default="SERVICENOW_WINS", nullable=False)  # SERVICENOW_WINS | OPSINTEL_WINS | LAST_WRITE_WINS | MANUAL_REVIEW
    sync_interval_seconds = Column(Integer, default=3600, nullable=False)
    last_synced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    def __repr__(self):
        return f"<IntegrationConfig {self.connector_name}: enabled={self.is_enabled}>"


class SyncState(Base):
    __tablename__ = "sync_states"

    id = Column(String, primary_key=True, default=_generate_uuid, index=True)
    connector_name = Column(String, default="servicenow", index=True, nullable=False)
    entity_name = Column(String, index=True, nullable=False)  # incident | problem | change | service | sla
    last_successful_sync = Column(DateTime, nullable=True)
    last_attempted_sync = Column(DateTime, nullable=True)
    records_fetched = Column(Integer, default=0, nullable=False)
    records_inserted = Column(Integer, default=0, nullable=False)
    records_updated = Column(Integer, default=0, nullable=False)
    records_failed = Column(Integer, default=0, nullable=False)
    status = Column(String, default="IDLE", nullable=False, index=True)  # IDLE | RUNNING | SUCCESS | PARTIAL_SUCCESS | FAILED
    error_summary = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    def __repr__(self):
        return f"<SyncState {self.connector_name}:{self.entity_name} [{self.status}]>"


class IntegrationFailure(Base):
    __tablename__ = "integration_failures"

    id = Column(String, primary_key=True, default=_generate_uuid, index=True)
    connector_name = Column(String, default="servicenow", index=True, nullable=False)
    entity_name = Column(String, index=True, nullable=False)
    external_id = Column(String, index=True, nullable=True)
    error_class = Column(String, nullable=True, index=True)
    error_message = Column(Text, nullable=False)
    payload_hash = Column(String, nullable=True)
    attempt_count = Column(Integer, default=1, nullable=False)
    first_failure_at = Column(DateTime, default=_utcnow, nullable=False)
    last_failure_at = Column(DateTime, default=_utcnow, nullable=False, index=True)
    status = Column(String, default="FAILED", nullable=False, index=True)  # FAILED | RETRYING | RESOLVED | IGNORED
    resolved_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<IntegrationFailure {self.connector_name}:{self.entity_name}:{self.external_id} [{self.status}]>"


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(String, primary_key=True, default=_generate_uuid, index=True)
    event_id = Column(String, unique=True, index=True, nullable=False)
    idempotency_key = Column(String, unique=True, index=True, nullable=False)
    connector_name = Column(String, default="servicenow", index=True, nullable=False)
    event_type = Column(String, index=True, nullable=False)  # incident.updated | problem.created etc.
    entity_name = Column(String, index=True, nullable=False)  # incident | problem | change | service | sla
    entity_id = Column(String, index=True, nullable=True)
    signature = Column(String, nullable=True)
    status = Column(String, default="PROCESSED", nullable=False, index=True)  # PROCESSED | FAILED | REJECTED
    received_at = Column(DateTime, default=_utcnow, nullable=False, index=True)
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    def __repr__(self):
        return f"<WebhookEvent {self.event_id} [{self.status}]>"


# ============================================================================
# Stage 9: Production Scheduler & Real Delivery Subsystem Models
# ============================================================================

class ScheduledJob(Base):
    __tablename__ = "scheduled_jobs"

    id = Column(String, primary_key=True, default=_generate_uuid, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    job_type = Column(String, index=True, nullable=False)  # report.generate | notification.send | executive.digest | servicenow.sync
    status = Column(String, index=True, default="ACTIVE", nullable=False)  # ACTIVE | PAUSED | DISABLED | ERROR
    cron_expression = Column(String, nullable=False, default="0 6 * * *")
    timezone = Column(String, default="UTC", nullable=False)
    payload_json = Column(Text, nullable=True)
    owner_user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    next_run_at = Column(DateTime, nullable=True, index=True)
    last_run_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    last_failure_at = Column(DateTime, nullable=True)
    max_retries = Column(Integer, default=3, nullable=False)
    retry_delay_seconds = Column(Integer, default=60, nullable=False)
    max_retry_delay_seconds = Column(Integer, default=3600, nullable=False)
    concurrency_policy = Column(String, default="FORBID", nullable=False)  # FORBID | ALLOW | REPLACE
    timeout_seconds = Column(Integer, default=300, nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    owner = relationship("User", foreign_keys=[owner_user_id], lazy="joined")
    executions = relationship("JobExecution", back_populates="job", cascade="all, delete-orphan", order_by="desc(JobExecution.created_at)")

    def __repr__(self):
        return f"<ScheduledJob {self.name} [{self.job_type}:{self.status}] next={self.next_run_at}>"


class JobExecution(Base):
    __tablename__ = "job_executions"

    id = Column(String, primary_key=True, default=_generate_uuid, index=True)
    job_id = Column(String, ForeignKey("scheduled_jobs.id", ondelete="CASCADE"), nullable=True, index=True)
    run_id = Column(String, unique=True, index=True, nullable=False)
    worker_id = Column(String, nullable=True, index=True)
    status = Column(String, index=True, default="QUEUED", nullable=False)  # QUEUED | RUNNING | SUCCEEDED | RETRYING | FAILED | CANCELLED | SKIPPED
    attempt_number = Column(Integer, default=1, nullable=False)
    started_at = Column(DateTime, nullable=True, index=True)
    finished_at = Column(DateTime, nullable=True)
    lease_acquired_at = Column(DateTime, nullable=True)
    lease_expires_at = Column(DateTime, nullable=True, index=True)
    next_retry_at = Column(DateTime, nullable=True, index=True)
    error_class = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    result_json = Column(Text, nullable=True)
    correlation_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    job = relationship("ScheduledJob", back_populates="executions")
    deliveries = relationship("NotificationDelivery", back_populates="execution", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<JobExecution {self.run_id} [{self.status}] attempt={self.attempt_number}>"


class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"

    id = Column(String, primary_key=True, default=_generate_uuid, index=True)
    execution_id = Column(String, ForeignKey("job_executions.id", ondelete="SET NULL"), nullable=True, index=True)
    job_id = Column(String, ForeignKey("scheduled_jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    channel = Column(String, index=True, nullable=False)  # EMAIL | SLACK | TEAMS
    recipient = Column(String, nullable=False, index=True)
    subject = Column(String, nullable=True)
    template_id = Column(String, nullable=True)
    status = Column(String, index=True, default="PENDING", nullable=False)  # PENDING | SENT | FAILED | SKIPPED
    provider_message_id = Column(String, nullable=True)
    attempt_count = Column(Integer, default=1, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    next_retry_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    execution = relationship("JobExecution", back_populates="deliveries")

    def __repr__(self):
        return f"<NotificationDelivery {self.channel}:{self.recipient} [{self.status}]>"


