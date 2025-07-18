import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Plus, Search, Server, Shield } from 'lucide-react'
import { useCustomerStore } from '@/store/customerStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Dialog } from '@/components/ui/dialog'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import TargetForm from '@/components/targets/TargetForm'
import TargetTable from '@/components/targets/TargetTable'
import { getTargets } from '@/services/targetService'
import type { Target } from '@/types'

export default function Targets() {
  const { selectedCustomer } = useCustomerStore()
  const [searchTerm, setSearchTerm] = useState('')
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [selectedTarget, setSelectedTarget] = useState<Target | null>(null)
  
  const { data: targets = [], isLoading, error } = useQuery({
    queryKey: ['targets', selectedCustomer?.id],
    queryFn: () => getTargets(selectedCustomer?.id),
    enabled: !!selectedCustomer,
  })
  
  const handleCreateSuccess = (newTarget: Target) => {
    setIsCreateDialogOpen(false)
  }
  
  const handleEditSuccess = (updatedTarget: Target) => {
    setIsEditDialogOpen(false)
    setSelectedTarget(null)
  }
  
  const handleEdit = (target: Target) => {
    setSelectedTarget(target)
    setIsEditDialogOpen(true)
  }
  
  // Se non c'è un customer selezionato
  if (!selectedCustomer) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <Shield className="h-16 w-16 text-muted-foreground mb-4" />
        <h2 className="text-2xl font-semibold mb-2">No Customer Selected</h2>
        <p className="text-muted-foreground text-center max-w-md">
          Please select a customer from the dropdown in the header to view and manage targets.
        </p>
      </div>
    )
  }
  
  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Targets</h2>
          <p className="text-muted-foreground">
            Manage scanning targets for {selectedCustomer.name}
          </p>
        </div>
        
        <Card>
          <CardContent className="flex items-center justify-center py-8">
            <div className="text-center">
              <Server className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Error loading targets</h3>
              <p className="text-muted-foreground">
                Failed to load targets. Please check your connection and try again.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Targets</h2>
          <p className="text-muted-foreground">
            Manage scanning targets for {selectedCustomer.name}
          </p>
        </div>
        
        <Button onClick={() => setIsCreateDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Target
        </Button>
      </div>
      
      {/* Search and Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Server className="h-5 w-5" />
            <span>Targets</span>
            {!isLoading && (
              <span className="text-sm font-normal text-muted-foreground">
                ({targets.length} total)
              </span>
            )}
          </CardTitle>
          <CardDescription>
            Hosts and domains to scan for vulnerabilities
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center space-x-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search targets by name, address, or description..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
                <p className="text-muted-foreground">Loading targets...</p>
              </div>
            </div>
          ) : (
            <TargetTable 
              targets={targets}
              onEdit={handleEdit}
              searchTerm={searchTerm}
            />
          )}
        </CardContent>
      </Card>
      
      {/* Create Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <TargetForm 
          onSuccess={handleCreateSuccess}
          onCancel={() => setIsCreateDialogOpen(false)}
        />
      </Dialog>
      
      {/* Edit Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        {selectedTarget && (
          <TargetForm 
            target={selectedTarget}
            onSuccess={handleEditSuccess}
            onCancel={() => {
              setIsEditDialogOpen(false)
              setSelectedTarget(null)
            }}
          />
        )}
      </Dialog>
    </div>
  )
}