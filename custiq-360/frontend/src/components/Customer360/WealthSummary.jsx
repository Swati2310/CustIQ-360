import React from 'react'
import { TrendingUp, Landmark, Shield, PiggyBank, AlertTriangle, Clock } from 'lucide-react'
import { formatDate, daysUntil } from '../../utils/format.js'
import { useCurrency } from '../../context/CurrencyContext.jsx'
import clsx from 'clsx'

const CATEGORY_CONFIG = {
  fd: {
    label: 'Fixed Deposits',
    icon: Landmark,
    color: 'bg-blue-100 text-blue-600',
    bgCard: 'border-blue-100',
  },
  mf: {
    label: 'Mutual Funds',
    icon: TrendingUp,
    color: 'bg-green-100 text-green-600',
    bgCard: 'border-green-100',
  },
  mutual_fund: {
    label: 'Mutual Funds',
    icon: TrendingUp,
    color: 'bg-green-100 text-green-600',
    bgCard: 'border-green-100',
  },
  insurance: {
    label: 'Insurance',
    icon: Shield,
    color: 'bg-purple-100 text-purple-600',
    bgCard: 'border-purple-100',
  },
  ppf: {
    label: 'PPF / Tax Savings',
    icon: PiggyBank,
    color: 'bg-amber-100 text-amber-600',
    bgCard: 'border-amber-100',
  },
  equity: {
    label: 'Equity / Stocks',
    icon: TrendingUp,
    color: 'bg-rose-100 text-rose-600',
    bgCard: 'border-rose-100',
  },
}

function getCategory(item) {
  const t = (item.type || item.product_type || item.investment_type || '').toLowerCase()
  if (t.includes('fd') || t.includes('fixed')) return 'fd'
  if (t.includes('mf') || t.includes('mutual')) return 'mf'
  if (t.includes('insur')) return 'insurance'
  if (t.includes('ppf')) return 'ppf'
  if (t.includes('equity') || t.includes('stock')) return 'equity'
  return t || 'fd'
}

export default function WealthSummary({ wealth = [] }) {
  const { formatAmount, formatCompact } = useCurrency()
  if (wealth.length === 0) {
    return (
      <div className="card p-8 text-center">
        <div className="w-12 h-12 rounded-xl bg-gray-100 flex items-center justify-center mx-auto mb-3">
          <TrendingUp className="w-6 h-6 text-gray-300" />
        </div>
        <p className="text-sm font-medium text-gray-500">No wealth products</p>
        <p className="text-xs text-gray-400 mt-1">No investment products on record</p>
      </div>
    )
  }

  // Group by category
  const grouped = {}
  wealth.forEach((item) => {
    const cat = getCategory(item)
    if (!grouped[cat]) grouped[cat] = []
    grouped[cat].push(item)
  })

  const totalWealth = wealth.reduce(
    (sum, w) => sum + parseFloat(w.current_value || w.amount || w.value || 0),
    0
  )

  return (
    <div className="card">
      <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-primary-600" />
          <h3 className="text-sm font-semibold text-gray-800">Wealth & Investments</h3>
          <span className="badge bg-primary-50 text-primary-700 text-xs">{wealth.length}</span>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-400">Total AUM</p>
          <p className="text-sm font-bold text-green-700">{formatCompact(totalWealth)}</p>
        </div>
      </div>

      <div className="p-5 space-y-5">
        {Object.entries(grouped).map(([cat, items]) => {
          const config = CATEGORY_CONFIG[cat] || {
            label: cat.toUpperCase(),
            icon: TrendingUp,
            color: 'bg-gray-100 text-gray-600',
            bgCard: 'border-gray-100',
          }
          const Icon = config.icon
          const catTotal = items.reduce(
            (sum, i) => sum + parseFloat(i.current_value || i.amount || i.value || 0),
            0
          )

          return (
            <div key={cat}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className={clsx('w-6 h-6 rounded-md flex items-center justify-center', config.color)}>
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                  <span className="text-xs font-semibold text-gray-700">{config.label}</span>
                  <span className="text-xs text-gray-400">({items.length})</span>
                </div>
                <span className="text-xs font-semibold text-gray-700">{formatCompact(catTotal)}</span>
              </div>

              <div className="space-y-2">
                {items.map((item, idx) => {
                  const maturityDate = item.maturity_date || item.expiry_date
                  const days = maturityDate ? daysUntil(maturityDate) : null
                  const maturingSoon = days !== null && days >= 0 && days <= 60
                  const expired = days !== null && days < 0
                  const value = parseFloat(item.current_value || item.amount || item.value || 0)

                  return (
                    <div
                      key={item.id || item.product_id || idx}
                      className={clsx(
                        'border rounded-lg px-3.5 py-3',
                        maturingSoon
                          ? 'border-orange-200 bg-orange-50'
                          : expired
                          ? 'border-red-200 bg-red-50'
                          : config.bgCard + ' bg-white'
                      )}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-xs font-semibold text-gray-800">
                              {item.product_name ||
                                item.name ||
                                item.scheme_name ||
                                item.description ||
                                (cat.toUpperCase() + ' ' + (idx + 1))}
                            </span>
                            {maturingSoon && (
                              <span className="badge bg-orange-100 text-orange-700 text-xs gap-1">
                                <Clock className="w-3 h-3 inline" /> Maturing Soon ({days}d)
                              </span>
                            )}
                            {expired && (
                              <span className="badge bg-red-100 text-red-700 text-xs gap-1">
                                <AlertTriangle className="w-3 h-3 inline" /> Matured
                              </span>
                            )}
                          </div>
                          <div className="flex gap-3 mt-1 text-xs text-gray-500">
                            {item.interest_rate && <span>{item.interest_rate}% p.a.</span>}
                            {maturityDate && (
                              <span>Matures: {formatDate(maturityDate)}</span>
                            )}
                            {item.units && <span>{item.units} units</span>}
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-bold text-gray-900">{formatAmount(value)}</p>
                          {item.invested_amount && item.invested_amount !== value && (
                            <p className="text-xs text-gray-400">
                              Inv: {formatAmount(item.invested_amount)}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
