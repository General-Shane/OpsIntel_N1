import pytest
from backend.services.notification_service import NotificationService

def test_send_notification():
    service = NotificationService()
    result = service.send_report_notification("reports/dummy_report.md")
    assert isinstance(result, dict)
    assert result.get("log") == "DISPATCHED"
