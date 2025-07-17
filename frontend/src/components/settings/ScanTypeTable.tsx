import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { MoreHorizontal, Edit, Trash2, CheckCircle, XCircle, Shield } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
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
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/components/ui/use-toast'
import { formatDate } from '@/lib/utils'
import { deleteScanType } from '@/services/scanTypeService'
import type { ScanType } from '@/types'

interface ScanTypeTableProps {
  scanTypes: ScanType[]
  onEdit: (scanType: ScanType) => void
  searchTerm: string
}

export default function ScanTypeTable({ scanTypes, onEdit, searchTerm }: ScanTypeTableProps) {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [scanTypeToDelete, setScanTypeToDelete] = useState<ScanType | null>(null)
  
  // Filtro dinamico
  const filteredScanTypes = scanTypes.filter(scanType =>
    scanType.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    scanType.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    scanType.port_list_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    scanType.enabled_plugins.some(plugin => 
      plugin.toLowerCase().includes(searchTerm.toLowerCase())
    )
  )
  
  const deleteMutation = useMutation({
    mutationFn: deleteScanType,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scanTypes'] })
      toast({
        title: 'Scan Type deleted',
        description: `${scanTypeToDelete?.name} has been deleted successfully.`,
      })
      setDeleteDialogOpen(false)
      setScanTypeToDelete(null)
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to delete scan type. It may be in use by existing scans.',
        variant: 'destructive',
      })
    },
  })
  
  const handleDeleteClick = (scanType: ScanType) => {
    setScanTypeToDelete(scanType)
    setDeleteDialogOpen(true)
  }
  
  const handleDeleteConfirm = () => {
    if (scanTypeToDelete) {
      deleteMutation.mutate(scanTypeToDelete.id)
    }
  }
  
  const renderBooleanIcon = (value: boolean) => {
    return value ? (
      <CheckCircle className="h-4 w-4 text-green-500" />
    ) : (
      <XCircle className="h-4 w-4 text-gray-400" />
    )
  }
  
  const truncateText = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + '...'
  }
  
  return (
    <>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Port List</TableHead>
              <TableHead>Plugins</TableHead>
              <TableHead>Configuration</TableHead>
              <TableHead>Created</TableHead>
              <TableHead className="w-[50px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredScanTypes.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                  {searchTerm ? 'No scan types match your search.' : 'No scan types found.'}
                </TableCell>
              </TableRow>
            ) : (
              filteredScanTypes.map((scanType) => (
                <TableRow key={scanType.id}>
                  <TableCell className="font-medium">
                    <div className="flex items-center space-x-2">
                      {scanType.only_discovery && (
                        <Shield className="h-4 w-4 text-blue-500" />
                      )}
                      <span>{scanType.name}</span>
                    </div>
                    {scanType.description && (
                      <div className="text-xs text-muted-foreground mt-1">
                        {truncateText(scanType.description, 60)}
                      </div>
                    )}
                  </TableCell>
                  <TableCell>
                    {scanType.only_discovery ? (
                      <Badge variant="secondary">Discovery</Badge>
                    ) : (
                      <Badge variant="default">Port Scan</Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    {scanType.only_discovery ? (
                      <span className="text-muted-foreground text-sm">N/A</span>
                    ) : scanType.port_list_name ? (
                      <span className="text-sm">{scanType.port_list_name}</span>
                    ) : (
                      <span className="text-muted-foreground text-sm">Default</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {scanType.only_discovery ? (
                      <span className="text-muted-foreground text-sm">None</span>
                    ) : scanType.enabled_plugins.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {scanType.enabled_plugins.slice(0, 2).map((plugin) => (
                          <Badge key={plugin} variant="outline" className="text-xs">
                            {plugin.replace('_', ' ')}
                          </Badge>
                        ))}
                        {scanType.enabled_plugins.length > 2 && (
                          <Badge variant="outline" className="text-xs">
                            +{scanType.enabled_plugins.length - 2}
                          </Badge>
                        )}
                      </div>
                    ) : (
                      <span className="text-muted-foreground text-sm">None</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="flex space-x-3 text-sm">
                      <div className="flex items-center space-x-1" title="Consider Alive">
                        <span className="text-xs text-muted-foreground">Alive:</span>
                        {renderBooleanIcon(scanType.consider_alive)}
                      </div>
                      <div className="flex items-center space-x-1" title="Quiet Mode">
                        <span className="text-xs text-muted-foreground">Quiet:</span>
                        {renderBooleanIcon(scanType.be_quiet)}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {formatDate(scanType.created_at)}
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
                        <DropdownMenuItem onClick={() => onEdit(scanType)}>
                          <Edit className="mr-2 h-4 w-4" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem 
                          onClick={() => handleDeleteClick(scanType)}
                          className="text-destructive"
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
      
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete the scan type "{scanTypeToDelete?.name}".
              This action cannot be undone. If this scan type is used by any existing scans,
              the deletion will fail.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}