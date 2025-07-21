from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.utils import timezone
import logging

from .models import Customer, PortList, ScanType, Target, Scan, ScanDetail
from .serializers import (
    CustomerSerializer, PortListSerializer, ScanTypeSerializer,
    TargetSerializer, ScanSerializer, ScanDetailSerializer,
    ScanCreateSerializer, ScanUpdateSerializer
)
from .filters import (
    CustomerFilter, TargetFilter, ScanFilter
)
from .services import ScanOrchestratorService, NmapResultsParser

logger = logging.getLogger(__name__)


class CustomerViewSet(viewsets.ModelViewSet):
    """ViewSet for Customer CRUD operations"""
    
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CustomerFilter
    search_fields = ['name', 'company_name', 'email', 'contact_person']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']
    
    @action(detail=True, methods=['get'])
    def targets(self, request, pk=None):
        """Get all targets for a specific customer"""
        customer = self.get_object()
        targets = customer.targets.all()
        
        # Apply search if provided
        search = request.query_params.get('search')
        if search:
            targets = targets.filter(
                Q(name__icontains=search) | Q(address__icontains=search)
            )
        
        serializer = TargetSerializer(targets, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def scans(self, request, pk=None):
        """Get all scans for a specific customer"""
        customer = self.get_object()
        scans = Scan.objects.filter(target__customer=customer)
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            scans = scans.filter(status=status_filter)
        
        serializer = ScanSerializer(scans, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get customer statistics"""
        customer = self.get_object()
        
        # Get counts
        targets_count = customer.targets.count()
        scans = Scan.objects.filter(target__customer=customer)
        scans_count = scans.count()
        
        # Get status distribution
        status_distribution = {}
        for status_choice in Scan.STATUS_CHOICES:
            status_code = status_choice[0]
            count = scans.filter(status=status_code).count()
            if count > 0:
                status_distribution[status_code] = count
        
        # Recent activity
        recent_scans = scans.order_by('-initiated_at')[:5]
        recent_scans_data = ScanSerializer(recent_scans, many=True).data
        
        return Response({
            'targets_count': targets_count,
            'scans_count': scans_count,
            'status_distribution': status_distribution,
            'recent_scans': recent_scans_data
        })


class PortListViewSet(viewsets.ModelViewSet):
    """ViewSet for PortList CRUD operations"""
    
    queryset = PortList.objects.all()
    serializer_class = PortListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['get'])
    def scan_types(self, request, pk=None):
        """Get scan types using this port list"""
        port_list = self.get_object()
        scan_types = port_list.scantype_set.all()
        serializer = ScanTypeSerializer(scan_types, many=True)
        return Response(serializer.data)


class ScanTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for ScanType CRUD operations"""
    
    queryset = ScanType.objects.all()
    serializer_class = ScanTypeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Optionally filter by plugins"""
        queryset = super().get_queryset()
        
        # Filter by enabled plugins
        if self.request.query_params.get('with_finger'):
            queryset = queryset.filter(plugin_finger=True)
        if self.request.query_params.get('with_enum'):
            queryset = queryset.filter(plugin_enum=True)
        if self.request.query_params.get('with_web'):
            queryset = queryset.filter(plugin_web=True)
        if self.request.query_params.get('with_vuln'):
            queryset = queryset.filter(plugin_vuln_lookup=True)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def scans(self, request, pk=None):
        """Get scans using this scan type"""
        scan_type = self.get_object()
        scans = scan_type.scans.all()
        serializer = ScanSerializer(scans, many=True)
        return Response(serializer.data)


class TargetViewSet(viewsets.ModelViewSet):
    """ViewSet for Target CRUD operations"""
    
    queryset = Target.objects.select_related('customer').all()
    serializer_class = TargetSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TargetFilter
    search_fields = ['name', 'address', 'description']
    ordering_fields = ['name', 'address', 'created_at']
    ordering = ['customer__name', 'name']
    
    @action(detail=True, methods=['get'])
    def scans(self, request, pk=None):
        """Get all scans for this target"""
        target = self.get_object()
        scans = target.scans.all()
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            scans = scans.filter(status=status_filter)
        
        serializer = ScanSerializer(scans, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def scan(self, request, pk=None):
        """Create and start a new scan for this target"""
        target = self.get_object()
        
        # Get scan_type from request data
        scan_type_id = request.data.get('scan_type_id')
        if not scan_type_id:
            return Response(
                {'error': 'scan_type_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            scan_type = ScanType.objects.get(id=scan_type_id)
        except ScanType.DoesNotExist:
            return Response(
                {'error': 'Invalid scan_type_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create scan using the specialized serializer
        scan_data = {
            'target': target.id,
            'scan_type': scan_type.id
        }
        
        serializer = ScanCreateSerializer(data=scan_data)
        if serializer.is_valid():
            scan = serializer.save()
            
            # Start the scan orchestration
            try:
                ScanOrchestratorService.start_scan(scan)
                logger.info(f"Scan {scan.id} started for target {target.name}")
            except Exception as e:
                logger.error(f"Failed to start scan {scan.id}: {str(e)}")
                scan.status = 'Failed'
                scan.error_message = f"Failed to start scan: {str(e)}"
                scan.save()
            
            # Return the created scan
            response_serializer = ScanSerializer(scan)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ScanViewSet(viewsets.ModelViewSet):
    """ViewSet for Scan CRUD operations"""
    
    queryset = Scan.objects.select_related('target', 'target__customer', 'scan_type').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ScanFilter
    search_fields = ['target__name', 'target__address', 'target__customer__name']
    ordering_fields = ['initiated_at', 'completed_at', 'status']
    ordering = ['-initiated_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return ScanCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ScanUpdateSerializer
        return ScanSerializer
    
    def perform_update(self, serializer):
        """
        Override to process nmap results when they are received
        """
        # Controlla se parsed_nmap_results è stato aggiornato
        if 'parsed_nmap_results' in serializer.validated_data:
            logger.info(f"Detected nmap results update for scan {serializer.instance.id}")
        
        # Salva le modifiche
        scan = serializer.save()
        
        # Se sono stati aggiornati i risultati nmap, processali
        if 'parsed_nmap_results' in serializer.validated_data and scan.parsed_nmap_results:
            logger.info(f"Processing nmap results for scan {scan.id}")
            from .services import NmapResultsParser
            NmapResultsParser.process_nmap_results(scan)
    
    def update(self, request, *args, **kwargs):
        """
        Override update to handle nmap results processing
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)
    
    def partial_update(self, request, *args, **kwargs):
        """
        Override partial_update to ensure it uses our custom update logic
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        """Create a new scan and start orchestration"""
        scan = serializer.save()
        
        # Start the scan orchestration
        try:
            ScanOrchestratorService.start_scan(scan)
            logger.info(f"Scan {scan.id} started for target {scan.target.name}")
        except Exception as e:
            logger.error(f"Failed to start scan {scan.id}: {str(e)}")
            scan.status = 'Failed'
            scan.error_message = f"Failed to start scan: {str(e)}"
            scan.save()
    
    @action(detail=True, methods=['post'])
    def restart(self, request, pk=None):
        """Restart a failed or completed scan"""
        scan = self.get_object()
        
        if scan.status not in ['Failed', 'Completed']:
            return Response(
                {'error': 'Can only restart failed or completed scans'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reset scan status and clear previous results
        scan.status = 'Pending'
        scan.started_at = None
        scan.completed_at = None
        scan.error_message = None
        scan.parsed_nmap_results = None
        scan.parsed_finger_results = None
        scan.parsed_enum_results = None
        scan.parsed_web_results = None
        scan.parsed_vuln_results = None
        scan.report_path = None
        scan.save()
        
        # Clear scan details if exists
        if hasattr(scan, 'details'):
            scan.details.delete()
        
        # Start the scan orchestration
        try:
            ScanOrchestratorService.start_scan(scan)
            logger.info(f"Scan {scan.id} restarted for target {scan.target.name}")
        except Exception as e:
            logger.error(f"Failed to restart scan {scan.id}: {str(e)}")
            scan.status = 'Failed'
            scan.error_message = f"Failed to restart scan: {str(e)}"
            scan.save()
        
        serializer = ScanSerializer(scan)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a running scan"""
        scan = self.get_object()
        
        if scan.status in ['Completed', 'Failed']:
            return Response(
                {'error': 'Cannot cancel completed or failed scans'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set scan as failed with cancellation message
        scan.status = 'Failed'
        scan.error_message = 'Scan cancelled by user'
        scan.completed_at = timezone.now()
        scan.save()
        
        logger.info(f"Scan {scan.id} cancelled by user")
        
        serializer = ScanSerializer(scan)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get overall scan statistics"""
        queryset = self.filter_queryset(self.get_queryset())
        
        total_scans = queryset.count()
        
        # Status distribution
        status_distribution = {}
        for status_choice in Scan.STATUS_CHOICES:
            status_code = status_choice[0]
            count = queryset.filter(status=status_code).count()
            if count > 0:
                status_distribution[status_code] = count
        
        # Recent scans
        recent_scans = queryset[:10]
        recent_scans_data = ScanSerializer(recent_scans, many=True).data
        
        return Response({
            'total_scans': total_scans,
            'status_distribution': status_distribution,
            'recent_scans': recent_scans_data
        })

class ScanDetailViewSet(viewsets.ModelViewSet):
    """ViewSet for ScanDetail CRUD operations"""
    
    queryset = ScanDetail.objects.select_related('scan').all()
    serializer_class = ScanDetailSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter by scan if provided"""
        queryset = super().get_queryset()
        scan_id = self.request.query_params.get('scan_id')
        if scan_id:
            queryset = queryset.filter(scan_id=scan_id)
        return queryset