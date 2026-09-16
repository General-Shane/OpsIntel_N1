import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.services.ingestion_service import IngestionService
from backend.core.models import IngestionJob
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Uploads any ITSM CSV file (Incidents, Problems, Changes, SLAs, Services) and ingests it into SQLite.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    content = await file.read()
    try:
        content_str = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding. Must be UTF-8")

    job_id = f"JOB_{uuid.uuid4().hex[:8].upper()}"
    job = IngestionJob(
        job_id=job_id,
        status="PENDING",
        filename=file.filename
    )
    db.add(job)
    db.commit()

    service = IngestionService(db)
    
    try:
        job.status = "PROCESSING"
        db.commit()
        
        result = service.process_csv(content_str)
        
        job.status = "COMPLETED"
        job.entity_type = result.get('type', 'Unknown')
        job.records_processed = result.get('success', 0)
        db.commit()
        
        return {
            "job_id": job_id,
            "filename": file.filename,
            "status": "COMPLETED",
            "result": result,
            "message": f"Successfully ingested {result.get('success', 0)} {result.get('type', 'records')} into SQLite database."
        }
    except Exception as e:
        logger.error("ingestion_failed", job_id=job_id, error=str(e))
        job.status = "FAILED"
        job.records_processed = 0
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
def get_ingestion_history(db: Session = Depends(get_db)):
    jobs = db.query(IngestionJob).order_by(IngestionJob.created_at.desc()).limit(20).all()
    return [{
        "id": job.job_id,
        "name": job.filename,
        "type": job.entity_type or "Unknown",
        "date": job.created_at.isoformat() + "Z",
        "records": job.records_processed,
        "status": job.status,
        "uploadedBy": "Admin User"
    } for job in jobs]
