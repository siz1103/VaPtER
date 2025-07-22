import django_filters
from django.db.models import Q
from .models import Customer, Target, Scan


class CustomerFilter(django_filters.FilterSet):
    """Filter for Customer model"""
    
    name = django_filters.CharFilter(lookup_expr='icontains')
    company_name = django_filters.CharFilter(lookup_expr='icontains')
    email = django_filters.CharFilter(lookup_expr='icontains')
    contact_person = django_filters.CharFilter(lookup_expr='icontains')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = Customer
        fields = ['name', 'company_name', 'email', 'contact_person']


class TargetFilter(django_filters.FilterSet):
    """Filter for Target model"""
    
    customer = django_filters.ModelChoiceFilter(queryset=Customer.objects.all())
    customer_name = django_filters.CharFilter(field_name='customer__name', lookup_expr='icontains')
    name = django_filters.CharFilter(lookup_expr='icontains')
    address = django_filters.CharFilter(lookup_expr='icontains')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    # Custom filter for targets with recent scans
    has_recent_scans = django_filters.BooleanFilter(method='filter_has_recent_scans')
    
    class Meta:
        model = Target
        fields = ['customer', 'name', 'address']
    
    def filter_has_recent_scans(self, queryset, name, value):
        """Filter targets that have scans in the last 30 days"""
        if value:
            from django.utils import timezone
            from datetime import timedelta
            thirty_days_ago = timezone.now() - timedelta(days=30)
            return queryset.filter(scans__initiated_at__gte=thirty_days_ago).distinct()
        return queryset


class ScanFilter(django_filters.FilterSet):
    """Filter for Scan model"""
    
    target = django_filters.ModelChoiceFilter(queryset=Target.objects.all())
    target_name = django_filters.CharFilter(field_name='target__name', lookup_expr='icontains')
    target_address = django_filters.CharFilter(field_name='target__address', lookup_expr='icontains')
    customer = django_filters.ModelChoiceFilter(field_name='target__customer', queryset=Customer.objects.all())
    customer_name = django_filters.CharFilter(field_name='target__customer__name', lookup_expr='icontains')
    
    status = django_filters.ChoiceFilter(choices=Scan.STATUS_CHOICES)
    status_in = django_filters.MultipleChoiceFilter(
        field_name='status',
        choices=Scan.STATUS_CHOICES,
        conjoined=False  # OR logic
    )
    
    # Date filters
    initiated_after = django_filters.DateTimeFilter(field_name='initiated_at', lookup_expr='gte')
    initiated_before = django_filters.DateTimeFilter(field_name='initiated_at', lookup_expr='lte')
    completed_after = django_filters.DateTimeFilter(field_name='completed_at', lookup_expr='gte')
    completed_before = django_filters.DateTimeFilter(field_name='completed_at', lookup_expr='lte')
    
    # Custom filters
    is_running = django_filters.BooleanFilter(method='filter_is_running')
    is_completed = django_filters.BooleanFilter(method='filter_is_completed')
    has_errors = django_filters.BooleanFilter(method='filter_has_errors')
    
    class Meta:
        model = Scan
        fields = ['target', 'scan_type', 'status']
    
    def filter_is_running(self, queryset, name, value):
        """Filter running scans"""
        running_statuses = [
            'Queued', 'Nmap Scan Running', 'Finger Scan Running',
            'Gce Scan Running', 'Web Scan Running', 'Vuln Lookup Running',
            'Report Generation Running'
        ]
        if value:
            return queryset.filter(status__in=running_statuses)
        else:
            return queryset.exclude(status__in=running_statuses)
    
    def filter_is_completed(self, queryset, name, value):
        """Filter completed scans"""
        if value:
            return queryset.filter(status='Completed')
        else:
            return queryset.exclude(status='Completed')
    
    def filter_has_errors(self, queryset, name, value):
        """Filter scans with errors"""
        if value:
            return queryset.filter(Q(status='Failed') | Q(error_message__isnull=False))
        else:
            return queryset.filter(status__ne='Failed', error_message__isnull=True)