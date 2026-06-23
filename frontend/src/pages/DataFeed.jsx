import { useState, useEffect } from 'react'
import { pipelineAPI } from '../api/client'
import { AlertCircle, Search, ChevronDown } from 'lucide-react'

export default function DataFeed() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [expandedComplaint, setExpandedComplaint] = useState(null)
  const [activeTab, setActiveTab] = useState('complaints')

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      setError('')
      const response = await pipelineAPI.getDataFeed()
      setData(response.data.data)
    } catch (err) {
      setError('Failed to fetch data feed. Please check your connection.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const filterComplaintsBySearch = () => {
    if (!data?.complaints) return []
    return data.complaints.filter(complaint =>
      complaint.business_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      complaint.complaint_type?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      complaint.message?.toLowerCase().includes(searchTerm.toLowerCase())
    )
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'resolved':
        return 'bg-green-100 text-green-800'
      case 'open':
        return 'bg-yellow-100 text-yellow-800'
      case 'escalated':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading data feed...</p>
        </div>
      </div>
    )
  }

  const complaints = filterComplaintsBySearch()

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900">Data Feed</h1>
        <p className="text-gray-600 mt-2">Raw complaints and actions from the past month</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 flex items-start gap-3">
          <AlertCircle size={20} className="mt-0.5 flex-shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-4 mb-6 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('complaints')}
          className={`px-4 py-2 font-medium transition ${
            activeTab === 'complaints'
              ? 'text-primary-600 border-b-2 border-primary-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Complaints ({data?.complaints?.length || 0})
        </button>
        <button
          onClick={() => setActiveTab('actions')}
          className={`px-4 py-2 font-medium transition ${
            activeTab === 'actions'
              ? 'text-primary-600 border-b-2 border-primary-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Actions ({data?.actions?.length || 0})
        </button>
      </div>

      {/* Complaints Tab */}
      {activeTab === 'complaints' && (
        <div>
          {data?.complaints && data.complaints.length > 0 && (
            <div className="mb-4">
              <div className="relative">
                <Search className="absolute left-3 top-3 text-gray-400" size={18} />
                <input
                  type="text"
                  placeholder="Search by business name, type, or message..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <p className="text-sm text-gray-500 mt-2">
                Showing {complaints.length} of {data.complaints.length} complaints
              </p>
            </div>
          )}

          <div className="space-y-3">
            {complaints.length > 0 ? (
              complaints.map((complaint) => (
                <div key={complaint.id} className="bg-white rounded-lg shadow border border-gray-200">
                  <button
                    onClick={() =>
                      setExpandedComplaint(
                        expandedComplaint === complaint.id ? null : complaint.id
                      )
                    }
                    className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition"
                  >
                    <div className="flex items-center gap-4 flex-1 text-left">
                      <div>
                        <h3 className="font-semibold text-gray-900">
                          {complaint.business_name}
                        </h3>
                        <p className="text-sm text-gray-600">ID: {complaint.id}</p>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(complaint.status)}`}>
                        {complaint.status}
                      </span>
                      <span className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-medium">
                        {complaint.complaint_type}
                      </span>
                    </div>
                    <ChevronDown
                      size={18}
                      className={`transition ${expandedComplaint === complaint.id ? 'rotate-180' : ''}`}
                    />
                  </button>

                  {expandedComplaint === complaint.id && (
                    <div className="border-t border-gray-200 p-4 bg-gray-50 space-y-3">
                      <div>
                        <p className="text-sm font-medium text-gray-700">Message</p>
                        <p className="text-gray-600 mt-1">{complaint.message}</p>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm font-medium text-gray-700">WhatsApp</p>
                          <p className="text-gray-600">{complaint.whatsapp_number}</p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-700">Created</p>
                          <p className="text-gray-600">
                            {new Date(complaint.first_response_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      {complaint.resolved_at && (
                        <div>
                          <p className="text-sm font-medium text-gray-700">Resolution Method</p>
                          <p className="text-gray-600">{complaint.resolution_method}</p>
                        </div>
                      )}
                      {complaint.assigned_to && (
                        <div>
                          <p className="text-sm font-medium text-gray-700">Assigned To</p>
                          <p className="text-gray-600">{complaint.assigned_to}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
                <p>No complaints match your search</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Actions Tab */}
      {activeTab === 'actions' && (
        <div className="space-y-3">
          {data?.actions && data.actions.length > 0 ? (
            data.actions.map((action) => (
              <div key={action.id} className="bg-white rounded-lg shadow p-4 border border-gray-200">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold text-gray-900">
                      Complaint ID: {action.complaint_id}
                    </p>
                    <p className="text-sm text-gray-600 mt-1">
                      <span className="font-medium">Action:</span> {action.action_type}
                    </p>
                    {action.outcome && (
                      <p className="text-sm text-gray-600 mt-1">
                        <span className="font-medium">Outcome:</span> {action.outcome}
                      </p>
                    )}
                    {action.staff_notified && (
                      <p className="text-sm text-gray-600 mt-1">
                        <span className="font-medium">Staff Notified:</span> {action.staff_notified}
                      </p>
                    )}
                  </div>
                  <p className="text-xs text-gray-500">
                    {new Date(action.taken_at).toLocaleString()}
                  </p>
                </div>
              </div>
            ))
          ) : (
            <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
              <p>No actions recorded in the past month</p>
            </div>
          )}
        </div>
      )}

      <button
        onClick={fetchData}
        className="mt-6 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition"
      >
        Refresh Data
      </button>
    </div>
  )
}
