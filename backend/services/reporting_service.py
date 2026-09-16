import os
import json
from datetime import datetime
from sqlalchemy.orm import Session
from backend.services.analytics_service import AnalyticsService
from backend.services.ai_service import AIService
from backend.services.pdf_service import generate_pdf_from_markdown
from backend.config import settings
import structlog

logger = structlog.get_logger(__name__)

class ReportingService:
    def __init__(self, db: Session):
        self.db = db
        self.analytics_service = AnalyticsService(db)
        self.ai_service = AIService()

    def generate_report(self, period: str = "daily") -> str:
        """
        Generates a 100% AI-synthesized 10-section Executive Operational Intelligence Report (Markdown & PDF).
        The generated report contains structured Markdown scorecards, formatted tables, visual trend charts,
        AI predictive insights, and linked Obsidian runbooks.
        """
        kpi_data = self.analytics_service.get_global_kpis()
        kpi_data["period"] = period.upper()
        service_health_list = self.analytics_service.get_service_health()
        trend_data = self.analytics_service.get_time_series_trends(days=14)

        now_dt = datetime.now()
        timestamp = now_dt.strftime("%Y%m%d_%H%M%S")
        gen_time = now_dt.strftime("%Y-%m-%d %H:%M:%S")

        # Synthesize full executive report via AI service
        markdown_content = self.ai_service.generate_full_report(
            kpi_data=kpi_data,
            services_health=service_health_list,
            trend_data=trend_data,
            period=period,
            timestamp=gen_time
        )
        
        reports_dir = os.path.join(settings.PROJECT_ROOT, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        filename = f"ops_report_{period.lower()}_{timestamp}.md"
        filepath = os.path.join(reports_dir, filename)

        pdf_filename = f"ops_report_{period.lower()}_{timestamp}.pdf"
        pdf_filepath = os.path.join(reports_dir, pdf_filename)
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(markdown_content)
                
            pdf_bytes = generate_pdf_from_markdown(markdown_content, title=f"OPSINTEL {period.capitalize()} Operational Intelligence Report")
            with open(pdf_filepath, "wb") as f_pdf:
                f_pdf.write(pdf_bytes)

            logger.info("report_generated", period=period, filepath=filepath, pdf_filepath=pdf_filepath)
            return filepath
        except Exception as e:
            logger.error("report_generation_failed", period=period, error=str(e))
            raise e
