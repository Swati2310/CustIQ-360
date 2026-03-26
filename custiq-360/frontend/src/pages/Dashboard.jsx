import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Users,
  Bell,
  TrendingUp,
  AlertTriangle,
  Search,
  Calculator,
  ChevronRight,
  Clock,
  Landmark,
} from 'lucide-react'
import { getAlerts, getCustomers, searchCustomers } from '../utils/api.js'
import { segmentColor, severityColor } from '../utils/format.js'
import { useCurrency } from '../context/CurrencyContext.jsx'
import AlertBanner from '../components/Alerts/AlertBanner.jsx'
import clsx from 'clsx'

const RECENT_KEY = 'custiq_recent_lookups'

function useDebounce(value, delay) {
  const [d, setD] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setD(value), delay)
    return () => clearTimeout(t)
  }, [value, delay])
  return d
}

function StatCard({ icon: Icon, label, value, sub, color = 'bg-primary-50 text-primary-600' }) {
  return (
    <div className="card p-5 flex items-start gap-4">
      <div className={clsx('w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0', color)}>
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <p className="text-xs text-gray-500 mb-0.5">{label}</p>
        <p className="text-xl font-bold text-gray-900">{value}</p>
        {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { formatCompact, setCurrency } = useCurrency()

  // Reset to INR when landing on dashboard (no customer context)
  useEffect(() => { setCurrency('INR') }, [])
  const [query, setQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searching, setSearching] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)
  const [alerts, setAlerts] = useState([])
  const [alertsLoading, setAlertsLoading] = useState(true)
  const [totalCustomers, setTotalCustomers] = useState(null)
  const [recentLookups, setRecentLookups] = useState([])
  const debouncedQuery = useDebounce(query, 300)

  // Load recent lookups
  useEffect(() => {
    try {
      const stored = JSON.parse(localStorage.getItem(RECENT_KEY) || '[]')
      setRecentLookups(stored)
    } catch {}
  }, [])

  // Load alerts and customer count
  useEffect(() => {
    getAlerts()
      .then((res) => setAlerts(res.data || []))
      .catch(() => setAlerts([]))
      .finally(() => setAlertsLoading(false))

    getCustomers('', 1, 1)
      .then((res) => setTotalCustomers(res.data?.total ?? null))
      .catch(() => setTotalCustomers(null))
  }, [])

  // Search on typed query
  useEffect(() => {
    if (debouncedQuery.trim().length < 2) return
    setSearching(true)
    searchCustomers(debouncedQuery.trim())
      .then((res) => {
        const data = res.data
        const list = Array.isArray(data) ? data : data?.customers || data?.results || []
        setSearchResults(list.slice(0, 8))
        setShowDropdown(true)
      })
      .catch(() => setSearchResults([]))
      .finally(() => setSearching(false))
  }, [debouncedQuery])

  // Load all customers when search is focused with empty query
  const handleSearchFocus = () => {
    if (query.trim().length < 2) {
      setSearching(true)
      getCustomers('', 1, 20)
        .then((res) => {
          const data = res.data
          const list = Array.isArray(data) ? data : data?.customers || data?.results || []
          setSearchResults(list.slice(0, 8))
          setShowDropdown(list.length > 0)
        })
        .catch(() => setSearchResults([]))
        .finally(() => setSearching(false))
    } else if (searchResults.length > 0) {
      setShowDropdown(true)
    }
  }

  const handleSelectCustomer = (c) => {
    const custId = c.customer_id || c.id
    // Save to recent
    const updated = [
      { id: custId, name: c.name || c.full_name, segment: c.segment, phone: c.phone || c.mobile },
      ...recentLookups.filter((r) => r.id !== custId),
    ].slice(0, 5)
    setRecentLookups(updated)
    try { localStorage.setItem(RECENT_KEY, JSON.stringify(updated)) } catch {}
    navigate(`/customer/${custId}`)
    setQuery('')
    setShowDropdown(false)
  }

  const highAlerts = alerts.filter((a) => (a.severity || '').toUpperCase() === 'HIGH')
  const totalAUM = alerts.reduce((sum, a) => sum + (parseFloat(a.portfolio_value || 0)), 0)

  const stats = [
    {
      icon: Users,
      label: 'Total Customers',
      value: totalCustomers !== null ? totalCustomers : '—',
      sub: 'Active relationships',
      color: 'bg-primary-50 text-primary-600',
    },
    {
      icon: Bell,
      label: 'Active Alerts',
      value: alerts.length,
      sub: `${highAlerts.length} high priority`,
      color: highAlerts.length > 0 ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600',
    },
    {
      icon: TrendingUp,
      label: 'Total AUM',
      value: totalAUM > 0 ? formatCompact(totalAUM) : '—',
      sub: 'Assets under management',
      color: 'bg-emerald-50 text-emerald-600',
    },
    {
      icon: AlertTriangle,
      label: 'High-Risk KYC',
      value: alerts.filter((a) => (a.alert_type || '').toLowerCase().includes('kyc')).length,
      sub: 'Needs immediate action',
      color: 'bg-amber-50 text-amber-600',
    },
  ]

  return (
    <div className="max-w-5xl mx-auto px-6 py-8 space-y-8">
      {/* Hero search */}
      <div className="text-center max-w-xl mx-auto">
        <div className="flex items-center justify-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-primary-600 flex items-center justify-center">
            <Landmark className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">CustIQ 360°</h1>
        </div>
        <p className="text-sm text-gray-500 mb-6">
          AI-Powered Relationship Manager Dashboard
        </p>

        {/* Main search */}
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={handleSearchFocus}
            onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
            placeholder="Search by customer name, phone, email or ID..."
            className="w-full pl-12 pr-4 py-3.5 text-sm border-2 border-gray-200 rounded-2xl focus:outline-none focus:border-primary-500 bg-white shadow-sm transition-all text-base"
          />

          {showDropdown && (
            <div className="absolute top-full mt-2 left-0 right-0 bg-white rounded-xl border border-gray-200 shadow-xl z-50 overflow-hidden text-left">
              {searching ? (
                <div className="px-4 py-4 text-sm text-gray-500 flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
                  Searching customers...
                </div>
              ) : searchResults.length === 0 ? (
                <div className="px-4 py-4 text-sm text-gray-500">No customers found</div>
              ) : (
                <ul>
                  {searchResults.map((c) => (
                    <li key={c.customer_id || c.id}>
                      <button
                        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-primary-50 text-left transition-colors"
                        onMouseDown={() => handleSelectCustomer(c)}
                      >
                        <div className="w-9 h-9 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-sm font-bold">
                          {(c.name || c.full_name || '?').charAt(0).toUpperCase()}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-semibold text-gray-900">{c.name || c.full_name}</p>
                          <p className="text-xs text-gray-500">
                            {c.phone || c.mobile} &bull; {c.customer_id || c.id}
                            {c.country_name && <> &bull; {c.country_name}</>}
                          </p>
                        </div>
                        {c.segment && (
                          <span className={clsx('badge text-xs', segmentColor(c.segment))}>
                            {c.segment}
                          </span>
                        )}
                        <ChevronRight className="w-4 h-4 text-gray-400" />
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s) => (
          <StatCard key={s.label} {...s} />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent lookups */}
        <div className="card">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-gray-400" />
              <h2 className="text-sm font-semibold text-gray-800">Recent Lookups</h2>
            </div>
          </div>
          <div className="p-2">
            {recentLookups.length === 0 ? (
              <div className="py-8 text-center text-sm text-gray-400">
                <Users className="w-8 h-8 text-gray-200 mx-auto mb-2" />
                No recent searches yet
              </div>
            ) : (
              <ul className="space-y-0.5">
                {recentLookups.map((r) => (
                  <li key={r.id}>
                    <button
                      onClick={() => navigate(`/customer/${r.id}`)}
                      className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-gray-50 text-left transition-colors"
                    >
                      <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-xs font-bold flex-shrink-0">
                        {(r.name || '?').charAt(0).toUpperCase()}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-800 truncate">{r.name}</p>
                        {r.phone && <p className="text-xs text-gray-400 truncate">{r.phone}</p>}
                      </div>
                      {r.segment && (
                        <span className={clsx('badge text-xs flex-shrink-0', segmentColor(r.segment))}>
                          {r.segment}
                        </span>
                      )}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Alerts preview */}
        <div className="lg:col-span-2 card">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bell className="w-4 h-4 text-gray-400" />
              <h2 className="text-sm font-semibold text-gray-800">Top Alerts</h2>
              {highAlerts.length > 0 && (
                <span className="badge bg-red-100 text-red-700 text-xs">{highAlerts.length} HIGH</span>
              )}
            </div>
            <button
              onClick={() => navigate('/alerts')}
              className="text-xs text-primary-600 hover:text-primary-800 font-medium flex items-center gap-1"
            >
              View all <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="p-4">
            {alertsLoading ? (
              <div className="py-6 flex items-center justify-center">
                <div className="w-5 h-5 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : (
              <AlertBanner alerts={alerts.slice(0, 3)} />
            )}
          </div>
        </div>
      </div>

      {/* Quick links */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <button
          onClick={() => navigate('/simulator')}
          className="card p-5 flex items-center gap-4 hover:border-primary-300 hover:shadow-md transition-all text-left group"
        >
          <div className="w-12 h-12 rounded-xl bg-primary-100 flex items-center justify-center group-hover:bg-primary-600 transition-colors">
            <Calculator className="w-6 h-6 text-primary-600 group-hover:text-white transition-colors" />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-800">Financial Simulator</p>
            <p className="text-xs text-gray-500 mt-0.5">EMI, FD & Loan comparison tools</p>
          </div>
          <ChevronRight className="w-4 h-4 text-gray-400 ml-auto group-hover:text-primary-600 transition-colors" />
        </button>

        <button
          onClick={() => navigate('/alerts')}
          className="card p-5 flex items-center gap-4 hover:border-red-300 hover:shadow-md transition-all text-left group"
        >
          <div className="w-12 h-12 rounded-xl bg-red-100 flex items-center justify-center group-hover:bg-red-500 transition-colors">
            <Bell className="w-6 h-6 text-red-500 group-hover:text-white transition-colors" />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-800">Alerts Center</p>
            <p className="text-xs text-gray-500 mt-0.5">
              {alerts.length} active alerts requiring attention
            </p>
          </div>
          <ChevronRight className="w-4 h-4 text-gray-400 ml-auto group-hover:text-red-500 transition-colors" />
        </button>
      </div>
    </div>
  )
}
