import React from 'react'
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  Shield,
  FileText,
  Home,
  Clock,
  RefreshCw,
  Briefcase,
  TrendingUp,
} from 'lucide-react'
import { formatDate, daysUntil } from '../../utils/format.js'
import { useCurrency } from '../../context/CurrencyContext.jsx'
import clsx from 'clsx'

function DocRow({ icon: Icon, label, status, expiryDate, number }) {
  const isVerified = status === true || String(status || '').toLowerCase() === 'verified'
  const days = expiryDate ? daysUntil(expiryDate) : null
  const expiringSoon = days !== null && days >= 0 && days <= 90
  const expired = days !== null && days < 0

  return (
    <div className={clsx(
      'py-3 px-3 rounded-xl mb-2 border',
      isVerified ? 'bg-green-50 border-green-100' : 'bg-red-50 border-red-100'
    )}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={clsx(
            'w-9 h-9 rounded-lg flex items-center justify-center',
            isVerified ? 'bg-green-100' : 'bg-red-100'
          )}>
            <Icon className={clsx('w-4 h-4', isVerified ? 'text-green-600' : 'text-red-500')} />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-800">{label}</p>
            <p className={clsx('text-xs font-medium', isVerified ? 'text-green-600' : 'text-red-500')}>
              {isVerified ? 'Verified' : 'Not Verified'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {expired && <span className="badge bg-red-100 text-red-700 text-xs">Expired</span>}
          {expiringSoon && !expired && (
            <span className="badge bg-orange-100 text-orange-700 text-xs gap-1">
              <Clock className="w-3 h-3 inline" /> {days}d left
            </span>
          )}
          {isVerified
            ? <CheckCircle className="w-5 h-5 text-green-500" />
            : <XCircle className="w-5 h-5 text-red-400" />
          }
        </div>
      </div>

      {/* Document details row */}
      <div className="mt-2 ml-12 flex flex-wrap gap-x-6 gap-y-1">
        {number && (
          <span className="text-xs text-gray-500">
            <span className="font-medium text-gray-600">Number:</span> {number}
          </span>
        )}
        {expiryDate && (
          <span className="text-xs text-gray-500">
            <span className="font-medium text-gray-600">Expiry:</span> {formatDate(expiryDate)}
          </span>
        )}
        {!number && !expiryDate && (
          <span className="text-xs text-gray-400 italic">No document details on file — upload via Document Extraction</span>
        )}
      </div>
    </div>
  )
}

export default function KYCStatus({ kyc, customer }) {
  const { formatCompact } = useCurrency()

  if (!kyc) {
    return (
      <div className="card p-6 text-center">
        <Shield className="w-10 h-10 text-gray-300 mx-auto mb-2" />
        <p className="text-sm text-gray-500">KYC data not available</p>
      </div>
    )
  }

  const riskColors = {
    low: 'bg-green-100 text-green-800',
    medium: 'bg-amber-100 text-amber-800',
    high: 'bg-red-100 text-red-800',
  }
  const risk = (kyc.risk_category || kyc.risk_profile || 'low').toLowerCase()
  const riskBadge = riskColors[risk] || riskColors.low

  // Check if any document expires within 90 days
  const docs = [
    {
      label: kyc.aadhaar?.type || 'Primary ID',
      icon: FileText,
      status: kyc.aadhaar?.verified ?? kyc.aadhaar_verified ?? kyc.aadhaar_status,
      expiry: kyc.aadhaar?.expiry || kyc.aadhaar_expiry,
      number: kyc.aadhaar?.number || kyc.aadhaar_number,
    },
    {
      label: kyc.pan?.type || 'Secondary ID',
      icon: Shield,
      status: kyc.pan?.verified ?? kyc.pan_verified ?? kyc.pan_status,
      expiry: kyc.pan?.expiry || kyc.pan_expiry,
      number: kyc.pan?.number || kyc.pan_number,
    },
    {
      label: kyc.address_proof?.type || 'Address Proof',
      icon: Home,
      status: kyc.address_proof?.verified ?? kyc.address_verified ?? kyc.address_proof_status,
      expiry: kyc.address_proof?.expiry || kyc.address_proof_expiry,
      number: kyc.address_proof?.number || kyc.address_proof_number,
    },
  ]

  const hasExpiringDocs = docs.some((d) => {
    const days = d.expiry ? daysUntil(d.expiry) : null
    return days !== null && days >= 0 && days <= 90
  })

  const hasExpiredDocs = docs.some((d) => {
    const days = d.expiry ? daysUntil(d.expiry) : null
    return days !== null && days < 0
  })

  const allVerified = docs.every(
    (d) => d.status === true || String(d.status || '').toLowerCase() === 'verified'
  )

  return (
    <div className="card">
      <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-primary-600" />
          <h3 className="text-sm font-semibold text-gray-800">KYC Status</h3>
        </div>
        <div className="flex items-center gap-2">
          <span className={clsx('badge text-xs', riskBadge)}>
            {(kyc.risk_category || kyc.risk_profile || 'Low').toUpperCase()} RISK
          </span>
          {allVerified && (
            <span className="badge bg-green-100 text-green-800 text-xs">KYC Complete</span>
          )}
        </div>
      </div>

      {/* Warning banners */}
      {hasExpiredDocs && (
        <div className="mx-5 mt-4 flex items-start gap-2 bg-red-50 border border-red-200 rounded-lg px-3 py-2.5">
          <AlertTriangle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-red-700 font-medium">
            One or more KYC documents have expired. Immediate renewal required.
          </p>
        </div>
      )}
      {!hasExpiredDocs && hasExpiringDocs && (
        <div className="mx-5 mt-4 flex items-start gap-2 bg-orange-50 border border-orange-200 rounded-lg px-3 py-2.5">
          <Clock className="w-4 h-4 text-orange-500 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-orange-700 font-medium">
            KYC documents expiring within 90 days. Please initiate renewal.
          </p>
        </div>
      )}

      <div className="px-5 pt-4 pb-2">
        {docs.map((doc) => (
          <DocRow
            key={doc.label}
            icon={doc.icon}
            label={doc.label}
            status={doc.status}
            expiryDate={doc.expiry}
            number={doc.number}
          />
        ))}
      </div>

      {/* Profile details sourced from documents */}
      {(customer?.occupation || customer?.annual_income) && (
        <div className="mx-5 mb-4 rounded-xl border border-blue-100 bg-blue-50 overflow-hidden">
          <div className="px-4 py-2 border-b border-blue-100 flex items-center gap-2">
            <FileText className="w-3.5 h-3.5 text-blue-500" />
            <span className="text-xs font-semibold text-blue-700">Profile Details (from Documents)</span>
          </div>
          <div className="px-4 py-3 flex flex-wrap gap-x-8 gap-y-2">
            {customer.occupation && (
              <div className="flex items-center gap-2">
                <Briefcase className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
                <span className="text-xs text-gray-500">Occupation:</span>
                <span className="text-xs font-semibold text-gray-800">{customer.occupation}</span>
              </div>
            )}
            {customer.annual_income && (
              <div className="flex items-center gap-2">
                <TrendingUp className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
                <span className="text-xs text-gray-500">Annual Income:</span>
                <span className="text-xs font-semibold text-gray-800">{formatCompact(customer.annual_income)}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Last updated */}
      {(kyc.last_updated || kyc.kyc_date || kyc.verified_on) && (
        <div className="px-5 py-3 border-t border-gray-100 flex items-center gap-2 text-xs text-gray-400">
          <RefreshCw className="w-3.5 h-3.5" />
          Last updated: {formatDate(kyc.last_updated || kyc.kyc_date || kyc.verified_on)}
        </div>
      )}
    </div>
  )
}
