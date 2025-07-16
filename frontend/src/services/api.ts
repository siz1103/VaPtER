// frontend/src/services/api.ts

import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  Customer,
  CreateCustomerData,
  Target,
  CreateTargetData,
  Scan,
  CreateScanData,
  StartScanData,
  ScanType,
  CreateScanTypeData,
  PortList,
  CreatePortListData,
  ApiResponse,
  DashboardStats,
  CustomerStats,
  HealthCheck,
} from '../types';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8080',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.api.interceptors.request.use(
      (config) => {
        console.log(`🔄 API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('🔴 API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.api.interceptors.response.use(
      (response: AxiosResponse) => {
        console.log(`✅ API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        console.error('🔴 API Response Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  // Health endpoints
  async getHealth(): Promise<HealthCheck> {
    const response = await this.api.get<HealthCheck>('/health/');
    return response.data;
  }

  async getDetailedHealth(): Promise<HealthCheck> {
    const response = await this.api.get<HealthCheck>('/health/detailed');
    return response.data;
  }

  // Customer endpoints
  async getCustomers(params?: { search?: string; page?: number }): Promise<ApiResponse<Customer>> {
    const response = await this.api.get<ApiResponse<Customer>>('/api/orchestrator/customers/', { params });
    return response.data;
  }

  async getCustomer(id: string): Promise<Customer> {
    const response = await this.api.get<Customer>(`/api/orchestrator/customers/${id}/`);
    return response.data;
  }

  async createCustomer(data: CreateCustomerData): Promise<Customer> {
    const response = await this.api.post<Customer>('/api/orchestrator/customers/', data);
    return response.data;
  }

  async updateCustomer(id: string, data: Partial<CreateCustomerData>): Promise<Customer> {
    const response = await this.api.patch<Customer>(`/api/orchestrator/customers/${id}/`, data);
    return response.data;
  }

  async deleteCustomer(id: string): Promise<void> {
    await this.api.delete(`/api/orchestrator/customers/${id}/`);
  }

  async getCustomerStatistics(id: string): Promise<CustomerStats> {
    const response = await this.api.get<CustomerStats>(`/api/orchestrator/customers/${id}/statistics/`);
    return response.data;
  }

  // Target endpoints
  async getTargets(params?: { customer?: string; search?: string; page?: number }): Promise<ApiResponse<Target>> {
    const response = await this.api.get<ApiResponse<Target>>('/api/orchestrator/targets/', { params });
    return response.data;
  }

  async getTarget(id: number): Promise<Target> {
    const response = await this.api.get<Target>(`/api/orchestrator/targets/${id}/`);
    return response.data;
  }

  async createTarget(data: CreateTargetData): Promise<Target> {
    const response = await this.api.post<Target>('/api/orchestrator/targets/', data);
    return response.data;
  }

  async updateTarget(id: number, data: Partial<CreateTargetData>): Promise<Target> {
    const response = await this.api.patch<Target>(`/api/orchestrator/targets/${id}/`, data);
    return response.data;
  }

  async deleteTarget(id: number): Promise<void> {
    await this.api.delete(`/api/orchestrator/targets/${id}/`);
  }

  async getTargetScans(id: number, params?: { page?: number }): Promise<ApiResponse<Scan>> {
    const response = await this.api.get<ApiResponse<Scan>>(`/api/orchestrator/targets/${id}/scans/`, { params });
    return response.data;
  }

  async startTargetScan(id: number, data: StartScanData): Promise<Scan> {
    const response = await this.api.post<Scan>(`/api/orchestrator/targets/${id}/scan/`, data);
    return response.data;
  }

  // Scan endpoints
  async getScans(params?: { 
    target?: number; 
    customer?: string; 
    status?: string; 
    is_running?: boolean; 
    page?: number 
  }): Promise<ApiResponse<Scan>> {
    const response = await this.api.get<ApiResponse<Scan>>('/api/orchestrator/scans/', { params });
    return response.data;
  }

  async getScan(id: number): Promise<Scan> {
    const response = await this.api.get<Scan>(`/api/orchestrator/scans/${id}/`);
    return response.data;
  }

  async createScan(data: CreateScanData): Promise<Scan> {
    const response = await this.api.post<Scan>('/api/orchestrator/scans/', data);
    return response.data;
  }

  async updateScan(id: number, data: Partial<Scan>): Promise<Scan> {
    const response = await this.api.patch<Scan>(`/api/orchestrator/scans/${id}/`, data);
    return response.data;
  }

  async deleteScan(id: number): Promise<void> {
    await this.api.delete(`/api/orchestrator/scans/${id}/`);
  }

  async restartScan(id: number): Promise<Scan> {
    const response = await this.api.post<Scan>(`/api/orchestrator/scans/${id}/restart/`);
    return response.data;
  }

  async cancelScan(id: number): Promise<Scan> {
    const response = await this.api.post<Scan>(`/api/orchestrator/scans/${id}/cancel/`);
    return response.data;
  }

  async getScansStatistics(): Promise<{ total_scans: number; status_distribution: Record<string, number>; recent_scans: Scan[] }> {
    const response = await this.api.get('/api/orchestrator/scans/statistics/');
    return response.data;
  }

  // Scan Type endpoints
  async getScanTypes(params?: { page?: number }): Promise<ApiResponse<ScanType>> {
    const response = await this.api.get<ApiResponse<ScanType>>('/api/orchestrator/scan-types/', { params });
    return response.data;
  }

  async getScanType(id: number): Promise<ScanType> {
    const response = await this.api.get<ScanType>(`/api/orchestrator/scan-types/${id}/`);
    return response.data;
  }

  async createScanType(data: CreateScanTypeData): Promise<ScanType> {
    const response = await this.api.post<ScanType>('/api/orchestrator/scan-types/', data);
    return response.data;
  }

  async updateScanType(id: number, data: Partial<CreateScanTypeData>): Promise<ScanType> {
    const response = await this.api.patch<ScanType>(`/api/orchestrator/scan-types/${id}/`, data);
    return response.data;
  }

  async deleteScanType(id: number): Promise<void> {
    await this.api.delete(`/api/orchestrator/scan-types/${id}/`);
  }

  // Port List endpoints
  async getPortLists(params?: { page?: number }): Promise<ApiResponse<PortList>> {
    const response = await this.api.get<ApiResponse<PortList>>('/api/orchestrator/port-lists/', { params });
    return response.data;
  }

  async getPortList(id: number): Promise<PortList> {
    const response = await this.api.get<PortList>(`/api/orchestrator/port-lists/${id}/`);
    return response.data;
  }

  async createPortList(data: CreatePortListData): Promise<PortList> {
    const response = await this.api.post<PortList>('/api/orchestrator/port-lists/', data);
    return response.data;
  }

  async updatePortList(id: number, data: Partial<CreatePortListData>): Promise<PortList> {
    const response = await this.api.patch<PortList>(`/api/orchestrator/port-lists/${id}/`, data);
    return response.data;
  }

  async deletePortList(id: number): Promise<void> {
    await this.api.delete(`/api/orchestrator/port-lists/${id}/`);
  }

  // Dashboard stats (computed)
  async getDashboardStats(): Promise<DashboardStats> {
    const [customersResponse, scansResponse] = await Promise.all([
      this.getCustomers(),
      this.getScansStatistics(),
    ]);

    const customers = customersResponse.results || [];
    const totalTargets = customers.reduce((sum, customer) => sum + customer.targets_count, 0);
    const runningScans = await this.getScans({ is_running: true });

    return {
      total_customers: customers.length,
      total_targets: totalTargets,
      total_scans: scansResponse.total_scans,
      recent_scans: scansResponse.recent_scans,
      status_distribution: scansResponse.status_distribution,
      running_scans: runningScans.results?.length || 0,
    };
  }
}

export const apiService = new ApiService();
export default apiService;