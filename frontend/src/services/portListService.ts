import apiClient from '@/lib/api'
import type { PortList, PaginatedResponse } from '@/types'

export async function getPortLists(): Promise<PortList[]> {
  const response = await apiClient.get<PaginatedResponse<PortList>>('/orchestrator/port-lists/')
  return response.data.results
}

export async function getPortList(id: number): Promise<PortList> {
  const response = await apiClient.get<PortList>(`/orchestrator/port-lists/${id}/`)
  return response.data
}

export async function createPortList(data: Partial<PortList>): Promise<PortList> {
  const response = await apiClient.post<PortList>('/orchestrator/port-lists/', data)
  return response.data
}

export async function updatePortList(id: number, data: Partial<PortList>): Promise<PortList> {
  const response = await apiClient.patch<PortList>(`/orchestrator/port-lists/${id}/`, data)
  return response.data
}

export async function deletePortList(id: number): Promise<void> {
  await apiClient.delete(`/orchestrator/port-lists/${id}/`)
}

// Utility function per validare il formato delle porte
export function validatePortFormat(ports: string): boolean {
  if (!ports.trim()) return true // Empty is valid
  
  // Pattern per validare porte: numeri singoli, range (1-1000), o combinazioni (22,80,443,1000-2000)
  const portPattern = /^(\d{1,5}(-\d{1,5})?)(,\s*\d{1,5}(-\d{1,5})?)*$/
  
  if (!portPattern.test(ports.trim())) return false
  
  // Validare che ogni numero sia nel range 1-65535
  const parts = ports.split(',').map(p => p.trim())
  
  for (const part of parts) {
    if (part.includes('-')) {
      const [start, end] = part.split('-').map(p => parseInt(p.trim()))
      if (start < 1 || start > 65535 || end < 1 || end > 65535 || start > end) {
        return false
      }
    } else {
      const port = parseInt(part)
      if (port < 1 || port > 65535) {
        return false
      }
    }
  }
  
  return true
}

// Utility function per contare approssimativamente le porte
export function countPorts(ports: string): number {
  if (!ports.trim()) return 0
  
  const parts = ports.split(',').map(p => p.trim())
  let count = 0
  
  for (const part of parts) {
    if (part.includes('-')) {
      const [start, end] = part.split('-').map(p => parseInt(p.trim()))
      count += end - start + 1
    } else {
      count += 1
    }
  }
  
  return count
}