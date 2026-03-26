import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, RefreshCw, AlertCircle } from 'lucide-react'
import useCustomer from '../hooks/useCustomer.js'
import { getRecommendations } from '../utils/api.js'
import { useCurrency } from '../context/CurrencyContext.jsx'
import ProfileCard from '../components/Customer360/ProfileCard.jsx'
import AccountsSummary from '../components/Customer360/AccountsSummary.jsx'
import LoansSummary from '../components/Customer360/LoansSummary.jsx'
import WealthSummary from '../components/Customer360/WealthSummary.jsx'
import KYCStatus from '../components/Customer360/KYCStatus.jsx'
import CrossSellCard from '../components/Recommendations/CrossSellCard.jsx'
import ChatPanel from '../components/Chat/ChatPanel.jsx'
import DocumentUploader from '../components/Documents/DocumentUploader.jsx'
import clsx from 'clsx'

const TABS = [
  { key: 'accounts', label: 'Accounts' },
  { key: 'loans', label: 'Loans' },
  { key: 'wealth', label: 'Wealth' },
  { key: 'kyc', label: 'KYC' },
]

const RECENT_KEY = 'custiq_recent_lookups'

export default function CustomerView() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { customer, accounts, loans, wealth, kyc, loading, error, refetch } = useCustomer(id)
  const { setCurrency } = useCurrency()
  const [activeTab, setActiveTab] = useState('accounts')
  const [recommendations, setRecommendations] = useState([])

  // Auto-switch currency to match the customer's country
  useEffect(() => {
    if (customer?.currency) {
      setCurrency(customer.currency)
    }
  }, [customer?.currency])

  // Update recent lookups
  useEffect(() => {
    if (!customer) return
    try {
      const existing = JSON.parse(localStorage.getItem(RECENT_KEY) || '[]')
      const custId = customer.customer_id || customer.id
      const entry = {
        id: custId,
        name: customer.name || customer.full_name,
        segment: customer.segment,
        phone: customer.phone || customer.mobile,
      }
      const updated = [entry, ...existing.filter((r) => r.id !== custId)].slice(0, 5)
      localStorage.setItem(RECENT_KEY, JSON.stringify(updated))
    } catch {}
  }, [customer])

  // Fetch recommendations
  useEffect(() => {
    if (!id) return
    getRecommendations(id)
      .then((res) => {
        const data = res.data
        setRecommendations(Array.isArray(data) ? data : data?.recommendations || [])
      })
      .catch(() => setRecommendations([]))
  }, [id])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-12 h-12 border-3 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" style={{ borderWidth: '3px' }} />
          <p className="text-sm text-gray-500">Loading customer data...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full px-6">
        <div className="text-center max-w-sm">
          <div className="w-14 h-14 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-7 h-7 text-red-500" />
          </div>
          <h2 className="text-base font-semibold text-gray-800 mb-1">Failed to load customer</h2>
          <p className="text-sm text-gray-500 mb-4">{error}</p>
          <div className="flex gap-2 justify-center">
            <button onClick={() => navigate(-1)} className="btn-secondary">
              <ArrowLeft className="w-4 h-4 inline mr-1.5" />
              Back
            </button>
            <button onClick={refetch} className="btn-primary">
              <RefreshCw className="w-4 h-4 inline mr-1.5" />
              Retry
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full overflow-hidden">
      {/* Left panel - scrollable */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-6 py-6 space-y-5">
          {/* Back + Refresh */}
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate(-1)}
              className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-800 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>
            <button
              onClick={refetch}
              className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-primary-600 transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh
            </button>
          </div>

          {/* Profile card */}
          {customer && (
            <ProfileCard customer={customer} accounts={accounts} wealth={wealth} />
          )}

          {/* Tabs */}
          <div className="border-b border-gray-200">
            <nav className="flex gap-0 -mb-px">
              {TABS.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={clsx(
                    'px-5 py-3 text-sm font-medium transition-all',
                    activeTab === tab.key
                      ? 'tab-active'
                      : 'tab-inactive'
                  )}
                >
                  {tab.label}
                  {tab.key === 'accounts' && accounts.length > 0 && (
                    <span className="ml-1.5 badge bg-gray-100 text-gray-600 text-xs">{accounts.length}</span>
                  )}
                  {tab.key === 'loans' && loans.length > 0 && (
                    <span className="ml-1.5 badge bg-gray-100 text-gray-600 text-xs">{loans.length}</span>
                  )}
                  {tab.key === 'wealth' && wealth.length > 0 && (
                    <span className="ml-1.5 badge bg-gray-100 text-gray-600 text-xs">{wealth.length}</span>
                  )}
                </button>
              ))}
            </nav>
          </div>

          {/* Tab content */}
          <div>
            {activeTab === 'accounts' && <AccountsSummary accounts={accounts} />}
            {activeTab === 'loans' && <LoansSummary loans={loans} />}
            {activeTab === 'wealth' && <WealthSummary wealth={wealth} />}
            {activeTab === 'kyc' && <KYCStatus kyc={kyc} customer={customer} />}
          </div>

          {/* Cross-sell recommendations */}
          {recommendations.length > 0 && (
            <CrossSellCard recommendations={recommendations} />
          )}

          {/* Document uploader */}
          <DocumentUploader customerId={customer?.customer_id} onApplied={refetch} />
        </div>
      </div>

      {/* Right panel - chat (fixed width, scrollable internally) */}
      <div className="w-96 flex-shrink-0 overflow-hidden flex flex-col">
        <ChatPanel customerId={id} />
      </div>
    </div>
  )
}
