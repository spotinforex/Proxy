import { useState } from 'react'
import { Lock } from 'lucide-react'

export default function Login({ onLogin }) {
  const [token, setToken] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!token.trim()) {
      setError('Please enter an API token')
      return
    }
    setLoading(true)
    setError('')

    // Simulate token validation
    setTimeout(() => {
      onLogin(token)
      setLoading(false)
    }, 500)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-600 to-primary-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-lg shadow-xl p-8">
          <div className="flex justify-center mb-6">
            <div className="bg-primary-100 p-4 rounded-lg">
              <Lock className="text-primary-600" size={32} />
            </div>
          </div>

          <h1 className="text-3xl font-bold text-center mb-2">Proxy Dashboard</h1>
          <p className="text-gray-600 text-center mb-8">
            MCIPP Complaint Resolution System
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="token" className="block text-sm font-medium text-gray-700 mb-2">
                API Token
              </label>
              <input
                id="token"
                type="password"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="Enter your webhook token"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Get your token from the WEBHOOK_TOKEN environment variable
              </p>
            </div>

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary-600 hover:bg-primary-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-lg transition"
            >
              {loading ? 'Authenticating...' : 'Login'}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-xs text-gray-500 text-center">
              This is an internal dashboard for MCIPP staff to monitor complaint resolution metrics.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
