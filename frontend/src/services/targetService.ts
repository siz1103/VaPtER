import apiClient from '@/lib/api'
import type { Target, PaginatedResponse, ScanType } from '@/types'

export async function getTargets(customerId?: string): Promise<Target[]> {
  const params = customerId ? { customer: customerId } : {}
  const response = await apiClient.get<PaginatedResponse<Target>>('/orchestrator/targets/', { params })
  return response.data.results
}

export async function getTarget(id: number): Promise<Target> {
  const response = await apiClient.get<Target>(`/orchestrator/targets/${id}/`)
  return response.data
}

export async function createTarget(data: Partial<Target>): Promise<Target> {
  const response = await apiClient.post<Target>('/orchestrator/targets/', data)
  return response.data
}

export async function updateTarget(id: number, data: Partial<Target>): Promise<Target> {
  const response = await apiClient.patch<Target>(`/orchestrator/targets/${id}/`, data)
  return response.data
}

export async function deleteTarget(id: number): Promise<void> {
  await apiClient.delete(`/orchestrator/targets/${id}/`)
}

export async function startScan(targetId: number, scanTypeId: number): Promise<any> {
  const response = await apiClient.post(`/orchestrator/targets/${targetId}/scan/`, {
    scan_type_id: scanTypeId
  })
  return response.data
}

// Utility functions per validazione
export function validateIPAddress(address: string): boolean {
  // IPv4 pattern
  const ipv4Pattern = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/
  
  // IPv6 pattern (simplified)
  const ipv6Pattern = /^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))$/
  
  return ipv4Pattern.test(address) || ipv6Pattern.test(address)
}

export function validateFQDN(fqdn: string): boolean {
  // FQDN validation
  if (fqdn.length > 253) return false
  
  const fqdnPattern = /^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$/
  
  if (!fqdnPattern.test(fqdn)) return false
  
  // Additional checks
  if (fqdn.includes('..') || fqdn.endsWith('.')) return false
  
  const labels = fqdn.split('.')
  for (const label of labels) {
    if (label.length > 63) return false
    if (label.startsWith('-') || label.endsWith('-')) return false
  }
  
  return true
}

export function validateAddress(address: string): { valid: boolean; type: 'ip' | 'fqdn' | 'invalid' } {
  if (!address) return { valid: false, type: 'invalid' }
  
  if (validateIPAddress(address)) {
    return { valid: true, type: 'ip' }
  }
  
  if (validateFQDN(address)) {
    return { valid: true, type: 'fqdn' }
  }
  
  return { valid: false, type: 'invalid' }
}