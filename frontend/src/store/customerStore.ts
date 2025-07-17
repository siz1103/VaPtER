import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Customer } from '@/types'

interface CustomerStore {
  selectedCustomer: Customer | null
  setSelectedCustomer: (customer: Customer | null) => void
}

export const useCustomerStore = create<CustomerStore>()(
  persist(
    (set) => ({
      selectedCustomer: null,
      setSelectedCustomer: (customer) => set({ selectedCustomer: customer }),
    }),
    {
      name: 'vapter-customer-storage',
    }
  )
)