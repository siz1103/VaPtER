import { NavLink } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Server, 
  Scan, 
  Settings,
  Network,
  FileSearch 
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Targets', href: '/targets', icon: Server },
  { name: 'Scans', href: '/scans', icon: Scan },
]

const settingsNavigation = [
  { name: 'Port Lists', href: '/settings/port-lists', icon: Network },
  { name: 'Scan Types', href: '/settings/scan-types', icon: FileSearch },
]

export default function Sidebar() {
  return (
    <aside className="w-64 border-r bg-card/50">
      <nav className="flex flex-col gap-6 p-4">
        <div>
          <h3 className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Main
          </h3>
          <div className="space-y-1">
            {navigation.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground',
                    isActive ? 'bg-accent text-accent-foreground' : 'text-muted-foreground'
                  )
                }
              >
                <item.icon className="h-4 w-4" />
                {item.name}
              </NavLink>
            ))}
          </div>
        </div>
        
        <div>
          <h3 className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Settings
          </h3>
          <div className="space-y-1">
            <NavLink
              to="/settings"
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground',
                  isActive ? 'bg-accent text-accent-foreground' : 'text-muted-foreground'
                )
              }
            >
              <Settings className="h-4 w-4" />
              Settings
            </NavLink>
            
            <div className="ml-4 space-y-1">
              {settingsNavigation.map((item) => (
                <NavLink
                  key={item.name}
                  to={item.href}
                  className={({ isActive }) =>
                    cn(
                      'flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors hover:bg-accent hover:text-accent-foreground',
                      isActive ? 'bg-accent text-accent-foreground' : 'text-muted-foreground'
                    )
                  }
                >
                  <item.icon className="h-3 w-3" />
                  {item.name}
                </NavLink>
              ))}
            </div>
          </div>
        </div>
      </nav>
    </aside>
  )
}