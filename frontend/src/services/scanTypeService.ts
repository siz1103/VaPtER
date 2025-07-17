import apiClient from '@/lib/api'
import type { ScanType, PaginatedResponse } from '@/types'

export async function getScanTypes(): Promise<ScanType[]> {
  const response = await apiClient.get<PaginatedResponse<ScanType>>('/orchestrator/scan-types/')
  return response.data.results
}

export async function getScanType(id: number): Promise<ScanType> {
  const response = await apiClient.get<ScanType>(`/orchestrator/scan-types/${id}/`)
  return response.data
}

export async function createScanType(data: Partial<ScanType>): Promise<ScanType> {
  const response = await apiClient.post<ScanType>('/orchestrator/scan-types/', data)
  return response.data
}

export async function updateScanType(id: number, data: Partial<ScanType>): Promise<ScanType> {
  const response = await apiClient.patch<ScanType>(`/orchestrator/scan-types/${id}/`, data)
  return response.data
}

export async function deleteScanType(id: number): Promise<void> {
  await apiClient.delete(`/orchestrator/scan-types/${id}/`)
}