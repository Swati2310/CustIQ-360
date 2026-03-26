import React from 'react'
import { Clock, Banknote, AlertTriangle, Bell, ChevronRight, CheckCircle } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { formatDate, severityColor } from '../../utils/format.js'
import clsx from 'clsx'

function getAlertIcon(type) {
  const t = (type || '').toLowerCase()
  if (t.includes('kyc') || t.includes('document')) return Clock
  if (t.includes('fd') || t.includes('fixed') || t.includes('deposit')) return Banknote
  if (t.includes('churn') || t.includes('dormant') || t.includes('risk')) return AlertTriangle
  if (t.includes('loan') || t.includes('emi')) return Banknote
  return Bell
}

export default function AlertBanner({ alerts = [] }) {
  const navigate = useNavigate()

  if (!alerts || alerts.length === 0) {
    return (
      <div className="card p-6 flex flex-col items-center text-center">
        <div className="w-12 h-12 rounded-xl bg-green-100 flex items-center justify-center mb-3">
          <CheckCircle className="w-6 h-6 text-green-600" />
        </div>
        <p className="text-sm font-semibold text-gray-700">No active alerts</p>
        <p className="text-xs text-gray-400 mt-1">All customers are in good standing</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {alerts.map((alert, idx) => {
        const colors = severityColor(alert.severity)
        const Icon = getAlertIcon(alert.alert_type || alert.type)
        const custId = alert.customer_id || alert.id

        return (
          <div
            key={alert.id || alert.alert_id || idx}
            className={clsx(
              'flex items-start gap-3 px-4 py-3.5 rounded-xl border transition-all hover:shadow-sm',
              colors.bg,
              colors.border
            )}
          >
            {/* Icon */}
            <div className={clsx('w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5', colors.bg, 'border', colors.border)}>
              <Icon className={clsx('w-4 h-4', colors.text)} />
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap mb-0.5">
                <span className={clsx('badge text-xs', colors.badge)}>
                  {(alert.severity || 'LOW').toUpperCase()}
                </span>
                {(alert.alert_type || alert.type) && (
                  <span className="text-xs text-gray-500 bg-white/70 px-2 py-0.5 rounded-full border border-gray-200">
                    {(alert.alert_type || alert.type).replace(/_/g, ' ')}
                  </span>
                )}
              </div>
              <p className={clsx('text-sm font-semibold', colors.text)}>
                {alert.customer_name || 'Customer'}
              </p>
              <p className="text-xs text-gray-600 mt-0.5 leading-relaxed">
                {alert.message || alert.description || alert.alert_message}
              </p>
              {alert.due_date && (
                <p className="text-xs text-gray-400 mt-1">
                  Due: {formatDate(alert.due_date)}
                </p>
              )}
            </div>

            {/* View customer link */}
            {custId && (
              <button
                onClick={() => navigate(`/customer/${custId}`)}
                className="flex items-center gap-1 text-xs font-medium text-primary-600 hover:text-primary-800 flex-shrink-0 mt-1 whitespace-nowrap"
              >
                View
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        )
      })}
    </div>
  )
}
