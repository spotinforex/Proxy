import { BarChart3, Database, Home } from 'lucide-react'

export default function Layout({ currentPage, onPageChange, onLogout, children }) {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Home },
    { id: 'report', label: 'Management Report', icon: BarChart3 },
    { id: 'data', label: 'Data Feed', icon: Database },
  ]

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-primary-700 text-white shadow-lg">
        <div className="p-6 border-b border-primary-600">
          <h1 className="text-2xl font-bold">Proxy</h1>
          <p className="text-sm text-primary-100 mt-1">MCIPP Dashboard</p>
        </div>

        <nav className="mt-8 space-y-2 px-4">
          {menuItems.map((item) => {
            const Icon = item.icon
            return (
              <button
                key={item.id}
                onClick={() => onPageChange(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition ${
                  currentPage === item.id
                    ? 'bg-primary-600 text-white'
                    : 'text-primary-100 hover:bg-primary-600'
                }`}
              >
                <Icon size={20} />
                <span>{item.label}</span>
              </button>
            )
          })}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="p-8">
          {children}
        </div>
      </main>
    </div>
  )
}
