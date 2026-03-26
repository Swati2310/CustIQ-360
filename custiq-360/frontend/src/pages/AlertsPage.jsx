import React, { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Bell,
  Clock,
  Banknote,
  AlertTriangle,
  User,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  ArrowUpDown,
  Filter,
  RefreshCw,
  CheckCircle,
} from 'lucide-react'
import { getAlerts } from '../utils/api.js'
import { formatDate, severityColor } from '../utils/format.js'
import clsx from 'clsx'

const TYPE_FILTERS = [
  { key: 'ALL', label: 'All Types' },
  { key: 'KYC', label: 'KYC' },
  { key: 'FD', label: 'FD Maturity' },
  { key: 'DORMANT', label: 'Dormant' },
  { key: 'LOAN', label: 'Loan / EMI' },
]

const SEVERITY_FILTERS = [
  { key: 'ALL', label: 'All Severity' },
  { key: 'HIGH', label: 'High', color: 'text-red-600' },
  { key: 'MEDIUM', label: 'Medium', color: 'text-amber-600' },
  { key: 'LOW', label: 'Low', color: 'text-blue-600' },
]

const SORT_OPTIONS = [
  { key: 'date_desc', label: 'Newest First' },
  { key: 'date_asc', label: 'Oldest First' },
  { key: 'severity_desc', label: 'Severity: High to Low' },
]

function getAlertIcon(type) {
  const t = (type || '').toLowerCase()
  if (t.includes('kyc') || t.includes('document')) return Clock
  if (t.includes('fd') || t.includes('fixed') || t.includes('deposit')) return Banknote
  if (t.includes('churn') || t.includes('dormant') || t.includes('risk')) return AlertTriangle
  if (t.includes('loan') || t.includes('emi')) return Banknote
  return Bell
}

function matchesTypeFilter(alert, typeFilter) {
  if (typeFilter === 'ALL') return true
  const t = (alert.alert_type || alert.type || '').toUpperCase()
  if (typeFilter === 'KYC') return t.includes('KYC') || t.includes('DOCUMENT')
  if (typeFilter === 'FD') return t.includes('FD') || t.includes('FIXED') || t.includes('DEPOSIT') || t.includes('MATURITY')
  if (typeFilter === 'DORMANT') return t.includes('DORMANT') || t.includes('CHURN')
  if (typeFilter === 'LOAN') return t.includes('LOAN') || t.includes('EMI') || t.includes('NPA')
  return true
}

const severityOrder = { HIGH: 3, MEDIUM: 2, LOW: 1 }

function AlertCard({ alert }) {
  const [expanded, setExpanded] = useState(false)
  const navigate = useNavigate()
  const colors = severityColor(alert.severity)
  const Icon = getAlertIcon(alert.alert_type || alert.type)
  const custId = alert.customer_id || alert.id

  return (
    <div
      className={clsx(
        'card border transition-all',
        colors.border,
        expanded ? 'shadow-md' : ''
      )}
    >
      <div
        className={clsx('p-4 cursor-pointer', colors.bg)}
        onClick={() => setExpanded((v) => !v)}
      >
        <div className="flex items-start gap-3">
          {/* Icon */}
          <div className={clsx('w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 border', colors.border, 'bg-white')}>
            <Icon className={clsx('w-4.5 h-4.5', colors.text)} size={18} />
          </div>

          {/* Main info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <span className={clsx('badge text-xs', colors.badge)}>
                {(alert.severity || 'LOW').toUpperCase()}
              </span>
              {(alert.alert_type || alert.type) && (
                <span className="badge bg-white/80 text-gray-600 border border-gray-200 text-xs">
                  {(alert.alert_type || alert.type).replace(/_/g, ' ')}
                </span>
              )}
              {alert.due_date && (
                <span className="text-xs text-gray-500 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {formatDate(alert.due_date)}
                </span>
              )}
            </div>

            <p className={clsx('text-sm font-semibold', colors.text)}>
              {alert.customer_name || 'Customer'}
            </p>
            <p className="text-xs text-gray-600 mt-0.5 leading-relaxed line-clamp-2">
              {alert.message || alert.description || alert.alert_message}
            </p>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 flex-shrink-0">
            {custId && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  navigate(`/customer/${custId}`)
                }}
                className="flex items-center gap-1 text-xs font-medium text-primary-600 hover:text-primary-800 bg-white border border-primary-200 hover:border-primary-400 px-2.5 py-1.5 rounded-lg transition-all"
              >
                <User className="w-3 h-3" />
                View
                <ChevronRight className="w-3 h-3" />
              </button>
            )}
            <button className="p-1.5 rounded-lg hover:bg-white/50 transition-colors">
              {expanded ? (
                <ChevronUp className="w-4 h-4 text-gray-500" />
              ) : (
                <ChevronDown className="w-4 h-4 text-gray-500" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className="px-4 py-3 border-t border-gray-100 bg-white space-y-2">
          {alert.customer_id && (
            <div className="flex gap-2 text-xs">
              <span className="text-gray-500">Customer ID:</span>
              <span className="font-mono font-medium text-gray-700">{alert.customer_id}</span>
            </div>
          )}
          {alert.message && (
            <div className="flex gap-2 text-xs">
              <span className="text-gray-500 flex-shrink-0">Message:</span>
              <span className="text-gray-700">{alert.message}</span>
            </div>
          )}
          {alert.created_at && (
            <div className="flex gap-2 text-xs">
              <span className="text-gray-500">Created:</span>
              <span className="text-gray-700">{formatDate(alert.created_at)}</span>
            </div>
          )}
          {alert.due_date && (
            <div className="flex gap-2 text-xs">
              <span className="text-gray-500">Due Date:</span>
              <span className="text-gray-700 font-medium">{formatDate(alert.due_date)}</span>
            </div>
          )}
          <div className="pt-2 flex gap-2">
            <button
              onClick={() => custId && navigate(`/customer/${custId}`)}
              className="btn-primary text-xs"
            >
              Open Customer Profile
            </button>
            <button className="btn-secondary text-xs">Mark as Resolved</button>
          </div>
        </div>
      )}
    </div>
  )
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [typeFilter, setTypeFilter] = useState('ALL')
  const [severityFilter, setSeverityFilter] = useState('ALL')
  const [sortKey, setSortKey] = useState('severity_desc')

  useEffect(() => {
    setLoading(true)
    getAlerts()
      .then((res) => setAlerts(res.data || []))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  const filtered = useMemo(() => {
    let list = [...alerts]

    // Type filter
    list = list.filter((a) => matchesTypeFilter(a, typeFilter))

    // Severity filter
    if (severityFilter !== 'ALL') {
      list = list.filter(
        (a) => (a.severity || '').toUpperCase() === severityFilter
      )
    }

    // Sort
    if (sortKey === 'date_desc') {
      list.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
    } else if (sortKey === 'date_asc') {
      list.sort((a, b) => new Date(a.created_at || 0) - new Date(b.created_at || 0))
    } else if (sortKey === 'severity_desc') {
      list.sort((a, b) => {
        const sa = severityOrder[(a.severity || 'LOW').toUpperCase()] || 1
        const sb = severityOrder[(b.severity || 'LOW').toUpperCase()] || 1
        return sb - sa
      })
    }

    return list
  }, [alerts, typeFilter, severityFilter, sortKey])

  const counts = useMemo(() => {
    const high = alerts.filter((a) => (a.severity || '').toUpperCase() === 'HIGH').length
    const medium = alerts.filter((a) => (a.severity || '').toUpperCase() === 'MEDIUM').length
    const low = alerts.filter((a) => (a.severity || '').toUpperCase() === 'LOW').length
    return { high, medium, low }
  }, [alerts])

  const refetch = () => {
    setLoading(true)
    setError(null)
    getAlerts()
      .then((res) => setAlerts(res.data || []))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Alerts Center</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Monitor customer KYC, FD maturity, loan EMI and churn alerts
          </p>
        </div>
        <button
          onClick={refetch}
          className="btn-secondary flex items-center gap-1.5"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh
        </button>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        <div className="card p-4 text-center border-t-2 border-red-400">
          <p className="text-2xl font-bold text-red-600">{counts.high}</p>
          <p className="text-xs text-gray-500 mt-0.5">High Priority</p>
        </div>
        <div className="card p-4 text-center border-t-2 border-amber-400">
          <p className="text-2xl font-bold text-amber-600">{counts.medium}</p>
          <p className="text-xs text-gray-500 mt-0.5">Medium Priority</p>
        </div>
        <div className="card p-4 text-center border-t-2 border-blue-400">
          <p className="text-2xl font-bold text-blue-600">{counts.low}</p>
          <p className="text-xs text-gray-500 mt-0.5">Low Priority</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 mb-5">
        {/* Type filter */}
        <div className="flex items-center gap-1">
          <Filter className="w-3.5 h-3.5 text-gray-400" />
          <div className="flex rounded-lg border border-gray-200 overflow-hidden bg-white">
            {TYPE_FILTERS.map((f) => (
              <button
                key={f.key}
                onClick={() => setTypeFilter(f.key)}
                className={clsx(
                  'px-3 py-1.5 text-xs font-medium transition-colors',
                  typeFilter === f.key
                    ? 'bg-primary-600 text-white'
                    : 'text-gray-600 hover:bg-gray-50'
                )}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        {/* Severity filter */}
        <div className="flex rounded-lg border border-gray-200 overflow-hidden bg-white">
          {SEVERITY_FILTERS.map((f) => (
            <button
              key={f.key}
              onClick={() => setSeverityFilter(f.key)}
              className={clsx(
                'px-3 py-1.5 text-xs font-medium transition-colors',
                severityFilter === f.key
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-600 hover:bg-gray-50'
              )}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Sort */}
        <div className="flex items-center gap-1.5 ml-auto">
          <ArrowUpDown className="w-3.5 h-3.5 text-gray-400" />
          <select
            value={sortKey}
            onChange={(e) => setSortKey(e.target.value)}
            className="text-xs border border-gray-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white text-gray-700"
          >
            {SORT_OPTIONS.map((o) => (
              <option key={o.key} value={o.key}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Alert count */}
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs text-gray-500">
          Showing <span className="font-semibold text-gray-700">{filtered.length}</span> of{' '}
          <span className="font-semibold text-gray-700">{alerts.length}</span> alerts
        </p>
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <div className="w-10 h-10 border-2 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
            <p className="text-sm text-gray-500">Loading alerts...</p>
          </div>
        </div>
      ) : error ? (
        <div className="card p-8 text-center">
          <AlertTriangle className="w-10 h-10 text-red-400 mx-auto mb-3" />
          <p className="text-sm font-medium text-gray-700">{error}</p>
          <button onClick={refetch} className="btn-primary mt-4">
            Try Again
          </button>
        </div>
      ) : filtered.length === 0 ? (
        <div className="card p-12 text-center">
          <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-3" />
          <p className="text-sm font-semibold text-gray-700">No alerts match your filters</p>
          <p className="text-xs text-gray-500 mt-1">Try adjusting the filter criteria</p>
          <button
            onClick={() => { setTypeFilter('ALL'); setSeverityFilter('ALL') }}
            className="btn-secondary mt-4"
          >
            Clear Filters
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((alert, idx) => (
            <AlertCard key={alert.id || alert.alert_id || idx} alert={alert} />
          ))}
        </div>
      )}
    </div>
  )
}
