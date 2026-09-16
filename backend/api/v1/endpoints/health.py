from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    message: str

@router.get("", response_model=HealthResponse)
def get_health():
    """
    Returns the basic health of the API.
    """
    return HealthResponse(status="HEALTHY", message="OPSINTEL API is running.")
