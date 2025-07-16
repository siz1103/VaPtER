// frontend/src/components/Layout/CustomerSelector.tsx

import React, { useState, useEffect } from 'react';
import { Listbox, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import {
  ChevronUpDownIcon,
  CheckIcon,
  PlusIcon,
  BuildingOfficeIcon,
} from '@heroicons/react/24/outline';
import { useApp } from '../../context/AppContext';
import { Customer } from '../../types';
import apiService from '../../services/api';
import CreateCustomerModal from '../Modals/CreateCustomerModal';

const CustomerSelector: React.FC = () => {
  const { state, dispatch, selectCustomer } = useApp();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Load customers on mount
  useEffect(() => {
    loadCustomers();
  }, []);

  // Auto-select customer from localStorage
  useEffect(() => {
    if (state.customers.length > 0 && !state.selectedCustomer) {
      const savedCustomerId = localStorage.getItem('selectedCustomerId');
      if (savedCustomerId) {
        const savedCustomer = state.customers.find(c => c.id === savedCustomerId);
        if (savedCustomer) {
          selectCustomer(savedCustomer);
        }
      }
    }
  }, [state.customers, state.selectedCustomer, selectCustomer]);

  const loadCustomers = async () => {
    setIsLoading(true);
    try {
      const response = await apiService.getCustomers();
      dispatch({ type: 'SET_CUSTOMERS', payload: response.results || [] });
    } catch (error) {
      console.error('Error loading customers:', error);
      dispatch({ type: 'SET_ERROR', payload: 'Failed to load customers' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCustomerSelect = (customer: Customer | null) => {
    selectCustomer(customer);
    
    // Load customer stats if customer is selected
    if (customer) {
      loadCustomerStats(customer.id);
    }
  };

  const loadCustomerStats = async (customerId: string) => {
    try {
      const stats = await apiService.getCustomerStatistics(customerId);
      dispatch({ type: 'SET_CUSTOMER_STATS', payload: stats });
    } catch (error) {
      console.error('Error loading customer stats:', error);
    }
  };

  const handleCreateCustomer = async (customer: Customer) => {
    dispatch({ type: 'ADD_CUSTOMER', payload: customer });
    selectCustomer(customer);
    setIsCreateModalOpen(false);
  };

  const displayValue = state.selectedCustomer 
    ? `${state.selectedCustomer.name} (${state.selectedCustomer.email})`
    : 'Select a customer...';

  return (
    <>
      <div className="w-full max-w-md">
        <Listbox value={state.selectedCustomer} onChange={handleCustomerSelect}>
          <div className="relative">
            <Listbox.Button className="relative w-full cursor-default rounded-lg bg-white py-2 pl-3 pr-10 text-left shadow-md focus:outline-none focus-visible:border-primary-500 focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-opacity-75 focus-visible:ring-offset-2 focus-visible:ring-offset-primary-300 sm:text-sm border border-gray-300">
              <span className="flex items-center">
                <BuildingOfficeIcon className="h-5 w-5 text-gray-400 mr-2" />
                <span className="block truncate">
                  {isLoading ? 'Loading...' : displayValue}
                </span>
              </span>
              <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                <ChevronUpDownIcon
                  className="h-5 w-5 text-gray-400"
                  aria-hidden="true"
                />
              </span>
            </Listbox.Button>
            
            <Transition
              as={Fragment}
              leave="transition ease-in duration-100"
              leaveFrom="opacity-100"
              leaveTo="opacity-0"
            >
              <Listbox.Options className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
                {/* Clear selection option */}
                <Listbox.Option
                  value={null}
                  className={({ active }) =>
                    `relative cursor-default select-none py-2 pl-10 pr-4 ${
                      active ? 'bg-primary-100 text-primary-900' : 'text-gray-900'
                    }`
                  }
                >
                  {({ selected }) => (
                    <>
                      <span className="block truncate font-medium text-gray-500">
                        No customer selected
                      </span>
                      {selected && (
                        <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-primary-600">
                          <CheckIcon className="h-5 w-5" aria-hidden="true" />
                        </span>
                      )}
                    </>
                  )}
                </Listbox.Option>

                {/* Customers list */}
                {state.customers.map((customer) => (
                  <Listbox.Option
                    key={customer.id}
                    value={customer}
                    className={({ active }) =>
                      `relative cursor-default select-none py-2 pl-10 pr-4 ${
                        active ? 'bg-primary-100 text-primary-900' : 'text-gray-900'
                      }`
                    }
                  >
                    {({ selected }) => (
                      <>
                        <div className="flex flex-col">
                          <span className={`block truncate ${selected ? 'font-medium' : 'font-normal'}`}>
                            {customer.name}
                          </span>
                          <span className="block truncate text-sm text-gray-500">
                            {customer.email}
                          </span>
                        </div>
                        {selected && (
                          <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-primary-600">
                            <CheckIcon className="h-5 w-5" aria-hidden="true" />
                          </span>
                        )}
                      </>
                    )}
                  </Listbox.Option>
                ))}

                {/* Create new customer option */}
                <Listbox.Option
                  value="create_new"
                  className={({ active }) =>
                    `relative cursor-default select-none py-2 pl-10 pr-4 border-t border-gray-200 ${
                      active ? 'bg-primary-100 text-primary-900' : 'text-primary-600'
                    }`
                  }
                  onClick={() => setIsCreateModalOpen(true)}
                >
                  <span className="flex items-center">
                    <PlusIcon className="h-4 w-4 mr-2" />
                    Create New Customer
                  </span>
                </Listbox.Option>
              </Listbox.Options>
            </Transition>
          </div>
        </Listbox>
      </div>

      {/* Create Customer Modal */}
      <CreateCustomerModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={handleCreateCustomer}
      />
    </>
  );
};

export default CustomerSelector;