// frontend/src/components/Modals/CreateTargetModal.tsx

import React, { useState, useEffect } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { useForm, SubmitHandler } from 'react-hook-form';
import { Customer, Target, CreateTargetData } from '../../types';
import apiService from '../../services/api';

interface CreateTargetModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (target: Target) => void;
  customer: Customer | null;
  target?: Target; // For editing existing target
}

const CreateTargetModal: React.FC<CreateTargetModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  customer,
  target,
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setValue,
  } = useForm<CreateTargetData>();

  // Set form values when editing
  useEffect(() => {
    if (target && customer) {
      setValue('customer', customer.id);
      setValue('name', target.name);
      setValue('address', target.address);
      setValue('description', target.description || '');
    } else if (customer) {
      setValue('customer', customer.id);
    }
  }, [target, customer, setValue]);

  const onSubmit: SubmitHandler<CreateTargetData> = async (data) => {
    if (!customer) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      let result: Target;
      
      if (target) {
        // Edit existing target
        result = await apiService.updateTarget(target.id, data);
      } else {
        // Create new target
        result = await apiService.createTarget(data);
      }
      
      onSuccess(result);
      reset();
      onClose();
    } catch (error: any) {
      console.error('Error saving target:', error);
      
      // Extract error message from response
      let errorMessage = 'Failed to save target';
      if (error.response?.data) {
        if (error.response.data.address) {
          errorMessage = Array.isArray(error.response.data.address) 
            ? error.response.data.address[0]
            : error.response.data.address;
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
                    {target ? 'Edit Target' : 'Create New Target'}
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
                  <input
                    type="hidden"
                    {...register('customer', { required: true })}
                  />

                  <div>
                    <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                      Target Name *
                    </label>
                    <input
                      {...register('name', { required: 'Target name is required' })}
                      type="text"
                      id="name"
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                      placeholder="Enter target name"
                    />
                    {errors.name && (
                      <p className="mt-1 text-sm text-error-600">{errors.name.message}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="address" className="block text-sm font-medium text-gray-700">
                      IP Address or FQDN *
                    </label>
                    <input
                      {...register('address', { 
                        required: 'Address is required',
                        pattern: {
                          value: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$|^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$/,
                          message: 'Enter a valid IP address or FQDN'
                        }
                      })}
                      type="text"
                      id="address"
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm font-mono"
                      placeholder="192.168.1.100 or example.com"
                    />
                    {errors.address && (
                      <p className="mt-1 text-sm text-error-600">{errors.address.message}</p>
                    )}
                    <p className="mt-1 text-sm text-gray-500">
                      Enter an IP address (e.g., 192.168.1.100) or a domain name (e.g., example.com)
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
                      {isLoading ? 'Saving...' : (target ? 'Update' : 'Create')}
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

export default CreateTargetModal;