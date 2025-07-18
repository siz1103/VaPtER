import { useState } from 'react'
import { MoreHorizontal, RotateCcw, Trash2, Edit, StopCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
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
import { useToast } from '@/components/ui/use-toast'
import { canRestartScan, canCancelScan, isActiveScan } from '@/services/scanService'
import type { Scan, ScanType } from '@/types'

interface ScanActionsProps {
  scan: Scan
  scanTypes: ScanType[]
  onRestart: (scanId: number) => void
  onCancel: (scanId: number) => void
  onDelete: (scanId: number) => void
  onChangeScanType: (scanId: number, scanTypeId: number) => void
}

export default function ScanActions({
  scan,
  scanTypes,
  onRestart,
  onCancel,
  onDelete,
  onChangeScanType,
}: ScanActionsProps) {
  const { toast } = useToast()
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [showChangeScanTypeDialog, setShowChangeScanTypeDialog] = useState(false)
  const [selectedScanType, setSelectedScanType] = useState<number | null>(null)
  
  const handleRestart = () => {
    onRestart(scan.id)
    toast({
      title: 'Scan Restarted',
      description: `Scan #${scan.id} has been restarted`,
    })
  }
  
  const handleCancel = () => {
    onCancel(scan.id)
    toast({
      title: 'Scan Cancelled',
      description: `Scan #${scan.id} has been cancelled`,
    })
  }
  
  const handleDelete = () => {
    onDelete(scan.id)
    setShowDeleteDialog(false)
    toast({
      title: 'Scan Deleted',
      description: `Scan #${scan.id} has been deleted`,
      variant: 'destructive',
    })
  }
  
  const handleChangeScanType = () => {
    if (selectedScanType) {
      onChangeScanType(scan.id, selectedScanType)
      setShowChangeScanTypeDialog(false)
      setSelectedScanType(null)
      toast({
        title: 'Scan Type Changed',
        description: `Scan #${scan.id} type has been updated`,
      })
    }
  }
  
  const canRestart = canRestartScan(scan.status)
  const canCancel = canCancelScan(scan.status)
  const isActive = isActiveScan(scan.status)
  
  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="h-8 w-8 p-0">
            <span className="sr-only">Open menu</span>
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          {canRestart && (
            <DropdownMenuItem onClick={handleRestart}>
              <RotateCcw className="mr-2 h-4 w-4" />
              Restart Scan
            </DropdownMenuItem>
          )}
          {canCancel && (
            <DropdownMenuItem onClick={handleCancel}>
              <StopCircle className="mr-2 h-4 w-4" />
              Cancel Scan
            </DropdownMenuItem>
          )}
          {!isActive && (
            <DropdownMenuItem onClick={() => setShowChangeScanTypeDialog(true)}>
              <Edit className="mr-2 h-4 w-4" />
              Change Scan Type
            </DropdownMenuItem>
          )}
          <DropdownMenuSeparator />
          {!isActive && (
            <DropdownMenuItem 
              onClick={() => setShowDeleteDialog(true)}
              className="text-destructive focus:text-destructive"
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Delete Scan
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Scan</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete scan #{scan.id}? This action cannot be undone.
              All scan results and data will be permanently removed.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Change Scan Type Dialog */}
      <Dialog open={showChangeScanTypeDialog} onOpenChange={setShowChangeScanTypeDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Change Scan Type</DialogTitle>
            <DialogDescription>
              Select a new scan type for scan #{scan.id}. This will update the scan configuration
              but will not restart the scan automatically.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Select value={selectedScanType?.toString()} onValueChange={(value) => setSelectedScanType(Number(value))}>
              <SelectTrigger>
                <SelectValue placeholder="Select scan type" />
              </SelectTrigger>
              <SelectContent>
                {scanTypes.map((scanType) => (
                  <SelectItem key={scanType.id} value={scanType.id.toString()}>
                    <div className="flex flex-col">
                      <span>{scanType.name}</span>
                      {scanType.description && (
                        <span className="text-xs text-muted-foreground">{scanType.description}</span>
                      )}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowChangeScanTypeDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleChangeScanType} disabled={!selectedScanType}>
              Update Scan Type
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}