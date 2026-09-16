import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
import httpx

from backend.config import settings
from backend.integrations.servicenow.auth import ServiceNowAuthProvider
from backend.integrations.servicenow.rate_limit import RateLimiter, execute_with_retry
from backend.integrations.servicenow.metrics import metrics
from backend.integrations.servicenow.exceptions import (
    ServiceNowError,
    ServiceNowAuthError,
    ServiceNowRateLimitError,
    ServiceNowTransientError,
    ServiceNowPermanentError,
    ServiceNowNotFoundError
)
from backend.integrations.servicenow.mappings import (
    opsintel_to_sn_incident,
    opsintel_to_sn_problem,
    opsintel_to_sn_change
)

class ServiceNowClient:
    """
    Enterprise client for ServiceNow Table APIs.
    Features:
      - Authenticated HTTP request execution with Token / Basic / OAuth2 credentials
      - Token bucket rate limiting and 429 Retry-After handling
      - Configurable exponential backoff retries on 5xx and transient errors
      - Automatic pagination and bounds checking
      - Metrics telemetry collection
    """
    def __init__(
        self,
        auth_provider: Optional[ServiceNowAuthProvider] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        backoff_base: Optional[float] = None,
        rate_limit_rps: Optional[float] = None
    ):
        self.auth = auth_provider or ServiceNowAuthProvider()
        self.timeout = timeout or settings.SERVICE_NOW_TIMEOUT_SECONDS
        self.max_retries = max_retries or settings.SERVICE_NOW_MAX_RETRIES
        self.backoff_base = backoff_base or settings.SERVICE_NOW_BACKOFF_BASE
        self.rate_limiter = RateLimiter(rate_limit_rps or settings.SERVICE_NOW_RATE_LIMIT_RPS)

    def test_connection(self) -> Dict[str, Any]:
        """
        Tests active connectivity against the configured ServiceNow instance.
        Returns latency and status metadata.
        """
        if not self.auth.is_configured:
            return {
                "status": "NOT_CONFIGURED",
                "message": "ServiceNow instance URL or credentials are not configured.",
                "latency_ms": 0,
                "config": self.auth.get_status_summary()
            }

        start = time.time()
        try:
            # Query a single service or incident to verify credentials and endpoint accessibility
            records = self.get_table_records(table="cmdb_ci_service", limit=1)
            latency_ms = round((time.time() - start) * 1000, 2)
            return {
                "status": "CONNECTED",
                "message": f"Successfully connected to ServiceNow instance ({self.auth.instance_url}).",
                "latency_ms": latency_ms,
                "records_reachable": len(records) >= 0,
                "config": self.auth.get_status_summary()
            }
        except ServiceNowAuthError as auth_err:
            latency_ms = round((time.time() - start) * 1000, 2)
            return {
                "status": "AUTH_FAILED",
                "message": f"Authentication failed: {str(auth_err)}",
                "latency_ms": latency_ms,
                "config": self.auth.get_status_summary()
            }
        except Exception as exc:
            latency_ms = round((time.time() - start) * 1000, 2)
            return {
                "status": "ERROR",
                "message": f"Connection failed: {str(exc)}",
                "latency_ms": latency_ms,
                "config": self.auth.get_status_summary()
            }

    def _execute_http(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
        """Executes a single HTTP request with rate-limiting, authentication, and retry handling."""
        if not self.auth.is_configured:
            raise ServiceNowAuthError("Cannot execute request: ServiceNow instance is not configured.")

        url = f"{self.auth.instance_url}{path}"
        
        def _request_fn():
            self.rate_limiter.acquire()
            metrics.inc_requests()
            with httpx.Client(timeout=self.timeout) as client:
                headers = self.auth.get_auth_headers(client)
                return client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data
                )

        try:
            return execute_with_retry(
                operation=_request_fn,
                max_retries=self.max_retries,
                backoff_base=self.backoff_base,
                on_rate_limit=lambda retry_after: metrics.inc_rate_limits()
            )
        except Exception as exc:
            metrics.inc_request_failures()
            raise exc

    def get_table_records(
        self,
        table: str,
        query: Optional[str] = None,
        fields: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieves a single page of records from ServiceNow Table API.
        Endpoint: GET /api/now/table/{table}
        """
        params: Dict[str, Any] = {
            "sysparm_limit": limit,
            "sysparm_offset": offset,
            "sysparm_display_value": "false",
            "sysparm_exclude_reference_link": "false"
        }
        if query:
            params["sysparm_query"] = query
        if fields:
            params["sysparm_fields"] = ",".join(fields)

        resp = self._execute_http("GET", f"/api/now/table/{table}", params=params)
        try:
            data = resp.json()
        except Exception as exc:
            raise ServiceNowPermanentError(f"Malformed JSON response from ServiceNow: {str(exc)}") from exc
        return data.get("result", [])

    def get_all_table_records(
        self,
        table: str,
        query: Optional[str] = None,
        fields: Optional[List[str]] = None,
        max_records: int = 1000,
        page_size: int = 100,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves all records from a ServiceNow table across multiple pages,
        with incremental filtering support via `sys_updated_on>=...`.
        """
        active_query = query or ""
        if since:
            since_str = since.strftime("%Y-%m-%d %H:%M:%S")
            time_filter = f"sys_updated_on>={since_str}"
            active_query = f"{active_query}^{time_filter}" if active_query else time_filter

        all_records: List[Dict[str, Any]] = []
        offset = 0
        current_page_size = min(page_size, max_records)

        while len(all_records) < max_records:
            fetch_limit = min(current_page_size, max_records - len(all_records))
            page_records = self.get_table_records(
                table=table,
                query=active_query,
                fields=fields,
                limit=fetch_limit,
                offset=offset
            )
            if not page_records:
                break

            all_records.extend(page_records)
            offset += len(page_records)

            if len(page_records) < fetch_limit:
                break

        return all_records

    def get_record_by_sys_id(self, table: str, sys_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single record by sys_id. Returns None if not found."""
        try:
            resp = self._execute_http("GET", f"/api/now/table/{table}/{sys_id}")
            try:
                data = resp.json()
            except Exception as exc:
                raise ServiceNowPermanentError(f"Malformed JSON response from ServiceNow: {str(exc)}") from exc
            return data.get("result")
        except ServiceNowNotFoundError:
            return None

    def create_record(self, table: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a new record in ServiceNow table via POST /api/now/table/{table}."""
        resp = self._execute_http("POST", f"/api/now/table/{table}", json_data=payload)
        try:
            data = resp.json()
        except Exception as exc:
            raise ServiceNowPermanentError(f"Malformed JSON response from ServiceNow: {str(exc)}") from exc
        return data.get("result", {})

    def update_record(self, table: str, sys_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Updates an existing record in ServiceNow table via PATCH /api/now/table/{table}/{sys_id}."""
        resp = self._execute_http("PATCH", f"/api/now/table/{table}/{sys_id}", json_data=payload)
        try:
            data = resp.json()
        except Exception as exc:
            raise ServiceNowPermanentError(f"Malformed JSON response from ServiceNow: {str(exc)}") from exc
        return data.get("result", {})

    # ========================================================================
    # Entity-Specific Helper Methods
    # ========================================================================

    def get_incidents(self, since: Optional[datetime] = None, limit: int = 500) -> List[Dict[str, Any]]:
        return self.get_all_table_records(table="incident", max_records=limit, since=since)

    def get_problems(self, since: Optional[datetime] = None, limit: int = 500) -> List[Dict[str, Any]]:
        return self.get_all_table_records(table="problem", max_records=limit, since=since)

    def get_changes(self, since: Optional[datetime] = None, limit: int = 500) -> List[Dict[str, Any]]:
        return self.get_all_table_records(table="change_request", max_records=limit, since=since)

    def get_services(self, since: Optional[datetime] = None, limit: int = 100) -> List[Dict[str, Any]]:
        return self.get_all_table_records(table="cmdb_ci_service", max_records=limit, since=since)

    def get_slas(self, since: Optional[datetime] = None, limit: int = 500) -> List[Dict[str, Any]]:
        return self.get_all_table_records(table="task_sla", max_records=limit, since=since)

    def writeback_incident(self, sys_id: str, update_dict: Dict[str, Any]) -> Dict[str, Any]:
        payload = opsintel_to_sn_incident(update_dict)
        metrics.inc_writebacks()
        return self.update_record(table="incident", sys_id=sys_id, payload=payload)

    def writeback_problem(self, sys_id: str, update_dict: Dict[str, Any]) -> Dict[str, Any]:
        payload = opsintel_to_sn_problem(update_dict)
        metrics.inc_writebacks()
        return self.update_record(table="problem", sys_id=sys_id, payload=payload)

    def writeback_change(self, sys_id: str, update_dict: Dict[str, Any]) -> Dict[str, Any]:
        payload = opsintel_to_sn_change(update_dict)
        metrics.inc_writebacks()
        return self.update_record(table="change_request", sys_id=sys_id, payload=payload)
