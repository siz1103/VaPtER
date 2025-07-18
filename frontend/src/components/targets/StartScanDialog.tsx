import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useToast } from '@/components/ui/use-toast'
import { startScan } from '@/services/targetService'
import { getScanTypes } from '@/services/scanTypeService'
import type { Target } from '@/types'
import { Scan } from 'lucide-react'

interface StartScanDialogProps {
  target: Target
  onSuccess: () => void
  onCancel: () => void
}

export default function StartScanDialog({ target, onSuccess, onCancel }: StartScanDialogProps) {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const [selectedScanType, setSelectedScanType] = useState<string>('')
  
  const { data: scanTypes = [], isLoading: loadingScanTypes } = useQuery({
    queryKey: ['scanTypes'],
    queryFn: getScanTypes,
  })
  
  const mutation = useMutation({
    mutationFn: async () => {
      if (!selectedScanType) {
        throw new Error('Please select a scan type')
      }
      return startScan(target.id, parseInt(selectedScanType))
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['targets'] })
      queryClient.invalidateQueries({ queryKey: ['scans'] })
      toast({
        title: 'Scan started',
        description: `Scan has been queued for ${target.name}`,
      })
      onSuccess()
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || error.message || 'Failed to start scan',
        variant: 'destructive',
      })
    },
  })
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate()
  }
  
  return (
    <DialogContent className="sm:max-w-[425px]">
      <form onSubmit={handleSubmit}>
        <DialogHeader>
          <DialogTitle>Start New Scan</DialogTitle>
          <DialogDescription>
            Select a scan type to start scanning {target.name} ({target.address})
          </DialogDescription>
        </DialogHeader>
        
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="scan_type">Scan Type *</Label>
            <Select
              value={selectedScanType}
              onValueChange={setSelectedScanType}
              disabled={loadingScanTypes}
            >
              <SelectTrigger>
                <SelectValue placeholder={loadingScanTypes ? "Loading scan types..." : "Select a scan type"} />
              </SelectTrigger>
              <SelectContent>
                {scanTypes.map((scanType) => (
                  <SelectItem key={scanType.id} value={scanType.id.toString()}>
                    <div>
                      <div className="font-medium">{scanType.name}</div>
                      {scanType.description && (
                        <div className="text-xs text-muted-foreground">
                          {scanType.description}
                        </div>
                      )}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          {selectedScanType && (
            <div className="bg-muted p-3 rounded-md">
              <p className="text-sm font-medium mb-1">Scan Configuration</p>
              <div className="text-xs text-muted-foreground space-y-1">
                {scanTypes.find(st => st.id.toString() === selectedScanType)?.only_discovery ? (
                  <div>Type: Discovery Only (Ping Scan)</div>
                ) : (
                  <>
                    <div>Type: Full Port Scan</div>
                    <div>
                      Plugins: {scanTypes.find(st => st.id.toString() === selectedScanType)?.enabled_plugins.join(', ') || 'None'}
                    </div>
                  </>
                )}
              </div>
            </div>
          )}
          
          {target.last_scan && (
            <div className="bg-orange-50 dark:bg-orange-900/20 p-3 rounded-md">
              <p className="text-sm font-medium mb-1">Previous Scan Information</p>
              <div className="text-xs space-y-1">
                <div>Status: {target.last_scan.status}</div>
                <div>Started: {new Date(target.last_scan.initiated_at).toLocaleString()}</div>
                {target.last_scan.completed_at && (
                  <div>Completed: {new Date(target.last_scan.completed_at).toLocaleString()}</div>
                )}
              </div>
            </div>
          )}
        </div>
        
        <DialogFooter>
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button 
            type="submit" 
            disabled={mutation.isPending || !selectedScanType}
          >
            <Scan className="mr-2 h-4 w-4" />
            {mutation.isPending ? 'Starting...' : 'Start Scan'}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  )
}