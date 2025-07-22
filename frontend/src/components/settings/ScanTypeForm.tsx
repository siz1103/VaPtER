import { useState, useEffect } from 'react'
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
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
import { createScanType, updateScanType } from '@/services/scanTypeService'
import { getPortLists } from '@/services/portListService'
import type { ScanType } from '@/types'

interface ScanTypeFormProps {
  scanType?: ScanType
  onSuccess: (scanType: ScanType) => void
  onCancel: () => void
}

export default function ScanTypeForm({ scanType, onSuccess, onCancel }: ScanTypeFormProps) {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const isEditing = !!scanType
  
  const [formData, setFormData] = useState({
    name: scanType?.name || '',
    only_discovery: scanType?.only_discovery || false,
    consider_alive: scanType?.consider_alive || false,
    be_quiet: scanType?.be_quiet || false,
    port_list: scanType?.port_list || undefined,
    plugin_finger: scanType?.plugin_finger || false,
    plugin_gce: scanType?.plugin_gce || false,
    plugin_web: scanType?.plugin_web || false,
    plugin_vuln_lookup: scanType?.plugin_vuln_lookup || false,
    description: scanType?.description || '',
  })
  
  // Fetch port lists per il dropdown
  const { data: portLists = [] } = useQuery({
    queryKey: ['portLists'],
    queryFn: getPortLists,
  })
  
  // Reset dei campi quando only_discovery cambia
  useEffect(() => {
    if (formData.only_discovery) {
      setFormData(prev => ({
        ...prev,
        port_list: undefined,
        plugin_finger: false,
        plugin_gce: false,
        plugin_web: false,
        plugin_vuln_lookup: false,
      }))
    }
  }, [formData.only_discovery])
  
  const mutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      console.log('Mutation starting with data:', data) // Debug log
      
      // Pulisci i dati prima dell'invio
      const cleanData = { ...data }
      if (cleanData.only_discovery) {
        cleanData.port_list = undefined
        cleanData.plugin_finger = false
        cleanData.plugin_gce = false
        cleanData.plugin_web = false
        cleanData.plugin_vuln_lookup = false
      }
      
      console.log('Clean data to send:', cleanData) // Debug log
      
      if (isEditing) {
        return updateScanType(scanType.id, cleanData)
      } else {
        return createScanType(cleanData)
      }
    },
    onSuccess: (data) => {
      console.log('Mutation success:', data) // Debug log
      queryClient.invalidateQueries({ queryKey: ['scanTypes'] })
      toast({
        title: isEditing ? 'Scan Type updated' : 'Scan Type created',
        description: `${data.name} has been ${isEditing ? 'updated' : 'created'} successfully.`,
      })
      onSuccess(data)
    },
    onError: (error: any) => {
      console.error('Mutation error:', error) // Debug log
      toast({
        title: 'Error',
        description: error.response?.data?.detail || `Failed to ${isEditing ? 'update' : 'create'} scan type`,
        variant: 'destructive',
      })
    },
  })
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    console.log('Form submitted!') // Debug log
    console.log('Form data:', formData) // Debug log
    
    if (!formData.name.trim()) {
      toast({
        title: 'Error',
        description: 'Scan type name is required',
        variant: 'destructive',
      })
      return
    }
    
    mutation.mutate(formData)
  }
  
  const handleChange = (field: keyof typeof formData) => (value: any) => {
    console.log(`Changing ${field} to:`, value) // Debug log
    setFormData(prev => ({ ...prev, [field]: value }))
  }
  
  const handleInputChange = (field: keyof typeof formData) => 
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      console.log(`Input change ${field} to:`, e.target.value) // Debug log
      setFormData(prev => ({ ...prev, [field]: e.target.value }))
    }
  
  return (
    <DialogContent className="sm:max-w-[600px]">
      <form onSubmit={handleSubmit} id="scan-type-form">
        <DialogHeader>
          <DialogTitle>{isEditing ? 'Edit Scan Type' : 'Create New Scan Type'}</DialogTitle>
          <DialogDescription>
            {isEditing ? 'Update scan type configuration' : 'Create a new scan type template'}
          </DialogDescription>
        </DialogHeader>
        
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="name">Name *</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={handleInputChange('name')}
              required
              placeholder="e.g., Quick Discovery Scan"
            />
          </div>
          
          <div className="grid gap-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={handleInputChange('description')}
              rows={2}
              placeholder="Description of this scan type..."
            />
          </div>
          
          <div className="space-y-4">
            <h4 className="text-sm font-medium">Scan Configuration</h4>
            
            <div className="flex items-center space-x-2">
              <Switch
                id="only_discovery"
                checked={formData.only_discovery}
                onCheckedChange={handleChange('only_discovery')}
              />
              <Label htmlFor="only_discovery" className="flex-1">
                Discovery Only
                <p className="text-xs text-muted-foreground">
                  Only check if host is alive (ping scan)
                </p>
              </Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Switch
                id="consider_alive"
                checked={formData.consider_alive}
                onCheckedChange={handleChange('consider_alive')}
                disabled={formData.only_discovery}
              />
              <Label htmlFor="consider_alive" className="flex-1">
                Consider All Hosts Alive
                <p className="text-xs text-muted-foreground">
                  Skip host discovery phase
                </p>
              </Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Switch
                id="be_quiet"
                checked={formData.be_quiet}
                onCheckedChange={handleChange('be_quiet')}
              />
              <Label htmlFor="be_quiet" className="flex-1">
                Quiet Mode
                <p className="text-xs text-muted-foreground">
                  Reduce verbosity of scan output
                </p>
              </Label>
            </div>
          </div>
          
          <div className="grid gap-2">
            <Label htmlFor="port_list">Port List</Label>
            <Select
              value={formData.port_list?.toString() || ''}
              onValueChange={(value) => {
                console.log('Port list selected:', value) // Debug log
                handleChange('port_list')(value ? parseInt(value) : undefined)
              }}
              disabled={formData.only_discovery}
            >
              <SelectTrigger>
                <SelectValue placeholder={formData.only_discovery ? "Not applicable for discovery scan" : "Select a port list (optional)"} />
              </SelectTrigger>
              <SelectContent>
                {portLists.map((portList) => (
                  <SelectItem key={portList.id} value={portList.id.toString()}>
                    {portList.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {formData.only_discovery && (
              <p className="text-xs text-muted-foreground">
                Port scanning is disabled for discovery-only scans
              </p>
            )}
          </div>
          
          <div className="space-y-4">
            <h4 className="text-sm font-medium">Plugins</h4>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center space-x-2">
                <Switch
                  id="plugin_finger"
                  checked={formData.plugin_finger}
                  onCheckedChange={handleChange('plugin_finger')}
                  disabled={formData.only_discovery}
                />
                <Label htmlFor="plugin_finger" className="text-sm">
                  Fingerprinting
                </Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Switch
                  id="plugin_gce"
                  checked={formData.plugin_gce}
                  onCheckedChange={handleChange('plugin_gce')}
                  disabled={formData.only_discovery}
                />
                <Label htmlFor="plugin_gce" className="text-sm">
                  G
                </Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Switch
                  id="plugin_web"
                  checked={formData.plugin_web}
                  onCheckedChange={handleChange('plugin_web')}
                  disabled={formData.only_discovery}
                />
                <Label htmlFor="plugin_web" className="text-sm">
                  Web Scanning
                </Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Switch
                  id="plugin_vuln_lookup"
                  checked={formData.plugin_vuln_lookup}
                  onCheckedChange={handleChange('plugin_vuln_lookup')}
                  disabled={formData.only_discovery}
                />
                <Label htmlFor="plugin_vuln_lookup" className="text-sm">
                  Vuln Lookup
                </Label>
              </div>
            </div>
            {formData.only_discovery && (
              <p className="text-xs text-muted-foreground">
                Plugins are disabled for discovery-only scans
              </p>
            )}
          </div>
        </div>
        
        <DialogFooter>
          <Button 
            type="button" 
            variant="outline" 
            onClick={() => {
              console.log('Cancel clicked') // Debug log
              onCancel()
            }}
          >
            Cancel
          </Button>
          <Button 
            type="submit" 
            form="scan-type-form"
            disabled={mutation.isPending}
          >
            {mutation.isPending
              ? (isEditing ? 'Updating...' : 'Creating...')
              : (isEditing ? 'Update' : 'Create')
            }
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  )
}