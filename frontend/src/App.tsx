import { Routes, Route } from 'react-router-dom'
import { Toaster } from '@/components/ui/toaster'
import Layout from '@/components/layout/Layout'
import Dashboard from '@/pages/Dashboard'
import PortLists from '@/pages/settings/PortLists'
import ScanTypes from '@/pages/settings/ScanTypes'

function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="targets" element={<div className="p-6">Targets Page (Coming Soon)</div>} />
          <Route path="scans" element={<div className="p-6">Scans Page (Coming Soon)</div>} />
          <Route path="settings">
            <Route path="port-lists" element={<PortLists />} />
            <Route path="scan-types" element={<ScanTypes />} />
          </Route>
        </Route>
      </Routes>
      <Toaster />
    </>
  )
}

export default App