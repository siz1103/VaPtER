// frontend/src/pages/Scans.tsx

import React, { useState, useEffect } from 'react';
import { 
  CpuChipIcon, 
  PlayIcon, 
  PauseIcon,
  ArrowPathIcon,
  XMarkIcon,
  EyeIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { useApp } from '../context/AppContext';
import { Scan, ScanStatus } from '../types';
import apiService from '../services/api';
import ScanDetailsModal from '../components/Modals/ScanDetailsModal';
import ConfirmDialog from '../components/Common/ConfirmDialog';

const Scans: React.FC = () => {
  const { state } = useApp();
  const [scans, setScans] = useState<Scan[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedScan, setSelectedScan] = useState<Scan | null>(null);
  const [scanToCancel, setScanToCancel] = useState<Scan | null>(null);
  const [scanToRestart, setScanToRestart] = useState<Scan | null>(null);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');

  // Auto-refresh for running scans
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (state.selectedCustomer) {
      loadScans();
      // Refresh every 5 seconds if there are running scans
      interval = setInterval(() => {
        const runningScans = scans.filter(scan => isRunning(scan.status));
        if (runningScans.length > 0) {
          loadScans();
        }
      }, 5000);
    } else {
      setScans([]);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [state.selectedCustomer]);

  const loadScans = async () => {
    if (!state.selectedCustomer) return;
    
    setIsLoading(true);
    try {
      const response = await apiService.getScans({ 
        customer: state.selectedCustomer.id 
      });
      setScans(response.results || []);
    } catch (error) {
      console.error('Error loading scans:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const isRunning = (status: ScanStatus): boolean => {
    return [
      'Pending',
      'Queued',
      'Nmap Scan Running',
      'Finger Scan Running',
      'Enum Scan Running',
      'Web Scan Running',
      'Vuln Lookup Running',
      'Report Generation Running',
    ].includes(status);
  };

  const handleCancelScan = async () => {
    if (!scanToCancel) return;
    
    try {
      await apiService.cancelScan(scanToCancel.id);
      loadScans();
      setScanToCancel(null);
    } catch (error) {
      console.error('Error canceling scan:', error);
    }
  };

  const handleRestartScan = async () => {
    if (!scanToRestart) return;
    
    try {
      await apiService.restartScan(scanToRestart.id);
      loadScans();
      setScanToRestart(null);
    } catch (error) {
      console.error('Error restarting scan:', error);
    }
  };

  const handleViewDetails = (scan: Scan) => {
    setSelectedScan(scan);
    setIsDetailsModalOpen(true);
  };

  const getStatusColor = (status: ScanStatus) => {
    switch (status) {
      case 'Completed':
        return 'text-success-600 bg-success-100';
      case 'Failed':
        return 'text-error-600 bg-error-100';
      case 'Pending':
      case 'Queued':
        return 'text-gray-600 bg-gray-100';
      default:
        return 'text-warning-600 bg-warning-100';
    }
  };

  const getStatusIcon = (status: ScanStatus) => {
    const iconClasses = "h-4 w-4";
    
    switch (status) {
      case 'Completed':
        return <CheckCircleIcon className={`${iconClasses} text-success-600`} />;
      case 'Failed':
        return <ExclamationTriangleIcon className={`${iconClasses} text-error-600`} />;
      case 'Pending':
      case 'Queued':
        return <ClockIcon className={`${iconClasses} text-gray-600`} />;
      default:
        return <div className={`${iconClasses} rounded-full bg-warning-600 animate-pulse`} />;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return '-';
    
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    if (minutes > 0) {
      return `${minutes}m ${remainingSeconds}s`;
    }
    return `${remainingSeconds}s`;
  };

  const getFilteredScans = () => {
    let filtered = scans;

    // Filter by status
    if (statusFilter !== 'all') {
      if (statusFilter === 'running') {
        filtered = filtered.filter(scan => isRunning(scan.status));
      } else {
        filtered = filtered.filter(scan => scan.status === statusFilter);
      }
    }

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(scan => 
        scan.target_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        scan.target_address.toLowerCase().includes(searchTerm.toLowerCase()) ||
        scan.scan_type_name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    return filtered;
  };

  const filteredScans = getFilteredScans();
  const runningScansCount = scans.filter(scan => isRunning(scan.status)).length;

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            Scans
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            {state.selectedCustomer 
              ? `View and manage scans for ${state.selectedCustomer.name}`
              : 'Select a customer to view their scans'
            }
          </p>
          {runningScansCount > 0 && (
            <div className="mt-2 flex items-center text-sm text-warning-600">
              <div className="h-2 w-2 bg-warning-600 rounded-full animate-pulse mr-2"></div>
              {runningScansCount} scan{runningScansCount > 1 ? 's' : ''} running
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      {!state.selectedCustomer ? (
        <div className="text-center py-12">
          <CpuChipIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Select a customer</h3>
          <p className="mt-1 text-sm text-gray-500">
            You need to select a customer to view and manage their scans.
          </p>
        </div>
      ) : (
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            {/* Filters and search */}
            <div className="mb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0">
              <div className="flex items-center space-x-4">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Scans for {state.selectedCustomer.name}
                </h3>
                <button
                  onClick={loadScans}
                  className="p-1 text-gray-400 hover:text-gray-600 rounded-md"
                  title="Refresh"
                >
                  <ArrowPathIcon className="h-5 w-5" />
                </button>
              </div>
              
              <div className="flex space-x-2">
                {/* Status filter */}
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                >
                  <option value="all">All Status</option>
                  <option value="running">Running</option>
                  <option value="Completed">Completed</option>
                  <option value="Failed">Failed</option>
                  <option value="Pending">Pending</option>
                </select>

                {/* Search */}
                <input
                  type="text"
                  placeholder="Search scans..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="block w-full sm:w-64 rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                />
              </div>
            </div>

            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              </div>
            ) : filteredScans.length === 0 ? (
              <div className="text-center py-8">
                <CpuChipIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">
                  {scans.length === 0 ? 'No scans' : 'No scans found'}
                </h3>
                <p className="mt-1 text-sm text-gray-500">
                  {scans.length === 0 
                    ? 'Get started by running a scan on one of your targets.'
                    : 'Try adjusting your filters or search terms.'
                  }
                </p>
              </div>
            ) : (
              <div className="overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Target
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Scan Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Started
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Duration
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredScans.map((scan) => (
                      <tr key={scan.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {scan.target_name}
                            </div>
                            <div className="text-sm text-gray-500">
                              <code className="bg-gray-100 px-1 py-0.5 rounded text-xs">
                                {scan.target_address}
                              </code>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {scan.scan_type_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(scan.status)}`}>
                            {getStatusIcon(scan.status)}
                            <span className="ml-1">{scan.status}</span>
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(scan.initiated_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDuration(scan.duration_seconds)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex justify-end space-x-2">
                            <button
                              onClick={() => handleViewDetails(scan)}
                              className="text-primary-600 hover:text-primary-900 p-1 rounded-md hover:bg-primary-50"
                              title="View Details"
                            >
                              <EyeIcon className="h-4 w-4" />
                            </button>
                            
                            {isRunning(scan.status) && (
                              <button
                                onClick={() => setScanToCancel(scan)}
                                className="text-error-600 hover:text-error-900 p-1 rounded-md hover:bg-error-50"
                                title="Cancel Scan"
                              >
                                <XMarkIcon className="h-4 w-4" />
                              </button>
                            )}
                            
                            {(scan.status === 'Failed' || scan.status === 'Completed') && (
                              <button
                                onClick={() => setScanToRestart(scan)}
                                className="text-warning-600 hover:text-warning-900 p-1 rounded-md hover:bg-warning-50"
                                title="Restart Scan"
                              >
                                <ArrowPathIcon className="h-4 w-4" />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Scan Details Modal */}
      {selectedScan && (
        <ScanDetailsModal
          isOpen={isDetailsModalOpen}
          onClose={() => {
            setIsDetailsModalOpen(false);
            setSelectedScan(null);
          }}
          scan={selectedScan}
        />
      )}

      {/* Cancel Scan Confirmation */}
      <ConfirmDialog
        isOpen={!!scanToCancel}
        onClose={() => setScanToCancel(null)}
        onConfirm={handleCancelScan}
        title="Cancel Scan"
        message={`Are you sure you want to cancel the scan for "${scanToCancel?.target_name}"?`}
        confirmText="Cancel Scan"
        confirmStyle="error"
        icon="warning"
      />

      {/* Restart Scan Confirmation */}
      <ConfirmDialog
        isOpen={!!scanToRestart}
        onClose={() => setScanToRestart(null)}
        onConfirm={handleRestartScan}
        title="Restart Scan"
        message={`Are you sure you want to restart the scan for "${scanToRestart?.target_name}"?`}
        confirmText="Restart"
        confirmStyle="warning"
        icon="info"
      />
    </div>
  );
};

export default Scans;