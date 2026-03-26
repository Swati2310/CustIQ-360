import React, { useState } from 'react'
import { CreditCard, ArrowUpRight, ArrowDownLeft, Building2 } from 'lucide-react'
import { formatDate, statusColor } from '../../utils/format.js'
import { useCurrency } from '../../context/CurrencyContext.jsx'
import clsx from 'clsx'

export default function AccountsSummary({ accounts = [] }) {
  const { formatAmount } = useCurrency()
  const [selectedAcc, setSelectedAcc] = useState(0)

  if (accounts.length === 0) {
    return (
      <div className="card p-6 text-center">
        <CreditCard className="w-10 h-10 text-gray-300 mx-auto mb-2" />
        <p className="text-sm text-gray-500">No accounts found</p>
      </div>
    )
  }

  const current = accounts[selectedAcc] || accounts[0]
  const transactions = current?.transactions || current?.recent_transactions || []

  return (
    <div className="card">
      <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <CreditCard className="w-4 h-4 text-primary-600" />
          <h3 className="text-sm font-semibold text-gray-800">Accounts</h3>
          <span className="badge bg-primary-50 text-primary-700 text-xs">{accounts.length}</span>
        </div>
      </div>

      {/* Accounts table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wider">
              <th className="px-5 py-3 text-left font-medium">Type</th>
              <th className="px-5 py-3 text-left font-medium">Account No.</th>
              <th className="px-5 py-3 text-right font-medium">Balance</th>
              <th className="px-5 py-3 text-left font-medium">Branch</th>
              <th className="px-5 py-3 text-center font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {accounts.map((acc, idx) => (
              <tr
                key={acc.account_id || acc.id || idx}
                className={clsx(
                  'cursor-pointer hover:bg-primary-50/50 transition-colors',
                  idx === selectedAcc && 'bg-primary-50/40'
                )}
                onClick={() => setSelectedAcc(idx)}
              >
                <td className="px-5 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-lg bg-primary-100 flex items-center justify-center">
                      <CreditCard className="w-3.5 h-3.5 text-primary-600" />
                    </div>
                    <span className="font-medium text-gray-800">
                      {acc.account_type || acc.type || 'Account'}
                    </span>
                  </div>
                </td>
                <td className="px-5 py-3 text-gray-500 font-mono text-xs">
                  {acc.account_number || acc.account_no || acc.account_id || '-'}
                </td>
                <td className="px-5 py-3 text-right font-semibold text-gray-900">
                  {formatAmount(acc.balance)}
                </td>
                <td className="px-5 py-3 text-gray-500">
                  <div className="flex items-center gap-1.5">
                    <Building2 className="w-3 h-3 text-gray-300" />
                    {acc.branch || acc.branch_name || '-'}
                  </div>
                </td>
                <td className="px-5 py-3 text-center">
                  <span
                    className={clsx(
                      'badge text-xs',
                      statusColor(acc.status)
                    )}
                  >
                    {acc.status || 'Active'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Recent transactions */}
      {transactions.length > 0 && (
        <div className="px-5 py-4 border-t border-gray-100">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
            Recent Transactions — {current.account_type || current.type}
          </p>
          <div className="space-y-2">
            {transactions.slice(0, 5).map((txn, i) => {
              const isCredit =
                (txn.type || '').toLowerCase() === 'credit' ||
                (txn.transaction_type || '').toLowerCase() === 'credit' ||
                parseFloat(txn.amount || 0) > 0
              return (
                <div
                  key={txn.transaction_id || i}
                  className="flex items-center justify-between py-1.5"
                >
                  <div className="flex items-center gap-2.5">
                    <div
                      className={clsx(
                        'w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0',
                        isCredit ? 'bg-green-100' : 'bg-red-100'
                      )}
                    >
                      {isCredit ? (
                        <ArrowDownLeft className="w-3.5 h-3.5 text-green-600" />
                      ) : (
                        <ArrowUpRight className="w-3.5 h-3.5 text-red-600" />
                      )}
                    </div>
                    <div>
                      <p className="text-xs font-medium text-gray-700 leading-tight">
                        {txn.description || txn.narration || txn.remarks || 'Transaction'}
                      </p>
                      <p className="text-xs text-gray-400 leading-tight">
                        {formatDate(txn.date || txn.transaction_date || txn.value_date)}
                      </p>
                    </div>
                  </div>
                  <span
                    className={clsx(
                      'text-sm font-semibold',
                      isCredit ? 'text-green-600' : 'text-red-600'
                    )}
                  >
                    {isCredit ? '+' : '-'}
                    {formatAmount(Math.abs(parseFloat(txn.amount || 0)))}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
