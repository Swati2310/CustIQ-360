import React, { useState, useMemo, useEffect } from 'react'
import { Percent, Calendar, TrendingUp } from 'lucide-react'
import { useCurrency } from '../../context/CurrencyContext.jsx'

const TENURE_UNITS = [
  { value: 'days',   label: 'Days' },
  { value: 'months', label: 'Months' },
  { value: 'years',  label: 'Years' },
]

function toDays(value, unit) {
  switch (unit) {
    case 'months': return Math.round(value * 30.44)
    case 'years':  return Math.round(value * 365)
    default:       return value
  }
}

function calculateFD(principal, annualRate, tenureDays) {
  if (!principal || !annualRate || !tenureDays) return { maturity: 0, interest: 0, yield: 0 }
  const years = tenureDays / 365
  const maturity = principal * Math.pow(1 + annualRate / (4 * 100), 4 * years)
  const interest = maturity - principal
  const effectiveYield = ((maturity / principal) ** (1 / years) - 1) * 100
  return { maturity, interest, yield: effectiveYield }
}

export default function FDSimulator() {
  const { currency, formatRaw, formatRawCompact } = useCurrency()

  const r = currency.rate
  const minPrincipal     = Math.max(1, Math.round(10000   * r / 100)  * 100)
  const maxPrincipal     = Math.max(1, Math.round(10000000 * r / 1000) * 1000)
  const stepPrincipal    = Math.max(1, Math.round(10000   * r / 100)  * 100)
  const defaultPrincipal = Math.max(minPrincipal, Math.round(500000 * r / 1000) * 1000)

  const [principal, setPrincipal] = useState(defaultPrincipal)
  const [rate, setRate] = useState(7.5)
  const [tenureValue, setTenureValue] = useState(365)
  const [tenureUnit, setTenureUnit] = useState('days')

  useEffect(() => { setPrincipal(defaultPrincipal) }, [currency.code])

  const tenureDays = useMemo(() => toDays(tenureValue, tenureUnit), [tenureValue, tenureUnit])

  const { maturity, interest, yield: effYield } = useMemo(
    () => calculateFD(principal, rate, tenureDays),
    [principal, rate, tenureDays]
  )

  const interestPct = maturity > 0 ? ((interest / principal) * 100).toFixed(2) : '0.00'

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Inputs */}
      <div className="card p-6 space-y-5">
        <div>
          <h3 className="text-base font-semibold text-gray-800 mb-1">FD Simulator</h3>
          <p className="text-xs text-gray-500">
            Amounts in{' '}
            <span className="font-semibold text-primary-600">
              {currency.symbol} {currency.code}
            </span>{' '}
            — compounded quarterly
          </p>
        </div>

        {/* Principal */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            Principal Amount ({currency.code})
          </label>
          <input
            type="number"
            value={principal}
            onChange={(e) => setPrincipal(Math.max(minPrincipal, Number(e.target.value)))}
            min={minPrincipal}
            step={stepPrincipal}
            className="input-field text-sm font-semibold"
            placeholder="Enter principal"
          />
          <input
            type="range"
            min={minPrincipal}
            max={maxPrincipal}
            step={stepPrincipal}
            value={principal}
            onChange={(e) => setPrincipal(Number(e.target.value))}
            className="w-full mt-2 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
          />
          <div className="flex justify-between text-xs text-gray-400 mt-0.5">
            <span>{formatRawCompact(minPrincipal)}</span>
            <span>{formatRawCompact(maxPrincipal)}</span>
          </div>
        </div>

        {/* Rate */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            <span className="flex items-center gap-1.5">
              <Percent className="w-3.5 h-3.5 text-gray-500" />
              Interest Rate (% p.a.)
            </span>
          </label>
          <input
            type="number"
            value={rate}
            onChange={(e) => setRate(Math.min(20, Math.max(1, Number(e.target.value))))}
            min={1}
            max={20}
            step={0.25}
            className="input-field text-sm font-semibold"
          />
          <input
            type="range"
            min={4}
            max={12}
            step={0.25}
            value={rate}
            onChange={(e) => setRate(Number(e.target.value))}
            className="w-full mt-2 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
          />
          <div className="flex justify-between text-xs text-gray-400 mt-0.5">
            <span>4%</span><span>12%</span>
          </div>
        </div>

        {/* Tenure */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            <span className="flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-gray-500" />
              Tenure
            </span>
          </label>
          <div className="flex gap-2">
            <input
              type="number"
              value={tenureValue}
              onChange={(e) => setTenureValue(Math.max(1, Number(e.target.value)))}
              min={1}
              className="input-field text-sm font-semibold flex-1"
            />
            <div className="flex rounded-lg border border-gray-300 overflow-hidden">
              {TENURE_UNITS.map((u) => (
                <button
                  key={u.value}
                  onClick={() => {
                    const days = toDays(tenureValue, tenureUnit)
                    if (u.value === 'days')   setTenureValue(days)
                    else if (u.value === 'months') setTenureValue(Math.round(days / 30.44))
                    else setTenureValue(Math.round(days / 365))
                    setTenureUnit(u.value)
                  }}
                  className={`px-3 py-2 text-xs font-medium transition-colors ${
                    tenureUnit === u.value
                      ? 'bg-primary-600 text-white'
                      : 'bg-white text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  {u.label}
                </button>
              ))}
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-1">= {tenureDays} days</p>
        </div>
      </div>

      {/* Results */}
      <div className="space-y-4">
        <div className="card p-5 bg-gradient-to-br from-green-600 to-emerald-700 border-0">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp className="w-4 h-4 text-green-200" />
            <p className="text-sm text-green-200">Maturity Amount</p>
          </div>
          <p className="text-3xl font-bold text-white">{formatRaw(Math.round(maturity))}</p>
          <p className="text-xs text-green-300 mt-1">
            After {tenureDays} days at {rate}% p.a.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="card p-4">
            <p className="text-xs text-gray-500 mb-1">Interest Earned</p>
            <p className="text-lg font-bold text-primary-700">{formatRawCompact(Math.round(interest))}</p>
            <p className="text-xs text-gray-400">{interestPct}% of principal</p>
          </div>
          <div className="card p-4">
            <p className="text-xs text-gray-500 mb-1">Effective Yield</p>
            <p className="text-lg font-bold text-gray-800">{effYield.toFixed(2)}%</p>
            <p className="text-xs text-gray-400">Per annum (effective)</p>
          </div>
        </div>

        <div className="card p-4">
          <p className="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-3">Summary</p>
          <div className="space-y-2.5">
            {[
              { label: 'Principal',                      value: formatRaw(principal),              color: 'text-gray-700' },
              { label: 'Interest (quarterly compound)',  value: formatRaw(Math.round(interest)),   color: 'text-primary-600' },
              { label: 'Total Maturity Value',           value: formatRaw(Math.round(maturity)),   color: 'text-green-700', bold: true },
              { label: 'Tenure',                        value: `${tenureDays} days (${(tenureDays / 365).toFixed(2)} yrs)`, color: 'text-gray-600' },
              { label: 'Effective Annual Yield',        value: `${effYield.toFixed(2)}%`,         color: 'text-gray-600' },
            ].map(({ label, value, color, bold }) => (
              <div key={label} className="flex justify-between items-center py-1 border-b border-gray-50 last:border-0">
                <span className="text-xs text-gray-500">{label}</span>
                <span className={`text-sm font-${bold ? 'bold' : 'semibold'} ${color}`}>{value}</span>
              </div>
            ))}
          </div>
        </div>

        <p className="text-xs text-gray-400 text-center">
          * Compounded quarterly. Tax deducted as per local regulations.
        </p>
      </div>
    </div>
  )
}
