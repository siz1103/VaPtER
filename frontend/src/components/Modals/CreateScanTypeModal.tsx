// frontend/src/components/Modals/CreateScanTypeModal.tsx

import React, { useState, useEffect } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { useForm, SubmitHandler } from 'react-hook-form';
import { ScanType, CreateScanTypeData, PortList } from '../../types';
import apiService from '../../services/api';

interface CreateScanTypeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (scanType: ScanType) => void;
  scanType?: ScanType; // For editing existing scan type
  portLists: PortList[];
}

const CreateScanTypeModal: React.FC<CreateScanTypeModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  scanType,
  portLists,
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
  } = useForm<CreateScanTypeData>({
    defaultValues: scanType ? {
      name: scanType.name,
      only_discovery: scanType.only_discovery,
      consider_alive: scanType.consider_alive,
      be_quiet: scanType.be_quiet,
      port_list: scanType.port_list,
      plugin_finger: scanType.plugin_finger,
      plugin_enum: scanType.plugin_enum,
      plugin_web: scanType.plugin_web,
      plugin_vuln_lookup: scanType.plugin_vuln_lookup,
      description: scanType.description || '',
    } : {
      only_discovery: false,
      consider_alive: false,
      be_quiet: false,
      plugin_finger: false,
      plugin_enum: false,
      plugin_web: false,
      plugin_vuln_lookup: false,
    },
  });

  const watchOnlyDiscovery = watch('only_discovery');

  const onSubmit: SubmitHandler<CreateScanTypeData> = async (data) => {
    setIsLoading(true);
    setError(null);
    
    try {
      let result: ScanType;
      
      // If discovery only, remove port_list
      if (data.only_discovery) {
        data.port_list = undefined;
      }
      
      if (scanType) {
        // Edit existing scan type
        result = await apiService.updateScanType(scanType.id, data);
      } else {
        // Create new scan type
        result = await apiService.createScanType(data);
      }
      
      onSuccess(result);
      reset();
      onClose();
    } catch (error: any) {
      console.error('Error saving scan type:', error);
      
      let errorMessage = 'Failed to save scan type';
      if (error.response?.data) {
        if (error.response.data.name) {
          errorMessage = Array.isArray(error.response.data.name) 
            ? error.response.data.name[0]
            : error.response.data.name;
        } else if (error.response.data.error) {
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
    onClose();
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
              <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                <div className="flex items-center justify-between mb-4">
                  <Dialog.Title
                    as="h3"
                    className="text-lg font-medium leading-6 text-gray-900"
                  >
                    {scanType ? 'Edit Scan Type' : 'Create New Scan Type'}
                  </Dialog.Title>
                  <button
                    type="button"
                    className="rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    onClick={handleClose}
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                {error && (
                  <div className="mb-4 p-3 bg-error-50 border border-error-200 rounded-md">
                    <p className="text-sm text-error-700">{error}</p>
                  </div>
                )}

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                  <div>
                    <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                      Name *
                    </label>
                    <input
                      {...register('name', { required: 'Name is required' })}
                      type="text"
                      id="name"
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                      placeholder="Enter scan type name"
                    />
                    {errors.name && (
                      <p className="mt-1 text-sm text-error-600">{errors.name.message}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                      Description
                    </label>
                    <textarea
                      {...register('description')}
                      id="description"
                      rows={3}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                      placeholder="Enter description (optional)"
                    />
                  </div>

                  {/* Scan Configuration */}
                  <div className="space-y-3">
                    <h4 className="text-sm font-medium text-gray-900">Scan Configuration</h4>
                    
                    <div className="space-y-2">
                      <label className="flex items-center">
                        <input
                          {...register('only_discovery')}
                          type="checkbox"
                          className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">Discovery Only (ping scan)</span>
                      </label>
                      
                      <label className="flex items-center">
                        <input
                          {...register('consider_alive')}
                          type="checkbox"
                          className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">Consider all hosts alive</span>
                      </label>
                      
                      <label className="flex items-center">
                        <input
                          {...register('be_quiet')}
                          type="checkbox"
                          className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">Quiet mode</span>
                      </label>
                    </div>
                  </div>

                  {/* Port List */}
                  {!watchOnlyDiscovery && (
                    <div>
                      <label htmlFor="port_list" className="block text-sm font-medium text-gray-700">
                        Port List
                      </label>
                      <select
                        {...register('port_list')}
                        id="port_list"
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                      >
                        <option value="">Select a port list (optional)</option>
                        {portLists.map((portList) => (
                          <option key={portList.id} value={portList.id}>
                            {portList.name}
                          </option>
                        ))}
                      </select>
                      <p className="mt-1 text-sm text-gray-500">
                        Choose a port list to scan specific ports
                      </p>
                    </div>
                  )}

                  {/* Plugins */}
                  <div className="space-y-3">
                    <h4 className="text-sm font-medium text-gray-900">Plugins</h4>
                    
                    <div className="space-y-2">
                      <label className="flex items-center">
                        <input
                          {...register('plugin_finger')}
                          type="checkbox"
                          className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">Fingerprinting</span>
                      </label>
                      
                      <label className="flex items-center">
                        <input
                          {...register('plugin_enum')}
                          type="checkbox"
                          className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">Enumeration</span>
                      </label>
                      
                      <label className="flex items-center">
                        <input
                          {...register('plugin_web')}
                          type="checkbox"
                          className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">Web Scanning</span>
                      </label>
                      
                      <label className="flex items-center">
                        <input
                          {...register('plugin_vuln_lookup')}
                          type="checkbox"
                          className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">Vulnerability Lookup</span>
                      </label>
                    </div>
                  </div>

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
                      className="rounded-md border border-transparent bg-primary-600 py-2 px-4 text-sm font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50"
                    >
                      {isLoading ? 'Saving...' : (scanType ? 'Update' : 'Create')}
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

export default CreateScanTypeModal;