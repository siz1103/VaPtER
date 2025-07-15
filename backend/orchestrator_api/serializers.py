from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Customer, PortList, ScanType, Target, Scan, ScanDetail


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for Customer model"""
    
    targets_count = serializers.SerializerMethodField()
    scans_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Customer
        fields = [
            'id', 'name', 'company_name', 'email', 'phone', 
            'contact_person', 'address', 'notes', 'created_at', 
            'updated_at', 'targets_count', 'scans_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_targets_count(self, obj):
        """Get number of targets for this customer"""
        return obj.targets.count()
    
    def get_scans_count(self, obj):
        """Get number of scans for this customer"""
        return Scan.objects.filter(target__customer=obj).count()
    
    def validate_email(self, value):
        """Validate unique email"""
        if self.instance:
            # Update case - exclude current instance
            if Customer.objects.exclude(id=self.instance.id).filter(email=value).exists():
                raise serializers.ValidationError("A customer with this email already exists.")
        else:
            # Create case
            if Customer.objects.filter(email=value).exists():
                raise serializers.ValidationError("A customer with this email already exists.")
        return value


class PortListSerializer(serializers.ModelSerializer):
    """Serializer for PortList model"""
    
    total_tcp_ports = serializers.SerializerMethodField()
    total_udp_ports = serializers.SerializerMethodField()
    
    class Meta:
        model = PortList
        fields = [
            'id', 'name', 'tcp_ports', 'udp_ports', 'description',
            'created_at', 'updated_at', 'total_tcp_ports', 'total_udp_ports'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_tcp_ports(self, obj):
        """Calculate approximate number of TCP ports"""
        if not obj.tcp_ports:
            return 0
        # This is a simplified calculation
        return len([p.strip() for p in obj.tcp_ports.split(',') if p.strip()])
    
    def get_total_udp_ports(self, obj):
        """Calculate approximate number of UDP ports"""
        if not obj.udp_ports:
            return 0
        # This is a simplified calculation
        return len([p.strip() for p in obj.udp_ports.split(',') if p.strip()])
    
    def validate(self, data):
        """Validate PortList data"""
        try:
            # Create a temporary instance to use the model's clean method
            instance = PortList(**data)
            instance.clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict if hasattr(e, 'message_dict') else str(e))
        return data


class ScanTypeSerializer(serializers.ModelSerializer):
    """Serializer for ScanType model"""
    
    port_list_name = serializers.CharField(source='port_list.name', read_only=True)
    enabled_plugins = serializers.SerializerMethodField()
    
    class Meta:
        model = ScanType
        fields = [
            'id', 'name', 'only_discovery', 'consider_alive', 'be_quiet',
            'port_list', 'port_list_name', 'plugin_finger', 'plugin_enum',
            'plugin_web', 'plugin_vuln_lookup', 'description', 'created_at',
            'updated_at', 'enabled_plugins'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_enabled_plugins(self, obj):
        """Get list of enabled plugins"""
        plugins = []
        if obj.plugin_finger:
            plugins.append('fingerprint')
        if obj.plugin_enum:
            plugins.append('enumeration')
        if obj.plugin_web:
            plugins.append('web_scanning')
        if obj.plugin_vuln_lookup:
            plugins.append('vulnerability_lookup')
        return plugins
    
    def validate(self, data):
        """Validate ScanType data"""
        # If only_discovery is True, port_list should not be required
        if data.get('only_discovery', False) and data.get('port_list'):
            raise serializers.ValidationError(
                "Port list should not be specified for discovery-only scans"
            )
        
        # If not discovery-only, port_list is recommended
        if not data.get('only_discovery', False) and not data.get('port_list'):
            # This is a warning, not an error
            pass
        
        return data


class TargetSerializer(serializers.ModelSerializer):
    """Serializer for Target model"""
    
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    scans_count = serializers.SerializerMethodField()
    last_scan = serializers.SerializerMethodField()
    
    class Meta:
        model = Target
        fields = [
            'id', 'customer', 'customer_name', 'name', 'address',
            'description', 'created_at', 'updated_at', 'scans_count', 'last_scan'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_scans_count(self, obj):
        """Get number of scans for this target"""
        return obj.scans.count()
    
    def get_last_scan(self, obj):
        """Get last scan information"""
        last_scan = obj.scans.first()  # Assuming ordering by -initiated_at
        if last_scan:
            return {
                'id': last_scan.id,
                'status': last_scan.status,
                'initiated_at': last_scan.initiated_at,
                'completed_at': last_scan.completed_at
            }
        return None
    
    def validate(self, data):
        """Validate Target data"""
        try:
            # Create a temporary instance to use the model's clean method
            instance = Target(**data)
            instance.clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict if hasattr(e, 'message_dict') else str(e))
        
        # Check unique constraint manually for better error message
        customer = data.get('customer')
        address = data.get('address')
        if customer and address:
            existing = Target.objects.filter(customer=customer, address=address)
            if self.instance:
                existing = existing.exclude(id=self.instance.id)
            if existing.exists():
                raise serializers.ValidationError(
                    f"Target with address '{address}' already exists for this customer"
                )
        
        return data


class ScanDetailSerializer(serializers.ModelSerializer):
    """Serializer for ScanDetail model"""
    
    class Meta:
        model = ScanDetail
        fields = [
            'id', 'scan', 'open_ports', 'os_guess',
            'nmap_started_at', 'nmap_completed_at',
            'finger_started_at', 'finger_completed_at',
            'enum_started_at', 'enum_completed_at',
            'web_started_at', 'web_completed_at',
            'vuln_started_at', 'vuln_completed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ScanSerializer(serializers.ModelSerializer):
    """Serializer for Scan model"""
    
    target_name = serializers.CharField(source='target.name', read_only=True)
    target_address = serializers.CharField(source='target.address', read_only=True)
    customer_name = serializers.CharField(source='target.customer.name', read_only=True)
    scan_type_name = serializers.CharField(source='scan_type.name', read_only=True)
    details = ScanDetailSerializer(read_only=True)
    duration_seconds = serializers.SerializerMethodField()
    
    class Meta:
        model = Scan
        fields = [
            'id', 'target', 'target_name', 'target_address', 'customer_name',
            'scan_type', 'scan_type_name', 'status', 'initiated_at',
            'started_at', 'completed_at', 'parsed_nmap_results',
            'parsed_finger_results', 'parsed_enum_results', 'parsed_web_results',
            'parsed_vuln_results', 'error_message', 'report_path', 'details',
            'duration_seconds', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'initiated_at', 'started_at', 'completed_at', 'created_at', 'updated_at'
        ]
    
    def get_duration_seconds(self, obj):
        """Get scan duration in seconds"""
        if obj.duration:
            return int(obj.duration.total_seconds())
        return None


class ScanCreateSerializer(serializers.ModelSerializer):
    """Specialized serializer for creating scans"""
    
    class Meta:
        model = Scan
        fields = ['target', 'scan_type']
    
    def validate(self, data):
        """Validate scan creation data"""
        target = data.get('target')
        scan_type = data.get('scan_type')
        
        if not target or not scan_type:
            raise serializers.ValidationError("Both target and scan_type are required")
        
        # Check if there's already a running scan for this target
        running_statuses = [
            'Queued', 'Nmap Scan Running', 'Finger Scan Running',
            'Enum Scan Running', 'Web Scan Running', 'Vuln Lookup Running',
            'Report Generation Running'
        ]
        
        if Scan.objects.filter(target=target, status__in=running_statuses).exists():
            raise serializers.ValidationError(
                f"Target '{target.name}' already has a running scan. Please wait for it to complete."
            )
        
        return data


class ScanUpdateSerializer(serializers.ModelSerializer):
    """Specialized serializer for updating scans (mainly for scanner modules)"""
    
    class Meta:
        model = Scan
        fields = [
            'status', 'started_at', 'completed_at', 'parsed_nmap_results',
            'parsed_finger_results', 'parsed_enum_results', 'parsed_web_results',
            'parsed_vuln_results', 'error_message', 'report_path'
        ]
    
    def validate_status(self, value):
        """Validate status transitions"""
        if self.instance:
            current_status = self.instance.status
            # Add status transition validation logic here if needed
            # For now, allow any transition (will be refined later)
        return value