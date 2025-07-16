// frontend/src/pages/Dashboard.tsx

import React, { useState, useEffect } from 'react';
import {
  UserGroupIcon,
  ServerIcon,
  CpuChipIcon,
  ChartBarIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';
import { useApp } from '../context/AppContext';
import apiService from '../services/api';
import { Scan } from '../types';

interface StatsCard {
  title: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  change?: string;
  changeType?: 'increase' | 'decrease' | 'neutral';
}

const Dashboard: React.FC = () => {
  const { state, dispatch } = useApp();
  const [isLoading, setIsLoading] = useState(true);
  const [recentScans, setRecentScans] = useState<Scan[]>([]);

  useEffect(() => {
    loadDashboardData();
  }, [state.selectedCustomer]);

  const loadDashboardData = async () => {
    setIsLoading(true);
    try {
      if (state.selectedCustomer) {
        // Load customer-specific data
        const customerStats = await apiService.getCustomerStatistics(state.selectedCustomer.id);
        const customerScans = await apiService.getScans({ 
          customer: state.selectedCustomer.id,
          page: 1 
        });
        
        dispatch({ type: 'SET_CUSTOMER_STATS', payload: customerStats });
        setRecentScans(customerScans.results?.slice(0, 5) || []);
      } else {
        // Load general dashboard data
        const dashboardStats = await apiService.getDashboardStats();
        dispatch({ type: 'SET_DASHBOARD_STATS', payload: dashboardStats });
        setRecentScans(dashboardStats.recent_scans || []);
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      dispatch({ type: 'SET_ERROR', payload: 'Failed to load dashboard data' });
    } finally {
      setIsLoading(false);
    }
  };

  const getStatsCards = (): StatsCard[] => {
    if (state.selectedCustomer && state.customerStats) {
      return [
        {
          title: 'Targets',
          value: state.customerStats.targets_count.toString(),
          icon: ServerIcon,
          color: 'bg-blue-500',
        },
        {
          title: 'Total Scans',
          value: state.customerStats.scans_count.toString(),
          icon: CpuChipIcon,
          color: 'bg-green-500',
        },
        {
          title: 'Completed',
          value: (state.customerStats.status_distribution.Completed || 0).toString(),
          icon: CheckCircleIcon,
          color: 'bg-emerald-500',
        },
        {
          title: 'Failed',
          value: (state.customerStats.status_distribution.Failed || 0).toString(),
          icon: XCircleIcon,
          color: 'bg-red-500',
        },
      ];
    } else if (state.dashboardStats) {
      return [
        {
          title: 'Customers',
          value: state.dashboardStats.total_customers.toString(),
          icon: UserGroupIcon,
          color: 'bg-purple-500',
        },
        {
          title: 'Targets',
          value: state.dashboardStats.total_targets.toString(),
          icon: ServerIcon,
          color: 'bg-blue-500',
        },
        {
          title: 'Total Scans',
          value: state.dashboardStats.total_scans.toString(),
          icon: CpuChipIcon,
          color: 'bg-green-500',
        },
        {
          title: 'Running',
          value: state.dashboardStats.running_scans.toString(),
          icon: ClockIcon,
          color: 'bg-yellow-500',
        },
      ];
    }
    return [];
  };

  const getStatusColor = (status: string) => {
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  const statsCards = getStatsCards();

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            {state.selectedCustomer ? `${state.selectedCustomer.name} Dashboard` : 'Dashboard'}
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            {state.selectedCustomer 
              ? `Overview of ${state.selectedCustomer.name}'s vulnerability assessment data`
              : 'Overview of your vulnerability assessment platform'
            }
          </p>
        </div>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {statsCards.map((card) => (
          <div key={card.title} className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className={`p-3 rounded-md ${card.color}`}>
                    <card.icon className="h-6 w-6 text-white" />
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      {card.title}
                    </dt>
                    <dd className="flex items-baseline">
                      <div className="text-2xl font-semibold text-gray-900">
                        {card.value}
                      </div>
                      {card.change && (
                        <div className={`ml-2 flex items-baseline text-sm font-semibold ${
                          card.changeType === 'increase' ? 'text-green-600' : 
                          card.changeType === 'decrease' ? 'text-red-600' : 'text-gray-500'
                        }`}>
                          {card.change}
                        </div>
                      )}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent scans */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Recent Scans
          </h3>
          
          {recentScans.length === 0 ? (
            <div className="text-center py-8">
              <CpuChipIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No scans yet</h3>
              <p className="mt-1 text-sm text-gray-500">
                {state.selectedCustomer 
                  ? 'No scans have been run for this customer yet.'
                  : 'Start by selecting a customer and creating targets for scanning.'
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
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {recentScans.map((scan) => (
                    <tr key={scan.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {scan.target_name}
                          </div>
                          <div className="text-sm text-gray-500">
                            {scan.target_address}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {scan.scan_type_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(scan.status)}`}>
                          {scan.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(scan.initiated_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {scan.duration_seconds 
                          ? `${Math.round(scan.duration_seconds / 60)}m`
                          : '-'
                        }
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;