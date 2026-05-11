import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Search, Bell, X, User, LogOut, Mic, MicOff } from 'lucide-react'
import { searchCustomers, getCustomers, getAlerts } from '../../utils/api.js'
import { getInitials, segmentColor } from '../../utils/format.js'
import { useCurrency } from '../../context/CurrencyContext.jsx'
import { useAuth } from '../../context/AuthContext.jsx'
import { useVoice } from '../../hooks/useVoice.js'
import clsx from 'clsx'

function useDebounce(value, delay) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  return debounced
}

export default function TopBar() {
  const navigate = useNavigate()
  const location = useLocation()
  const { currency } = useCurrency()
  const { user, logout } = useAuth()
  const showCurrencyBadge = location.pathname !== '/'

  const { isListening: voiceSearching, isSupported: voiceSupported, start: startVoice, stop: stopVoice } = useVoice({
    onResult: (text) => { setQuery(text); setShowDropdown(true) },
    lang: 'en-US',
  })

  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [showDropdown, setShowDropdown] = useState(false)
  const [searching, setSearching] = useState(false)
  const [alertCount, setAlertCount] = useState(0)
  const dropdownRef = useRef(null)
  const inputRef = useRef(null)
  const debouncedQuery = useDebounce(query, 300)

  // Fetch alert count
  useEffect(() => {
    getAlerts()
      .then((res) => {
        const alerts = res.data || []
        const high = alerts.filter((a) => (a.severity || '').toUpperCase() === 'HIGH')
        setAlertCount(high.length || alerts.length)
      })
      .catch(() => {})
  }, [])

  // Search customers on typed query
  useEffect(() => {
    if (debouncedQuery.trim().length < 2) {
      // Don't clear results here — focus handler may have loaded all customers
      return
    }
    setSearching(true)
    searchCustomers(debouncedQuery.trim())
      .then((res) => {
        const data = res.data
        const list = Array.isArray(data) ? data : data?.customers || data?.results || []
        setResults(list.slice(0, 8))
        setShowDropdown(true)
      })
      .catch(() => setResults([]))
      .finally(() => setSearching(false))
  }, [debouncedQuery])

  // Load all customers when search is focused with empty query
  const handleFocus = useCallback(() => {
    if (query.trim().length < 2) {
      setSearching(true)
      getCustomers('', 1, 20)
        .then((res) => {
          const data = res.data
          const list = Array.isArray(data) ? data : data?.customers || data?.results || []
          setResults(list.slice(0, 8))
          setShowDropdown(list.length > 0)
        })
        .catch(() => setResults([]))
        .finally(() => setSearching(false))
    } else if (results.length > 0) {
      setShowDropdown(true)
    }
  }, [query, results])

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleSelect = useCallback(
    (customer) => {
      navigate(`/customer/${customer.customer_id || customer.id}`)
      setQuery('')
      setShowDropdown(false)
      setResults([])
    },
    [navigate]
  )

  const clearSearch = () => {
    setQuery('')
    setResults([])
    setShowDropdown(false)
    inputRef.current?.focus()
  }

  return (
    <header className="h-14 glass border-b border-gray-100 flex items-center px-6 gap-4 flex-shrink-0 z-30 shadow-sm animate-fade-in">
      {/* Search */}
      <div className="flex-1 max-w-xl relative" ref={dropdownRef}>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={handleFocus}
            placeholder={voiceSearching ? 'Listening…' : 'Search customers by name, phone or email…'}
            className={clsx(
              'w-full pl-10 py-2 text-sm border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all',
              voiceSearching
                ? 'pr-8 border-red-300 bg-red-50'
                : query ? 'pr-14' : 'pr-8',
              !voiceSearching && 'bg-gray-50 focus:bg-white'
            )}
          />
          {/* Voice / Clear buttons */}
          <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
            {voiceSupported && (
              <button
                onClick={voiceSearching ? stopVoice : startVoice}
                title={voiceSearching ? 'Stop' : 'Voice search'}
                className={clsx(
                  'w-6 h-6 rounded-lg flex items-center justify-center transition-all',
                  voiceSearching
                    ? 'text-red-500 animate-pulse'
                    : 'text-gray-400 hover:text-primary-600'
                )}
              >
                {voiceSearching ? <MicOff className="w-3.5 h-3.5" /> : <Mic className="w-3.5 h-3.5" />}
              </button>
            )}
            {query && !voiceSearching && (
              <button onClick={clearSearch} className="text-gray-400 hover:text-gray-600">
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>

        {/* Dropdown */}
        {showDropdown && (
          <div className="absolute top-full mt-1 left-0 right-0 bg-white rounded-2xl border border-gray-100 shadow-xl z-50 overflow-hidden animate-scale-in">
            {searching ? (
              <div className="px-4 py-3 text-sm text-gray-500 flex items-center gap-2">
                <div className="w-3.5 h-3.5 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
                Searching...
              </div>
            ) : results.length === 0 ? (
              <div className="px-4 py-3 text-sm text-gray-500">No customers found</div>
            ) : (
              <>
                {!query && (
                  <div className="px-4 py-2 text-xs text-gray-400 bg-gray-50 border-b border-gray-100">
                    All customers
                  </div>
                )}
                <ul>
                  {results.map((c) => (
                    <li key={c.customer_id || c.id}>
                      <button
                        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50 text-left transition-colors"
                        onClick={() => handleSelect(c)}
                      >
                        <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-xs font-bold flex-shrink-0">
                          {getInitials(c.name || c.full_name)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {c.name || c.full_name}
                          </p>
                          <p className="text-xs text-gray-500 truncate">
                            {c.phone || c.mobile} &bull; {c.customer_id || c.id}
                            {c.country_name && <> &bull; {c.country_name}</>}
                          </p>
                        </div>
                        {c.segment && (
                          <span className={clsx('badge text-xs', segmentColor(c.segment))}>
                            {c.segment}
                          </span>
                        )}
                      </button>
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>
        )}
      </div>

      {/* Right side */}
      <div className="flex items-center gap-3 ml-auto">
        {/* Active currency badge — hidden on dashboard */}
        {showCurrencyBadge && (
          <div
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-gray-100 text-gray-600 text-xs font-medium"
            title={`Displaying amounts in ${currency.name}`}
          >
            <span>{currency.symbol}</span>
            <span>{currency.code}</span>
          </div>
        )}

        {/* Alerts bell */}
        <button
          onClick={() => navigate('/alerts')}
          className="relative p-2 rounded-lg hover:bg-gray-100 transition-colors"
          title="View Alerts"
        >
          <Bell className="w-5 h-5 text-gray-500" />
          {alertCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center font-bold leading-none">
              {alertCount > 9 ? '9+' : alertCount}
            </span>
          )}
        </button>

        {/* RM identity + logout */}
        <div className="flex items-center gap-2 pl-3 border-l border-gray-200">
          <div className="w-7 h-7 rounded-full bg-primary-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
            {user ? getInitials(user.name) : <User className="w-4 h-4" />}
          </div>
          <div className="hidden md:block">
            <p className="text-xs font-semibold text-gray-700 leading-tight">{user?.name || 'RM Portal'}</p>
            <p className="text-xs text-gray-400 leading-tight">{user?.id} &bull; {user?.country}</p>
          </div>
          <button
            onClick={logout}
            title="Sign out"
            className="ml-1 p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  )
}
