import React, { useState, useMemo, useEffect } from 'react'
import { ArrowLeftRight, TrendingDown, Check, X } from 'lucide-react'
import { useCurrency } from '../../context/CurrencyContext.jsx'

function calculateEMI(principal, annualRate, tenureMonths) {
  if (!principal || !annualRate || !tenureMonths) return { emi: 0, totalInterest: 0, totalPayment: 0 }
  const monthlyRate = annualRate / 12 / 100
  if (monthlyRate === 0) {
    return { emi: principal / tenureMonths, totalInterest: 0, totalPayment: principal }
  }
  const emi = (principal * monthlyRate * Math.pow(1 + monthlyRate, tenureMonths)) /
    (Math.pow(1 + monthlyRate, tenureMonths) - 1)
  const totalPayment = emi * tenureMonths
  return { emi, totalInterest: totalPayment - principal, totalPayment }
}

function ScenarioForm({ title, values, onChange, color, currency }) {
  const fields = [
    { key: 'principal', label: `Loan Amount (${currency.code})`, min: 1, max: 999999999, step: 1 },
    { key: 'rate',      label: 'Interest Rate (%)',              min: 6, max: 24,        step: 0.25 },
    { key: 'tenure',    label: 'Tenure (months)',                min: 12, max: 360,      step: 12 },
  ]

  return (
    <div className={`card p-5 border-t-4 ${color}`}>
      <h4 className="text-sm font-bold text-gray-800 mb-4">{title}</h4>
      <div className="space-y-4">
        {fields.map(({ key, label, min, max, step }) => (
          <div key={key}>
            <label className="block text-xs font-medium text-gray-600 mb-1.5">{label}</label>
            <input
              type="number"
              value={values[key]}
              onChange={(e) => onChange(key, Math.max(min, Math.min(max, Number(e.target.value))))}
              min={min}
              max={max}
              step={step}
              className="input-field text-sm font-semibold"
            />
            <input
              type="range"
              min={min}
              max={max}
              step={step}
              value={values[key]}
              onChange={(e) => onChange(key, Number(e.target.value))}
              className="w-full mt-1.5 h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
            />
          </div>
        ))}
      </div>
    </div>
  )
}

function DiffCell({ a, b, format, higherIsBetter = false }) {
  const diff = b - a
  const pct = a !== 0 ? ((diff / a) * 100).toFixed(1) : '0.0'
  const better = higherIsBetter ? diff > 0 : diff < 0
  const neutral = diff === 0

  return (
    <div className="text-right">
      {neutral ? (
        <span className="text-xs text-gray-400">Equal</span>
      ) : (
        <span className={`flex items-center justify-end gap-1 text-xs font-semibold ${better ? 'text-green-600' : 'text-red-600'}`}>
          {better ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
          {diff > 0 ? '+' : ''}{format(Math.round(diff))}
          <span className="font-normal text-gray-400">({diff > 0 ? '+' : ''}{pct}%)</span>
        </span>
      )}
    </div>
  )
}

export default function LoanScenario() {
  const { currency, formatRaw, formatRawCompact } = useCurrency()

  const r = currency.rate
  const defaultPrincipal = Math.max(1, Math.round(2000000 * r / 1000) * 1000)

  const [sc1, setSc1] = useState({ principal: defaultPrincipal, rate: 10,  tenure: 240 })
  const [sc2, setSc2] = useState({ principal: defaultPrincipal, rate: 8.5, tenure: 180 })

  // Reset principals when currency changes
  useEffect(() => {
    const p = Math.max(1, Math.round(2000000 * r / 1000) * 1000)
    setSc1((prev) => ({ ...prev, principal: p }))
    setSc2((prev) => ({ ...prev, principal: p }))
  }, [currency.code])

  const res1 = useMemo(() => calculateEMI(sc1.principal, sc1.rate, sc1.tenure), [sc1])
  const res2 = useMemo(() => calculateEMI(sc2.principal, sc2.rate, sc2.tenure), [sc2])

  const update1 = (key, val) => setSc1((p) => ({ ...p, [key]: val }))
  const update2 = (key, val) => setSc2((p) => ({ ...p, [key]: val }))

  const rows = [
    { label: 'Monthly EMI',    a: res1.emi,           b: res2.emi,           format: (v) => formatRaw(Math.round(Math.abs(v))),        higherIsBetter: false },
    { label: 'Total Interest', a: res1.totalInterest, b: res2.totalInterest, format: (v) => formatRawCompact(Math.abs(v)),              higherIsBetter: false },
    { label: 'Total Payment',  a: res1.totalPayment,  b: res2.totalPayment,  format: (v) => formatRawCompact(Math.abs(v)),              higherIsBetter: false },
  ]

  const winner = res1.totalInterest < res2.totalInterest ? 'A'
    : res2.totalInterest < res1.totalInterest ? 'B' : null

  return (
    <div className="space-y-6">
      {/* Currency note */}
      <p className="text-xs text-gray-500">
        Amounts in{' '}
        <span className="font-semibold text-primary-600">{currency.symbol} {currency.code}</span>
      </p>

      {/* Scenario forms */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <ScenarioForm title="Scenario A" values={sc1} onChange={update1} color="border-primary-500" currency={currency} />
        <ScenarioForm title="Scenario B" values={sc2} onChange={update2} color="border-amber-500"   currency={currency} />
      </div>

      {/* Comparison badge */}
      {winner && (
        <div className={`flex items-center justify-center gap-2 py-3 px-4 rounded-xl ${
          winner === 'A' ? 'bg-primary-50 border border-primary-200' : 'bg-amber-50 border border-amber-200'
        }`}>
          <TrendingDown className={`w-5 h-5 ${winner === 'A' ? 'text-primary-600' : 'text-amber-600'}`} />
          <p className={`text-sm font-semibold ${winner === 'A' ? 'text-primary-700' : 'text-amber-700'}`}>
            Scenario {winner} saves {formatRaw(Math.round(Math.abs(res1.totalInterest - res2.totalInterest)))} in total interest
          </p>
        </div>
      )}

      {/* Comparison table */}
      <div className="card overflow-hidden">
        <div className="bg-gray-50 px-5 py-3 border-b border-gray-100">
          <div className="grid grid-cols-4 gap-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">
            <span>Metric</span>
            <span className="text-center text-primary-700">Scenario A</span>
            <span className="text-center text-amber-700">Scenario B</span>
            <span className="text-right">Difference (B − A)</span>
          </div>
        </div>

        <div className="divide-y divide-gray-50">
          {[
            { label: 'Principal', a: sc1.principal, b: sc2.principal, format: formatRaw },
            { label: 'Rate (p.a.)', a: sc1.rate, b: sc2.rate, format: (v) => `${v}%` },
            { label: 'Tenure',    a: sc1.tenure,    b: sc2.tenure,    format: (v) => `${v} mo` },
          ].map(({ label, a, b, format }) => (
            <div key={label} className="px-5 py-3 grid grid-cols-4 gap-4 items-center">
              <span className="text-xs text-gray-500">{label}</span>
              <span className="text-sm font-medium text-primary-700 text-center">{format(a)}</span>
              <span className="text-sm font-medium text-amber-700 text-center">{format(b)}</span>
              <span className="text-xs text-gray-400 text-right">—</span>
            </div>
          ))}

          {rows.map(({ label, a, b, format, higherIsBetter }) => (
            <div key={label} className="px-5 py-3 grid grid-cols-4 gap-4 items-center bg-white hover:bg-gray-50 transition-colors">
              <span className="text-sm font-medium text-gray-700">{label}</span>
              <span className="text-sm font-bold text-primary-700 text-center">{format(a)}</span>
              <span className="text-sm font-bold text-amber-700 text-center">{format(b)}</span>
              <DiffCell a={a} b={b} format={format} higherIsBetter={higherIsBetter} />
            </div>
          ))}
        </div>
      </div>

      <div className="flex justify-center">
        <div className="flex items-center gap-3">
          <div className="px-4 py-2 bg-primary-100 text-primary-700 rounded-xl text-sm font-bold">A</div>
          <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
            <ArrowLeftRight className="w-4 h-4 text-gray-500" />
          </div>
          <div className="px-4 py-2 bg-amber-100 text-amber-700 rounded-xl text-sm font-bold">B</div>
        </div>
      </div>
    </div>
  )
}
