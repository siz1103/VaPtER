import { Shield } from 'lucide-react'
import CustomerDropdown from './CustomerDropdown'

export default function Header() {
  return (
    <header className="border-b bg-card/50 backdrop-blur">
      <div className="flex h-16 items-center px-4">
        <div className="flex items-center space-x-4">
          <Shield className="h-8 w-8 text-primary" />
          <h1 className="text-xl font-bold">VaPtER</h1>
        </div>
        
        <div className="ml-auto flex items-center space-x-4">
          <CustomerDropdown />
        </div>
      </div>
    </header>
  )
}