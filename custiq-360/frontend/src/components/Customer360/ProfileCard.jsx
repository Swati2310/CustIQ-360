import React from 'react'
import { Phone, Mail, Calendar, TrendingUp, BadgeCheck, Globe2 } from 'lucide-react'
import { formatDate, getInitials, segmentColor } from '../../utils/format.js'
import { useCurrency } from '../../context/CurrencyContext.jsx'
import clsx from 'clsx'

const REGION_COLORS = {
  'South Asia': 'bg-orange-100 text-orange-700',
  'APAC': 'bg-cyan-100 text-cyan-700',
  'SEPA': 'bg-blue-100 text-blue-700',
  'EMEA': 'bg-violet-100 text-violet-700',
}

function calcPortfolio(accounts = [], wealth = []) {
  const accTotal = accounts.reduce((sum, a) => sum + (parseFloat(a.balance) || 0), 0)
  const wealthTotal = wealth.reduce((sum, w) => sum + (parseFloat(w.current_value || w.amount || 0)), 0)
  return accTotal + wealthTotal
}

export default function ProfileCard({ customer, accounts = [], wealth = [] }) {
  const { formatCompact } = useCurrency()
  if (!customer) return null

  const name = customer.name || customer.full_name || 'Unknown'
  const initials = getInitials(name)
  const portfolio = calcPortfolio(accounts, wealth)

  const segmentColors = {
    hni: 'bg-amber-100 text-banking-gold border border-amber-300',
    affluent: 'bg-blue-100 text-blue-700 border border-blue-300',
    mass: 'bg-gray-100 text-gray-600 border border-gray-300',
  }
  const segKey = (customer.segment || 'mass').toLowerCase()
  const segBadge = segmentColors[segKey] || segmentColors.mass

  const avatarColors = {
    hni: 'bg-amber-500',
    affluent: 'bg-blue-600',
    mass: 'bg-primary-600',
  }
  const avatarBg = avatarColors[segKey] || avatarColors.mass

  return (
    <div className="card p-5">
      <div className="flex items-start gap-4">
        {/* Avatar */}
        <div
          className={clsx(
            'w-14 h-14 rounded-xl flex items-center justify-center text-white text-xl font-bold flex-shrink-0 shadow-sm',
            avatarBg
          )}
        >
          {initials}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h2 className="text-lg font-bold text-gray-900 leading-tight">{name}</h2>
            <span className={clsx('badge text-xs font-semibold', segBadge)}>
              {(customer.segment || 'Mass').toUpperCase()}
            </span>
            {customer.region && (
              <span className={clsx('badge text-xs', REGION_COLORS[customer.region] || 'bg-gray-100 text-gray-600')}>
                {customer.region}
              </span>
            )}
          </div>
          <p className="text-xs text-gray-400 mt-0.5 font-mono">
            ID: {customer.customer_id || customer.id}
          </p>

          <div className="mt-3 grid grid-cols-1 gap-1.5">
            {customer.phone && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Phone className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                <span>{customer.phone || customer.mobile}</span>
              </div>
            )}
            {customer.email && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Mail className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                <span className="truncate">{customer.email}</span>
              </div>
            )}
            {(customer.relationship_since || customer.created_at) && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Calendar className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                <span>
                  Relationship since{' '}
                  {formatDate(customer.relationship_since || customer.created_at)}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Portfolio */}
        <div className="text-right flex-shrink-0">
          <div className="flex items-center gap-1 justify-end text-xs text-gray-400 mb-1">
            <TrendingUp className="w-3.5 h-3.5" />
            Total Portfolio
          </div>
          <p className="text-xl font-bold text-gray-900">{formatCompact(portfolio)}</p>
          {customer.risk_category && (
            <div className="mt-2 flex items-center gap-1 justify-end">
              <BadgeCheck className="w-3.5 h-3.5 text-primary-500" />
              <span className="text-xs text-gray-500">{customer.risk_category}</span>
            </div>
          )}
        </div>
      </div>

      {/* Additional details row */}
      {(customer.country_name || customer.city || customer.occupation || customer.annual_income) && (
        <div className="mt-4 pt-4 border-t border-gray-100 flex flex-wrap gap-4 text-xs text-gray-500">
          {customer.country_name && (
            <span className="flex items-center gap-1">
              <Globe2 className="w-3 h-3 text-gray-400" />
              <span className="font-medium text-gray-700">{customer.country_name}</span>
              {customer.currency && customer.currency !== 'INR' && (
                <span className="text-gray-400">({customer.currency})</span>
              )}
            </span>
          )}
          {customer.city && (
            <span>
              <span className="font-medium text-gray-700">City:</span> {customer.city}
            </span>
          )}
          {customer.occupation && (
            <span>
              <span className="font-medium text-gray-700">Occupation:</span> {customer.occupation}
            </span>
          )}
          {customer.annual_income && (
            <span>
              <span className="font-medium text-gray-700">Annual Income:</span>{' '}
              {formatCompact(customer.annual_income)}
            </span>
          )}
        </div>
      )}
    </div>
  )
}
