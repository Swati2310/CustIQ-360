import React from 'react'
import { Banknote, TrendingDown, AlertCircle } from 'lucide-react'
import { formatDate, statusColor } from '../../utils/format.js'
import { useCurrency } from '../../context/CurrencyContext.jsx'
import clsx from 'clsx'

function ProgressBar({ value, max, color = 'bg-primary-500' }) {
  const pct = max > 0 ? Math.min(100, Math.max(0, (value / max) * 100)) : 0
  return (
    <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
      <div
        className={clsx('h-full rounded-full transition-all', color)}
        style={{ width: `${pct}%` }}
      />
    </div>
  )
}

export default function LoansSummary({ loans = [] }) {
  const { formatAmount, formatCompact } = useCurrency()
  if (loans.length === 0) {
    return (
      <div className="card p-8 text-center">
        <div className="w-12 h-12 rounded-xl bg-gray-100 flex items-center justify-center mx-auto mb-3">
          <Banknote className="w-6 h-6 text-gray-300" />
        </div>
        <p className="text-sm font-medium text-gray-500">No active loans</p>
        <p className="text-xs text-gray-400 mt-1">Customer has no loan accounts</p>
      </div>
    )
  }

  const totalOutstanding = loans.reduce(
    (sum, l) => sum + parseFloat(l.outstanding_amount || l.outstanding || 0),
    0
  )

  return (
    <div className="card">
      <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Banknote className="w-4 h-4 text-primary-600" />
          <h3 className="text-sm font-semibold text-gray-800">Loans</h3>
          <span className="badge bg-primary-50 text-primary-700 text-xs">{loans.length}</span>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-400">Total Outstanding</p>
          <p className="text-sm font-bold text-red-600">{formatCompact(totalOutstanding)}</p>
        </div>
      </div>

      <div className="divide-y divide-gray-50">
        {loans.map((loan, idx) => {
          const sanctioned = parseFloat(loan.sanctioned_amount || loan.loan_amount || 0)
          const outstanding = parseFloat(loan.outstanding_amount || loan.outstanding || 0)
          const repaid = sanctioned - outstanding
          const repaidPct = sanctioned > 0 ? Math.round((repaid / sanctioned) * 100) : 0
          const isNPA = (loan.status || '').toLowerCase() === 'npa'
          const isOverdue = (loan.status || '').toLowerCase() === 'overdue'

          return (
            <div key={loan.loan_id || loan.id || idx} className="px-5 py-4">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2.5">
                  <div
                    className={clsx(
                      'w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0',
                      isNPA || isOverdue ? 'bg-red-100' : 'bg-primary-100'
                    )}
                  >
                    {isNPA || isOverdue ? (
                      <AlertCircle className="w-4.5 h-4.5 text-red-600" size={18} />
                    ) : (
                      <TrendingDown className="w-4.5 h-4.5 text-primary-600" size={18} />
                    )}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-gray-800">
                      {loan.loan_type || loan.type || 'Loan'}
                    </p>
                    <p className="text-xs text-gray-400 font-mono">
                      {loan.loan_id || loan.id || '-'}
                    </p>
                  </div>
                </div>
                <span className={clsx('badge text-xs', statusColor(loan.status))}>
                  {loan.status || 'Active'}
                </span>
              </div>

              {/* Amounts grid */}
              <div className="grid grid-cols-3 gap-3 mb-3">
                <div>
                  <p className="text-xs text-gray-400">Sanctioned</p>
                  <p className="text-sm font-semibold text-gray-700">{formatAmount(sanctioned)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-400">Outstanding</p>
                  <p className={clsx('text-sm font-semibold', isNPA ? 'text-red-600' : 'text-gray-700')}>
                    {formatAmount(outstanding)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-400">EMI / Month</p>
                  <p className="text-sm font-semibold text-gray-700">
                    {formatAmount(loan.emi_amount || loan.emi || 0)}
                  </p>
                </div>
              </div>

              {/* Progress bar */}
              <div className="mb-2">
                <div className="flex justify-between text-xs text-gray-400 mb-1">
                  <span>Repayment Progress</span>
                  <span className="font-medium text-primary-600">{repaidPct}%</span>
                </div>
                <ProgressBar
                  value={repaid}
                  max={sanctioned}
                  color={isNPA ? 'bg-red-400' : repaidPct > 70 ? 'bg-green-500' : 'bg-primary-500'}
                />
              </div>

              {/* Rate & tenure */}
              <div className="flex gap-4 mt-2 text-xs text-gray-500">
                {loan.interest_rate && (
                  <span>
                    <span className="font-medium">Rate:</span> {loan.interest_rate}%
                  </span>
                )}
                {loan.tenure_months && (
                  <span>
                    <span className="font-medium">Tenure:</span> {loan.tenure_months} months
                  </span>
                )}
                {loan.next_due_date && (
                  <span>
                    <span className="font-medium">Next Due:</span> {formatDate(loan.next_due_date)}
                  </span>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
