import { useState } from 'react'
import { pipelineAPI } from '../api/client'
import { Download, Filter, RefreshCw, AlertCircle } from 'lucide-react'

export default function ManagementReport() {
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [useFilter, setUseFilter] = useState(false)
  const [filters, setFilters] = useState({ complaint_type: '', status: '' })

  const complaintTypes = ['service_issue', 'billing', 'registration', 'other']
  const statuses = ['open', 'resolved', 'escalated']

  const fetchReport = async () => {
    try {
      setLoading(true)
      setError('')

      let response
      if (useFilter && (filters.complaint_type || filters.status)) {
        response = await pipelineAPI.generateFilteredReport(filters)
      } else {
        response = await pipelineAPI.generateReport()
      }

      setReport(response.data)
    } catch (err) {
      setError('Failed to generate report. Please try again.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const downloadReport = () => {
    if (!report) return
    const dataStr = JSON.stringify(report, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `management-report-${new Date().toISOString().split('T')[0]}.json`
    link.click()
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900">Management Report</h1>
        <p className="text-gray-600 mt-2">AI-generated analysis of complaints and actions</p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex items-center gap-4 mb-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={useFilter}
              onChange={(e) => setUseFilter(e.target.checked)}
              className="w-4 h-4"
            />
            <span className="text-gray-700 font-medium">Use Filters</span>
          </label>
          <Filter size={18} className="text-gray-400" />
        </div>

        {useFilter && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Complaint Type (Optional)
              </label>
              <select
                value={filters.complaint_type}
                onChange={(e) => setFilters({ ...filters, complaint_type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">All Types</option>
                {complaintTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Status (Optional)
              </label>
              <select
                value={filters.status}
                onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">All Statuses</option>
                {statuses.map(status => (
                  <option key={status} value={status}>{status}</option>
                ))}
              </select>
            </div>
          </div>
        )}

        <button
          onClick={fetchReport}
          disabled={loading}
          className="mt-4 flex items-center gap-2 px-6 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-400 text-white rounded-lg transition"
        >
          <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
          {loading ? 'Generating...' : 'Generate Report'}
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 flex items-start gap-3">
          <AlertCircle size={20} className="mt-0.5 flex-shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {report && (
        <div className="space-y-6">
          {/* Summary */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-2xl font-semibold mb-4">Report Summary</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-gray-600 text-sm">Complaints Processed</p>
                <p className="text-2xl font-bold text-blue-600">{report.complaints_count}</p>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg">
                <p className="text-gray-600 text-sm">Actions Recorded</p>
                <p className="text-2xl font-bold text-purple-600">{report.actions_count}</p>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <p className="text-gray-600 text-sm">Period</p>
                <p className="text-lg font-bold text-green-600">{report.period}</p>
              </div>
              <div className="bg-orange-50 p-4 rounded-lg">
                <p className="text-gray-600 text-sm">Status</p>
                <p className="text-lg font-bold text-orange-600 capitalize">{report.status}</p>
              </div>
            </div>
          </div>

          {/* Agent Analysis */}
          {report.agent_response && (
            <div className="space-y-6">
              {/* Summary */}
              {report.agent_response.summary && (
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-2xl font-semibold mb-4 text-gray-900">Summary</h2>
                  <p className="text-gray-700 leading-relaxed">{report.agent_response.summary}</p>
                </div>
              )}

              {/* Complaint Breakdown */}
              {report.agent_response['Complaint Breakdown'] && (
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-2xl font-semibold mb-4 text-gray-900">Complaint Breakdown</h2>
                  <div className="text-gray-700 space-y-2">
                    {typeof report.agent_response['Complaint Breakdown'] === 'string' ? (
                      <p className="whitespace-pre-wrap">{report.agent_response['Complaint Breakdown']}</p>
                    ) : (
                      <pre className="bg-gray-50 p-4 rounded overflow-auto text-sm">
                        {JSON.stringify(report.agent_response['Complaint Breakdown'], null, 2)}
                      </pre>
                    )}
                  </div>
                </div>
              )}

              {/* Unresolved Items */}
              {report.agent_response['Unresolved Items'] && (
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-2xl font-semibold mb-4 text-gray-900">Unresolved Items</h2>
                  <div className="text-gray-700 space-y-2">
                    {Array.isArray(report.agent_response['Unresolved Items']) ? (
                      <ul className="space-y-3">
                        {report.agent_response['Unresolved Items'].map((item, idx) => (
                          <li key={idx} className="flex gap-3">
                            <span className="text-red-500 font-semibold">•</span>
                            <span>{typeof item === 'string' ? item : JSON.stringify(item)}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="whitespace-pre-wrap">{report.agent_response['Unresolved Items']}</p>
                    )}
                  </div>
                </div>
              )}

              {/* Program Health */}
              {report.agent_response['Program Health'] && (
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-2xl font-semibold mb-4 text-gray-900">Program Health</h2>
                  <div className="bg-blue-50 border-l-4 border-blue-500 p-4">
                    <p className="text-gray-700">{report.agent_response['Program Health']}</p>
                  </div>
                </div>
              )}

              {/* Recommendations */}
              {report.agent_response['Recommendations'] && (
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-2xl font-semibold mb-4 text-gray-900">Recommendations</h2>
                  <div className="space-y-3">
                    {Array.isArray(report.agent_response['Recommendations']) ? (
                      <ol className="space-y-3 list-decimal list-inside">
                        {report.agent_response['Recommendations'].map((rec, idx) => (
                          <li key={idx} className="text-gray-700">
                            <span className="ml-2">{typeof rec === 'string' ? rec : JSON.stringify(rec)}</span>
                          </li>
                        ))}
                      </ol>
                    ) : (
                      <p className="text-gray-700 whitespace-pre-wrap">{report.agent_response['Recommendations']}</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Download Button */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-2xl font-semibold mb-4">Export Report</h2>
            <p className="text-gray-600 mb-4">Download the complete report data as JSON for further analysis or integration.</p>
            <button
              onClick={downloadReport}
              className="flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg transition font-medium"
            >
              <Download size={18} />
              Download Report as JSON
            </button>
          </div>
        </div>
      )}

      {!report && !loading && (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <p className="text-gray-500 text-lg">Generate a report to see analysis</p>
        </div>
      )}
    </div>
  )
}
