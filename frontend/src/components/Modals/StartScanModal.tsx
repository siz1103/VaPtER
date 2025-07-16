// frontend/src/components/Modals/StartScanModal.tsx

import React, { useState, useEffect } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { XMarkIcon, PlayIcon } from '@heroicons/react/24/outline';
import { useForm, SubmitHandler } from 'react-hook-form';
import { Target, ScanType, StartScanData } from '../../types';
import apiService from '../../services/api';

interface StartScanModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  target: Target;
}

interface FormData {
  scan_type_id: number;
}

const StartScanModal: React.FC<StartScanModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  target,
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scanTypes, setScanTypes] = useState<ScanType[]>([]);
  const [selectedScanType, setSelectedScanType] = useState<ScanType | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
  } = useForm<FormData>();

  const watchedScanTypeId = watch('scan_type_id');

  // Load scan types on mount
  useEffect(() => {
    loadScanTypes();
  }, []);

  // Update selected scan type when form value changes
  useEffect(() => {
    if (watchedScanTypeId && scanTypes.length > 0) {
      const scanType = scanTypes.find(st => st.id === parseInt(watchedScanTypeId.toString()));
      setSelectedScanType(scanType || null);
    }
  }, [watchedScanTypeId, scanTypes]);

  const loadScanTypes = async () => {
    try {
      const response = await apiService.getScanTypes();
      setScanTypes(response.results || []);
    } catch (error) {
      console.error('Error loading scan types:', error);
      setError('Failed to load scan types');
    }
  };

  const onSubmit: SubmitHandler<FormData> = async (data) => {
    setIsLoading(true);
    setError(null);
    
    try {
      await apiService.startTargetScan(target.id, data);
      onSuccess();
      reset();
      onClose();
    } catch (error: any) {
      console.error('Error starting scan:', error);
      
      let errorMessage = 'Failed to start scan';
      if (error.response?.data) {
        if (error.response.data.error) {
          errorMessage = error.response.data.error;
        } else if (error.response.data.detail) {
          errorMessage = error.response.data.detail;
        }
      }
      
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    reset();
    setError(null);
    setSelectedScanType(null);
    onClose();
  };

  const getPluginBadges = (scanType: ScanType) => {
    const badges = [];
    
    if (scanType.plugin_finger) badges.push('Fingerprint');
    if (scanType.plugin_enum) badges.push('Enumeration');
    if (scanType.plugin_web) badges.push('Web Scanning');
    if (scanType.plugin_vuln_lookup) badges.push('Vulnerability Lookup');
    
    return badges;
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={handleClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-lg transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                <div className="flex items-center justify-between mb-4">
                  <Dialog.Title
                    as="h3"
                    className="text-lg font-medium leading-6 text-gray-900"
                  >
                    Start Scan
                  </Dialog.Title>
                  <button
                    type="button"
                    className="rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    onClick={handleClose}
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                {/* Target info */}
                <div className="mb-4 p-3 bg-gray-50 rounded-md">
                  <h4 className="text-sm font-medium text-gray-900">Target Information</h4>
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">{target.name}</span>
                    {' '}({target.address})
                  </p>
                  {target.description && (
                    <p className="text-sm text-gray-500 mt-1">{target.description}</p>
                  )}
                </div>

                {error && (
                  <div className="mb-4 p-3 bg-error-50 border border-error-200 rounded-md">
                    <p className="text-sm text-error-700">{error}</p>
                  </div>
                )}

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                  <div>
                    <label htmlFor="scan_type_id" className="block text-sm font-medium text-gray-700 mb-2">
                      Select Scan Type *
                    </label>
                    <div className="space-y-2">
                      {scanTypes.map((scanType) => (
                        <div key={scanType.id} className="relative">
                          <label className="flex items-start p-3 border rounded-md cursor-pointer hover:bg-gray-50">
                            <input
                              {...register('scan_type_id', { required: 'Please select a scan type' })}
                              type="radio"
                              value={scanType.id}
                              className="mt-1 h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                            />
                            <div className="ml-3 flex-1">
                              <div className="flex items-center justify-between">
                                <span className="text-sm font-medium text-gray-900">
                                  {scanType.name}
                                </span>
                                {scanType.only_discovery && (
                                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                    Discovery Only
                                  </span>
                                )}
                              </div>
                              {scanType.description && (
                                <p className="text-sm text-gray-500 mt-1">
                                  {scanType.description}
                                </p>
                              )}
                              {scanType.port_list_name && (
                                <p className="text-xs text-gray-500 mt-1">
                                  Port List: {scanType.port_list_name}
                                </p>
                              )}
                              {/* Plugin badges */}
                              {getPluginBadges(scanType).length > 0 && (
                                <div className="flex flex-wrap gap-1 mt-2">
                                  {getPluginBadges(scanType).map((plugin) => (
                                    <span
                                      key={plugin}
                                      className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800"
                                    >
                                      {plugin}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          </label>
                        </div>
                      ))}
                    </div>
                    {errors.scan_type_id && (
                      <p className="mt-1 text-sm text-error-600">{errors.scan_type_id.message}</p>
                    )}
                  </div>

                  {/* Scan type details */}
                  {selectedScanType && (
                    <div className="p-3 bg-primary-50 rounded-md">
                      <h4 className="text-sm font-medium text-primary-900 mb-2">
                        Scan Configuration
                      </h4>
                      <div className="space-y-1 text-sm text-primary-800">
                        <div className="flex items-center space-x-2">
                          <span className="w-2 h-2 bg-primary-500 rounded-full"></span>
                          <span>
                            {selectedScanType.only_discovery ? 'Discovery scan (ping only)' : 'Port scanning enabled'}
                          </span>
                        </div>
                        {selectedScanType.consider_alive && (
                          <div className="flex items-center space-x-2">
                            <span className="w-2 h-2 bg-primary-500 rounded-full"></span>
                            <span>Skip host discovery (consider all hosts alive)</span>
                          </div>
                        )}
                        {selectedScanType.be_quiet && (
                          <div className="flex items-center space-x-2">
                            <span className="w-2 h-2 bg-primary-500 rounded-full"></span>
                            <span>Quiet mode enabled</span>
                          </div>
                        )}
                        {getPluginBadges(selectedScanType).length > 0 && (
                          <div className="flex items-center space-x-2">
                            <span className="w-2 h-2 bg-primary-500 rounded-full"></span>
                            <span>
                              Additional plugins: {getPluginBadges(selectedScanType).join(', ')}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  <div className="flex justify-end space-x-3 pt-4">
                    <button
                      type="button"
                      onClick={handleClose}
                      className="rounded-md border border-gray-300 bg-white py-2 px-4 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={isLoading}
                      className="inline-flex items-center rounded-md border border-transparent bg-primary-600 py-2 px-4 text-sm font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50"
                    >
                      {isLoading ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          Starting...
                        </>
                      ) : (
                        <>
                          <PlayIcon className="-ml-1 mr-2 h-4 w-4" />
                          Start Scan
                        </>
                      )}
                    </button>
                  </div>
                </form>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
};

export default StartScanModal;