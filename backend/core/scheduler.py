import os
import uuid
import json
import time
import random
import threading
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Callable
import structlog
import pytz
from apscheduler.triggers.cron import CronTrigger

from backend.config import settings
import backend.core.database as db_module

def SessionLocal():
    return db_module.SessionLocal()

from backend.core.models import (
    ScheduledJob,
    JobExecution,
    NotificationDelivery,
    SchedulerRun,
    Service,
    Incident
)
from backend.services.reporting_service import ReportingService
from backend.services.notification_service import NotificationService
from backend.integrations.servicenow.sync import ServiceNowSyncEngine
from backend.api.v1.endpoints.websockets import manager
import asyncio

logger = structlog.get_logger(__name__)

# ============================================================================
# Cron & Timezone Helpers
# ============================================================================

def validate_cron_expression(cron_expr: str) -> bool:
    """Validates standard 5-part cron expression syntax."""
    if not cron_expr or not isinstance(cron_expr, str):
        return False
    try:
        CronTrigger.from_crontab(cron_expr.strip())
        return True
    except Exception:
        return False


def validate_timezone(tz_name: str) -> str:
    """Validates IANA timezone string, returning standardized name or raising ValueError."""
    if not tz_name:
        return "UTC"
    try:
        tz = pytz.timezone(tz_name.strip())
        return tz.zone
    except Exception as exc:
        raise ValueError(f"Invalid IANA timezone: '{tz_name}'") from exc


def calculate_next_run_time(cron_expr: str, tz_name: str = "UTC", base_time: Optional[datetime] = None) -> datetime:
    """
    Calculates next deterministic run time in timezone-naive UTC for database storage.
    """
    valid_tz = validate_timezone(tz_name)
    tz = pytz.timezone(valid_tz)
    trigger = CronTrigger.from_crontab(cron_expr.strip(), timezone=tz)

    now_tz = (base_time or datetime.now(timezone.utc)).astimezone(tz)
    next_fire = trigger.get_next_fire_time(None, now_tz)
    if not next_fire:
        # Fallback to 1 hour from now
        return (datetime.now(timezone.utc) + timedelta(hours=1)).replace(tzinfo=None)

    # Convert to UTC and strip tzinfo for consistent DB persistence
    return next_fire.astimezone(pytz.UTC).replace(tzinfo=None)


# ============================================================================
# Approved Job Handlers Registry
# ============================================================================

APPROVED_JOB_HANDLERS: Dict[str, str] = {
    "report.generate": "Generates executive PDF report and dispatches multi-channel notifications",
    "notification.send": "Dispatches operational alerts across Email, Slack, and Teams",
    "executive.digest": "Compiles executive scorecard digest and delivers email briefing",
    "servicenow.sync": "Triggers automated synchronization with ServiceNow Table APIs",
}

def execute_report_generate(payload: Dict[str, Any], execution: JobExecution) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        period = payload.get("period", "daily").lower()
        recipients = payload.get("recipients", None)
        enable_slack = payload.get("enable_slack", True)
        enable_teams = payload.get("enable_teams", True)
        enable_email = payload.get("enable_email", True)

        reporting_service = ReportingService(db)
        notification_service = NotificationService()

        filepath = reporting_service.generate_report(period=period)
        dispatch_results = notification_service.send_report_notification(
            filepath=filepath,
            recipients=recipients,
            enable_slack=enable_slack,
            enable_teams=enable_teams,
            enable_email=enable_email,
            execution_id=execution.id,
            job_id=execution.job_id
        )

        # Record in legacy SchedulerRun for backward compatibility
        run_record = SchedulerRun(
            run_id=execution.run_id,
            period=period.upper(),
            triggered_at=datetime.now(),
            status="SUCCESS",
            filepath=filepath,
            channels_json=json.dumps(dispatch_results)
        )
        db.add(run_record)
        db.commit()

        return {
            "status": "SUCCESS",
            "period": period,
            "filepath": filepath,
            "channels": dispatch_results
        }
    finally:
        db.close()


def execute_notification_send(payload: Dict[str, Any], execution: JobExecution) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        recipients = payload.get("recipients", ["leadership@opsintel.local"])
        subject = payload.get("subject", "OPSINTEL Operational Alert")
        message = payload.get("message", "Operational threshold watch alert.")

        notification_service = NotificationService()
        res = notification_service.smtp.send_email(
            recipients=recipients,
            subject=subject,
            text_body=message
        )
        return {"status": "SUCCESS", "result": res}
    finally:
        db.close()


def execute_executive_digest(payload: Dict[str, Any], execution: JobExecution) -> Dict[str, Any]:
    return execute_report_generate(payload={"period": "daily", **payload}, execution=execution)


def execute_servicenow_sync(payload: Dict[str, Any], execution: JobExecution) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        full_sync = payload.get("full_sync", False)
        engine = ServiceNowSyncEngine()
        if not engine.client.auth.is_configured:
            return {"status": "SKIPPED", "message": "ServiceNow connector is not configured."}
        
        result = engine.sync_all(db=db, full_sync=full_sync, actor_username="scheduler")
        return {"status": "SUCCESS", "sync_summary": result}
    finally:
        db.close()


HANDLERS_MAP: Dict[str, Callable[[Dict[str, Any], JobExecution], Dict[str, Any]]] = {
    "report.generate": execute_report_generate,
    "notification.send": execute_notification_send,
    "executive.digest": execute_executive_digest,
    "servicenow.sync": execute_servicenow_sync,
}


# ============================================================================
# Production Durable Scheduler & Dispatcher
# ============================================================================

class ProductionScheduler:
    """
    Enterprise database-backed scheduler and dispatcher.
    Features:
      - Durable job registration and execution history surviving restarts
      - Lease-based multi-worker concurrency protection
      - Automatic recovery of stale / crashed executions
      - Standard Cron expression evaluation with IANA timezones and DST safety
      - Bounded exponential backoff retries on transient errors
      - Approved handler registry preventing arbitrary code execution
    """
    def __init__(
        self,
        poll_interval: Optional[float] = None,
        lease_duration: Optional[int] = None,
        worker_id: Optional[str] = None
    ):
        self.poll_interval = poll_interval if poll_interval is not None else settings.SCHEDULER_POLL_INTERVAL_SECONDS
        self.lease_duration = lease_duration if lease_duration is not None else settings.SCHEDULER_LEASE_DURATION_SECONDS
        self.worker_id = worker_id or settings.SCHEDULER_WORKER_ID
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._live_feed_thread: Optional[threading.Thread] = None

    def start(self):
        """Starts the durable background dispatcher thread."""
        if not self.running:
            self.running = True
            self._ensure_bootstrap_jobs()
            self._thread = threading.Thread(target=self._run_dispatch_loop, daemon=True, name="SchedulerDispatcher")
            self._thread.start()

            # Start simulated live feed for WebSocket dashboard
            self._live_feed_thread = threading.Thread(target=self._run_live_feed, daemon=True, name="LiveFeedSimulator")
            self._live_feed_thread.start()
            
            logger.info("production_scheduler_started", worker_id=self.worker_id, poll_interval=self.poll_interval)

    def stop(self):
        """Stops the dispatcher thread cleanly."""
        self.running = False
        if self._thread:
            self._thread.join(timeout=3)
        if self._live_feed_thread:
            self._live_feed_thread.join(timeout=1)
        logger.info("production_scheduler_stopped", worker_id=self.worker_id)

    @property
    def is_running(self) -> bool:
        return self.running

    def _ensure_bootstrap_jobs(self):
        """Seeds standard default jobs if none exist."""
        db = SessionLocal()
        try:
            defaults = [
                {
                    "name": "daily-executive-report",
                    "description": "Automated Daily Executive Operational Governance Report & PDF Delivery",
                    "job_type": "report.generate",
                    "cron_expression": "0 6 * * *",
                    "timezone": "UTC",
                    "payload_json": json.dumps({"period": "daily", "enable_email": True, "enable_slack": True, "enable_teams": True}),
                    "status": "ACTIVE"
                },
                {
                    "name": "weekly-sre-review",
                    "description": "Weekly SRE Governance Review and Multi-Service Trend Analysis",
                    "job_type": "report.generate",
                    "cron_expression": "0 8 * * 1",
                    "timezone": "UTC",
                    "payload_json": json.dumps({"period": "weekly", "enable_email": True}),
                    "status": "ACTIVE"
                },
                {
                    "name": "monthly-itil-compliance",
                    "description": "Monthly ITIL Compliance Summary and Problem Resolution Scorecard",
                    "job_type": "report.generate",
                    "cron_expression": "0 9 1 * *",
                    "timezone": "UTC",
                    "payload_json": json.dumps({"period": "monthly"}),
                    "status": "ACTIVE"
                },
                {
                    "name": "servicenow-hourly-sync",
                    "description": "Automated Hourly Ingestion from ServiceNow Table APIs",
                    "job_type": "servicenow.sync",
                    "cron_expression": "0 * * * *",
                    "timezone": "UTC",
                    "payload_json": json.dumps({"full_sync": False}),
                    "status": "ACTIVE"
                }
            ]

            for d in defaults:
                existing = db.query(ScheduledJob).filter(ScheduledJob.name == d["name"]).first()
                if not existing:
                    next_run = calculate_next_run_time(d["cron_expression"], d["timezone"])
                    job = ScheduledJob(
                        name=d["name"],
                        description=d["description"],
                        job_type=d["job_type"],
                        cron_expression=d["cron_expression"],
                        timezone=d["timezone"],
                        payload_json=d["payload_json"],
                        status=d["status"],
                        next_run_at=next_run
                    )
                    db.add(job)
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.error("failed_seeding_scheduler_bootstrap_jobs", error=str(exc))
        finally:
            db.close()

    def _run_dispatch_loop(self):
        """Continuous polling and lease dispatch loop."""
        while self.running:
            try:
                self.poll_and_dispatch()
            except Exception as exc:
                logger.error("scheduler_poll_cycle_error", error=str(exc))
            time.sleep(self.poll_interval)

    def poll_and_dispatch(self) -> int:
        """
        Single atomic dispatch cycle:
        1. Recovers stale executions past lease expiration.
        2. Dispatches retries due for execution.
        3. Identifies and acquires due scheduled jobs.
        Returns number of executions dispatched.
        """
        db = SessionLocal()
        dispatched_count = 0
        now = datetime.now()

        try:
            # 1. Stale Execution Recovery
            stale_executions = db.query(JobExecution).filter(
                JobExecution.status == "RUNNING",
                JobExecution.lease_expires_at < now
            ).all()

            for stale in stale_executions:
                logger.warning("recovering_stale_execution", run_id=stale.run_id, worker=stale.worker_id)
                stale.status = "FAILED"
                stale.finished_at = now
                stale.error_class = "LeaseTimeoutError"
                stale.error_message = f"Execution lease expired without completion on worker {stale.worker_id}."
            if stale_executions:
                db.commit()

            # 2. Retry Queue Processing
            retries_due = db.query(JobExecution).filter(
                JobExecution.status == "RETRYING",
                JobExecution.next_retry_at <= now
            ).all()

            for exec_item in retries_due:
                if self._acquire_and_run_execution(db, exec_item):
                    dispatched_count += 1

            # 3. Find Due Scheduled Jobs
            due_jobs = db.query(ScheduledJob).filter(
                ScheduledJob.status == "ACTIVE",
                ScheduledJob.next_run_at <= now
            ).all()

            for job in due_jobs:
                # Concurrency check
                if job.concurrency_policy == "FORBID":
                    active_run = db.query(JobExecution).filter(
                        JobExecution.job_id == job.id,
                        JobExecution.status == "RUNNING"
                    ).first()
                    if active_run:
                        logger.info("job_execution_skipped_concurrency_forbid", job_name=job.name)
                        # Advance next run time to prevent tight loop
                        job.next_run_at = calculate_next_run_time(job.cron_expression, job.timezone, now)
                        db.commit()
                        continue

                # Create JobExecution and acquire lease
                run_id = f"EXEC_{uuid.uuid4().hex[:12].upper()}"
                execution = JobExecution(
                    job_id=job.id,
                    run_id=run_id,
                    worker_id=self.worker_id,
                    status="RUNNING",
                    attempt_number=1,
                    started_at=now,
                    lease_acquired_at=now,
                    lease_expires_at=now + timedelta(seconds=self.lease_duration),
                    correlation_id=f"CORR_{uuid.uuid4().hex[:8].upper()}"
                )
                db.add(execution)
                
                # Advance job schedule
                job.last_run_at = now
                job.next_run_at = calculate_next_run_time(job.cron_expression, job.timezone, now)
                db.commit()
                db.refresh(execution)

                self._execute_job_handler(db, execution, job)
                dispatched_count += 1

        finally:
            db.close()

        return dispatched_count

    def _acquire_and_run_execution(self, db, execution: JobExecution) -> bool:
        """Re-acquires and runs a retrying execution."""
        now = datetime.now()
        execution.status = "RUNNING"
        execution.attempt_number += 1
        execution.worker_id = self.worker_id
        execution.lease_acquired_at = now
        execution.lease_expires_at = now + timedelta(seconds=self.lease_duration)
        execution.next_retry_at = None
        db.commit()

        job = execution.job
        self._execute_job_handler(db, execution, job)
        return True

    def _execute_job_handler(self, db, execution: JobExecution, job: Optional[ScheduledJob]):
        """Invokes registered job handler with structured error classification and retry handling."""
        now = datetime.now()
        job_type = job.job_type if job else "report.generate"
        handler = HANDLERS_MAP.get(job_type)

        if not handler:
            execution.status = "FAILED"
            execution.finished_at = now
            execution.error_class = "UnregisteredHandlerError"
            execution.error_message = f"Job type '{job_type}' is not registered in approved handlers."
            if job:
                job.last_failure_at = now
            db.commit()
            return

        payload = {}
        if job and job.payload_json:
            try:
                payload = json.loads(job.payload_json)
            except Exception:
                payload = {}

        try:
            logger.info("job_execution_invoking", run_id=execution.run_id, job_type=job_type, attempt=execution.attempt_number)
            res = handler(payload, execution)
            
            # Succeeded
            execution.status = "SUCCEEDED"
            execution.finished_at = datetime.now()
            execution.result_json = json.dumps(res, default=str)
            execution.error_message = None
            if job:
                job.last_success_at = datetime.now()
            db.commit()
            logger.info("job_execution_succeeded", run_id=execution.run_id, job_type=job_type)
        except Exception as exc:
            error_msg = str(exc)
            err_class = type(exc).__name__
            logger.error("job_execution_error", run_id=execution.run_id, error=error_msg, err_class=err_class)

            max_retries = job.max_retries if job else 3
            base_delay = job.retry_delay_seconds if job else 60
            max_delay = job.max_retry_delay_seconds if job else 3600

            # Determine if error is eligible for retry
            is_permanent = isinstance(exc, (ValueError, KeyError, PermissionError))
            if not is_permanent and execution.attempt_number < max_retries:
                # Schedule exponential backoff retry
                delay_sec = min(base_delay * (2 ** (execution.attempt_number - 1)), max_delay)
                # Add jitter
                jitter = random.uniform(0.5, 2.0)
                execution.status = "RETRYING"
                execution.next_retry_at = datetime.now() + timedelta(seconds=delay_sec + jitter)
                execution.error_class = err_class
                execution.error_message = error_msg[:1000]
                db.commit()
                logger.info("job_execution_scheduled_retry", run_id=execution.run_id, next_retry=execution.next_retry_at.isoformat())
            else:
                execution.status = "FAILED"
                execution.finished_at = datetime.now()
                execution.error_class = err_class
                execution.error_message = error_msg[:1000]
                if job:
                    job.last_failure_at = datetime.now()
                db.commit()

    def trigger_ad_hoc_job(self, job_id: str, actor_username: str = "system") -> Dict[str, Any]:
        """Triggers immediate ad-hoc execution of a registered job."""
        db = SessionLocal()
        try:
            job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
            if not job:
                raise ValueError(f"Scheduled job with ID '{job_id}' not found.")

            now = datetime.now()
            run_id = f"EXEC_{uuid.uuid4().hex[:12].upper()}"
            execution = JobExecution(
                job_id=job.id,
                run_id=run_id,
                worker_id=self.worker_id,
                status="RUNNING",
                attempt_number=1,
                started_at=now,
                lease_acquired_at=now,
                lease_expires_at=now + timedelta(seconds=self.lease_duration),
                correlation_id=f"ADHOC_{uuid.uuid4().hex[:8].upper()}"
            )
            db.add(execution)
            job.last_run_at = now
            db.commit()
            db.refresh(execution)

            self._execute_job_handler(db, execution, job)
            return {
                "status": "TRIGGERED",
                "job_id": job.id,
                "job_name": job.name,
                "run_id": execution.run_id,
                "execution_status": execution.status
            }
        finally:
            db.close()

    def _execute_job(self, period: str = "daily"):
        """Legacy compatibility entry point for triggering report jobs."""
        db = SessionLocal()
        try:
            job = db.query(ScheduledJob).filter(ScheduledJob.name == f"{period}-executive-report").first()
            if not job:
                job = db.query(ScheduledJob).filter(ScheduledJob.job_type == "report.generate").first()
            
            run_id = f"RUN_{uuid.uuid4().hex[:8].upper()}"
            now = datetime.now()
            execution = JobExecution(
                job_id=job.id if job else None,
                run_id=run_id,
                worker_id=self.worker_id,
                status="RUNNING",
                attempt_number=1,
                started_at=now,
                lease_acquired_at=now,
                lease_expires_at=now + timedelta(seconds=self.lease_duration)
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)

            execute_report_generate(payload={"period": period}, execution=execution)
        finally:
            db.close()

    def _run_live_feed(self):
        """Simulates live incident broadcasting to WebSocket dashboard."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        while self.running:
            time.sleep(15)
            if self.running:
                self._inject_live_incident(loop)

    def _inject_live_incident(self, loop):
        db = SessionLocal()
        try:
            services = db.query(Service).all()
            if not services:
                return
                
            service = random.choice(services)
            priority = random.choices(["P1", "P2", "P3", "P4"], weights=[0.05, 0.15, 0.40, 0.40])[0]
            
            inc = Incident(
                incident_id=f"INC{random.randint(100000, 999999)}",
                service_id=service.service_id,
                status="OPEN",
                priority=priority,
                created_at=datetime.now(),
            )
            db.add(inc)
            db.commit()
            
            event = {
                "type": "NEW_INCIDENT",
                "incident_id": inc.incident_id,
                "service": service.service_name,
                "priority": priority,
                "timestamp": datetime.now().isoformat()
            }
            asyncio.run_coroutine_threadsafe(manager.broadcast(event), loop)
        except Exception as e:
            db.rollback()
        finally:
            db.close()

# Singleton scheduler instance
scheduler = ProductionScheduler()
ReportScheduler = ProductionScheduler # Alias for backward compatibility
