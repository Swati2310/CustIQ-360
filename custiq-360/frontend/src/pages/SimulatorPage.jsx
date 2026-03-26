import React, { useState } from 'react'
import { Calculator, TrendingUp, ArrowLeftRight, Globe } from 'lucide-react'
import EMICalculator from '../components/Simulator/EMICalculator.jsx'
import FDSimulator from '../components/Simulator/FDSimulator.jsx'
import LoanScenario from '../components/Simulator/LoanScenario.jsx'
import { useCurrency, CURRENCIES } from '../context/CurrencyContext.jsx'
import clsx from 'clsx'

const TABS = [
  { key: 'emi',     label: 'EMI Calculator',  icon: Calculator,    description: 'Calculate monthly EMI for any loan' },
  { key: 'fd',      label: 'FD Simulator',     icon: TrendingUp,    description: 'Simulate Fixed Deposit returns' },
  { key: 'compare', label: 'Loan Comparison',  icon: ArrowLeftRight, description: 'Compare two loan scenarios side by side' },
]

export default function SimulatorPage() {
  const [activeTab, setActiveTab] = useState('emi')
  const { currency, setCurrency } = useCurrency()

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      {/* Page header */}
      <div className="flex items-start justify-between mb-6 flex-wrap gap-4">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Financial Simulator</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Interactive tools to plan and compare financial products for your customers
          </p>
        </div>

        {/* Currency selector */}
        <div className="flex items-center gap-2 bg-white border border-gray-200 rounded-xl px-3 py-2 shadow-sm">
          <Globe className="w-4 h-4 text-gray-400 flex-shrink-0" />
          <label className="text-xs text-gray-500 font-medium whitespace-nowrap">Currency</label>
          <select
            value={currency.code}
            onChange={(e) => setCurrency(e.target.value)}
            className="text-sm font-semibold text-gray-800 border-none outline-none bg-transparent cursor-pointer"
          >
            {CURRENCIES.map((c) => (
              <option key={c.code} value={c.code}>
                {c.symbol} {c.code} — {c.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Tab navigation */}
      <div className="flex gap-3 mb-6 flex-wrap">
        {TABS.map(({ key, label, icon: Icon, description }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={clsx(
              'flex items-center gap-2.5 px-4 py-3 rounded-xl border-2 transition-all text-left',
              activeTab === key
                ? 'border-primary-500 bg-primary-50 text-primary-700 shadow-sm'
                : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300 hover:bg-gray-50'
            )}
          >
            <div className={clsx('w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0',
              activeTab === key ? 'bg-primary-100' : 'bg-gray-100')}>
              <Icon className={clsx('w-4 h-4', activeTab === key ? 'text-primary-600' : 'text-gray-500')} />
            </div>
            <div>
              <p className={clsx('text-sm font-semibold leading-tight', activeTab === key ? 'text-primary-700' : 'text-gray-700')}>
                {label}
              </p>
              <p className="text-xs text-gray-400 leading-tight hidden sm:block">{description}</p>
            </div>
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div>
        {activeTab === 'emi'     && <EMICalculator />}
        {activeTab === 'fd'      && <FDSimulator />}
        {activeTab === 'compare' && <LoanScenario />}
      </div>

      <p className="text-xs text-gray-400 text-center mt-8">
        * All calculations are indicative and for planning purposes only. Actual rates and amounts may vary.
        Consult with the banking team for accurate figures.
      </p>
    </div>
  )
}
