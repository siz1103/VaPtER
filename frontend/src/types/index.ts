export interface Customer {
  id: string
  name: string
  company_name?: string
  email: string
  phone?: string
  contact_person?: string
  address?: string
  notes?: string
  created_at: string
  updated_at: string
  targets_count: number
  scans_count: number
}

export interface PortList {
  id: number
  name: string
  tcp_ports?: string
  udp_ports?: string
  description?: string
  total_tcp_ports: number
  total_udp_ports: number
  created_at: string
  updated_at: string
}

export interface ScanType {
  id: number
  name: string
  only_discovery: boolean
  consider_alive: boolean
  be_quiet: boolean
  port_list?: number
  port_list_name?: string
  plugin_finger: boolean
  plugin_enum: boolean
  plugin_web: boolean
  plugin_vuln_lookup: boolean
  description?: string
  enabled_plugins: string[]
  created_at: string
  updated_at: string
}

export interface Target {
  id: number
  customer: string
  customer_name: string
  name: string
  address: string
  description?: string
  scans_count: number
  last_scan?: {
    id: number
    status: string
    initiated_at: string
    completed_at?: string
  }
  created_at: string
  updated_at: string
}

export interface Scan {
  id: number
  target: number
  target_name: string
  target_address: string
  customer_name: string
  scan_type: number
  scan_type_name: string
  status: ScanStatus
  initiated_at: string
  started_at?: string
  completed_at?: string
  duration_seconds?: number
  parsed_nmap_results?: any
  parsed_finger_results?: any
  parsed_enum_results?: any
  parsed_web_results?: any
  parsed_vuln_results?: any
  error_message?: string
  report_path?: string
  details?: ScanDetail
  created_at: string
  updated_at: string
}

export interface ScanDetail {
  id: number
  scan: number
  open_ports?: any
  os_guess?: any
  nmap_started_at?: string
  nmap_completed_at?: string
  finger_started_at?: string
  finger_completed_at?: string
  enum_started_at?: string
  enum_completed_at?: string
  web_started_at?: string
  web_completed_at?: string
  vuln_started_at?: string
  vuln_completed_at?: string
  created_at: string
  updated_at: string
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
  | 'Failed'

export interface PaginatedResponse<T> {
  count: number
  next?: string
  previous?: string
  results: T[]
}

export interface ApiError {
  detail?: string
  error?: string
  [key: string]: any
}