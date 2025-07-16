// frontend/src/components/Layout/Header.tsx

import React, { useState, useEffect } from 'react';
import { 
  BellIcon, 
  UserCircleIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import CustomerSelector from './CustomerSelector';
import { useApp } from '../../context/AppContext';
import apiService from '../../services/api';

const Header: React.FC = () => {
  const { state } = useApp();
  const [healthStatus, setHealthStatus] = useState<'healthy' | 'unhealthy' | 'unknown'>('unknown');
  const [runningScans, setRunningScans] = useState(0);

  // Check health status periodically
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const health = await apiService.getDetailedHealth();
        setHealthStatus(health.status === 'healthy' ? 'healthy' : 'unhealthy');
      } catch (error) {
        setHealthStatus('unhealthy');
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, []);

  // Get running scans count
  useEffect(() => {
    const getRunningScans = async () => {
      try {
        const scans = await apiService.getScans({ is_running: true });
        setRunningScans(scans.results?.length || 0);
      } catch (error) {
        console.error('Error getting running scans:', error);
      }
    };

    getRunningScans();
    const interval = setInterval(getRunningScans, 10000); // Check every 10 seconds

    return () => clearInterval(interval);
  }, []);

  const getHealthIcon = () => {
    switch (healthStatus) {
      case 'healthy':
        return <CheckCircleIcon className="h-5 w-5 text-success-500" />;
      case 'unhealthy':
        return <ExclamationTriangleIcon className="h-5 w-5 text-error-500" />;
      default:
        return <div className="h-5 w-5 rounded-full bg-gray-300 animate-pulse" />;
    }
  };

  const getHealthText = () => {
    switch (healthStatus) {
      case 'healthy':
        return 'System Healthy';
      case 'unhealthy':
        return 'System Issues';
      default:
        return 'Checking...';
    }
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Left side - Customer selector */}
          <div className="flex items-center space-x-4">
            <CustomerSelector />
            
            {/* Customer info */}
            {state.selectedCustomer && (
              <div className="hidden md:flex items-center space-x-2 text-sm text-gray-600">
                <span>•</span>
                <span>{state.selectedCustomer.targets_count} targets</span>
                <span>•</span>
                <span>{state.selectedCustomer.scans_count} scans</span>
              </div>
            )}
          </div>

          {/* Right side - Status and user info */}
          <div className="flex items-center space-x-4">
            {/* System health indicator */}
            <div className="flex items-center space-x-2">
              {getHealthIcon()}
              <span className="text-sm text-gray-600 hidden sm:inline">
                {getHealthText()}
              </span>
            </div>

            {/* Running scans notification */}
            {runningScans > 0 && (
              <div className="flex items-center space-x-2">
                <div className="relative">
                  <div className="h-3 w-3 rounded-full bg-primary-600 animate-pulse"></div>
                </div>
                <span className="text-sm text-gray-600 hidden sm:inline">
                  {runningScans} scans running
                </span>
              </div>
            )}

            {/* Notifications */}
            <button className="p-2 text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 rounded-md">
              <BellIcon className="h-5 w-5" />
            </button>

            {/* User menu */}
            <div className="flex items-center space-x-2">
              <UserCircleIcon className="h-8 w-8 text-gray-400" />
              <span className="text-sm text-gray-700 hidden sm:inline">
                Admin User
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;