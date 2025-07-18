import { Badge } from '@/components/ui/badge'
import { getStatusColor, isActiveScan } from '@/services/scanService'
import type { ScanStatus } from '@/types'

interface ScanStatusBadgeProps {
  status: ScanStatus
  className?: string
}

export default function ScanStatusBadge({ status, className }: ScanStatusBadgeProps) {
  const color = getStatusColor(status)
  const isActive = isActiveScan(status)
  
  return (
    <Badge 
      variant={color as any} 
      className={`${className} ${isActive ? 'animate-pulse' : ''}`}
    >
      {isActive && <span className="mr-1">⚡</span>}
      {status}
    </Badge>
  )
}