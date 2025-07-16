// frontend/src/components/Common/ConfirmDialog.tsx

import React from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { 
  ExclamationTriangleIcon,
  InformationCircleIcon,
  CheckCircleIcon,
  XCircleIcon 
} from '@heroicons/react/24/outline';

interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  confirmStyle?: 'primary' | 'error' | 'warning' | 'success';
  icon?: 'warning' | 'info' | 'success' | 'error';
}

const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  confirmStyle = 'primary',
  icon = 'warning',
}) => {
  const getIcon = () => {
    const iconClasses = "h-6 w-6";
    
    switch (icon) {
      case 'warning':
        return <ExclamationTriangleIcon className={`${iconClasses} text-warning-600`} />;
      case 'info':
        return <InformationCircleIcon className={`${iconClasses} text-primary-600`} />;
      case 'success':
        return <CheckCircleIcon className={`${iconClasses} text-success-600`} />;
      case 'error':
        return <XCircleIcon className={`${iconClasses} text-error-600`} />;
      default:
        return <ExclamationTriangleIcon className={`${iconClasses} text-warning-600`} />;
    }
  };

  const getConfirmButtonClasses = () => {
    const baseClasses = "inline-flex items-center rounded-md border border-transparent px-4 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2";
    
    switch (confirmStyle) {
      case 'primary':
        return `${baseClasses} bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500`;
      case 'error':
        return `${baseClasses} bg-error-600 text-white hover:bg-error-700 focus:ring-error-500`;
      case 'warning':
        return `${baseClasses} bg-warning-600 text-white hover:bg-warning-700 focus:ring-warning-500`;
      case 'success':
        return `${baseClasses} bg-success-600 text-white hover:bg-success-700 focus:ring-success-500`;
      default:
        return `${baseClasses} bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500`;
    }
  };

  const getIconBackgroundClasses = () => {
    switch (icon) {
      case 'warning':
        return 'bg-warning-100';
      case 'info':
        return 'bg-primary-100';
      case 'success':
        return 'bg-success-100';
      case 'error':
        return 'bg-error-100';
      default:
        return 'bg-warning-100';
    }
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
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
                <div className="flex items-center mb-4">
                  <div className={`flex-shrink-0 flex items-center justify-center h-10 w-10 rounded-full ${getIconBackgroundClasses()}`}>
                    {getIcon()}
                  </div>
                  <div className="ml-3">
                    <Dialog.Title
                      as="h3"
                      className="text-lg font-medium leading-6 text-gray-900"
                    >
                      {title}
                    </Dialog.Title>
                  </div>
                </div>

                <div className="mb-6">
                  <p className="text-sm text-gray-500">
                    {message}
                  </p>
                </div>

                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={onClose}
                    className="inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
                  >
                    {cancelText}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      onConfirm();
                      onClose();
                    }}
                    className={getConfirmButtonClasses()}
                  >
                    {confirmText}
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
};

export default ConfirmDialog;