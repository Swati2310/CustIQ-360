import React, { useState, useMemo, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { Percent, Calendar, TrendingDown } from 'lucide-react'
import { useCurrency } from '../../context/CurrencyContext.jsx'

function calculateEMI(principal, annualRate, tenureMonths) {
  if (!principal || !annualRate || !tenureMonths) return { emi: 0, totalInterest: 0, totalPayment: 0 }
  const monthlyRate = annualRate / 12 / 100
  if (monthlyRate === 0) {
    const emi = principal / tenureMonths
    return { emi, totalInterest: 0, totalPayment: principal }
  }
  const emi = (principal * monthlyRate * Math.pow(1 + monthlyRate, tenureMonths)) /
    (Math.pow(1 + monthlyRate, tenureMonths) - 1)
  const totalPayment = emi * tenureMonths
  const totalInterest = totalPayment - principal
  return { emi, totalInterest, totalPayment }
}

function SliderInput({ label, icon: Icon, value, min, max, step, onChange, format }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1.5">
          {Icon && <Icon className="w-3.5 h-3.5 text-gray-500" />}
          <span className="text-sm font-medium text-gray-700">{label}</span>
        </div>
        <input
          type="number"
          value={value}
          min={min}
          max={max}
          step={step}
          onChange={(e) => onChange(Number(e.target.value))}
          className="w-28 text-right border border-gray-300 rounded-lg px-2.5 py-1 text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
      />
      <div className="flex justify-between text-xs text-gray-400 mt-1">
        <span>{format(min)}</span>
        <span>{format(max)}</span>
      </div>
    </div>
  )
}

export default function EMICalculator() {
  const { currency, formatRaw, formatRawCompact } = useCurrency()

  // Scale ranges to active currency (rate converts 1 INR → local)
  const r = currency.rate
  const minPrincipal  = Math.max(1, Math.round(100000  * r / 100)  * 100)
  const maxPrincipal  = Math.max(1, Math.round(10000000 * r / 1000) * 1000)
  const stepPrincipal = Math.max(1, Math.round(50000   * r / 100)  * 100)
  const defaultPrincipal = Math.max(minPrincipal, Math.round(1000000 * r / 1000) * 1000)

  const [principal, setPrincipal] = useState(defaultPrincipal)
  const [rate, setRate] = useState(10)
  const [tenure, setTenure] = useState(120)

  // Reset principal when currency changes so it stays in-range
  useEffect(() => { setPrincipal(defaultPrincipal) }, [currency.code])

  const { emi, totalInterest, totalPayment } = useMemo(
    () => calculateEMI(principal, rate, tenure),
    [principal, rate, tenure]
  )

  const chartData = [
    { name: 'Principal', value: Math.round(principal),    fill: '#4f46e5' },
    { name: 'Interest',  value: Math.round(totalInterest), fill: '#f59e0b' },
    { name: 'Total',     value: Math.round(totalPayment),  fill: '#10b981' },
  ]

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null
    return (
      <div className="bg-white border border-gray-200 rounded-lg shadow-lg px-3 py-2 text-xs">
        {payload.map((p) => (
          <div key={p.name} className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: p.fill }} />
            <span className="text-gray-600">{p.name}:</span>
            <span className="font-semibold text-gray-900">{formatRaw(p.value)}</span>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Inputs */}
      <div className="card p-6 space-y-6">
        <div>
          <h3 className="text-base font-semibold text-gray-800 mb-1">EMI Calculator</h3>
          <p className="text-xs text-gray-500">
            Amounts in{' '}
            <span className="font-semibold text-primary-600">
              {currency.symbol} {currency.code}
            </span>{' '}
            — adjust parameters to calculate monthly EMI
          </p>
        </div>

        <SliderInput
          label={`Loan Amount (${currency.code})`}
          value={principal}
          min={minPrincipal}
          max={maxPrincipal}
          step={stepPrincipal}
          onChange={setPrincipal}
          format={(v) => formatRawCompact(v)}
        />

        <SliderInput
          label="Interest Rate (% p.a.)"
          icon={Percent}
          value={rate}
          min={6}
          max={24}
          step={0.5}
          onChange={setRate}
          format={(v) => `${v}%`}
        />

        <SliderInput
          label="Tenure (months)"
          icon={Calendar}
          value={tenure}
          min={12}
          max={360}
          step={12}
          onChange={setTenure}
          format={(v) => `${v}m`}
        />
      </div>

      {/* Results */}
      <div className="space-y-4">
        <div className="grid grid-cols-1 gap-3">
          <div className="card p-5 bg-primary-600 border-primary-600">
            <div className="flex items-center gap-2 mb-1">
              <TrendingDown className="w-4 h-4 text-primary-200" />
              <p className="text-sm text-primary-200">Monthly EMI</p>
            </div>
            <p className="text-3xl font-bold text-white">{formatRaw(Math.round(emi))}</p>
            <p className="text-xs text-primary-300 mt-1">per month for {tenure} months</p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="card p-4">
              <p className="text-xs text-gray-500 mb-1">Total Interest</p>
              <p className="text-lg font-bold text-amber-600">{formatRawCompact(Math.round(totalInterest))}</p>
              <p className="text-xs text-gray-400">
                {totalPayment > 0 ? Math.round((totalInterest / totalPayment) * 100) : 0}% of total
              </p>
            </div>
            <div className="card p-4">
              <p className="text-xs text-gray-500 mb-1">Total Payment</p>
              <p className="text-lg font-bold text-gray-800">{formatRawCompact(Math.round(totalPayment))}</p>
              <p className="text-xs text-gray-400">Principal + Interest</p>
            </div>
          </div>
        </div>

        {/* Bar chart */}
        <div className="card p-4">
          <p className="text-xs font-semibold text-gray-600 mb-3 uppercase tracking-wider">
            Principal vs Interest Breakdown
          </p>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={chartData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
              <YAxis
                tick={{ fontSize: 10, fill: '#6b7280' }}
                tickFormatter={(v) => formatRawCompact(v)}
                axisLine={false}
                tickLine={false}
                width={70}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {chartData.map((entry, idx) => (
                  <Cell key={idx} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
