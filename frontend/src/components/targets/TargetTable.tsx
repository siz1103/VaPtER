import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { MoreHorizontal, Edit, Trash2, Scan as ScanIcon, Activity, Shield, Network, AlertTriangle, Monitor } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
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
import { Dialog } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/components/ui/use-toast'
import { formatDate, getStatusColor } from '@/lib/utils'
import { deleteTarget } from '@/services/targetService'
import StartScanDialog from './StartScanDialog'
import type { Target } from '@/types'

interface TargetTableProps {
  targets: Target[]
  onEdit: (target: Target) => void
  searchTerm: string
}

export default function TargetTable({ targets, onEdit, searchTerm }: TargetTableProps) {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [targetToDelete, setTargetToDelete] = useState<Target | null>(null)
  const [scanDialogOpen, setScanDialogOpen] = useState(false)
  const [targetToScan, setTargetToScan] = useState<Target | null>(null)
  
  // Filtro dinamico
  const filteredTargets = targets.filter(target =>
    target.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    target.address.toLowerCase().includes(searchTerm.toLowerCase()) ||
    target.description?.toLowerCase().includes(searchTerm.toLowerCase())
  )
  
  const deleteMutation = useMutation({
    mutationFn: deleteTarget,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['targets'] })
      toast({
        title: 'Target deleted',
        description: `${targetToDelete?.name} has been deleted successfully.`,
      })
      setDeleteDialogOpen(false)
      setTargetToDelete(null)
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to delete target. Please check your connection and try again.',
        variant: 'destructive',
      })
    },
  })
  
  const handleDeleteClick = (target: Target) => {
    setTargetToDelete(target)
    setDeleteDialogOpen(true)
  }
  
  const handleDeleteConfirm = () => {
    if (targetToDelete) {
      deleteMutation.mutate(targetToDelete.id)
    }
  }
  
  const handleScanClick = (target: Target) => {
    setTargetToScan(target)
    setScanDialogOpen(true)
  }
  
  const getAddressTypeIcon = (address: string) => {
    // Simple check for IP vs domain
    const isIP = /^\d+\.\d+\.\d+\.\d+$/.test(address) || address.includes(':')
    return isIP ? <Network className="h-3 w-3" /> : <Shield className="h-3 w-3" />
  }
  
  const getScanStatusBadge = (lastScan?: Target['last_scan']) => {
    if (!lastScan) {
      return <Badge variant="outline" className="text-xs">Never scanned</Badge>
    }
    
    const statusColor = getStatusColor(lastScan.status)
    const isRunning = lastScan.status.includes('Running') || lastScan.status === 'Queued'
    
    return (
      <Badge 
        variant={lastScan.status === 'Completed' ? 'default' : lastScan.status === 'Failed' ? 'destructive' : 'secondary'}
        className="text-xs"
      >
        {isRunning && <Activity className="h-3 w-3 mr-1 animate-pulse" />}
        {lastScan.status}
      </Badge>
    )
  }
  
  // Function to get vulnerabilities count - will be replaced with real data
  const getVulnerabilitiesCount = (target: Target) => {
    // This would come from the last scan results - for now return 0
    return 0
  }
  
  // Format open ports for display
  const formatOpenPorts = (ports: number[] | string[]) => {
    if (!ports || ports.length === 0) return '-'
    
    // Convert all to string for consistent display
    const portStrings = ports.map(p => String(p))
    
    // Show first 3 ports
    const displayPorts = portStrings.slice(0, 3).join(', ')
    
    // Add count if more than 3
    if (portStrings.length > 3) {
      return `${displayPorts} +${portStrings.length - 3}`
    }
    
    return displayPorts
  }
  
  return (
    <>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Address</TableHead>
              <TableHead>OS</TableHead>
              <TableHead>Scans</TableHead>
              <TableHead>Last Scan</TableHead>
              <TableHead>Vulnerabilities</TableHead>
              <TableHead>Open Ports</TableHead>
              <TableHead>Created</TableHead>
              <TableHead className="w-[50px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredTargets.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                  {searchTerm ? 'No targets match your search.' : 'No targets found. Create your first target to get started.'}
                </TableCell>
              </TableRow>
            ) : (
              filteredTargets.map((target) => {
                const vulnCount = getVulnerabilitiesCount(target)
                
                return (
                  <TableRow key={target.id}>
                    <TableCell className="font-medium">
                      <div>
                        {target.name}
                        {target.description && (
                          <div className="text-xs text-muted-foreground mt-1">
                            {target.description.length > 50 
                              ? target.description.substring(0, 50) + '...'
                              : target.description
                            }
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        {getAddressTypeIcon(target.address)}
                        <span className="text-sm">{target.address}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-1">
                        {target.os_guess ? (
                          <>
                            <Monitor className="h-3 w-3 text-blue-500" />
                            <span className="text-sm">{target.os_guess}</span>
                          </>
                        ) : (
                          <span className="text-sm text-muted-foreground">-</span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm">{target.scans_count || 0}</span>
                    </TableCell>
                    <TableCell>
                      {getScanStatusBadge(target.last_scan)}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-1">
                        {vulnCount > 0 ? (
                          <>
                            <AlertTriangle className="h-4 w-4 text-orange-500" />
                            <span className="text-sm font-medium">{vulnCount}</span>
                          </>
                        ) : (
                          <span className="text-sm text-muted-foreground">-</span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm font-mono">
                        {formatOpenPorts(target.open_ports)}
                      </span>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDate(target.created_at)}
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                            <span className="sr-only">Open menu</span>
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleScanClick(target)}>
                            <ScanIcon className="mr-2 h-4 w-4" />
                            Start Scan
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem onClick={() => onEdit(target)}>
                            <Edit className="mr-2 h-4 w-4" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => handleDeleteClick(target)}
                            className="text-destructive"
                          >
                            <Trash2 className="mr-2 h-4 w-4" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
      </div>
      
      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete the target "{targetToDelete?.name}" ({targetToDelete?.address}).
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setTargetToDelete(null)}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      
      {/* Start Scan Dialog */}
      {targetToScan && (
        <StartScanDialog
          open={scanDialogOpen}
          onOpenChange={setScanDialogOpen}
          target={targetToScan}
          onSuccess={() => {
            setScanDialogOpen(false)
            setTargetToScan(null)
            queryClient.invalidateQueries({ queryKey: ['targets'] })
          }}
        />
      )}
    </>
  )
}