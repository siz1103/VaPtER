import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { MoreHorizontal, Edit, Trash2 } from 'lucide-react'
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
import { useToast } from '@/components/ui/use-toast'
import { formatDate } from '@/lib/utils'
import { deletePortList } from '@/services/portListService'
import type { PortList } from '@/types'

interface PortListTableProps {
  portLists: PortList[]
  onEdit: (portList: PortList) => void
  searchTerm: string
}

export default function PortListTable({ portLists, onEdit, searchTerm }: PortListTableProps) {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [portListToDelete, setPortListToDelete] = useState<PortList | null>(null)
  
  // Filtro dinamico
  const filteredPortLists = portLists.filter(portList =>
    portList.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    portList.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    portList.tcp_ports?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    portList.udp_ports?.toLowerCase().includes(searchTerm.toLowerCase())
  )
  
  const deleteMutation = useMutation({
    mutationFn: deletePortList,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portLists'] })
      toast({
        title: 'Port List deleted',
        description: `${portListToDelete?.name} has been deleted successfully.`,
      })
      setDeleteDialogOpen(false)
      setPortListToDelete(null)
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to delete port list. It may be in use by scan types.',
        variant: 'destructive',
      })
    },
  })
  
  const handleDeleteClick = (portList: PortList) => {
    setPortListToDelete(portList)
    setDeleteDialogOpen(true)
  }
  
  const handleDeleteConfirm = () => {
    if (portListToDelete) {
      deleteMutation.mutate(portListToDelete.id)
    }
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
              <TableHead>TCP Ports</TableHead>
              <TableHead>UDP Ports</TableHead>
              <TableHead>Description</TableHead>
              <TableHead>Created</TableHead>
              <TableHead className="w-[50px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredPortLists.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                  {searchTerm ? 'No port lists match your search.' : 'No port lists found.'}
                </TableCell>
              </TableRow>
            ) : (
              filteredPortLists.map((portList) => (
                <TableRow key={portList.id}>
                  <TableCell className="font-medium">
                    {portList.name}
                  </TableCell>
                  <TableCell>
                    {portList.tcp_ports ? (
                      <div className="space-y-1">
                        <div className="text-sm">
                          {truncateText(portList.tcp_ports, 30)}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          ~{portList.total_tcp_ports} ports
                        </div>
                      </div>
                    ) : (
                      <span className="text-muted-foreground">None</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {portList.udp_ports ? (
                      <div className="space-y-1">
                        <div className="text-sm">
                          {truncateText(portList.udp_ports, 30)}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          ~{portList.total_udp_ports} ports
                        </div>
                      </div>
                    ) : (
                      <span className="text-muted-foreground">None</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {portList.description ? (
                      <span className="text-sm">
                        {truncateText(portList.description, 50)}
                      </span>
                    ) : (
                      <span className="text-muted-foreground">No description</span>
                    )}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {formatDate(portList.created_at)}
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
                        <DropdownMenuItem onClick={() => onEdit(portList)}>
                          <Edit className="mr-2 h-4 w-4" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem 
                          onClick={() => handleDeleteClick(portList)}
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
              This will permanently delete the port list "{portListToDelete?.name}".
              This action cannot be undone. If this port list is used by any scan types,
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