import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from ..services.backend_client import backend_client

logger = logging.getLogger(__name__)
router = APIRouter()


async def _proxy_to_backend(request: Request, path: str = "") -> JSONResponse:
    """
    Generic proxy function to forward requests to Django backend
    
    Args:
        request: FastAPI request object
        path: Additional path to append to the API path
    
    Returns:
        JSONResponse: Response from backend
    """
    try:
        # Construct full path
        full_path = f"/api/orchestrator/{path}" if path else "/api/orchestrator/"
        
        # Extract query parameters
        params = dict(request.query_params) if request.query_params else None
        
        # Extract JSON body for POST/PUT/PATCH requests
        json_data = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                json_data = await request.json()
            except:
                json_data = None
        
        # Extract relevant headers (exclude some FastAPI/uvicorn specific headers)
        headers = {}
        for name, value in request.headers.items():
            if name.lower() not in ['host', 'content-length', 'connection']:
                headers[name] = value
        
        # Make request to backend
        response = await backend_client.proxy_request(
            method=request.method,
            path=full_path,
            params=params,
            json_data=json_data,
            headers=headers
        )
        
        # Get response content
        try:
            content = response.json()
        except:
            content = {"detail": "Invalid JSON response from backend"}
        
        # Return response with same status code
        return JSONResponse(
            status_code=response.status_code,
            content=content,
            headers=dict(response.headers)
        )
    
    except HTTPException:
        # Re-raise HTTPExceptions (these are our own gateway errors)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in proxy: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal gateway error")


# Root orchestrator endpoint
@router.api_route("/", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def orchestrator_root(request: Request):
    """Proxy root orchestrator API calls"""
    return await _proxy_to_backend(request)


# Customers endpoints
@router.api_route("/customers/", methods=["GET", "POST"])
async def customers_list(request: Request):
    """Proxy customers list/create endpoints"""
    return await _proxy_to_backend(request, "customers/")


@router.api_route("/customers/{customer_id}/", methods=["GET", "PUT", "PATCH", "DELETE"])
async def customers_detail(request: Request, customer_id: str):
    """Proxy customers detail endpoints"""
    return await _proxy_to_backend(request, f"customers/{customer_id}/")


@router.api_route("/customers/{customer_id}/targets/", methods=["GET"])
async def customer_targets(request: Request, customer_id: str):
    """Proxy customer targets endpoint"""
    return await _proxy_to_backend(request, f"customers/{customer_id}/targets/")


@router.api_route("/customers/{customer_id}/scans/", methods=["GET"])
async def customer_scans(request: Request, customer_id: str):
    """Proxy customer scans endpoint"""
    return await _proxy_to_backend(request, f"customers/{customer_id}/scans/")


@router.api_route("/customers/{customer_id}/statistics/", methods=["GET"])
async def customer_statistics(request: Request, customer_id: str):
    """Proxy customer statistics endpoint"""
    return await _proxy_to_backend(request, f"customers/{customer_id}/statistics/")


# Port Lists endpoints
@router.api_route("/port-lists/", methods=["GET", "POST"])
async def port_lists(request: Request):
    """Proxy port lists endpoints"""
    return await _proxy_to_backend(request, "port-lists/")


@router.api_route("/port-lists/{port_list_id}/", methods=["GET", "PUT", "PATCH", "DELETE"])
async def port_lists_detail(request: Request, port_list_id: int):
    """Proxy port lists detail endpoints"""
    return await _proxy_to_backend(request, f"port-lists/{port_list_id}/")


# Scan Types endpoints
@router.api_route("/scan-types/", methods=["GET", "POST"])
async def scan_types(request: Request):
    """Proxy scan types endpoints"""
    return await _proxy_to_backend(request, "scan-types/")


@router.api_route("/scan-types/{scan_type_id}/", methods=["GET", "PUT", "PATCH", "DELETE"])
async def scan_types_detail(request: Request, scan_type_id: int):
    """Proxy scan types detail endpoints"""
    return await _proxy_to_backend(request, f"scan-types/{scan_type_id}/")


# Targets endpoints
@router.api_route("/targets/", methods=["GET", "POST"])
async def targets_list(request: Request):
    """Proxy targets list/create endpoints"""
    return await _proxy_to_backend(request, "targets/")


@router.api_route("/targets/{target_id}/", methods=["GET", "PUT", "PATCH", "DELETE"])
async def targets_detail(request: Request, target_id: int):
    """Proxy targets detail endpoints"""
    return await _proxy_to_backend(request, f"targets/{target_id}/")


@router.api_route("/targets/{target_id}/scans/", methods=["GET"])
async def target_scans(request: Request, target_id: int):
    """Proxy target scans endpoint"""
    return await _proxy_to_backend(request, f"targets/{target_id}/scans/")


@router.api_route("/targets/{target_id}/scan/", methods=["POST"])
async def target_scan_create(request: Request, target_id: int):
    """Proxy target scan creation endpoint"""
    return await _proxy_to_backend(request, f"targets/{target_id}/scan/")


# Scans endpoints
@router.api_route("/scans/", methods=["GET", "POST"])
async def scans_list(request: Request):
    """Proxy scans list/create endpoints"""
    return await _proxy_to_backend(request, "scans/")


@router.api_route("/scans/{scan_id}/", methods=["GET", "PUT", "PATCH", "DELETE"])
async def scans_detail(request: Request, scan_id: int):
    """Proxy scans detail endpoints"""
    return await _proxy_to_backend(request, f"scans/{scan_id}/")


@router.api_route("/scans/{scan_id}/restart/", methods=["POST"])
async def scans_restart(request: Request, scan_id: int):
    """Proxy scan restart endpoint"""
    return await _proxy_to_backend(request, f"scans/{scan_id}/restart/")


@router.api_route("/scans/{scan_id}/cancel/", methods=["POST"])
async def scans_cancel(request: Request, scan_id: int):
    """Proxy scan cancel endpoint"""
    return await _proxy_to_backend(request, f"scans/{scan_id}/cancel/")


@router.api_route("/scans/statistics/", methods=["GET"])
async def scans_statistics(request: Request):
    """Proxy scans statistics endpoint"""
    return await _proxy_to_backend(request, "scans/statistics/")


# Scan Details endpoints
@router.api_route("/scan-details/", methods=["GET", "POST"])
async def scan_details_list(request: Request):
    """Proxy scan details endpoints"""
    return await _proxy_to_backend(request, "scan-details/")


@router.api_route("/scan-details/{scan_detail_id}/", methods=["GET", "PUT", "PATCH", "DELETE"])
async def scan_details_detail(request: Request, scan_detail_id: int):
    """Proxy scan details detail endpoints"""
    return await _proxy_to_backend(request, f"scan-details/{scan_detail_id}/")


# Catch-all route for any other orchestrator paths
@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def orchestrator_catchall(request: Request, path: str):
    """Catch-all proxy for any other orchestrator API paths"""
    return await _proxy_to_backend(request, path)