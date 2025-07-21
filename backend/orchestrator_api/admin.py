# backend/orchestrator_api/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

from .models import Customer, PortList, ScanType, Target, Scan, ScanDetail, FingerprintDetail


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Admin configuration for Customer model"""
    
    list_display = ['name', 'company_name', 'email', 'contact_person', 'targets_count', 'scans_count', 'created_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['name', 'company_name', 'email', 'contact_person']
    readonly_fields = ['created_at', 'updated_at', 'deleted_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'company_name', 'email')
        }),
        ('Contact Details', {
            'fields': ('contact_person', 'phone', 'address')
        }),
        ('Additional', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        })
    )
    
    def targets_count(self, obj):
        """Display number of targets"""
        count = obj.targets.count()
        if count > 0:
            url = reverse('admin:orchestrator_api_target_changelist') + f'?customer__id__exact={obj.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        return count
    targets_count.short_description = 'Targets'
    
    def scans_count(self, obj):
        """Display number of scans"""
        count = Scan.objects.filter(target__customer=obj).count()
        if count > 0:
            url = reverse('admin:orchestrator_api_scan_changelist') + f'?target__customer__id__exact={obj.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        return count
    scans_count.short_description = 'Scans'


@admin.register(PortList)
class PortListAdmin(admin.ModelAdmin):
    """Admin configuration for PortList model"""
    
    list_display = ['name', 'tcp_ports_preview', 'udp_ports_preview', 'scan_types_count', 'created_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'deleted_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Port Configuration', {
            'fields': ('tcp_ports', 'udp_ports'),
            'description': 'Enter ports as comma-separated values (e.g., "22,80,443") or ranges (e.g., "1-1000")'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        })
    )
    
    def tcp_ports_preview(self, obj):
        """Display TCP ports preview"""
        if obj.tcp_ports:
            preview = obj.tcp_ports[:50]
            if len(obj.tcp_ports) > 50:
                preview += '...'
            return preview
        return '-'
    tcp_ports_preview.short_description = 'TCP Ports'
    
    def udp_ports_preview(self, obj):
        """Display UDP ports preview"""
        if obj.udp_ports:
            preview = obj.udp_ports[:50]
            if len(obj.udp_ports) > 50:
                preview += '...'
            return preview
        return '-'
    udp_ports_preview.short_description = 'UDP Ports'
    
    def scan_types_count(self, obj):
        """Display number of scan types using this port list"""
        count = obj.scantype_set.count()
        if count > 0:
            url = reverse('admin:orchestrator_api_scantype_changelist') + f'?port_list__id__exact={obj.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        return count
    scan_types_count.short_description = 'Scan Types'


@admin.register(ScanType)
class ScanTypeAdmin(admin.ModelAdmin):
    """Admin configuration for ScanType model"""
    
    list_display = ['name', 'port_list', 'plugins_enabled', 'discovery_only', 'scans_count', 'created_at']
    list_filter = ['only_discovery', 'plugin_finger', 'plugin_enum', 'plugin_web', 'plugin_vuln_lookup', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'deleted_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'port_list')
        }),
        ('Scan Configuration', {
            'fields': ('only_discovery', 'consider_alive', 'be_quiet')
        }),
        ('Plugins', {
            'fields': ('plugin_finger', 'plugin_enum', 'plugin_web', 'plugin_vuln_lookup'),
            'description': 'Select which plugins to run after the initial nmap scan'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        })
    )
    
    def plugins_enabled(self, obj):
        """Display enabled plugins"""
        plugins = []
        if obj.plugin_finger:
            plugins.append('Fingerprint')
        if obj.plugin_enum:
            plugins.append('Enum')
        if obj.plugin_web:
            plugins.append('Web')
        if obj.plugin_vuln_lookup:
            plugins.append('Vuln')
        return ', '.join(plugins) if plugins else 'None'
    plugins_enabled.short_description = 'Plugins'
    
    def discovery_only(self, obj):
        """Display discovery only status"""
        return obj.only_discovery
    discovery_only.boolean = True
    discovery_only.short_description = 'Discovery Only'
    
    def scans_count(self, obj):
        """Display number of scans using this scan type"""
        count = obj.scans.count()
        if count > 0:
            url = reverse('admin:orchestrator_api_scan_changelist') + f'?scan_type__id__exact={obj.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        return count
    scans_count.short_description = 'Scans'


@admin.register(Target)
class TargetAdmin(admin.ModelAdmin):
    """Admin configuration for Target model"""
    
    list_display = ['name', 'address', 'customer', 'scans_count', 'last_scan_status', 'created_at']
    list_filter = ['customer', 'created_at', 'updated_at']
    search_fields = ['name', 'address', 'customer__name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'deleted_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('customer', 'name', 'address')
        }),
        ('Additional', {
            'fields': ('description',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        })
    )
    
    def scans_count(self, obj):
        """Display number of scans"""
        count = obj.scans.count()
        if count > 0:
            url = reverse('admin:orchestrator_api_scan_changelist') + f'?target__id__exact={obj.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        return count
    scans_count.short_description = 'Scans'
    
    def last_scan_status(self, obj):
        """Display last scan status"""
        last_scan = obj.scans.first()
        if last_scan:
            color = 'green' if last_scan.status == 'Completed' else 'red' if last_scan.status == 'Failed' else 'orange'
            return format_html(
                '<span style="color: {};">{}</span>',
                color,
                last_scan.status
            )
        return '-'
    last_scan_status.short_description = 'Last Scan'


class ScanDetailInline(admin.StackedInline):
    """Inline admin for ScanDetail"""
    model = ScanDetail
    readonly_fields = ['created_at', 'updated_at']
    fields = [
        ('open_ports', 'os_guess'),
        ('nmap_started_at', 'nmap_completed_at'),
        ('finger_started_at', 'finger_completed_at'),
        ('enum_started_at', 'enum_completed_at'),
        ('web_started_at', 'web_completed_at'),
        ('vuln_started_at', 'vuln_completed_at'),
        ('created_at', 'updated_at')
    ]
    extra = 0


@admin.register(Scan)
class ScanAdmin(admin.ModelAdmin):
    """Admin configuration for Scan model"""
    
    list_display = ['id', 'target_info', 'scan_type', 'status_colored', 'duration_display', 'initiated_at']
    list_filter = ['status', 'scan_type', 'target__customer', 'initiated_at']
    search_fields = ['target__name', 'target__address', 'target__customer__name']
    readonly_fields = [
        'initiated_at', 'created_at', 'updated_at', 'deleted_at', 'duration_display',
        'parsed_nmap_results_formatted', 'parsed_finger_results_formatted', 
        'parsed_enum_results_formatted', 'parsed_web_results_formatted', 
        'parsed_vuln_results_formatted'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('target', 'scan_type', 'status')
        }),
        ('Timing', {
            'fields': ('initiated_at', 'started_at', 'completed_at', 'duration_display')
        }),
        ('Results', {
            'fields': ('parsed_nmap_results', 'parsed_finger_results', 
                      'parsed_enum_results', 'parsed_web_results', 
                      'parsed_vuln_results'),
            'classes': ('collapse',)
        }),
        ('Formatted Results (Read Only)', {
            'fields': ('parsed_nmap_results_formatted', 'parsed_finger_results_formatted', 
                      'parsed_enum_results_formatted', 'parsed_web_results_formatted', 
                      'parsed_vuln_results_formatted'),
            'classes': ('collapse',)
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Report', {
            'fields': ('report_path',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [ScanDetailInline]
    
    def target_info(self, obj):
        """Display target information"""
        return f"{obj.target.customer.name} - {obj.target.name} ({obj.target.address})"
    target_info.short_description = 'Target'
    
    def status_colored(self, obj):
        """Display colored status"""
        colors = {
            'Completed': 'green',
            'Failed': 'red',
            'Pending': 'gray',
            'Queued': 'blue',
        }
        # Default to orange for running states
        color = colors.get(obj.status, 'orange')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.status
        )
    status_colored.short_description = 'Status'
    
    def duration_display(self, obj):
        """Display scan duration"""
        if obj.duration:
            return str(obj.duration)
        return '-'
    duration_display.short_description = 'Duration'
    
    def parsed_nmap_results_formatted(self, obj):
        """Display formatted nmap results"""
        if obj.parsed_nmap_results:
            return mark_safe(f'<pre style="white-space: pre-wrap; max-height: 300px; overflow-y: auto;">{json.dumps(obj.parsed_nmap_results, indent=2)}</pre>')
        return '-'
    parsed_nmap_results_formatted.short_description = 'Nmap Results (Formatted)'
    
    def parsed_finger_results_formatted(self, obj):
        """Display formatted fingerprint results"""
        if obj.parsed_finger_results:
            return mark_safe(f'<pre style="white-space: pre-wrap; max-height: 300px; overflow-y: auto;">{json.dumps(obj.parsed_finger_results, indent=2)}</pre>')
        return '-'
    parsed_finger_results_formatted.short_description = 'Fingerprint Results (Formatted)'
    
    def parsed_enum_results_formatted(self, obj):
        """Display formatted enum results"""
        if obj.parsed_enum_results:
            return mark_safe(f'<pre style="white-space: pre-wrap; max-height: 300px; overflow-y: auto;">{json.dumps(obj.parsed_enum_results, indent=2)}</pre>')
        return '-'
    parsed_enum_results_formatted.short_description = 'Enum Results (Formatted)'
    
    def parsed_web_results_formatted(self, obj):
        """Display formatted web results"""
        if obj.parsed_web_results:
            return mark_safe(f'<pre style="white-space: pre-wrap; max-height: 300px; overflow-y: auto;">{json.dumps(obj.parsed_web_results, indent=2)}</pre>')
        return '-'
    parsed_web_results_formatted.short_description = 'Web Results (Formatted)'
    
    def parsed_vuln_results_formatted(self, obj):
        """Display formatted vulnerability results"""
        if obj.parsed_vuln_results:
            return mark_safe(f'<pre style="white-space: pre-wrap; max-height: 300px; overflow-y: auto;">{json.dumps(obj.parsed_vuln_results, indent=2)}</pre>')
        return '-'
    parsed_vuln_results_formatted.short_description = 'Vulnerability Results (Formatted)'


@admin.register(ScanDetail)
class ScanDetailAdmin(admin.ModelAdmin):
    """Admin configuration for ScanDetail model"""
    
    list_display = ['scan_id', 'scan_target', 'scan_status', 'nmap_duration', 'created_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['scan__target__name', 'scan__target__address']
    readonly_fields = [
        'created_at', 'updated_at', 'deleted_at', 
        'open_ports_formatted', 'os_guess_formatted'
    ]
    
    fieldsets = (
        ('Scan Information', {
            'fields': ('scan',)
        }),
        ('Raw Results', {
            'fields': ('open_ports', 'os_guess'),
            'classes': ('collapse',)
        }),
        ('Formatted Results (Read Only)', {
            'fields': ('open_ports_formatted', 'os_guess_formatted'),
            'classes': ('collapse',)
        }),
        ('Module Timing', {
            'fields': (
                ('nmap_started_at', 'nmap_completed_at'),
                ('finger_started_at', 'finger_completed_at'),
                ('enum_started_at', 'enum_completed_at'),
                ('web_started_at', 'web_completed_at'),
                ('vuln_started_at', 'vuln_completed_at')
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        })
    )
    
    def scan_id(self, obj):
        """Display scan ID with link"""
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:orchestrator_api_scan_change', args=[obj.scan.id]),
            obj.scan.id
        )
    scan_id.short_description = 'Scan ID'
    
    def scan_target(self, obj):
        """Display scan target"""
        return f"{obj.scan.target.name} ({obj.scan.target.address})"
    scan_target.short_description = 'Target'
    
    def scan_status(self, obj):
        """Display scan status"""
        return obj.scan.status
    scan_status.short_description = 'Status'
    
    def nmap_duration(self, obj):
        """Display nmap duration"""
        if obj.nmap_started_at and obj.nmap_completed_at:
            return obj.nmap_completed_at - obj.nmap_started_at
        return '-'
    nmap_duration.short_description = 'Nmap Duration'
    
    def open_ports_formatted(self, obj):
        """Display formatted open ports"""
        if obj.open_ports:
            return mark_safe(f'<pre style="white-space: pre-wrap; max-height: 300px; overflow-y: auto;">{json.dumps(obj.open_ports, indent=2)}</pre>')
        return '-'
    open_ports_formatted.short_description = 'Open Ports (Formatted)'
    
    def os_guess_formatted(self, obj):
        """Display formatted OS guess"""
        if obj.os_guess:
            return mark_safe(f'<pre style="white-space: pre-wrap; max-height: 300px; overflow-y: auto;">{json.dumps(obj.os_guess, indent=2)}</pre>')
        return '-'
    os_guess_formatted.short_description = 'OS Detection (Formatted)'

@admin.register(FingerprintDetail)
class FingerprintDetailAdmin(admin.ModelAdmin):
    """Admin configuration for FingerprintDetail model"""
    
    list_display = [
        'scan_id', 'target_address', 'port_display', 'service_name', 
        'service_version', 'confidence_score', 'fingerprint_method', 'created_at'
    ]
    list_filter = [
        'protocol', 'service_name', 'fingerprint_method', 'confidence_score', 
        'created_at', 'scan__status'
    ]
    search_fields = [
        'target__address', 'service_name', 'service_version', 'service_product',
        'port'
    ]
    readonly_fields = ['created_at', 'updated_at', 'deleted_at']
    
    fieldsets = (
        ('Scan Information', {
            'fields': ('scan', 'target')
        }),
        ('Port & Service Details', {
            'fields': ('port', 'protocol', 'service_name', 'service_version', 
                      'service_product', 'service_info')
        }),
        ('Fingerprint Information', {
            'fields': ('fingerprint_method', 'confidence_score', 'raw_response')
        }),
        ('Additional Data', {
            'fields': ('additional_info',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        })
    )
    
    def scan_id(self, obj):
        """Display scan ID with link"""
        url = reverse('admin:orchestrator_api_scan_change', args=[obj.scan.id])
        return format_html('<a href="{}">{}</a>', url, obj.scan.id)
    scan_id.short_description = 'Scan'
    
    def target_address(self, obj):
        """Display target address"""
        return obj.target.address
    target_address.short_description = 'Target'
    target_address.admin_order_field = 'target__address'
    
    def port_display(self, obj):
        """Display port with protocol"""
        return f"{obj.port}/{obj.protocol}"
    port_display.short_description = 'Port'
    port_display.admin_order_field = 'port'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('scan', 'target')
    
# Customize admin site
admin.site.site_header = 'VaPtER Administration'
admin.site.site_title = 'VaPtER Admin'
admin.site.index_title = 'Welcome to VaPtER Administration'