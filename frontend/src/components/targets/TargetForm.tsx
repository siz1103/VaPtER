import { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useCustomerStore } from '@/store/customerStore'
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
import { createTarget, updateTarget, validateAddress } from '@/services/targetService'
import type { Target } from '@/types'
import { AlertCircle, CheckCircle2 } from 'lucide-react'

interface TargetFormProps {
  target?: Target
  onSuccess: (target: Target) => void
  onCancel: () => void
}

export default function TargetForm({ target, onSuccess, onCancel }: TargetFormProps) {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { selectedCustomer } = useCustomerStore()
  const isEditing = !!target
  
  const [formData, setFormData] = useState({
    name: target?.name || '',
    address: target?.address || '',
    description: target?.description || '',
  })
  
  const [addressValidation, setAddressValidation] = useState<{
    valid: boolean
    type: 'ip' | 'fqdn' | 'invalid'
    message?: string
  }>({ valid: true, type: 'invalid' })
  
  // Validazione real-time dell'indirizzo
  useEffect(() => {
    if (formData.address) {
      const validation = validateAddress(formData.address)
      let message = ''
      
      if (!validation.valid) {
        message = 'Enter a valid IP address (e.g., 192.168.1.1) or domain name (e.g., example.com)'
      } else if (validation.type === 'ip') {
        message = 'Valid IP address'
      } else if (validation.type === 'fqdn') {
        message = 'Valid domain name'
      }
      
      setAddressValidation({ ...validation, message })
    } else {
      setAddressValidation({ valid: true, type: 'invalid' })
    }
  }, [formData.address])
  
  const mutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      if (!selectedCustomer) {
        throw new Error('No customer selected')
      }
      
      const targetData = {
        ...data,
        customer: selectedCustomer.id,
      }
      
      if (isEditing) {
        return updateTarget(target.id, targetData)
      } else {
        return createTarget(targetData)
      }
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['targets'] })
      toast({
        title: isEditing ? 'Target updated' : 'Target created',
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
    
    if (!addressValidation.valid) {
      toast({
        title: 'Invalid address',
        description: 'Please enter a valid IP address or domain name',
        variant: 'destructive',
      })
      return
    }
    
    mutation.mutate(formData)
  }
  
  const handleChange = (field: keyof typeof formData) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setFormData(prev => ({ ...prev, [field]: e.target.value }))
  }
  
  return (
    <DialogContent className="sm:max-w-[500px]">
      <form onSubmit={handleSubmit}>
        <DialogHeader>
          <DialogTitle>{isEditing ? 'Edit Target' : 'Create New Target'}</DialogTitle>
          <DialogDescription>
            {isEditing 
              ? 'Update target information' 
              : `Add a new target for ${selectedCustomer?.name || 'the selected customer'}`
            }
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
              placeholder="e.g., Web Server, Mail Server"
            />
          </div>
          
          <div className="grid gap-2">
            <Label htmlFor="address">
              Address (IP or Domain) *
              {formData.address && (
                <span className={`text-xs ml-2 ${addressValidation.valid ? 'text-green-500' : 'text-red-500'}`}>
                  {addressValidation.valid ? (
                    <span className="inline-flex items-center">
                      <CheckCircle2 className="h-3 w-3 mr-1" />
                      {addressValidation.message}
                    </span>
                  ) : (
                    <span className="inline-flex items-center">
                      <AlertCircle className="h-3 w-3 mr-1" />
                      Invalid format
                    </span>
                  )}
                </span>
              )}
            </Label>
            <Input
              id="address"
              value={formData.address}
              onChange={handleChange('address')}
              required
              placeholder="192.168.1.1 or example.com"
              className={formData.address && !addressValidation.valid ? 'border-red-500' : ''}
            />
            {formData.address && addressValidation.message && (
              <p className={`text-xs ${addressValidation.valid ? 'text-muted-foreground' : 'text-red-500'}`}>
                {addressValidation.message}
              </p>
            )}
          </div>
          
          <div className="grid gap-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={handleChange('description')}
              rows={3}
              placeholder="Additional information about this target..."
            />
          </div>
          
          {isEditing && target && (
            <div className="bg-muted p-3 rounded-md">
              <p className="text-sm font-medium mb-1">Target Information</p>
              <div className="text-xs text-muted-foreground space-y-1">
                <div>Customer: {target.customer_name}</div>
                <div>Total Scans: {target.scans_count}</div>
                {target.last_scan && (
                  <div>Last Scan: {target.last_scan.status}</div>
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
            disabled={mutation.isPending || (formData.address && !addressValidation.valid)}
          >
            {mutation.isPending ? 'Saving...' : isEditing ? 'Update' : 'Create'}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  )
}