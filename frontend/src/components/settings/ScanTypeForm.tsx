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
    plugin_enum: scanType?.plugin_enum || false,
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
        plugin_enum: false,
        plugin_web: false,
        plugin_vuln_lookup: false,
      }))
    }
  }, [formData.only_discovery])
  
  const mutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      // Pulisci i dati prima dell'invio
      const cleanData = { ...data }
      if (cleanData.only_discovery) {
        cleanData.port_list = undefined
        cleanData.plugin_finger = false
        cleanData.plugin_enum = false
        cleanData.plugin_web = false
        cleanData.plugin_vuln_lookup = false
      }
      
      if (isEditing) {
        return updateScanType(scanType.id, cleanData)
      } else {
        return createScanType(cleanData)
      }
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['scanTypes'] })
      toast({
        title: isEditing ? 'Scan Type updated' : 'Scan Type created',
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
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate(formData)
  }
  
  const handleChange = (field: keyof typeof formData) => (
    value: any
  ) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }
  
  const handleInputChange = (field: keyof typeof formData) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setFormData(prev => ({ ...prev, [field]: e.target.value }))
  }
  
  return (
    <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
      <form onSubmit={handleSubmit}>
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
              onValueChange={(value) => handleChange('port_list')(value ? parseInt(value) : undefined)}
              disabled={formData.only_discovery}
            >
              <SelectTrigger>
                <SelectValue placeholder={formData.only_discovery ? "Not applicable for discovery scan" : "Select a port list"} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">No port list</SelectItem>
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
                  id="plugin_enum"
                  checked={formData.plugin_enum}
                  onCheckedChange={handleChange('plugin_enum')}
                  disabled={formData.only_discovery}
                />
                <Label htmlFor="plugin_enum" className="text-sm">
                  Enumeration
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
                  Vulnerability Lookup
                </Label>
              </div>
            </div>
            {formData.only_discovery && (
              <p className="text-xs text-muted-foreground">
                Plugins are disabled for discovery-only scans
              </p>
            )}
          </div>
          
          {!formData.only_discovery && (
            <div className="bg-muted p-3 rounded-md">
              <p className="text-sm font-medium mb-1">Scan Summary</p>
              <div className="text-xs text-muted-foreground space-y-1">
                <div>Port List: {formData.port_list ? portLists.find(pl => pl.id === formData.port_list)?.name || 'Unknown' : 'Default ports'}</div>
                <div>Host Discovery: {formData.consider_alive ? 'Disabled' : 'Enabled'}</div>
                <div>Verbosity: {formData.be_quiet ? 'Quiet' : 'Normal'}</div>
                <div>
                  Plugins: {[
                    formData.plugin_finger && 'Fingerprinting',
                    formData.plugin_enum && 'Enumeration', 
                    formData.plugin_web && 'Web Scanning',
                    formData.plugin_vuln_lookup && 'Vulnerability Lookup'
                  ].filter(Boolean).join(', ') || 'None'}
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