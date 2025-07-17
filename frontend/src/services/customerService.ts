import apiClient from '@/lib/api'
import type { Customer, PaginatedResponse } from '@/types'

export async function getCustomers(): Promise<Customer[]> {
  const response = await apiClient.get<PaginatedResponse<Customer>>('/orchestrator/customers/')
  return response.data.results
}

export async function getCustomer(id: string): Promise<Customer> {
  const response = await apiClient.get<Customer>(`/orchestrator/customers/${id}/`)
  return response.data
}

export async function createCustomer(data: Partial<Customer>): Promise<Customer> {
  const response = await apiClient.post<Customer>('/orchestrator/customers/', data)
  return response.data
}

export async function updateCustomer(id: string, data: Partial<Customer>): Promise<Customer> {
  const response = await apiClient.patch<Customer>(`/orchestrator/customers/${id}/`, data)
  return response.data
}

export async function deleteCustomer(id: string): Promise<void> {
  await apiClient.delete(`/orchestrator/customers/${id}/`)
}