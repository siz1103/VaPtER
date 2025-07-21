import api from '@/lib/api';
import { FingerprintDetail, ServiceSummaryResponse } from '@/types';

export const fingerprintService = {
  // Get all fingerprint details
  async getAll(params?: {
    scan?: number;
    target?: number;
    port?: number;
    protocol?: string;
    service_name?: string;
  }) {
    const response = await api.get<FingerprintDetail[]>('/fingerprint-details/', { params });
    return response.data;
  },

  // Get fingerprint detail by ID
  async getById(id: number) {
    const response = await api.get<FingerprintDetail>(`/fingerprint-details/${id}/`);
    return response.data;
  },

  // Get fingerprints by scan
  async getByScan(scanId: number) {
    const response = await api.get<FingerprintDetail[]>('/fingerprint-details/by_scan/', {
      params: { scan_id: scanId }
    });
    return response.data;
  },

  // Get fingerprints by target
  async getByTarget(targetId: number, latestOnly: boolean = false) {
    const response = await api.get<FingerprintDetail[]>('/fingerprint-details/by_target/', {
      params: { 
        target_id: targetId,
        latest_only: latestOnly
      }
    });
    return response.data;
  },

  // Get service summary
  async getServiceSummary() {
    const response = await api.get<ServiceSummaryResponse>('/fingerprint-details/service_summary/');
    return response.data;
  },

  // Format port display
  formatPort(fingerprint: FingerprintDetail): string {
    return `${fingerprint.port}/${fingerprint.protocol}`;
  },

  // Format service display
  formatService(fingerprint: FingerprintDetail): string {
    let service = fingerprint.service_name || 'Unknown';
    if (fingerprint.service_version) {
      service += ` ${fingerprint.service_version}`;
    }
    if (fingerprint.service_product && fingerprint.service_product !== fingerprint.service_name) {
      service += ` (${fingerprint.service_product})`;
    }
    return service;
  },

  // Get confidence level label
  getConfidenceLevel(score: number): { label: string; color: string } {
    if (score >= 90) return { label: 'High', color: 'text-green-500' };
    if (score >= 70) return { label: 'Medium', color: 'text-yellow-500' };
    if (score >= 50) return { label: 'Low', color: 'text-orange-500' };
    return { label: 'Very Low', color: 'text-red-500' };
  }
};