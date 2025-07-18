// frontend/src/components/scans/ScanForm.tsx

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { useToast } from '@/components/ui/use-toast'
import { useCustomerStore } from '@/store/customerStore'
import { getTargets, startScan } from '@/services/targetService'
import { getScanTypes } from '@/services/scanTypeService'
import type { Target, ScanType } from '@/types'

interface ScanFormProps {
  onSuccess: () => void
  onCancel: () => void
}

export default function ScanForm({ onSuccess, onCancel }: ScanFormProps) {
  const [selectedTarget, setSelectedTarget] = useState<number | null>(null)
  const [selectedScanType, setSelectedScanType] = useState<number | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  
  const { toast } = useToast()
  const { selectedCustomer } = useCustomerStore()
  const queryClient = useQueryClient()
  
  // Fetch targets for the selected customer
  const { data: targets = [], isLoading: isLoadingTargets } = useQuery({
    queryKey: ['targets', selectedCustomer?.id],
    queryFn: () => getTargets(selectedCustomer?.id),
    enabled: !!selectedCustomer,
  })
  
  // Fetch scan types
  const { data: scanTypes = [], isLoading: isLoadingScanTypes } = useQuery({
    queryKey: ['scanTypes'],
    queryFn: getScanTypes,
  })
  
  // Start scan mutation
  const startScanMutation = useMutation({
    mutationFn: ({ targetId, scanTypeId }: { targetId: number; scanTypeId: number }) =>
      startScan(targetId, scanTypeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scans'] })
      toast({
        title: 'Scan Started',
        description: 'The vulnerability scan has been initiated successfully.',
      })
      onSuccess()
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.error || 'Failed to start scan',
        variant: 'destructive',
      })
    },
  })
  
  const handleSubmit = async () => {
    if (!selectedTarget || !selectedScanType) {
      toast({
        title: 'Validation Error',
        description: 'Please select both a target and scan type.',
        variant: 'destructive',
      })
      return
    }
    
    setIsSubmitting(true)
    try {
      await startScanMutation.mutateAsync({
        targetId: selectedTarget,
        scanTypeId: selectedScanType,
      })
    } finally {
      setIsSubmitting(false)
    }
  }
  
  const selectedTargetData = targets.find(t => t.id === selectedTarget)
  const selectedScanTypeData = scanTypes.find(st => st.id === selectedScanType)
  
  return (
    <DialogContent className="sm:max-w-[425px]">
      <DialogHeader>
        <DialogTitle>Create New Scan</DialogTitle>
        <DialogDescription>
          Select a target and scan type to start a new vulnerability assessment for {selectedCustomer?.name}.
        </DialogDescription>
      </DialogHeader>
      
      <div className="grid gap-4 py-4">
        {/* Target Selection */}
        <div className="grid gap-2">
          <Label htmlFor="target">Target</Label>
          <Select 
            value={selectedTarget?.toString()} 
            onValueChange={(value) => setSelectedTarget(Number(value))}
            disabled={isLoadingTargets}
          >
            <SelectTrigger>
              <SelectValue placeholder={isLoadingTargets ? "Loading targets..." : "Select target"} />
            </SelectTrigger>
            <SelectContent>
              {targets.map((target) => (
                <SelectItem key={target.id} value={target.id.toString()}>
                  <div className="flex flex-col">
                    <span className="font-medium">{target.name}</span>
                    <span className="text-sm text-muted-foreground">{target.address}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {targets.length === 0 && !isLoadingTargets && (
            <p className="text-sm text-muted-foreground">
              No targets available. Create a target first.
            </p>
          )}
        </div>
        
        {/* Scan Type Selection */}
        <div className="grid gap-2">
          <Label htmlFor="scanType">Scan Type</Label>
          <Select 
            value={selectedScanType?.toString()} 
            onValueChange={(value) => setSelectedScanType(Number(value))}
            disabled={isLoadingScanTypes}
          >
            <SelectTrigger>
              <SelectValue placeholder={isLoadingScanTypes ? "Loading scan types..." : "Select scan type"} />
            </SelectTrigger>
            <SelectContent>
              {scanTypes.map((scanType) => (
                <SelectItem key={scanType.id} value={scanType.id.toString()}>
                  <div className="flex flex-col">
                    <span className="font-medium">{scanType.name}</span>
                    {scanType.description && (
                      <span className="text-sm text-muted-foreground">{scanType.description}</span>
                    )}
                    {scanType.enabled_plugins.length > 0 && (
                      <span className="text-xs text-muted-foreground">
                        Plugins: {scanType.enabled_plugins.join(', ')}
                      </span>
                    )}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        {/* Selection Summary */}
        {selectedTarget && selectedScanType && (
          <div className="border rounded-md p-3 bg-muted/50">
            <h4 className="font-medium mb-2">Scan Summary</h4>
            <div className="space-y-1 text-sm">
              <div>
                <span className="text-muted-foreground">Target:</span> {selectedTargetData?.name} ({selectedTargetData?.address})
              </div>
              <div>
                <span className="text-muted-foreground">Scan Type:</span> {selectedScanTypeData?.name}
              </div>
              <div>
                <span className="text-muted-foreground">Customer:</span> {selectedCustomer?.name}
              </div>
            </div>
          </div>
        )}
      </div>
      
      <DialogFooter>
        <Button variant="outline" onClick={onCancel} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button 
          onClick={handleSubmit} 
          disabled={!selectedTarget || !selectedScanType || isSubmitting}
        >
          {isSubmitting ? 'Starting...' : 'Start Scan'}
        </Button>
      </DialogFooter>
    </DialogContent>
  )
}