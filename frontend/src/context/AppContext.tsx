import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { Customer, DashboardStats, CustomerStats } from '../types';

interface AppState {
  selectedCustomer: Customer | null;
  customers: Customer[];
  dashboardStats: DashboardStats | null;
  customerStats: CustomerStats | null;
  isLoading: boolean;
  error: string | null;
}

type AppAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_CUSTOMERS'; payload: Customer[] }
  | { type: 'SET_SELECTED_CUSTOMER'; payload: Customer | null }
  | { type: 'SET_DASHBOARD_STATS'; payload: DashboardStats }
  | { type: 'SET_CUSTOMER_STATS'; payload: CustomerStats | null }
  | { type: 'ADD_CUSTOMER'; payload: Customer }
  | { type: 'UPDATE_CUSTOMER'; payload: Customer }
  | { type: 'DELETE_CUSTOMER'; payload: string };

const initialState: AppState = {
  selectedCustomer: null,
  customers: [],
  dashboardStats: null,
  customerStats: null,
  isLoading: false,
  error: null,
};

const appReducer = (state: AppState, action: AppAction): AppState => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload, isLoading: false };
    case 'SET_CUSTOMERS':
      return { ...state, customers: action.payload };
    case 'SET_SELECTED_CUSTOMER':
      return { ...state, selectedCustomer: action.payload };
    case 'SET_DASHBOARD_STATS':
      return { ...state, dashboardStats: action.payload };
    case 'SET_CUSTOMER_STATS':
      return { ...state, customerStats: action.payload };
    case 'ADD_CUSTOMER':
      return { ...state, customers: [...state.customers, action.payload] };
    case 'UPDATE_CUSTOMER':
      return {
        ...state,
        customers: state.customers.map(customer =>
          customer.id === action.payload.id ? action.payload : customer
        ),
        selectedCustomer: state.selectedCustomer?.id === action.payload.id 
          ? action.payload 
          : state.selectedCustomer,
      };
    case 'DELETE_CUSTOMER':
      return {
        ...state,
        customers: state.customers.filter(customer => customer.id !== action.payload),
        selectedCustomer: state.selectedCustomer?.id === action.payload 
          ? null 
          : state.selectedCustomer,
      };
    default:
      return state;
  }
};

interface AppContextType {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
  selectCustomer: (customer: Customer | null) => void;
  clearError: () => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};

interface AppProviderProps {
  children: ReactNode;
}

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Load customer from localStorage on mount
  useEffect(() => {
    const savedCustomerId = localStorage.getItem('selectedCustomerId');
    if (savedCustomerId) {
      // We'll load the customer data when customers are fetched
      // This is handled in the main App component
    }
  }, []);

  // Save selected customer to localStorage
  useEffect(() => {
    if (state.selectedCustomer) {
      localStorage.setItem('selectedCustomerId', state.selectedCustomer.id);
    } else {
      localStorage.removeItem('selectedCustomerId');
    }
  }, [state.selectedCustomer]);

  const selectCustomer = (customer: Customer | null) => {
    dispatch({ type: 'SET_SELECTED_CUSTOMER', payload: customer });
    // Clear customer-specific stats when changing customer
    dispatch({ type: 'SET_CUSTOMER_STATS', payload: null });
  };

  const clearError = () => {
    dispatch({ type: 'SET_ERROR', payload: null });
  };

  const contextValue: AppContextType = {
    state,
    dispatch,
    selectCustomer,
    clearError,
  };

  return (
    <AppContext.Provider value={contextValue}>
      {children}
    </AppContext.Provider>
  );
};