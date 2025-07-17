import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Plus, Search, Network } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Dialog } from '@/components/ui/dialog'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import PortListForm from '@/components/settings/PortListForm'
import PortListTable from '@/components/settings/PortListTable'
import { getPortLists } from '@/services/portListService'
import type { PortList } from '@/types'

export default function PortLists() {
  const [searchTerm, setSearchTerm] = useState('')
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [selectedPortList, setSelectedPortList] = useState<PortList | null>(null)
  
  const { data: portLists = [], isLoading, error } = useQuery({
    queryKey: ['portLists'],
    queryFn: getPortLists,
  })
  
  const handleCreateSuccess = (newPortList: PortList) => {
    setIsCreateDialogOpen(false)
  }
  
  const handleEditSuccess = (updatedPortList: PortList) => {
    setIsEditDialogOpen(false)
    setSelectedPortList(null)
  }
  
  const handleEdit = (portList: PortList) => {
    setSelectedPortList(portList)
    setIsEditDialogOpen(true)
  }
  
  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Port Lists</h2>
          <p className="text-muted-foreground">Manage port configurations for scanning</p>
        </div>
        
        <Card>
          <CardContent className="flex items-center justify-center py-8">
            <div className="text-center">
              <Network className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Error loading port lists</h3>
              <p className="text-muted-foreground">
                Failed to load port lists. Please check your connection and try again.
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
          <h2 className="text-3xl font-bold tracking-tight">Port Lists</h2>
          <p className="text-muted-foreground">
            Manage port configurations for scanning operations
          </p>
        </div>
        
        <Button onClick={() => setIsCreateDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Create Port List
        </Button>
      </div>
      
      {/* Search and Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Network className="h-5 w-5" />
            <span>Port Lists</span>
            {!isLoading && (
              <span className="text-sm font-normal text-muted-foreground">
                ({portLists.length} total)
              </span>
            )}
          </CardTitle>
          <CardDescription>
            Configure port ranges for different types of network scans
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center space-x-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search port lists by name, description, or ports..."
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
                <p className="text-muted-foreground">Loading port lists...</p>
              </div>
            </div>
          ) : (
            <PortListTable 
              portLists={portLists}
              onEdit={handleEdit}
              searchTerm={searchTerm}
            />
          )}
        </CardContent>
      </Card>
      
      {/* Create Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <PortListForm 
          onSuccess={handleCreateSuccess}
          onCancel={() => setIsCreateDialogOpen(false)}
        />
      </Dialog>
      
      {/* Edit Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        {selectedPortList && (
          <PortListForm 
            portList={selectedPortList}
            onSuccess={handleEditSuccess}
            onCancel={() => {
              setIsEditDialogOpen(false)
              setSelectedPortList(null)
            }}
          />
        )}
      </Dialog>
    </div>
  )
}