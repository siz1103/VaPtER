import uuid
from django.db import models
from django.core.validators import RegexValidator
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import ipaddress


class TimestampMixin(models.Model):
    """Abstract base class with timestamp fields"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    """Abstract base class with soft delete functionality"""
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False):
        """Override delete to perform soft delete"""
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.save(using=using)
    
    def hard_delete(self, using=None, keep_parents=False):
        """Perform actual delete from database"""
        super().delete(using=using, keep_parents=keep_parents)
    
    def restore(self):
        """Restore soft deleted object"""
        self.deleted_at = None
        self.save()


class SoftDeleteManager(models.Manager):
    """Manager that excludes soft deleted objects by default"""
    
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)
    
    def with_deleted(self):
        """Include soft deleted objects"""
        return super().get_queryset()
    
    def deleted_only(self):
        """Only soft deleted objects"""
        return super().get_queryset().filter(deleted_at__isnull=False)


class Customer(TimestampMixin, SoftDeleteMixin):
    """Customer model for multi-tenancy"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    contact_person = models.CharField(max_length=255, blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    objects = SoftDeleteManager()
    all_objects = models.Manager()  # Includes soft deleted
    
    class Meta:
        db_table = 'customer'
        ordering = ['name']
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
    
    def __str__(self):
        return self.name


class PortList(TimestampMixin, SoftDeleteMixin):
    """Port list configuration for scans"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    tcp_ports = models.TextField(
        null=True, 
        blank=True,
        help_text="Comma-separated list of TCP ports (e.g., '22,80,443' or '1-1000')"
    )
    udp_ports = models.TextField(
        null=True, 
        blank=True,
        help_text="Comma-separated list of UDP ports (e.g., '53,161,514' or '1-1000')"
    )
    description = models.TextField(null=True, blank=True)
    
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    
    class Meta:
        db_table = 'port_list'
        ordering = ['name']
        verbose_name = 'Port List'
        verbose_name_plural = 'Port Lists'
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Validate port format"""
        if not self.tcp_ports and not self.udp_ports:
            raise ValidationError("At least one of TCP ports or UDP ports must be specified")
        
        # Validate port format (basic validation)
        for ports, port_type in [(self.tcp_ports, 'TCP'), (self.udp_ports, 'UDP')]:
            if ports:
                self._validate_port_string(ports, port_type)
    
    def _validate_port_string(self, ports_string, port_type):
        """Validate port string format"""
        try:
            parts = [p.strip() for p in ports_string.split(',')]
            for part in parts:
                if '-' in part:
                    # Range validation
                    start, end = part.split('-')
                    start_port, end_port = int(start), int(end)
                    if not (1 <= start_port <= 65535) or not (1 <= end_port <= 65535):
                        raise ValidationError(f"Invalid {port_type} port range: {part}")
                    if start_port > end_port:
                        raise ValidationError(f"Invalid {port_type} port range: {part} (start > end)")
                else:
                    # Single port validation
                    port = int(part)
                    if not (1 <= port <= 65535):
                        raise ValidationError(f"Invalid {port_type} port: {part}")
        except ValueError:
            raise ValidationError(f"Invalid {port_type} port format: {ports_string}")


class ScanType(TimestampMixin, SoftDeleteMixin):
    """Scan type configuration"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    only_discovery = models.BooleanField(
        default=False,
        help_text="Only check if host is alive (ping scan)"
    )
    consider_alive = models.BooleanField(
        default=False,
        help_text="Consider all hosts alive (skip ping)"
    )
    be_quiet = models.BooleanField(
        default=False,
        help_text="Reduce verbosity of scan output"
    )
    port_list = models.ForeignKey(
        PortList,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Port list to scan"
    )
    
    # Plugin flags
    plugin_finger = models.BooleanField(
        default=False,
        help_text="Enable fingerprinting plugin"
    )
    plugin_gce = models.BooleanField(
        default=False,
        help_text="Enable GCE plugin"
    )
    plugin_web = models.BooleanField(
        default=False,
        help_text="Enable web scanning plugin"
    )
    plugin_vuln_lookup = models.BooleanField(
        default=False,
        help_text="Enable vulnerability lookup plugin"
    )
    
    description = models.TextField(null=True, blank=True)
    
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    
    class Meta:
        db_table = 'scan_type'
        ordering = ['name']
        verbose_name = 'Scan Type'
        verbose_name_plural = 'Scan Types'
    
    def __str__(self):
        return self.name


class Target(TimestampMixin, SoftDeleteMixin):
    """Target hosts for scanning"""
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='targets'
    )
    name = models.CharField(max_length=255)
    address = models.CharField(
        max_length=50,
        help_text="IP address or FQDN"
    )
    description = models.TextField(null=True, blank=True)
    
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    
    class Meta:
        db_table = 'target'
        ordering = ['customer', 'name']
        unique_together = [['customer', 'address']]
        verbose_name = 'Target'
        verbose_name_plural = 'Targets'
    
    def __str__(self):
        return f"{self.customer.name} - {self.name} ({self.address})"
    
    def clean(self):
        """Validate target address"""
        if not self.address:
            return
        
        # Try to validate as IP address first
        try:
            ipaddress.ip_address(self.address)
            return
        except ValueError:
            pass
        
        # If not IP, validate as FQDN (basic validation)
        fqdn_validator = RegexValidator(
            regex=r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$',
            message='Enter a valid IP address or FQDN'
        )
        fqdn_validator(self.address)


class Scan(TimestampMixin, SoftDeleteMixin):
    """Scan instance"""
    
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Queued', 'Queued'),
        ('Nmap Scan Running', 'Nmap Scan Running'),
        ('Nmap Scan Completed', 'Nmap Scan Completed'),
        ('Finger Scan Running', 'Finger Scan Running'),
        ('Finger Scan Completed', 'Finger Scan Completed'),
        ('GCE Scan Running', 'GCE Scan Running'),
        ('GCE Scan Completed', 'GCE Scan Completed'),
        ('Web Scan Running', 'Web Scan Running'),
        ('Web Scan Completed', 'Web Scan Completed'),
        ('Vuln Lookup Running', 'Vuln Lookup Running'),
        ('Vuln Lookup Completed', 'Vuln Lookup Completed'),
        ('Report Generation Running', 'Report Generation Running'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    ]
    
    id = models.AutoField(primary_key=True)
    target = models.ForeignKey(
        Target,
        on_delete=models.CASCADE,
        related_name='scans'
    )
    scan_type = models.ForeignKey(
        ScanType,
        on_delete=models.CASCADE,
        related_name='scans'
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='Pending'
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='scans'
    )
    initiated_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Results storage
    parsed_nmap_results = models.JSONField(null=True, blank=True)
    parsed_finger_results = models.JSONField(null=True, blank=True)
    parsed_gce_results = models.JSONField(null=True, blank=True)
    parsed_web_results = models.JSONField(null=True, blank=True)
    parsed_vuln_results = models.JSONField(null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(null=True, blank=True)
    
    # Report
    report_path = models.CharField(max_length=500, null=True, blank=True)
    
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    
    class Meta:
        db_table = 'scan'
        ordering = ['-initiated_at']
        verbose_name = 'Scan'
        verbose_name_plural = 'Scans'
    
    def __str__(self):
        return f"Scan #{self.id} - {self.target.name} ({self.status})"
    
    @property
    def customer(self):
        """Get customer through target"""
        return self.target.customer
    
    @property
    def duration(self):
        """Calculate scan duration"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


class ScanDetail(TimestampMixin, SoftDeleteMixin):
    """Additional scan details and parsed results"""
    id = models.AutoField(primary_key=True)
    scan = models.OneToOneField(
        Scan,
        on_delete=models.CASCADE,
        related_name='details'
    )
    
    # Parsed results from scans
    open_ports = models.JSONField(
        null=True, 
        blank=True,
        help_text="Parsed open ports with services and versions"
    )
    os_guess = models.JSONField(
        null=True, 
        blank=True,
        help_text="Operating system detection results"
    )
    
    # Timing information for individual modules
    nmap_started_at = models.DateTimeField(null=True, blank=True)
    nmap_completed_at = models.DateTimeField(null=True, blank=True)
    finger_started_at = models.DateTimeField(null=True, blank=True)
    finger_completed_at = models.DateTimeField(null=True, blank=True)
    gce_started_at = models.DateTimeField(null=True, blank=True)
    gce_completed_at = models.DateTimeField(null=True, blank=True)
    web_started_at = models.DateTimeField(null=True, blank=True)
    web_completed_at = models.DateTimeField(null=True, blank=True)
    vuln_started_at = models.DateTimeField(null=True, blank=True)
    vuln_completed_at = models.DateTimeField(null=True, blank=True)
    
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    
    class Meta:
        db_table = 'scan_detail'
        verbose_name = 'Scan Detail'
        verbose_name_plural = 'Scan Details'
    
    def __str__(self):
        return f"Details for Scan #{self.scan.id}"
    
class FingerprintDetail(TimestampMixin, SoftDeleteMixin):
    """Detailed fingerprint results for each port/service"""
    
    id = models.AutoField(primary_key=True)
    scan = models.ForeignKey(
        Scan,
        on_delete=models.CASCADE,
        related_name='fingerprint_details'
    )
    target = models.ForeignKey(
        Target,
        on_delete=models.CASCADE,
        related_name='fingerprint_details'
    )
    port = models.IntegerField()
    protocol = models.CharField(
        max_length=10,
        choices=[('tcp', 'TCP'), ('udp', 'UDP')],
        default='tcp'
    )
    service_name = models.CharField(max_length=100, null=True, blank=True)
    service_version = models.CharField(max_length=255, null=True, blank=True)
    service_product = models.CharField(max_length=255, null=True, blank=True)
    service_info = models.TextField(null=True, blank=True)
    fingerprint_method = models.CharField(
        max_length=50,
        help_text="Method used for fingerprinting (e.g., fingerprintx, banner)"
    )
    confidence_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Confidence score 0-100"
    )
    raw_response = models.TextField(null=True, blank=True)
    additional_info = models.JSONField(null=True, blank=True)
    
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    
    class Meta:
        db_table = 'fingerprint_detail'
        ordering = ['scan', 'port']
        verbose_name = 'Fingerprint Detail'
        verbose_name_plural = 'Fingerprint Details'
        indexes = [
            models.Index(fields=['scan', 'port']),
            models.Index(fields=['target', 'port']),
        ]
    
    def __str__(self):
        return f"Fingerprint - {self.target.address}:{self.port}/{self.protocol} - {self.service_name or 'Unknown'}"