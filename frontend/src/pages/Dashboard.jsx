import { useState, useEffect } from 'react'
import { pipelineAPI } from '../api/client'
import { BarChart3, AlertCircle, TrendingUp, CheckCircle } from 'lucide-react'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      setError('')
      const response = await pipelineAPI.getDataFeed()
      const data = response.data.data
      setStats({
        totalComplaints: data.complaints.length,
        totalActions: data.actions.length,
        resolvedComplaints: data.complaints.filter(c => c.status === 'resolved').length,
        openComplaints: data.complaints.filter(c => c.status === 'open').length,
        escalatedComplaints: data.complaints.filter(c => c.status === 'escalated').length,
      })
    } catch (err) {
      setError('Failed to fetch dashboard data. Please check your connection.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard data...</p>
        </div>
      </div>
    )
  }

  const StatCard = ({ icon: Icon, label, value, color }) => (
    <div className="bg-white rounded-lg shadow p-6 border-l-4" style={{ borderLeftColor: color }}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-600 text-sm">{label}</p>
          <p className="text-3xl font-bold mt-2">{value}</p>
        </div>
        <div className="p-3 rounded-lg" style={{ backgroundColor: color + '20' }}>
          <Icon size={24} style={{ color }} />
        </div>
      </div>
    </div>
  )

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-2">Monitor complaints and resolutions for the past month</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 flex items-start gap-3">
          <AlertCircle size={20} className="mt-0.5 flex-shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
          <StatCard
            icon={BarChart3}
            label="Total Complaints"
            value={stats.totalComplaints}
            color="#0ea5e9"
          />
          <StatCard
            icon={TrendingUp}
            label="Open"
            value={stats.openComplaints}
            color="#f59e0b"
          />
          <StatCard
            icon={CheckCircle}
            label="Resolved"
            value={stats.resolvedComplaints}
            color="#10b981"
          />
          <StatCard
            icon={AlertCircle}
            label="Escalated"
            value={stats.escalatedComplaints}
            color="#ef4444"
          />
          <StatCard
            icon={BarChart3}
            label="Total Actions"
            value={stats.totalActions}
            color="#8b5cf6"
          />
        </div>
      )}

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Quick Stats</h2>
        <div className="space-y-3">
          <div className="flex justify-between items-center pb-3 border-b">
            <span className="text-gray-600">Resolution Rate</span>
            <span className="font-semibold">
              {stats && stats.totalComplaints > 0
                ? ((stats.resolvedComplaints / stats.totalComplaints) * 100).toFixed(1)
                : 0}%
            </span>
          </div>
          <div className="flex justify-between items-center pb-3 border-b">
            <span className="text-gray-600">Escalation Rate</span>
            <span className="font-semibold">
              {stats && stats.totalComplaints > 0
                ? ((stats.escalatedComplaints / stats.totalComplaints) * 100).toFixed(1)
                : 0}%
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600">Average Actions per Complaint</span>
            <span className="font-semibold">
              {stats && stats.totalComplaints > 0
                ? (stats.totalActions / stats.totalComplaints).toFixed(2)
                : 0}
            </span>
          </div>
        </div>
      </div>

      <button
        onClick={fetchData}
        className="mt-6 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition"
      >
        Refresh Data
      </button>
    </div>
  )
}
