import { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useToast } from '@/components/ui/use-toast'
import { createPortList, updatePortList, validatePortFormat, countPorts } from '@/services/portListService'
import type { PortList } from '@/types'

interface PortListFormProps {
  portList?: PortList
  onSuccess: (portList: PortList) => void
  onCancel: () => void
}

export default function PortListForm({ portList, onSuccess, onCancel }: PortListFormProps) {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const isEditing = !!portList
  
  const [formData, setFormData] = useState({
    name: portList?.name || '',
    tcp_ports: portList?.tcp_ports || '',
    udp_ports: portList?.udp_ports || '',
    description: portList?.description || '',
  })
  
  const [errors, setErrors] = useState({
    tcp_ports: '',
    udp_ports: '',
  })
  
  const [portCounts, setPortCounts] = useState({
    tcp: 0,
    udp: 0,
  })
  
  // Calcola conteggio porte quando cambiano i valori
  useEffect(() => {
    setPortCounts({
      tcp: countPorts(formData.tcp_ports),
      udp: countPorts(formData.udp_ports),
    })
  }, [formData.tcp_ports, formData.udp_ports])
  
  const mutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      if (isEditing) {
        return updatePortList(portList.id, data)
      } else {
        return createPortList(data)
      }
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['portLists'] })
      toast({
        title: isEditing ? 'Port List updated' : 'Port List created',
        description: `${data.name} has been ${isEditing ? 'updated' : 'created'} successfully.`,
      })
      onSuccess(data)
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'An error occurred. Please try again.',
        variant: 'destructive',
      })
    },
  })
  
  const validateField = (field: 'tcp_ports' | 'udp_ports', value: string) => {
    if (value && !validatePortFormat(value)) {
      return 'Invalid port format. Use: 22,80,443 or 1-1000 or combinations'
    }
    return ''
  }
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validazione
    const tcpError = validateField('tcp_ports', formData.tcp_ports)
    const udpError = validateField('udp_ports', formData.udp_ports)
    
    setErrors({
      tcp_ports: tcpError,
      udp_ports: udpError,
    })
    
    if (tcpError || udpError) {
      return
    }
    
    // Verifica che almeno un tipo di porta sia specificato
    if (!formData.tcp_ports.trim() && !formData.udp_ports.trim()) {
      toast({
        title: 'Validation Error',
        description: 'At least one of TCP ports or UDP ports must be specified.',
        variant: 'destructive',
      })
      return
    }
    
    mutation.mutate(formData)
  }
  
  const handleChange = (field: keyof typeof formData) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const value = e.target.value
    setFormData(prev => ({ ...prev, [field]: value }))
    
    // Validazione in tempo reale per le porte
    if (field === 'tcp_ports' || field === 'udp_ports') {
      const error = validateField(field, value)
      setErrors(prev => ({ ...prev, [field]: error }))
    }
  }
  
  return (
    <DialogContent className="sm:max-w-[500px]">
      <form onSubmit={handleSubmit}>
        <DialogHeader>
          <DialogTitle>{isEditing ? 'Edit Port List' : 'Create New Port List'}</DialogTitle>
          <DialogDescription>
            {isEditing ? 'Update port list configuration' : 'Create a new port list for scanning'}
          </DialogDescription>
        </DialogHeader>
        
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="name">Name *</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={handleChange('name')}
              required
              placeholder="e.g., Common TCP Ports"
            />
          </div>
          
          <div className="grid gap-2">
            <Label htmlFor="tcp_ports">
              TCP Ports
              {portCounts.tcp > 0 && (
                <span className="text-sm text-muted-foreground ml-2">
                  (~{portCounts.tcp} ports)
                </span>
              )}
            </Label>
            <Input
              id="tcp_ports"
              value={formData.tcp_ports}
              onChange={handleChange('tcp_ports')}
              placeholder="e.g., 22,80,443,1000-2000"
              className={errors.tcp_ports ? 'border-red-500' : ''}
            />
            {errors.tcp_ports && (
              <p className="text-sm text-red-500">{errors.tcp_ports}</p>
            )}
            <p className="text-xs text-muted-foreground">
              Format: single ports (22,80,443) or ranges (1-1000) or combinations
            </p>
          </div>
          
          <div className="grid gap-2">
            <Label htmlFor="udp_ports">
              UDP Ports
              {portCounts.udp > 0 && (
                <span className="text-sm text-muted-foreground ml-2">
                  (~{portCounts.udp} ports)
                </span>
              )}
            </Label>
            <Input
              id="udp_ports"
              value={formData.udp_ports}
              onChange={handleChange('udp_ports')}
              placeholder="e.g., 53,161,514"
              className={errors.udp_ports ? 'border-red-500' : ''}
            />
            {errors.udp_ports && (
              <p className="text-sm text-red-500">{errors.udp_ports}</p>
            )}
            <p className="text-xs text-muted-foreground">
              Format: single ports (53,161) or ranges (1-1000) or combinations
            </p>
          </div>
          
          <div className="grid gap-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={handleChange('description')}
              rows={3}
              placeholder="Description of this port list..."
            />
          </div>
          
          {(formData.tcp_ports || formData.udp_ports) && (
            <div className="bg-muted p-3 rounded-md">
              <p className="text-sm font-medium mb-1">Port Summary</p>
              <div className="text-xs text-muted-foreground space-y-1">
                {formData.tcp_ports && (
                  <div>TCP: ~{portCounts.tcp} ports</div>
                )}
                {formData.udp_ports && (
                  <div>UDP: ~{portCounts.udp} ports</div>
                )}
                <div className="font-medium">
                  Total: ~{portCounts.tcp + portCounts.udp} ports
                </div>
              </div>
            </div>
          )}
        </div>
        
        <DialogFooter>
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? 'Saving...' : isEditing ? 'Update' : 'Create'}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  )
}