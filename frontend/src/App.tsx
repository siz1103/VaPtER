import { Routes, Route } from 'react-router-dom'
import { Toaster } from '@/components/ui/toaster'
import Layout from '@/components/layout/Layout'
import Dashboard from '@/pages/Dashboard'
import Targets from '@/pages/Targets'
import Scans from '@/pages/Scans'
import PortLists from '@/pages/settings/PortLists'
import ScanTypes from '@/pages/settings/ScanTypes'

function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="targets" element={<Targets />} />
          <Route path="scans" element={<Scans />} />
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