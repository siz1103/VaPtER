// frontend/src/pages/Targets.tsx

import React, { useState, useEffect } from 'react';
import { 
  ServerIcon, 
  PlusIcon, 
  PencilIcon, 
  TrashIcon,
  PlayIcon,
  EyeIcon,
} from '@heroicons/react/24/outline';
import { useApp } from '../context/AppContext';
import { Target } from '../types';
import apiService from '../services/api';
import CreateTargetModal from '../components/Modals/CreateTargetModal';
import StartScanModal from '../components/Modals/StartScanModal';
import ConfirmDialog from '../components/Common/ConfirmDialog';

const Targets: React.FC = () => {
  const { state } = useApp();
  const [targets, setTargets] = useState<Target[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isStartScanModalOpen, setIsStartScanModalOpen] = useState(false);
  const [selectedTarget, setSelectedTarget] = useState<Target | null>(null);
  const [targetToEdit, setTargetToEdit] = useState<Target | null>(null);
  const [targetToDelete, setTargetToDelete] = useState<Target | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    if (state.selectedCustomer) {
      loadTargets();
    } else {
      setTargets([]);
    }
  }, [state.selectedCustomer]);

  const loadTargets = async () => {
    if (!state.selectedCustomer) return;
    
    setIsLoading(true);
    try {
      const response = await apiService.getTargets({ 
        customer: state.selectedCustomer.id 
      });
      setTargets(response.results || []);
    } catch (error) {
      console.error('Error loading targets:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateTarget = async (target: Target) => {
    setTargets([...targets, target]);
    setIsCreateModalOpen(false);
  };

  const handleUpdateTarget = async (target: Target) => {
    setTargets(targets.map(t => t.id === target.id ? target : t));
    setTargetToEdit(null);
    setIsCreateModalOpen(false);
  };

  const handleDeleteTarget = async () => {
    if (!targetToDelete) return;
    
    try {
      await apiService.deleteTarget(targetToDelete.id);
      setTargets(targets.filter(t => t.id !== targetToDelete.id));
      setTargetToDelete(null);
    } catch (error) {
      console.error('Error deleting target:', error);
    }
  };

  const handleStartScan = (target: Target) => {
    setSelectedTarget(target);
    setIsStartScanModalOpen(true);
  };

  const handleScanStarted = () => {
    setIsStartScanModalOpen(false);
    setSelectedTarget(null);
    // Refresh targets to update scan counts
    loadTargets();
  };

  const filteredTargets = targets.filter(target => 
    target.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    target.address.toLowerCase().includes(searchTerm.toLowerCase())
  );

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

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            Targets
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            {state.selectedCustomer 
              ? `Manage targets for ${state.selectedCustomer.name}`
              : 'Select a customer to view their targets'
            }
          </p>
        </div>
        <div className="mt-4 flex md:mt-0 md:ml-4">
          <button
            type="button"
            onClick={() => setIsCreateModalOpen(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
            disabled={!state.selectedCustomer}
          >
            <PlusIcon className="-ml-1 mr-2 h-5 w-5" aria-hidden="true" />
            Add Target
          </button>
        </div>
      </div>

      {/* Content */}
      {!state.selectedCustomer ? (
        <div className="text-center py-12">
          <ServerIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Select a customer</h3>
          <p className="mt-1 text-sm text-gray-500">
            You need to select a customer to view and manage their targets.
          </p>
        </div>
      ) : (
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            {/* Search and filters */}
            <div className="mb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-2 sm:mb-0">
                Targets for {state.selectedCustomer.name}
              </h3>
              <div className="w-full sm:w-64">
                <input
                  type="text"
                  placeholder="Search targets..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                />
              </div>
            </div>

            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              </div>
            ) : filteredTargets.length === 0 ? (
              <div className="text-center py-8">
                <ServerIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">
                  {targets.length === 0 ? 'No targets' : 'No targets found'}
                </h3>
                <p className="mt-1 text-sm text-gray-500">
                  {targets.length === 0 
                    ? 'Get started by creating a new target to scan.'
                    : 'Try adjusting your search terms.'
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
                        Address
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Scans
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Last Scan
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Created
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredTargets.map((target) => (
                      <tr key={target.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {target.name}
                            </div>
                            {target.description && (
                              <div className="text-sm text-gray-500 truncate max-w-xs">
                                {target.description}
                              </div>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          <code className="bg-gray-100 px-2 py-1 rounded text-xs">
                            {target.address}
                          </code>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                            {target.scans_count} scans
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {target.last_scan ? (
                            <div>
                              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(target.last_scan.status)}`}>
                                {target.last_scan.status}
                              </span>
                              <div className="text-xs text-gray-500 mt-1">
                                {formatDate(target.last_scan.initiated_at)}
                              </div>
                            </div>
                          ) : (
                            <span className="text-sm text-gray-500">No scans</span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(target.created_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex justify-end space-x-2">
                            <button
                              onClick={() => handleStartScan(target)}
                              className="text-primary-600 hover:text-primary-900 p-1 rounded-md hover:bg-primary-50"
                              title="Start Scan"
                            >
                              <PlayIcon className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => {
                                setTargetToEdit(target);
                                setIsCreateModalOpen(true);
                              }}
                              className="text-gray-600 hover:text-gray-900 p-1 rounded-md hover:bg-gray-50"
                              title="Edit"
                            >
                              <PencilIcon className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => setTargetToDelete(target)}
                              className="text-error-600 hover:text-error-900 p-1 rounded-md hover:bg-error-50"
                              title="Delete"
                            >
                              <TrashIcon className="h-4 w-4" />
                            </button>
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

      {/* Create/Edit Target Modal */}
      <CreateTargetModal
        isOpen={isCreateModalOpen}
        onClose={() => {
          setIsCreateModalOpen(false);
          setTargetToEdit(null);
        }}
        onSuccess={targetToEdit ? handleUpdateTarget : handleCreateTarget}
        target={targetToEdit || undefined}
        customer={state.selectedCustomer}
      />

      {/* Start Scan Modal */}
      {selectedTarget && (
        <StartScanModal
          isOpen={isStartScanModalOpen}
          onClose={() => {
            setIsStartScanModalOpen(false);
            setSelectedTarget(null);
          }}
          onSuccess={handleScanStarted}
          target={selectedTarget}
        />
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={!!targetToDelete}
        onClose={() => setTargetToDelete(null)}
        onConfirm={handleDeleteTarget}
        title="Delete Target"
        message={`Are you sure you want to delete "${targetToDelete?.name}"? This action cannot be undone.`}
        confirmText="Delete"
        confirmStyle="error"
      />
    </div>
  );
};

export default Targets;