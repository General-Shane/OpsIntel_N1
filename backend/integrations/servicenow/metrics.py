from dataclasses import dataclass, field
from typing import Dict, Any
import threading

@dataclass
class ServiceNowMetrics:
    requests_total: int = 0
    request_failures_total: int = 0
    rate_limits_total: int = 0
    sync_records_total: int = 0
    sync_failures_total: int = 0
    writebacks_total: int = 0
    webhooks_total: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def inc_requests(self, count: int = 1):
        with self._lock:
            self.requests_total += count

    def inc_request_failures(self, count: int = 1):
        with self._lock:
            self.request_failures_total += count

    def inc_rate_limits(self, count: int = 1):
        with self._lock:
            self.rate_limits_total += count

    def inc_sync_records(self, count: int = 1):
        with self._lock:
            self.sync_records_total += count

    def inc_sync_failures(self, count: int = 1):
        with self._lock:
            self.sync_failures_total += count

    def inc_writebacks(self, count: int = 1):
        with self._lock:
            self.writebacks_total += count

    def inc_webhooks(self, count: int = 1):
        with self._lock:
            self.webhooks_total += count

    def get_summary(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "service_now_requests_total": self.requests_total,
                "service_now_request_failures_total": self.request_failures_total,
                "service_now_rate_limits_total": self.rate_limits_total,
                "service_now_sync_records_total": self.sync_records_total,
                "service_now_sync_failures_total": self.sync_failures_total,
                "service_now_writebacks_total": self.writebacks_total,
                "service_now_webhooks_total": self.webhooks_total,
            }

metrics = ServiceNowMetrics()
