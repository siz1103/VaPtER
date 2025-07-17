import { Routes, Route } from 'react-router-dom'
import { Toaster } from '@/components/ui/toaster'
import Layout from '@/components/layout/Layout'
import Dashboard from '@/pages/Dashboard'

function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="targets" element={<div className="p-6">Targets Page (Coming Soon)</div>} />
          <Route path="scans" element={<div className="p-6">Scans Page (Coming Soon)</div>} />
          <Route path="settings">
            <Route path="port-lists" element={<div className="p-6">Port Lists (Coming Soon)</div>} />
            <Route path="scan-types" element={<div className="p-6">Scan Types (Coming Soon)</div>} />
          </Route>
        </Route>
      </Routes>
      <Toaster />
    </>
  )
}

export default App