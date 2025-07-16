// frontend/src/types/index.ts

export interface Customer {
  id: string;
  name: string;
  company_name: string;
  email: string;
  phone: string;
  contact_person: string;
  address: string;
  notes: string;
  created_at: string;
  updated_at: string;
  targets_count: number;
  scans_count: number;
}

export interface CreateCustomerData {
  name: string;
  company_name?: string;
  email: string;
  phone?: string;
  contact_person?: string;
  address?: string;
  notes?: string;
}

export interface PortList {
  id: number;
  name: string;
  tcp_ports: string | null;
  udp_ports: string | null;
  description: string | null;
  created_at: string;
  updated_at: string;
  total_tcp_ports: number;
  total_udp_ports: number;
}

export interface CreatePortListData {
  name: string;
  tcp_ports?: string;
  udp_ports?: string;
  description?: string;
}

export interface ScanType {
  id: number;
  name: string;
  only_discovery: boolean;
  consider_alive: boolean;
  be_quiet: boolean;
  port_list: number | null;
  port_list_name: string | null;
  plugin_finger: boolean;
  plugin_enum: boolean;
  plugin_web: boolean;
  plugin_vuln_lookup: boolean;
  description: string | null;
  created_at: string;
  updated_at: string;
  enabled_plugins: string[];
}

export interface CreateScanTypeData {
  name: string;
  only_discovery?: boolean;
  consider_alive?: boolean;
  be_quiet?: boolean;
  port_list?: number;
  plugin_finger?: boolean;
  plugin_enum?: boolean;
  plugin_web?: boolean;
  plugin_vuln_lookup?: boolean;
  description?: string;
}

export interface Target {
  id: number;
  customer: string;
  customer_name: string;
  name: string;
  address: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  scans_count: number;
  last_scan: {
    id: number;
    status: string;
    initiated_at: string;
    completed_at: string | null;
  } | null;
}

export interface CreateTargetData {
  customer: string;
  name: string;
  address: string;
  description?: string;
}

export interface Scan {
  id: number;
  target: number;
  target_name: string;
  target_address: string;
  customer_name: string;
  scan_type: number;
  scan_type_name: string;
  status: ScanStatus;
  initiated_at: string;
  started_at: string | null;
  completed_at: string | null;
  parsed_nmap_results: NmapResults | null;
  parsed_finger_results: any | null;
  parsed_enum_results: any | null;
  parsed_web_results: any | null;
  parsed_vuln_results: any | null;
  error_message: string | null;
  report_path: string | null;
  duration_seconds: number | null;
  created_at: string;
  updated_at: string;
  details?: ScanDetail;
}

export interface CreateScanData {
  target: number;
  scan_type: number;
}

export interface StartScanData {
  scan_type_id: number;
}

export interface ScanDetail {
  id: number;
  scan: number;
  open_ports: OpenPort[] | null;
  os_guess: OSGuess | null;
  nmap_started_at: string | null;
  nmap_completed_at: string | null;
  finger_started_at: string | null;
  finger_completed_at: string | null;
  enum_started_at: string | null;
  enum_completed_at: string | null;
  web_started_at: string | null;
  web_completed_at: string | null;
  vuln_started_at: string | null;
  vuln_completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface OpenPort {
  protocol: string;
  portid: string;
  state: string;
  service?: {
    name: string;
    product?: string;
    version?: string;
    extrainfo?: string;
    method?: string;
    conf?: string;
  };
  scripts?: Array<{
    id: string;
    output: string;
  }>;
}

export interface OSGuess {
  name: string;
  accuracy: string;
  line?: string;
  type?: string;
  vendor?: string;
  osfamily?: string;
  osgen?: string;
}

export interface NmapResults {
  scan_info: {
    type: string;
    protocol: string;
    numservices: string;
    services: string;
  };
  hosts: Array<{
    state: string;
    addresses: Array<{
      addr: string;
      addrtype: string;
    }>;
    hostnames: Array<{
      name: string;
      type: string;
    }>;
    ports: OpenPort[];
    os: OSGuess;
  }>;
  stats: {
    finished?: {
      time: string;
      timestr: string;
      elapsed: string;
    };
    hosts?: {
      up: string;
      down: string;
      total: string;
    };
  };
}

export type ScanStatus = 
  | 'Pending'
  | 'Queued'
  | 'Nmap Scan Running'
  | 'Nmap Scan Completed'
  | 'Finger Scan Running'
  | 'Finger Scan Completed'
  | 'Enum Scan Running'
  | 'Enum Scan Completed'
  | 'Web Scan Running'
  | 'Web Scan Completed'
  | 'Vuln Lookup Running'
  | 'Vuln Lookup Completed'
  | 'Report Generation Running'
  | 'Completed'
  | 'Failed';

export interface ApiResponse<T> {
  count?: number;
  next?: string | null;
  previous?: string | null;
  results?: T[];
  data?: T;
}

export interface ApiError {
  error: string;
  detail?: string;
  status?: string;
}

export interface DashboardStats {
  total_customers: number;
  total_targets: number;
  total_scans: number;
  recent_scans: Scan[];
  status_distribution: Record<string, number>;
  running_scans: number;
}

export interface CustomerStats {
  targets_count: number;
  scans_count: number;
  status_distribution: Record<string, number>;
  recent_scans: Scan[];
}

export interface HealthCheck {
  status: string;
  service: string;
  version: string;
  timestamp: number;
  checks?: {
    backend: {
      status: string;
      url: string;
      response_time_ms: number;
    };
  };
}