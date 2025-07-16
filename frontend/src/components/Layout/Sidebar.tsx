// frontend/src/components/Layout/Sidebar.tsx

import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  HomeIcon,
  ServerIcon,
  CpuChipIcon,
  CogIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import { useApp } from '../../context/AppContext';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Targets', href: '/targets', icon: ServerIcon },
  { name: 'Scans', href: '/scans', icon: CpuChipIcon },
  { name: 'Settings', href: '/settings', icon: CogIcon },
];

const Sidebar: React.FC = () => {
  const location = useLocation();
  const { state } = useApp();

  return (
    <div className="hidden md:flex md:w-64 md:flex-col">
      <div className="flex flex-col flex-grow pt-5 bg-white border-r border-gray-200 overflow-y-auto">
        <div className="flex items-center flex-shrink-0 px-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ChartBarIcon className="h-8 w-8 text-primary-600" />
            </div>
            <div className="ml-3">
              <h2 className="text-lg font-semibold text-gray-900">VaPtER</h2>
              <p className="text-sm text-gray-500">Vulnerability Assessment</p>
            </div>
          </div>
        </div>
        
        <div className="mt-8 flex-1 flex flex-col">
          <nav className="flex-1 px-4 space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href || 
                              (item.href !== '/dashboard' && location.pathname.startsWith(item.href));
              
              return (
                <NavLink
                  key={item.name}
                  to={item.href}
                  className={`${
                    isActive
                      ? 'bg-primary-100 text-primary-700 border-primary-500'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900 border-transparent'
                  } group flex items-center px-3 py-2 text-sm font-medium border-l-4 transition-colors duration-150`}
                >
                  <item.icon
                    className={`${
                      isActive ? 'text-primary-500' : 'text-gray-400 group-hover:text-gray-500'
                    } mr-3 h-5 w-5`}
                    aria-hidden="true"
                  />
                  {item.name}
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Customer Info */}
        {state.selectedCustomer && (
          <div className="flex-shrink-0 px-4 py-4 border-t border-gray-200">
            <div className="text-sm">
              <p className="font-medium text-gray-900">Selected Customer</p>
              <p className="text-gray-600 truncate">{state.selectedCustomer.name}</p>
              <p className="text-gray-500 text-xs truncate">{state.selectedCustomer.email}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Sidebar;