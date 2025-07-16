import time
from fastapi import APIRouter, HTTPException
from ..services.backend_client import backend_client
from ..config import settings

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check for API Gateway"""
    return {
        "status": "healthy",
        "service": "api_gateway",
        "version": settings.VERSION,
        "timestamp": time.time()
    }


@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check including backend connectivity"""
    start_time = time.time()
    
    # Check backend connectivity
    backend_healthy = await backend_client.health_check()
    backend_check_time = time.time() - start_time
    
    status = "healthy" if backend_healthy else "unhealthy"
    
    health_data = {
        "status": status,
        "service": "api_gateway",
        "version": settings.VERSION,
        "timestamp": time.time(),
        "checks": {
            "backend": {
                "status": "healthy" if backend_healthy else "unhealthy",
                "url": settings.BACKEND_URL,
                "response_time_ms": round(backend_check_time * 1000, 2)
            }
        }
    }
    
    # Return 503 if any dependency is unhealthy
    if not backend_healthy:
        raise HTTPException(status_code=503, detail=health_data)
    
    return health_data


@router.get("/readiness")
async def readiness_check():
    """Kubernetes readiness probe endpoint"""
    backend_healthy = await backend_client.health_check()
    
    if not backend_healthy:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "reason": "backend_unavailable"
            }
        )
    
    return {
        "status": "ready",
        "service": "api_gateway"
    }


@router.get("/liveness")
async def liveness_check():
    """Kubernetes liveness probe endpoint"""
    return {
        "status": "alive",
        "service": "api_gateway",
        "timestamp": time.time()
    }