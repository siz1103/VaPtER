// frontend/src/components/Modals/ScanDetailsModal.tsx

import React from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { 
  XMarkIcon, 
  ServerIcon, 
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon,
  CodeBracketIcon,
} from '@heroicons/react/24/outline';
import { Scan, OpenPort } from '../../types';

interface ScanDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  scan: Scan;
}

const ScanDetailsModal: React.FC<ScanDetailsModalProps> = ({
  isOpen,
  onClose,
  scan,
}) => {
  const formatDate = (dateString: string | null) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString();
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

  const renderOpenPorts = (ports: OpenPort[]) => {
    if (!ports || ports.length === 0) {
      return (
        <div className="text-center py-4 text-gray-500">
          No open ports found
        </div>
      );
    }

    return (
      <div className="space-y-2">
        {ports.map((port, index) => (
          <div key={index} className="border rounded-md p-3 bg-gray-50">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="font-mono text-sm bg-primary-100 text-primary-800 px-2 py-1 rounded">
                  {port.portid}/{port.protocol}
                </span>
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                  port.state === 'open' ? 'bg-success-100 text-success-800' : 'bg-gray-100 text-gray-800'
                }`}>
                  {port.state}
                </span>
              </div>
              {port.service && (
                <div className="text-sm text-gray-600">
                  {port.service.name}
                </div>
              )}
            </div>
            
            {port.service && (port.service.product || port.service.version) && (
              <div className="mt-2 text-sm text-gray-700">
                {port.service.product && <span className="font-medium">{port.service.product}</span>}
                {port.service.version && <span className="ml-1">v{port.service.version}</span>}
                {port.service.extrainfo && <span className="ml-1 text-gray-500">({port.service.extrainfo})</span>}
              </div>
            )}
            
            {port.scripts && port.scripts.length > 0 && (
              <div className="mt-2">
                <div className="text-xs text-gray-500 mb-1">Scripts:</div>
                <div className="space-y-1">
                  {port.scripts.map((script, scriptIndex) => (
                    <div key={scriptIndex} className="text-xs">
                      <span className="font-mono text-gray-600">{script.id}:</span>
                      <pre className="mt-1 text-xs text-gray-700 whitespace-pre-wrap bg-white p-2 rounded border">
                        {script.output}
                      </pre>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  const renderOSGuess = () => {
    const osGuess = scan.parsed_nmap_results?.hosts?.[0]?.os;
    
    if (!osGuess) {
      return (
        <div className="text-center py-4 text-gray-500">
          No OS detection results
        </div>
      );
    }

    return (
      <div className="bg-gray-50 rounded-md p-3">
        <div className="flex items-center space-x-2 mb-2">
          <ServerIcon className="h-5 w-5 text-gray-500" />
          <span className="font-medium text-gray-900">{osGuess.name}</span>
          {osGuess.accuracy && (
            <span className="text-sm text-gray-500">({osGuess.accuracy}% accuracy)</span>
          )}
        </div>
        
        {(osGuess.vendor || osGuess.osfamily || osGuess.type) && (
          <div className="space-y-1 text-sm text-gray-600">
            {osGuess.vendor && <div><span className="font-medium">Vendor:</span> {osGuess.vendor}</div>}
            {osGuess.osfamily && <div><span className="font-medium">OS Family:</span> {osGuess.osfamily}</div>}
            {osGuess.type && <div><span className="font-medium">Type:</span> {osGuess.type}</div>}
          </div>
        )}
      </div>
    );
  };

  const renderScanStats = () => {
    const stats = scan.parsed_nmap_results?.stats;
    
    if (!stats) return null;

    return (
      <div className="grid grid-cols-2 gap-4">
        {stats.hosts && (
          <div className="bg-gray-50 rounded-md p-3">
            <div className="text-sm font-medium text-gray-900 mb-1">Hosts</div>
            <div className="space-y-1 text-sm text-gray-600">
              <div>Total: {stats.hosts.total}</div>
              <div>Up: {stats.hosts.up}</div>
              <div>Down: {stats.hosts.down}</div>
            </div>
          </div>
        )}
        
        {stats.finished && (
          <div className="bg-gray-50 rounded-md p-3">
            <div className="text-sm font-medium text-gray-900 mb-1">Timing</div>
            <div className="space-y-1 text-sm text-gray-600">
              <div>Elapsed: {stats.finished.elapsed}s</div>
              <div>Finished: {new Date(parseInt(stats.finished.time) * 1000).toLocaleString()}</div>
            </div>
          </div>
        )}
      </div>
    );
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
              <Dialog.Panel className="w-full max-w-4xl transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                <div className="flex items-center justify-between mb-6">
                  <Dialog.Title
                    as="h3"
                    className="text-lg font-medium leading-6 text-gray-900"
                  >
                    Scan Details - {scan.target_name}
                  </Dialog.Title>
                  <button
                    type="button"
                    className="rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    onClick={onClose}
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                {/* Scan summary */}
                <div className="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-gray-50 rounded-md p-4">
                    <h4 className="text-sm font-medium text-gray-900 mb-2">Scan Information</h4>
                    <div className="space-y-1 text-sm text-gray-600">
                      <div><span className="font-medium">Target:</span> {scan.target_name} ({scan.target_address})</div>
                      <div><span className="font-medium">Scan Type:</span> {scan.scan_type_name}</div>
                      <div><span className="font-medium">Status:</span> 
                        <span className={`ml-1 inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(scan.status)}`}>
                          {scan.status}
                        </span>
                      </div>
                      <div><span className="font-medium">Started:</span> {formatDate(scan.initiated_at)}</div>
                      <div><span className="font-medium">Duration:</span> {formatDuration(scan.duration_seconds)}</div>
                    </div>
                  </div>

                  {scan.error_message && (
                    <div className="bg-error-50 border border-error-200 rounded-md p-4">
                      <h4 className="text-sm font-medium text-error-900 mb-2">Error Details</h4>
                      <p className="text-sm text-error-700">{scan.error_message}</p>
                    </div>
                  )}
                </div>

                {/* Results tabs */}
                <div className="space-y-6">
                  {/* Nmap Results */}
                  {scan.parsed_nmap_results && (
                    <div>
                      <h4 className="text-base font-medium text-gray-900 mb-3 flex items-center">
                        <CodeBracketIcon className="h-5 w-5 mr-2" />
                        Nmap Results
                      </h4>
                      
                      {/* Open Ports */}
                      <div className="mb-4">
                        <h5 className="text-sm font-medium text-gray-700 mb-2">Open Ports</h5>
                        <div className="max-h-64 overflow-y-auto">
                          {renderOpenPorts(scan.parsed_nmap_results.hosts?.[0]?.ports || [])}
                        </div>
                      </div>

                      {/* OS Detection */}
                      <div className="mb-4">
                        <h5 className="text-sm font-medium text-gray-700 mb-2">OS Detection</h5>
                        {renderOSGuess()}
                      </div>

                      {/* Scan Statistics */}
                      <div>
                        <h5 className="text-sm font-medium text-gray-700 mb-2">Scan Statistics</h5>
                        {renderScanStats()}
                      </div>
                    </div>
                  )}

                  {/* Other plugin results */}
                  {scan.parsed_finger_results && (
                    <div>
                      <h4 className="text-base font-medium text-gray-900 mb-3 flex items-center">
                        <ShieldCheckIcon className="h-5 w-5 mr-2" />
                        Fingerprint Results
                      </h4>
                      <div className="bg-gray-50 rounded-md p-4">
                        <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                          {JSON.stringify(scan.parsed_finger_results, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}

                  {scan.parsed_enum_results && (
                    <div>
                      <h4 className="text-base font-medium text-gray-900 mb-3">Enumeration Results</h4>
                      <div className="bg-gray-50 rounded-md p-4">
                        <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                          {JSON.stringify(scan.parsed_enum_results, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}

                  {scan.parsed_web_results && (
                    <div>
                      <h4 className="text-base font-medium text-gray-900 mb-3">Web Scan Results</h4>
                      <div className="bg-gray-50 rounded-md p-4">
                        <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                          {JSON.stringify(scan.parsed_web_results, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}

                  {scan.parsed_vuln_results && (
                    <div>
                      <h4 className="text-base font-medium text-gray-900 mb-3">Vulnerability Results</h4>
                      <div className="bg-gray-50 rounded-md p-4">
                        <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                          {JSON.stringify(scan.parsed_vuln_results, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex justify-end mt-6">
                  <button
                    type="button"
                    onClick={onClose}
                    className="rounded-md bg-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
                  >
                    Close
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

export default ScanDetailsModal;