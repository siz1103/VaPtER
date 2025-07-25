// frontend/src/services/scanService.ts

import apiClient from '@/lib/api'
import type { Scan, PaginatedResponse, ScanType } from '@/types'

export async function getScans(customerId?: string): Promise<Scan[]> {
  const params: Record<string, any> = {}
  
  if (customerId) {
    // Using target__customer filter as defined in backend ScanFilter
    params['customer'] = customerId
  }
  
  console.log('getScans params:', params) // Debug log to verify filter
  
  const response = await apiClient.get<PaginatedResponse<Scan>>('/orchestrator/scans/', { params })
  return response.data.results
}

export async function getScan(id: number): Promise<Scan> {
  const response = await apiClient.get<Scan>(`/orchestrator/scans/${id}/`)
  return response.data
}

export async function deleteScan(id: number): Promise<void> {
  await apiClient.delete(`/orchestrator/scans/${id}/`)
}

export async function restartScan(id: number): Promise<Scan> {
  const response = await apiClient.post<Scan>(`/orchestrator/scans/${id}/restart/`)
  return response.data
}

export async function updateScanType(id: number, scanTypeId: number): Promise<Scan> {
  const response = await apiClient.patch<Scan>(`/orchestrator/scans/${id}/`, {
    scan_type: scanTypeId
  })
  return response.data
}

export async function cancelScan(id: number): Promise<Scan> {
  const response = await apiClient.post<Scan>(`/orchestrator/scans/${id}/cancel/`)
  return response.data
}

// Utility functions per status management
export function isActiveScan(status: string): boolean {
  const activeStatuses = [
    'Pending',
    'Queued', 
    'Nmap Scan Running',
    'Finger Scan Running',
    'Gce Scan Running',
    'Web Scan Running',
    'Vuln Lookup Running',
    'Report Generation Running'
  ]
  return activeStatuses.includes(status)
}

export function canRestartScan(status: string): boolean {
  return status === 'Failed' || status === 'Completed'
}

export function canCancelScan(status: string): boolean {
  return isActiveScan(status)
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'Pending':
    case 'Queued':
      return 'default'
    case 'Nmap Scan Running':
    case 'Finger Scan Running':
    case 'Gce Scan Running':
    case 'Web Scan Running':
    case 'Vuln Lookup Running':
    case 'Report Generation Running':
      return 'blue'
    case 'Completed':
    case 'Nmap Scan Completed':
    case 'Finger Scan Completed':
    case 'Gce Scan Completed':
    case 'Web Scan Completed':
    case 'Vuln Lookup Completed':
      return 'green'
    case 'Failed':
      return 'destructive'
    default:
      return 'secondary'
  }
}