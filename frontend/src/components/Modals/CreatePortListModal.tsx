// frontend/src/components/Modals/CreatePortListModal.tsx

import React, { useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { useForm, SubmitHandler } from 'react-hook-form';
import { PortList, CreatePortListData } from '../../types';
import apiService from '../../services/api';

interface CreatePortListModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (portList: PortList) => void;
  portList?: PortList; // For editing existing port list
}

const CreatePortListModal: React.FC<CreatePortListModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  portList,
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<CreatePortListData>({
    defaultValues: portList ? {
      name: portList.name,
      tcp_ports: portList.tcp_ports || '',
      udp_ports: portList.udp_ports || '',
      description: portList.description || '',
    } : {},
  });

  const onSubmit: SubmitHandler<CreatePortListData> = async (data) => {
    setIsLoading(true);
    setError(null);
    
    try {
      let result: PortList;
      
      if (portList) {
        // Edit existing port list
        result = await apiService.updatePortList(portList.id, data);
      } else {
        // Create new port list
        result = await apiService.createPortList(data);
      }
      
      onSuccess(result);
      reset();
      onClose();
    } catch (error: any) {
      console.error('Error saving port list:', error);
      
      let errorMessage = 'Failed to save port list';
      if (error.response?.data) {
        if (error.response.data.name) {
          errorMessage = Array.isArray(error.response.data.name) 
            ? error.response.data.name[0]
            : error.response.data.name;
        } else if (error.response.data.tcp_ports) {
          errorMessage = 'Invalid TCP ports format';
        } else if (error.response.data.udp_ports) {
          errorMessage = 'Invalid UDP ports format';
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

  const validatePorts = (value: string) => {
    if (!value) return true; // Empty is valid
    
    const parts = value.split(',').map(p => p.trim());
    for (const part of parts) {
      if (part.includes('-')) {
        // Range validation
        const [start, end] = part.split('-').map(p => p.trim());
        if (!/^\d+$/.test(start) || !/^\d+$/.test(end)) {
          return 'Invalid port range format';
        }
        const startPort = parseInt(start);
        const endPort = parseInt(end);
        if (startPort < 1 || startPort > 65535 || endPort < 1 || endPort > 65535) {
          return 'Port numbers must be between 1 and 65535';
        }
        if (startPort > endPort) {
          return 'Start port must be less than end port';
        }
      } else {
        // Single port validation
        if (!/^\d+$/.test(part)) {
          return 'Invalid port number format';
        }
        const port = parseInt(part);
        if (port < 1 || port > 65535) {
          return 'Port numbers must be between 1 and 65535';
        }
      }
    }
    return true;
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
                    {portList ? 'Edit Port List' : 'Create New Port List'}
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
                      placeholder="Enter port list name"
                    />
                    {errors.name && (
                      <p className="mt-1 text-sm text-error-600">{errors.name.message}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="tcp_ports" className="block text-sm font-medium text-gray-700">
                      TCP Ports
                    </label>
                    <input
                      {...register('tcp_ports', { 
                        validate: validatePorts,
                        required: function(value) {
                          const udpPorts = (this as any).getValues('udp_ports');
                          return (!value && !udpPorts) ? 'At least one of TCP or UDP ports is required' : true;
                        }
                      })}
                      type="text"
                      id="tcp_ports"
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm font-mono"
                      placeholder="80,443,8080-8090"
                    />
                    {errors.tcp_ports && (
                      <p className="mt-1 text-sm text-error-600">{errors.tcp_ports.message}</p>
                    )}
                    <p className="mt-1 text-sm text-gray-500">
                      Enter port numbers separated by commas. Use ranges like 80-90.
                    </p>
                  </div>

                  <div>
                    <label htmlFor="udp_ports" className="block text-sm font-medium text-gray-700">
                      UDP Ports
                    </label>
                    <input
                      {...register('udp_ports', { 
                        validate: validatePorts,
                        required: function(value) {
                          const tcpPorts = (this as any).getValues('tcp_ports');
                          return (!value && !tcpPorts) ? 'At least one of TCP or UDP ports is required' : true;
                        }
                      })}
                      type="text"
                      id="udp_ports"
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm font-mono"
                      placeholder="53,161,500-600"
                    />
                    {errors.udp_ports && (
                      <p className="mt-1 text-sm text-error-600">{errors.udp_ports.message}</p>
                    )}
                    <p className="mt-1 text-sm text-gray-500">
                      Enter port numbers separated by commas. Use ranges like 53-123.
                    </p>
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

                  {/* Examples */}
                  <div className="bg-gray-50 rounded-md p-3">
                    <h4 className="text-sm font-medium text-gray-900 mb-2">Examples</h4>
                    <div className="space-y-1 text-sm text-gray-600">
                      <div><strong>Single ports:</strong> 80,443,8080</div>
                      <div><strong>Port ranges:</strong> 1-1000,8000-9000</div>
                      <div><strong>Mixed:</strong> 22,80,443,8000-8999</div>
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
                      {isLoading ? 'Saving...' : (portList ? 'Update' : 'Create')}
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

export default CreatePortListModal;