import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Building2, Plus, Check } from 'lucide-react'
import { useCustomerStore } from '@/store/customerStore'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Dialog } from '@/components/ui/dialog'
import CustomerForm from '../customers/CustomerForm'
import { getCustomers } from '@/services/customerService'
import type { Customer } from '@/types'

export default function CustomerDropdown() {
  const { selectedCustomer, setSelectedCustomer } = useCustomerStore()
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  
  const { data: customers = [], isLoading } = useQuery({
    queryKey: ['customers'],
    queryFn: getCustomers,
  })
  
  const handleSelectCustomer = (customer: Customer) => {
    setSelectedCustomer(customer)
  }
  
  const handleCreateSuccess = (newCustomer: Customer) => {
    setSelectedCustomer(newCustomer)
    setIsCreateDialogOpen(false)
  }
  
  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" className="w-[240px] justify-start">
            <Building2 className="mr-2 h-4 w-4" />
            {selectedCustomer ? selectedCustomer.name : 'Select Customer'}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="w-[240px]">
          <DropdownMenuLabel>Customers</DropdownMenuLabel>
          <DropdownMenuSeparator />
          
          {isLoading ? (
            <DropdownMenuItem disabled>Loading...</DropdownMenuItem>
          ) : customers.length === 0 ? (
            <DropdownMenuItem disabled>No customers found</DropdownMenuItem>
          ) : (
            customers.map((customer) => (
              <DropdownMenuItem
                key={customer.id}
                onClick={() => handleSelectCustomer(customer)}
              >
                {selectedCustomer?.id === customer.id && (
                  <Check className="mr-2 h-4 w-4" />
                )}
                {customer.name}
              </DropdownMenuItem>
            ))
          )}
          
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => setIsCreateDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Create New Customer
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <CustomerForm 
          onSuccess={handleCreateSuccess}
          onCancel={() => setIsCreateDialogOpen(false)}
        />
      </Dialog>
    </>
  )
}