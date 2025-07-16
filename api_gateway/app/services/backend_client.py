import httpx
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException
from ..config import settings

logger = logging.getLogger(__name__)


class BackendClient:
    """HTTP client for communicating with Django backend"""
    
    def __init__(self):
        self.base_url = settings.BACKEND_URL.rstrip('/')
        self.timeout = settings.BACKEND_TIMEOUT
        
        # Create HTTP client with default settings
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Content-Type": "application/json",
                "User-Agent": f"{settings.PROJECT_NAME}/{settings.VERSION}"
            }
        )
    
    async def proxy_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> httpx.Response:
        """
        Proxy a request to the backend Django service
        
        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            path: API path (e.g., '/api/orchestrator/customers/')
            params: Query parameters
            json_data: JSON data for request body
            headers: Additional headers
        
        Returns:
            httpx.Response: Response from backend
        
        Raises:
            HTTPException: If backend is unreachable or returns error
        """
        try:
            # Prepare headers
            request_headers = {}
            if headers:
                request_headers.update(headers)
            
            # Log the proxied request
            logger.info(f"Proxying {method} {path} to backend")
            
            # Make request to backend
            response = await self.client.request(
                method=method,
                url=path,
                params=params,
                json=json_data,
                headers=request_headers
            )
            
            # Log response status
            logger.debug(f"Backend responded with status {response.status_code}")
            
            return response
            
        except httpx.TimeoutException:
            logger.error(f"Timeout while proxying {method} {path} to backend")
            raise HTTPException(
                status_code=504,
                detail="Backend service timeout"
            )
        except httpx.ConnectError:
            logger.error(f"Connection error while proxying {method} {path} to backend")
            raise HTTPException(
                status_code=503,
                detail="Backend service unavailable"
            )
        except Exception as e:
            logger.error(f"Unexpected error while proxying {method} {path}: {str(e)}")
            raise HTTPException(
                status_code=502,
                detail="Backend proxy error"
            )
    
    async def get(self, path: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        """Proxy GET request"""
        return await self.proxy_request("GET", path, params=params, headers=headers)
    
    async def post(self, path: str, json_data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        """Proxy POST request"""
        return await self.proxy_request("POST", path, params=params, json_data=json_data, headers=headers)
    
    async def put(self, path: str, json_data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        """Proxy PUT request"""
        return await self.proxy_request("PUT", path, params=params, json_data=json_data, headers=headers)
    
    async def patch(self, path: str, json_data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        """Proxy PATCH request"""
        return await self.proxy_request("PATCH", path, params=params, json_data=json_data, headers=headers)
    
    async def delete(self, path: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        """Proxy DELETE request"""
        return await self.proxy_request("DELETE", path, params=params, headers=headers)
    
    async def health_check(self) -> bool:
        """Check if backend is healthy"""
        try:
            response = await self.get("/api/orchestrator/customers/", params={"page_size": 1})
            return response.status_code < 500
        except Exception:
            return False
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Global backend client instance
backend_client = BackendClient()