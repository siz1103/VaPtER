import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date): string {
  const d = new Date(date)
  return d.toLocaleDateString('it-IT', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatDuration(seconds?: number): string {
  if (!seconds) return '-'
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  
  if (hours > 0) {
    return `${hours}h ${minutes}m ${secs}s`
  } else if (minutes > 0) {
    return `${minutes}m ${secs}s`
  } else {
    return `${secs}s`
  }
}

export function getStatusColor(status: string): string {
  const statusMap: Record<string, string> = {
    'Pending': 'text-gray-500',
    'Queued': 'text-blue-500',
    'Completed': 'text-green-500',
    'Failed': 'text-red-500',
    'Running': 'text-yellow-500',
  }
  
  // Check for running states
  if (status.includes('Running')) {
    return 'text-yellow-500'
  }
  
  return statusMap[status] || 'text-gray-500'
}