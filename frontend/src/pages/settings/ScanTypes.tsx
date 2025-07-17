import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Plus, Search, FileSearch } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Dialog } from '@/components/ui/dialog'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import ScanTypeForm from '@/components/settings/ScanTypeForm'
import ScanTypeTable from '@/components/settings/ScanTypeTable'
import { getScanTypes } from '@/services/scanTypeService'
import type { ScanType } from '@/types'

export default function ScanTypes() {
  const [searchTerm, setSearchTerm] = useState('')
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [selectedScanType, setSelectedScanType] = useState<ScanType | null>(null)
  
  const { data: scanTypes = [], isLoading, error } = useQuery({
    queryKey: ['scanTypes'],
    queryFn: getScanTypes,
  })
  
  const handleCreateSuccess = (newScanType: ScanType) => {
    setIsCreateDialogOpen(false)
  }
  
  const handleEditSuccess = (updatedScanType: ScanType) => {
    setIsEditDialogOpen(false)
    setSelectedScanType(null)
  }
  
  const handleEdit = (scanType: ScanType) => {
    setSelectedScanType(scanType)
    setIsEditDialogOpen(true)
  }
  
  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Scan Types</h2>
          <p className="text-muted-foreground">Manage scan configurations and templates</p>
        </div>
        
        <Card>
          <CardContent className="flex items-center justify-center py-8">
            <div className="text-center">
              <FileSearch className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Error loading scan types</h3>
              <p className="text-muted-foreground">
                Failed to load scan types. Please check your connection and try again.
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
          <h2 className="text-3xl font-bold tracking-tight">Scan Types</h2>
          <p className="text-muted-foreground">
            Manage scan configurations and templates for vulnerability assessments
          </p>
        </div>
        
        <Button onClick={() => setIsCreateDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Create Scan Type
        </Button>
      </div>
      
      {/* Search and Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <FileSearch className="h-5 w-5" />
            <span>Scan Types</span>
            {!isLoading && (
              <span className="text-sm font-normal text-muted-foreground">
                ({scanTypes.length} total)
              </span>
            )}
          </CardTitle>
          <CardDescription>
            Pre-configured scan templates for different types of vulnerability assessments
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center space-x-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search scan types by name, description, or configuration..."
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
                <p className="text-muted-foreground">Loading scan types...</p>
              </div>
            </div>
          ) : (
            <ScanTypeTable 
              scanTypes={scanTypes}
              onEdit={handleEdit}
              searchTerm={searchTerm}
            />
          )}
        </CardContent>
      </Card>
      
      {/* Create Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <ScanTypeForm 
          onSuccess={handleCreateSuccess}
          onCancel={() => setIsCreateDialogOpen(false)}
        />
      </Dialog>
      
      {/* Edit Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        {selectedScanType && (
          <ScanTypeForm 
            scanType={selectedScanType}
            onSuccess={handleEditSuccess}
            onCancel={() => {
              setIsEditDialogOpen(false)
              setSelectedScanType(null)
            }}
          />
        )}
      </Dialog>
    </div>
  )
}