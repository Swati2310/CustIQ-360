import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Users, Bell, TrendingUp, AlertTriangle,
  Search, Calculator, ChevronRight, Clock,
  Sparkles, Globe2, Activity, Mic, MicOff,
} from 'lucide-react'
import { getAlerts, getCustomers, searchCustomers } from '../utils/api.js'
import { segmentColor, severityColor } from '../utils/format.js'
import { useCurrency } from '../context/CurrencyContext.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { useVoice } from '../hooks/useVoice.js'
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

function StatCard({ icon: Icon, label, value, sub, gradient, delay = 0 }) {
  return (
    <div
      className="card-hover p-5 flex items-start gap-4 animate-slide-up overflow-hidden relative"
      style={{ animationDelay: `${delay}ms` }}
    >
      {/* Subtle gradient tint in corner */}
      <div className="absolute -top-4 -right-4 w-20 h-20 rounded-full opacity-10 blur-xl" style={{ background: gradient }} />
      <div
        className="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm"
        style={{ background: gradient }}
      >
        <Icon className="w-5 h-5 text-white" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-gray-400 font-medium mb-0.5">{label}</p>
        <p className="text-2xl font-bold text-gray-900 animate-count-up">{value}</p>
        {sub && <p className="text-xs text-gray-400 mt-0.5 truncate">{sub}</p>}
      </div>
    </div>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { formatCompact, setCurrency } = useCurrency()
  const { user } = useAuth()

  useEffect(() => { setCurrency('INR') }, [])

  const [query, setQuery]               = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searching, setSearching]       = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)
  const [alerts, setAlerts]             = useState([])
  const [alertsLoading, setAlertsLoading] = useState(true)
  const [totalCustomers, setTotalCustomers] = useState(null)
  const [recentLookups, setRecentLookups]   = useState([])
  const debouncedQuery = useDebounce(query, 300)

  const { isListening: voiceSearching, isSupported: voiceSupported, start: startVoice, stop: stopVoice } = useVoice({
    onResult: (text) => { setQuery(text); setShowDropdown(true) },
    lang: 'en-US',
  })

  useEffect(() => {
    try {
      const stored = JSON.parse(localStorage.getItem(RECENT_KEY) || '[]')
      setRecentLookups(stored)
    } catch {}
  }, [])

  useEffect(() => {
    getAlerts()
      .then((res) => setAlerts(res.data || []))
      .catch(() => setAlerts([]))
      .finally(() => setAlertsLoading(false))
    getCustomers('', 1, 1)
      .then((res) => setTotalCustomers(res.data?.total ?? null))
      .catch(() => setTotalCustomers(null))
  }, [])

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
  const kycAlerts  = alerts.filter((a) => (a.alert_type || '').toLowerCase().includes('kyc'))
  const totalAUM   = alerts.reduce((sum, a) => sum + (parseFloat(a.portfolio_value || 0)), 0)

  const stats = [
    { icon: Users,         label: 'Total Customers',  value: totalCustomers ?? '—', sub: 'Active relationships',         gradient: 'linear-gradient(135deg,#6366f1,#8b5cf6)', delay: 0   },
    { icon: Activity,      label: 'Active Alerts',     value: alerts.length,          sub: `${highAlerts.length} high priority`, gradient: highAlerts.length > 0 ? 'linear-gradient(135deg,#ef4444,#f97316)' : 'linear-gradient(135deg,#10b981,#34d399)', delay: 80  },
    { icon: TrendingUp,    label: 'Total AUM',         value: totalAUM > 0 ? formatCompact(totalAUM) : '—', sub: 'Assets under management', gradient: 'linear-gradient(135deg,#059669,#10b981)', delay: 160 },
    { icon: AlertTriangle, label: 'High-Risk KYC',     value: kycAlerts.length,       sub: 'Needs immediate action',      gradient: 'linear-gradient(135deg,#f59e0b,#fbbf24)', delay: 240 },
  ]

  return (
    <div className="max-w-5xl mx-auto px-6 py-8 space-y-8">

      {/* Hero section */}
      <div className="animate-fade-in">
        {/* Greeting */}
        <div className="flex items-center gap-2 mb-6">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border"
            style={{ background: 'linear-gradient(135deg,rgba(99,102,241,0.08),rgba(139,92,246,0.08))', borderColor: 'rgba(99,102,241,0.2)', color: '#6366f1' }}>
            <Sparkles className="w-3 h-3" />
            AI-Powered Intelligence
          </div>
        </div>

        <div className="text-center max-w-xl mx-auto">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Good {getGreeting()},{' '}
            <span className="gradient-text">{user?.name?.split(' ')[0] || 'RM'}</span>
          </h1>
          <p className="text-sm text-gray-400 mb-7 flex items-center justify-center gap-1.5">
            <Globe2 className="w-3.5 h-3.5" />
            {user?.branch || 'Global'} · {new Date().toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' })}
          </p>

          {/* Main search */}
          <div className="relative animate-slide-up" style={{ animationDelay: '150ms' }}>
            <div className="absolute -inset-0.5 rounded-2xl opacity-30 blur-sm"
              style={{ background: 'linear-gradient(135deg,#6366f1,#8b5cf6)' }} />
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onFocus={handleSearchFocus}
                onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
                placeholder={voiceSearching ? 'Listening… say a customer name' : 'Search customers by name, phone, email or ID…'}
                className={clsx(
                  'w-full pl-12 pr-14 py-4 text-sm border rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white shadow-sm transition-all',
                  voiceSearching ? 'border-red-300 bg-red-50' : 'border-gray-200'
                )}
              />
              {voiceSupported && (
                <button
                  onClick={voiceSearching ? stopVoice : startVoice}
                  title={voiceSearching ? 'Stop listening' : 'Search by voice'}
                  className={clsx(
                    'absolute right-4 top-1/2 -translate-y-1/2 w-8 h-8 rounded-xl flex items-center justify-center transition-all',
                    voiceSearching
                      ? 'bg-red-500 text-white animate-pulse shadow-md'
                      : 'text-gray-400 hover:text-primary-600 hover:bg-primary-50'
                  )}
                >
                  {voiceSearching ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                </button>
              )}
            </div>

            {showDropdown && (
              <div className="absolute top-full mt-2 left-0 right-0 bg-white rounded-2xl border border-gray-100 shadow-xl z-50 overflow-hidden text-left animate-scale-in">
                {searching ? (
                  <div className="px-4 py-4 text-sm text-gray-500 flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
                    Searching customers…
                  </div>
                ) : searchResults.length === 0 ? (
                  <div className="px-4 py-4 text-sm text-gray-400">No customers found</div>
                ) : (
                  <ul>
                    {searchResults.map((c, i) => (
                      <li key={c.customer_id || c.id}
                        className="animate-fade-in"
                        style={{ animationDelay: `${i * 30}ms` }}>
                        <button
                          className="w-full flex items-center gap-3 px-4 py-3 hover:bg-primary-50 text-left transition-colors"
                          onMouseDown={() => handleSelectCustomer(c)}
                        >
                          <div className="w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold text-white flex-shrink-0"
                            style={{ background: 'linear-gradient(135deg,#6366f1,#8b5cf6)' }}>
                            {(c.name || c.full_name || '?').charAt(0).toUpperCase()}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold text-gray-900">{c.name || c.full_name}</p>
                            <p className="text-xs text-gray-400">
                              {c.phone || c.mobile} · {c.customer_id || c.id}
                              {c.country_name && <> · {c.country_name}</>}
                            </p>
                          </div>
                          {c.segment && (
                            <span className={clsx('badge text-xs', segmentColor(c.segment))}>
                              {c.segment}
                            </span>
                          )}
                          <ChevronRight className="w-4 h-4 text-gray-300 flex-shrink-0" />
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s) => <StatCard key={s.label} {...s} />)}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Recent lookups */}
        <div className="card animate-slide-up" style={{ animationDelay: '200ms' }}>
          <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-primary-50 flex items-center justify-center">
              <Clock className="w-3.5 h-3.5 text-primary-600" />
            </div>
            <h2 className="text-sm font-semibold text-gray-800">Recent Lookups</h2>
          </div>
          <div className="p-2">
            {recentLookups.length === 0 ? (
              <div className="py-8 text-center text-sm text-gray-400">
                <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-3">
                  <Users className="w-5 h-5 text-gray-300" />
                </div>
                No recent searches yet
              </div>
            ) : (
              <ul className="space-y-0.5">
                {recentLookups.map((r, i) => (
                  <li key={r.id} className="animate-slide-in-left" style={{ animationDelay: `${i * 50}ms` }}>
                    <button
                      onClick={() => navigate(`/customer/${r.id}`)}
                      className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-gray-50 text-left transition-all group"
                    >
                      <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
                        style={{ background: 'linear-gradient(135deg,#6366f1,#8b5cf6)' }}>
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
        <div className="lg:col-span-2 card animate-slide-up" style={{ animationDelay: '280ms' }}>
          <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-red-50 flex items-center justify-center">
                <Bell className="w-3.5 h-3.5 text-red-500" />
              </div>
              <h2 className="text-sm font-semibold text-gray-800">Top Alerts</h2>
              {highAlerts.length > 0 && (
                <span className="badge bg-red-100 text-red-600 text-xs animate-pulse">{highAlerts.length} HIGH</span>
              )}
            </div>
            <button
              onClick={() => navigate('/alerts')}
              className="text-xs text-primary-600 hover:text-primary-800 font-medium flex items-center gap-1 transition-colors"
            >
              View all <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="p-4">
            {alertsLoading ? (
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="skeleton h-14 w-full" />
                ))}
              </div>
            ) : (
              <AlertBanner alerts={alerts.slice(0, 3)} />
            )}
          </div>
        </div>
      </div>

      {/* Quick links */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 animate-slide-up" style={{ animationDelay: '360ms' }}>
        <button
          onClick={() => navigate('/simulator')}
          className="card p-5 flex items-center gap-4 hover:shadow-md hover:-translate-y-0.5 transition-all text-left group overflow-hidden relative"
        >
          <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
            style={{ background: 'linear-gradient(135deg,rgba(99,102,241,0.03),rgba(139,92,246,0.06))' }} />
          <div className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 transition-all duration-200 group-hover:scale-110"
            style={{ background: 'linear-gradient(135deg,#6366f1,#8b5cf6)' }}>
            <Calculator className="w-6 h-6 text-white" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-gray-800">Financial Simulator</p>
            <p className="text-xs text-gray-400 mt-0.5">EMI, FD & Loan comparison tools</p>
          </div>
          <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-primary-500 group-hover:translate-x-1 transition-all" />
        </button>

        <button
          onClick={() => navigate('/alerts')}
          className="card p-5 flex items-center gap-4 hover:shadow-md hover:-translate-y-0.5 transition-all text-left group overflow-hidden relative"
        >
          <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
            style={{ background: 'linear-gradient(135deg,rgba(239,68,68,0.03),rgba(249,115,22,0.06))' }} />
          <div className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 transition-all duration-200 group-hover:scale-110"
            style={{ background: 'linear-gradient(135deg,#ef4444,#f97316)' }}>
            <Bell className="w-6 h-6 text-white" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-gray-800">Alerts Center</p>
            <p className="text-xs text-gray-400 mt-0.5">
              {alerts.length} active alerts requiring attention
            </p>
          </div>
          <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-red-500 group-hover:translate-x-1 transition-all" />
        </button>
      </div>
    </div>
  )
}

function getGreeting() {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
}
