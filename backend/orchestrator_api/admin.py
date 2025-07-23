# backend/orchestrator_api/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json
#from django.utils.html import format_html, mark_safe
from .models import (
    Customer, PortList, ScanType, Target, Scan, ScanDetail, 
    FingerprintDetail, GceResult
)

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
    list_filter = ['only_discovery', 'plugin_finger', 'plugin_gce', 'plugin_web', 'plugin_vuln_lookup', 'created_at']
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
            'fields': ('plugin_finger', 'plugin_gce', 'plugin_web', 'plugin_vuln_lookup'),
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
        if obj.plugin_gce:
            plugins.append('Gce')
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
        ('gce_started_at', 'gce_completed_at'),
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
        'parsed_gce_results_formatted', 'parsed_web_results_formatted', 
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
                      'parsed_gce_results', 'parsed_web_results', 
                      'parsed_vuln_results'),
            'classes': ('collapse',)
        }),
        ('Formatted Results (Read Only)', {
            'fields': ('parsed_nmap_results_formatted', 'parsed_finger_results_formatted', 
                      'parsed_gce_results_formatted', 'parsed_web_results_formatted', 
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
    
    def parsed_gce_results_formatted(self, obj):
        """Display formatted gce results"""
        if obj.parsed_gce_results:
            return mark_safe(f'<pre style="white-space: pre-wrap; max-height: 300px; overflow-y: auto;">{json.dumps(obj.parsed_gce_results, indent=2)}</pre>')
        return '-'
    parsed_gce_results_formatted.short_description = 'Gce Results (Formatted)'
    
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
                ('gce_started_at', 'gce_completed_at'),
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

@admin.register(GceResult)
class GceResultAdmin(admin.ModelAdmin):
    """Admin configuration for GceResult model"""
    
    list_display = ['id', 'scan_link', 'target_link', 'gce_status', 'progress_display', 'vulnerabilities_summary', 'scan_duration', 'created_at']
    list_filter = ['gce_scan_status', 'report_format', 'created_at']
    search_fields = ['scan__id', 'target__name', 'target__address', 'gce_task_id', 'gce_report_id']
    readonly_fields = [
        'created_at', 'updated_at', 'deleted_at', 
        'gce_task_id', 'gce_report_id', 'gce_target_id',
        'report_preview', 'vulnerability_count_formatted', 'scan_duration'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Scan Information', {
            'fields': ('scan', 'target')
        }),
        ('GCE Identifiers', {
            'fields': ('gce_task_id', 'gce_report_id', 'gce_target_id'),
            'classes': ('collapse',)
        }),
        ('Scan Status', {
            'fields': ('gce_scan_status', 'gce_scan_progress', 'gce_scan_started_at', 'gce_scan_completed_at', 'scan_duration')
        }),
        ('Results', {
            'fields': ('report_format', 'vulnerability_count_formatted', 'report_preview')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        })
    )
    
    def scan_link(self, obj):
        """Display scan as link"""
        url = reverse('admin:orchestrator_api_scan_change', args=[obj.scan.id])
        return format_html('<a href="{}">{}</a>', url, obj.scan.id)
    scan_link.short_description = 'Scan'
    
    def target_link(self, obj):
        """Display target as link"""
        url = reverse('admin:orchestrator_api_target_change', args=[obj.target.id])
        return format_html('<a href="{}">{}</a>', url, f"{obj.target.name} ({obj.target.address})")
    target_link.short_description = 'Target'
    
    def gce_status(self, obj):
        """Display GCE scan status with color"""
        status = obj.gce_scan_status or 'Unknown'
        colors = {
            'Done': 'green',
            'Running': 'orange',
            'Stopped': 'red',
            'Interrupted': 'red',
            'Unknown': 'gray'
        }
        color = colors.get(status, 'black')
        return format_html('<span style="color: {};">{}</span>', color, status)
    gce_status.short_description = 'Status'
    
    def progress_display(self, obj):
        """Display scan progress"""
        return f"{obj.gce_scan_progress}%"
    progress_display.short_description = 'Progress'
    
    def vulnerabilities_summary(self, obj):
        """Display vulnerability count summary"""
        if obj.vulnerability_count:
            counts = obj.vulnerability_count
            parts = []
            if counts.get('critical', 0) > 0:
                parts.append(format_html('<span style="color: darkred;">C:{}</span>', counts['critical']))
            if counts.get('high', 0) > 0:
                parts.append(format_html('<span style="color: red;">H:{}</span>', counts['high']))
            if counts.get('medium', 0) > 0:
                parts.append(format_html('<span style="color: orange;">M:{}</span>', counts['medium']))
            if counts.get('low', 0) > 0:
                parts.append(format_html('<span style="color: yellow;">L:{}</span>', counts['low']))
            if counts.get('log', 0) > 0:
                parts.append(format_html('<span style="color: gray;">I:{}</span>', counts['log']))
            
            return format_html(' / '.join(parts)) if parts else '-'
        return '-'
    vulnerabilities_summary.short_description = 'Vulnerabilities'
    
    def scan_duration(self, obj):
        """Calculate and display scan duration"""
        if obj.gce_scan_started_at and obj.gce_scan_completed_at:
            duration = obj.gce_scan_completed_at - obj.gce_scan_started_at
            return str(duration).split('.')[0]  # Remove microseconds
        return '-'
    scan_duration.short_description = 'Duration'
    
    def vulnerability_count_formatted(self, obj):
        """Display formatted vulnerability count"""
        if obj.vulnerability_count:
            return mark_safe(f'<pre>{json.dumps(obj.vulnerability_count, indent=2)}</pre>')
        return '-'
    vulnerability_count_formatted.short_description = 'Vulnerability Count Details'
    
    def report_preview(self, obj):
        """Display a preview of the report"""
        if obj.full_report:
            preview = obj.full_report[:1000] + '...' if len(obj.full_report) > 1000 else obj.full_report
            return mark_safe(f'<pre style="white-space: pre-wrap; max-height: 300px; overflow-y: auto;">{preview}</pre>')
        return '-'
    report_preview.short_description = 'Report Preview (first 1000 chars)'
    
# Customize admin site
admin.site.site_header = 'VaPtER Administration'
admin.site.site_title = 'VaPtER Admin'
admin.site.index_title = 'Welcome to VaPtER Administration'