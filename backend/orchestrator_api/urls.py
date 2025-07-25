from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomerViewSet, PortListViewSet, ScanTypeViewSet,
    TargetViewSet, ScanViewSet, ScanDetailViewSet,
    FingerprintDetailViewSet, GceResultViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'port-lists', PortListViewSet, basename='portlist')
router.register(r'scan-types', ScanTypeViewSet, basename='scantype')
router.register(r'targets', TargetViewSet, basename='target')
router.register(r'scans', ScanViewSet, basename='scan')
router.register(r'scan-details', ScanDetailViewSet, basename='scandetail')
router.register(r'fingerprint-details', FingerprintDetailViewSet)
router.register(r'gce-results', GceResultViewSet)

urlpatterns = [
    # API routes
    path('', include(router.urls)),
    path('scans/<int:pk>/gce-progress/', ScanViewSet.as_view({'patch': 'update_gce_progress'}), name='scan-gce-progress'),
    path('scans/<int:pk>/gce-results/', ScanViewSet.as_view({'post': 'create_gce_results'}), name='scan-gce-results'),
]

# API endpoints will be available at:
# /api/orchestrator/customers/
# /api/orchestrator/port-lists/
# /api/orchestrator/scan-types/
# /api/orchestrator/targets/
# /api/orchestrator/scans/
# /api/orchestrator/scan-details/

# Additional custom endpoints:
# /api/orchestrator/customers/{id}/targets/
# /api/orchestrator/customers/{id}/scans/
# /api/orchestrator/customers/{id}/statistics/
# /api/orchestrator/targets/{id}/scans/
# /api/orchestrator/targets/{id}/scan/  (POST to create scan)
# /api/orchestrator/scans/{id}/restart/  (POST)
# /api/orchestrator/scans/{id}/cancel/  (POST)
# /api/orchestrator/scans/statistics/
# /api/orchestrator/scans/{id}/gce-progress/ (PATCH)
# /api/orchestrator/scans/{id}/gce-results/ (POST)