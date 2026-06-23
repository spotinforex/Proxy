import { useState, useEffect } from 'react'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import ManagementReport from './pages/ManagementReport'
import DataFeed from './pages/DataFeed'
import { setAuthToken } from './api/client'

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(true)
  const [currentPage, setCurrentPage] = useState('dashboard')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setAuthToken('default_token')
  }, [])

  const handleLogin = (token) => {
    setAuthToken(token)
    setIsAuthenticated(true)
    setCurrentPage('dashboard')
  }

  const handleLogout = () => {
    setAuthToken(null)
    setIsAuthenticated(false)
    setCurrentPage('dashboard')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <Layout
      currentPage={currentPage}
      onPageChange={setCurrentPage}
      onLogout={handleLogout}
    >
      <div style={{ display: currentPage === 'dashboard' ? 'block' : 'none' }}>
        <Dashboard />
      </div>
      <div style={{ display: currentPage === 'report' ? 'block' : 'none' }}>
        <ManagementReport />
      </div>
      <div style={{ display: currentPage === 'data' ? 'block' : 'none' }}>
        <DataFeed />
      </div>
    </Layout>
  )
}
