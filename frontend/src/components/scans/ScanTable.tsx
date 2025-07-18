import { useState } from 'react'
import { formatDistanceToNow } from 'date-fns'
import { ChevronDown, ChevronRight, Target, Calendar, Clock, Server } from 'lucide-react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import ScanStatusBadge from './ScanStatusBadge'
import ScanActions from './ScanActions'
import type { Scan, ScanType } from '@/types'

interface ScanTableProps {
  scans: Scan[]
  scanTypes: ScanType[]
  searchTerm: string
  onRestart: (scanId: number) => void
  onCancel: (scanId: number) => void
  onDelete: (scanId: number) => void
  onChangeScanType: (scanId: number, scanTypeId: number) => void
}

interface ScanRowProps {
  scan: Scan
  scanTypes: ScanType[]
  onRestart: (scanId: number) => void
  onCancel: (scanId: number) => void
  onDelete: (scanId: number) => void
  onChangeScanType: (scanId: number, scanTypeId: number) => void
}

function ScanRow({ scan, scanTypes, onRestart, onCancel, onDelete, onChangeScanType }: ScanRowProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  
  const formatDuration = (scan: Scan) => {
    if (scan.started_at && scan.completed_at) {
      const duration = new Date(scan.completed_at).getTime() - new Date(scan.started_at).getTime()
      const minutes = Math.floor(duration / 60000)
      const seconds = Math.floor((duration % 60000) / 1000)
      return `${minutes}m ${seconds}s`
    }
    return '-'
  }
  
  const hasResults = scan.parsed_nmap_results && Object.keys(scan.parsed_nmap_results).length > 0
  
  return (
    <Collapsible asChild open={isExpanded} onOpenChange={setIsExpanded}>
      <>
        <TableRow className="group">
          <TableCell>
            <CollapsibleTrigger asChild>
              <Button variant="ghost" size="sm" className="p-0 h-6 w-6">
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
              </Button>
            </CollapsibleTrigger>
          </TableCell>
          <TableCell className="font-medium">#{scan.id}</TableCell>
          <TableCell>
            <div className="flex items-center space-x-2">
              <Server className="h-4 w-4 text-muted-foreground" />
              <div>
                <div className="font-medium">{scan.target_name}</div>
                <div className="text-sm text-muted-foreground">{scan.target_address}</div>
              </div>
            </div>
          </TableCell>
          <TableCell>
            <Badge variant="outline">{scan.scan_type_name}</Badge>
          </TableCell>
          <TableCell>
            <ScanStatusBadge status={scan.status} />
          </TableCell>
          <TableCell>
            <div className="flex items-center space-x-1 text-sm text-muted-foreground">
              <Calendar className="h-3 w-3" />
              <span>{formatDistanceToNow(new Date(scan.initiated_at), { addSuffix: true })}</span>
            </div>
          </TableCell>
          <TableCell>
            <div className="flex items-center space-x-1 text-sm text-muted-foreground">
              <Clock className="h-3 w-3" />
              <span>{formatDuration(scan)}</span>
            </div>
          </TableCell>
          <TableCell>
            <ScanActions
              scan={scan}
              scanTypes={scanTypes}
              onRestart={onRestart}
              onCancel={onCancel}
              onDelete={onDelete}
              onChangeScanType={onChangeScanType}
            />
          </TableCell>
        </TableRow>
        
        {/* Expanded Content */}
        <CollapsibleContent asChild>
          <TableRow>
            <TableCell colSpan={8}>
              <div className="py-4 space-y-4">
                {/* Scan Details */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <div className="font-medium text-muted-foreground">Initiated</div>
                    <div>{new Date(scan.initiated_at).toLocaleString()}</div>
                  </div>
                  {scan.started_at && (
                    <div>
                      <div className="font-medium text-muted-foreground">Started</div>
                      <div>{new Date(scan.started_at).toLocaleString()}</div>
                    </div>
                  )}
                  {scan.completed_at && (
                    <div>
                      <div className="font-medium text-muted-foreground">Completed</div>
                      <div>{new Date(scan.completed_at).toLocaleString()}</div>
                    </div>
                  )}
                </div>
                
                {/* Error Message */}
                {scan.error_message && (
                  <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
                    <div className="font-medium text-destructive mb-1">Error</div>
                    <div className="text-sm text-destructive/80">{scan.error_message}</div>
                  </div>
                )}
                
                {/* Nmap Results */}
                {hasResults && (
                  <div>
                    <div className="font-medium text-muted-foreground mb-2">Nmap Results</div>
                    <div className="bg-muted p-3 rounded-md">
                      <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                        {JSON.stringify(scan.parsed_nmap_results, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
                
                {/* Other Results Placeholders */}
                {scan.parsed_finger_results && (
                  <div>
                    <div className="font-medium text-muted-foreground mb-2">Fingerprint Results</div>
                    <div className="bg-muted p-3 rounded-md">
                      <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                        {JSON.stringify(scan.parsed_finger_results, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
                
                {scan.parsed_enum_results && (
                  <div>
                    <div className="font-medium text-muted-foreground mb-2">Enumeration Results</div>
                    <div className="bg-muted p-3 rounded-md">
                      <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                        {JSON.stringify(scan.parsed_enum_results, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
                
                {scan.parsed_web_results && (
                  <div>
                    <div className="font-medium text-muted-foreground mb-2">Web Scan Results</div>
                    <div className="bg-muted p-3 rounded-md">
                      <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                        {JSON.stringify(scan.parsed_web_results, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
                
                {scan.parsed_vuln_results && (
                  <div>
                    <div className="font-medium text-muted-foreground mb-2">Vulnerability Results</div>
                    <div className="bg-muted p-3 rounded-md">
                      <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                        {JSON.stringify(scan.parsed_vuln_results, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            </TableCell>
          </TableRow>
        </CollapsibleContent>
      </>
    </Collapsible>
  )
}

export default function ScanTable({
  scans,
  scanTypes,
  searchTerm,
  onRestart,
  onCancel,
  onDelete,
  onChangeScanType,
}: ScanTableProps) {
  // Filter scans based on search term
  const filteredScans = scans.filter((scan) =>
    scan.target_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    scan.target_address.toLowerCase().includes(searchTerm.toLowerCase()) ||
    scan.scan_type_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    scan.status.toLowerCase().includes(searchTerm.toLowerCase()) ||
    scan.id.toString().includes(searchTerm)
  )
  
  if (filteredScans.length === 0) {
    return (
      <div className="text-center py-8">
        <Target className="mx-auto h-12 w-12 text-muted-foreground/50" />
        <h3 className="mt-4 text-lg font-semibold">No scans found</h3>
        <p className="text-muted-foreground">
          {searchTerm ? 'No scans match your search criteria.' : 'No scans have been created yet.'}
        </p>
      </div>
    )
  }
  
  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-8"></TableHead>
            <TableHead className="w-20">ID</TableHead>
            <TableHead>Target</TableHead>
            <TableHead>Scan Type</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Initiated</TableHead>
            <TableHead>Duration</TableHead>
            <TableHead className="w-12"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {filteredScans.map((scan) => (
            <ScanRow
              key={scan.id}
              scan={scan}
              scanTypes={scanTypes}
              onRestart={onRestart}
              onCancel={onCancel}
              onDelete={onDelete}
              onChangeScanType={onChangeScanType}
            />
          ))}
        </TableBody>
      </Table>
    </div>
  )
}