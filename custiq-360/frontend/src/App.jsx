import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Layout/Sidebar.jsx'
import TopBar from './components/Layout/TopBar.jsx'
import Dashboard from './pages/Dashboard.jsx'
import CustomerView from './pages/CustomerView.jsx'
import SimulatorPage from './pages/SimulatorPage.jsx'
import AlertsPage from './pages/AlertsPage.jsx'
import LoginPage from './pages/LoginPage.jsx'
import { AuthProvider, useAuth } from './context/AuthContext.jsx'

function AppShell() {
  const { user } = useAuth()

  if (!user) return <LoginPage />

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/customer/:id" element={<CustomerView />} />
            <Route path="/simulator" element={<SimulatorPage />} />
            <Route path="/alerts" element={<AlertsPage />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  )
}
