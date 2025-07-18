// frontend/src/pages/Scans.tsx

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Search, Activity, AlertTriangle } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useCustomerStore } from '@/store/customerStore'
import { useToast } from '@/components/ui/use-toast'
import ScanTable from '@/components/scans/ScanTable'
import { 
  getScans, 
  deleteScan, 
  restartScan, 
  updateScanType, 
  cancelScan,
  isActiveScan 
} from '@/services/scanService'
import { getScanTypes } from '@/services/scanTypeService'

export default function Scans() {
  const [searchTerm, setSearchTerm] = useState('')
  const { selectedCustomer } = useCustomerStore()
  const { toast } = useToast()
  const queryClient = useQueryClient()
  
  // Fetch scans with polling for active scans
  const { 
    data: scans = [], 
    isLoading: isLoadingScans, 
    error: scansError,
    refetch: refetchScans
  } = useQuery({
    queryKey: ['scans', selectedCustomer?.id],
    queryFn: () => getScans(selectedCustomer?.id),
    enabled: !!selectedCustomer,
    refetchInterval: (data) => {
      // Poll every 3 seconds if there are active scans
      const hasActiveScans = data?.some(scan => isActiveScan(scan.status))
      return hasActiveScans ? 3000 : false
    },
  })
  
  // Fetch scan types for change scan type functionality
  const { data: scanTypes = [] } = useQuery({
    queryKey: ['scanTypes'],
    queryFn: getScanTypes,
  })
  
  // Mutations
  const deleteMutation = useMutation({
    mutationFn: deleteScan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scans'] })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.error || 'Failed to delete scan',
        variant: 'destructive',
      })
    },
  })
  
  const restartMutation = useMutation({
    mutationFn: restartScan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scans'] })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.error || 'Failed to restart scan',
        variant: 'destructive',
      })
    },
  })
  
  const cancelMutation = useMutation({
    mutationFn: cancelScan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scans'] })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.error || 'Failed to cancel scan',
        variant: 'destructive',
      })
    },
  })
  
  const changeScanTypeMutation = useMutation({
    mutationFn: ({ scanId, scanTypeId }: { scanId: number; scanTypeId: number }) =>
      updateScanType(scanId, scanTypeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scans'] })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.error || 'Failed to update scan type',
        variant: 'destructive',
      })
    },
  })
  
  // Handlers
  const handleDelete = (scanId: number) => {
    deleteMutation.mutate(scanId)
  }
  
  const handleRestart = (scanId: number) => {
    restartMutation.mutate(scanId)
  }
  
  const handleCancel = (scanId: number) => {
    cancelMutation.mutate(scanId)
  }
  
  const handleChangeScanType = (scanId: number, scanTypeId: number) => {
    changeScanTypeMutation.mutate({ scanId, scanTypeId })
  }
  
  // Show customer selection message if no customer is selected
  if (!selectedCustomer) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle className="flex items-center justify-center space-x-2">
              <Activity className="h-6 w-6" />
              <span>Select Customer</span>
            </CardTitle>
            <CardDescription>
              Please select a customer from the dropdown to view their scans
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-center text-muted-foreground text-sm">
              Use the customer dropdown in the header to choose a customer and view their vulnerability scans.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }
  
  // Show error state
  if (scansError) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle className="flex items-center justify-center space-x-2 text-destructive">
              <AlertTriangle className="h-6 w-6" />
              <span>Error Loading Scans</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-center text-muted-foreground text-sm">
              Failed to load scans. Please check your connection and try again.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }
  
  // Calculate stats
  const activeScans = scans.filter(scan => isActiveScan(scan.status))
  const completedScans = scans.filter(scan => scan.status === 'Completed')
  const failedScans = scans.filter(scan => scan.status === 'Failed')
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Scans</h2>
          <p className="text-muted-foreground">
            Vulnerability assessment scans for {selectedCustomer.name}
          </p>
        </div>
      </div>
      
      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Scans</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{scans.length}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Scans</CardTitle>
            <div className="h-4 w-4 bg-blue-500 rounded-full animate-pulse" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{activeScans.length}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
            <div className="h-4 w-4 bg-green-500 rounded-full" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{completedScans.length}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Failed</CardTitle>
            <div className="h-4 w-4 bg-red-500 rounded-full" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{failedScans.length}</div>
          </CardContent>
        </Card>
      </div>
      
      {/* Scans Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Activity className="h-5 w-5" />
            <span>Scans</span>
            {!isLoadingScans && (
              <span className="text-sm font-normal text-muted-foreground">
                ({scans.length} total)
              </span>
            )}
          </CardTitle>
          <CardDescription>
            Vulnerability assessment scans and their results
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center space-x-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search scans by ID, target, scan type, or status..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          
          {isLoadingScans ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
                <p className="text-muted-foreground">Loading scans...</p>
              </div>
            </div>
          ) : (
            <ScanTable 
              scans={scans}
              scanTypes={scanTypes}
              searchTerm={searchTerm}
              onRestart={handleRestart}
              onCancel={handleCancel}
              onDelete={handleDelete}
              onChangeScanType={handleChangeScanType}
            />
          )}
        </CardContent>
      </Card>
    </div>
  )
}