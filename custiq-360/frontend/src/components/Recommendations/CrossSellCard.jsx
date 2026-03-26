import React from 'react'
import { Sparkles, ShoppingBag, CheckCircle, AlertTriangle, ChevronRight } from 'lucide-react'
import clsx from 'clsx'

const priorityConfig = {
  high: { badge: 'bg-red-100 text-red-700 border border-red-200', label: 'High Priority' },
  medium: { badge: 'bg-amber-100 text-amber-700 border border-amber-200', label: 'Medium' },
  low: { badge: 'bg-gray-100 text-gray-600 border border-gray-200', label: 'Low' },
}

const productIcons = {
  'fixed deposit': '🏦',
  fd: '🏦',
  'mutual fund': '📈',
  mf: '📈',
  insurance: '🛡️',
  loan: '💰',
  'credit card': '💳',
  ppf: '🪙',
  default: '💼',
}

function getProductEmoji(name) {
  const lower = (name || '').toLowerCase()
  for (const [key, emoji] of Object.entries(productIcons)) {
    if (lower.includes(key)) return emoji
  }
  return productIcons.default
}

export default function CrossSellCard({ recommendations = [] }) {
  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="card p-5 text-center">
        <div className="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center mx-auto mb-2">
          <Sparkles className="w-5 h-5 text-gray-300" />
        </div>
        <p className="text-sm text-gray-500">No recommendations available</p>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2">
        <Sparkles className="w-4 h-4 text-primary-600" />
        <h3 className="text-sm font-semibold text-gray-800">Cross-Sell Recommendations</h3>
        <span className="badge bg-primary-50 text-primary-700 text-xs">{recommendations.length}</span>
      </div>

      {/* Horizontal scrollable strip */}
      <div className="flex gap-3 p-4 overflow-x-auto pb-4">
        {recommendations.map((rec, idx) => {
          const priority = (rec.priority || 'medium').toLowerCase()
          const pConf = priorityConfig[priority] || priorityConfig.medium
          const isApproved =
            rec.compliance_status === 'approved' ||
            rec.compliance_status === 'APPROVED' ||
            rec.compliance === true ||
            rec.compliant === true

          return (
            <div
              key={rec.id || idx}
              className="flex-shrink-0 w-56 border border-gray-200 rounded-xl p-4 bg-white hover:border-primary-300 hover:shadow-md transition-all group"
            >
              {/* Product icon */}
              <div className="text-2xl mb-2">{getProductEmoji(rec.product_name || rec.product)}</div>

              {/* Badges row */}
              <div className="flex gap-1.5 mb-2 flex-wrap">
                <span className={clsx('badge text-xs', pConf.badge)}>{pConf.label}</span>
                {isApproved ? (
                  <span className="badge bg-green-100 text-green-700 border border-green-200 text-xs gap-1">
                    <CheckCircle className="w-3 h-3 inline" /> Approved
                  </span>
                ) : (
                  <span className="badge bg-yellow-100 text-yellow-700 border border-yellow-200 text-xs gap-1">
                    <AlertTriangle className="w-3 h-3 inline" /> Review
                  </span>
                )}
              </div>

              {/* Product name */}
              <p className="text-sm font-semibold text-gray-800 leading-tight mb-1.5">
                {rec.product_name || rec.product || 'Product'}
              </p>

              {/* Reason */}
              <p className="text-xs text-gray-500 leading-relaxed mb-3 line-clamp-2">
                {rec.reason || rec.rationale || 'Personalized recommendation based on customer profile'}
              </p>

              {/* CTA button */}
              <button className="w-full flex items-center justify-center gap-1.5 bg-primary-600 hover:bg-primary-700 text-white text-xs font-semibold py-2 px-3 rounded-lg transition-colors group-hover:shadow-sm">
                <ShoppingBag className="w-3.5 h-3.5" />
                Offer Product
                <ChevronRight className="w-3 h-3" />
              </button>
            </div>
          )
        })}
      </div>
    </div>
  )
}
