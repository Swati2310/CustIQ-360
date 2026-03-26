import React, { createContext, useContext, useState } from 'react'

/**
 * Supported currencies for APAC / SEPA / EMEA regions.
 * Rates are approximate INR → target currency conversions.
 * In production these should be fetched from a live forex API.
 */
export const CURRENCIES = [
  { code: 'INR', symbol: '₹',    name: 'Indian Rupee',        region: 'South Asia', rate: 1,       locale: 'en-IN' },
  { code: 'USD', symbol: '$',    name: 'US Dollar',           region: 'Americas',   rate: 0.012,   locale: 'en-US' },
  { code: 'EUR', symbol: '€',    name: 'Euro',                region: 'SEPA',       rate: 0.011,   locale: 'de-DE' },
  { code: 'GBP', symbol: '£',    name: 'British Pound',       region: 'EMEA',       rate: 0.0095,  locale: 'en-GB' },
  { code: 'SGD', symbol: 'S$',   name: 'Singapore Dollar',    region: 'APAC',       rate: 0.016,   locale: 'en-SG' },
  { code: 'AED', symbol: 'د.إ',  name: 'UAE Dirham',          region: 'EMEA',       rate: 0.044,   locale: 'en-AE' },
  { code: 'JPY', symbol: '¥',    name: 'Japanese Yen',        region: 'APAC',       rate: 1.78,    locale: 'ja-JP' },
  { code: 'AUD', symbol: 'A$',   name: 'Australian Dollar',   region: 'APAC',       rate: 0.019,   locale: 'en-AU' },
  { code: 'HKD', symbol: 'HK$',  name: 'Hong Kong Dollar',    region: 'APAC',       rate: 0.094,   locale: 'zh-HK' },
  { code: 'SAR', symbol: 'SR',   name: 'Saudi Riyal',         region: 'EMEA',       rate: 0.045,   locale: 'en-SA' },
  { code: 'MYR', symbol: 'RM',   name: 'Malaysian Ringgit',   region: 'APAC',       rate: 0.056,   locale: 'ms-MY' },
  { code: 'ZAR', symbol: 'R',    name: 'South African Rand',  region: 'EMEA',       rate: 0.22,    locale: 'en-ZA' },
]

const CurrencyContext = createContext(null)

export function CurrencyProvider({ children }) {
  const [currencyCode, setCurrencyCode] = useState('INR')

  const currency = CURRENCIES.find((c) => c.code === currencyCode) || CURRENCIES[0]

  /** Set currency by code; falls back to INR if unknown */
  const setCurrency = (code) => {
    const valid = CURRENCIES.find((c) => c.code === code)
    setCurrencyCode(valid ? code : 'INR')
  }

  /** Convert INR amount and format with selected currency symbol */
  const formatAmount = (amountInINR) => {
    if (amountInINR === null || amountInINR === undefined || isNaN(amountInINR)) {
      return `${currency.symbol}0`
    }
    const num = Number(amountInINR)
    const converted = num * currency.rate
    const decimals = currency.code === 'JPY' ? 0 : 0
    const formatted = new Intl.NumberFormat(currency.locale, {
      maximumFractionDigits: decimals,
    }).format(Math.abs(converted))
    return `${converted < 0 ? '-' : ''}${currency.symbol}${formatted}`
  }

  /** Compact format: crores/lakhs for INR, M/B/K for others */
  const formatCompact = (amountInINR) => {
    if (amountInINR === null || amountInINR === undefined || isNaN(amountInINR)) {
      return `${currency.symbol}0`
    }
    const num = Number(amountInINR)
    const converted = num * currency.rate
    const abs = Math.abs(converted)

    if (currency.code === 'INR') {
      if (abs >= 1e7) return `₹${(converted / 1e7).toFixed(2)} Cr`
      if (abs >= 1e5) return `₹${(converted / 1e5).toFixed(2)} L`
      return formatAmount(amountInINR)
    }

    if (abs >= 1e9) return `${currency.symbol}${(converted / 1e9).toFixed(2)}B`
    if (abs >= 1e6) return `${currency.symbol}${(converted / 1e6).toFixed(2)}M`
    if (abs >= 1e3) return `${currency.symbol}${(converted / 1e3).toFixed(1)}K`
    return formatAmount(amountInINR)
  }

  /**
   * Format a raw amount that is already in the active currency (no INR conversion).
   * Used by simulators where the user inputs/sees local-currency amounts directly.
   */
  const formatRaw = (amount) => {
    if (amount === null || amount === undefined || isNaN(amount)) return `${currency.symbol}0`
    const num = Number(amount)
    const abs = Math.abs(num)
    const formatted = new Intl.NumberFormat(currency.locale, { maximumFractionDigits: 0 }).format(abs)
    return `${num < 0 ? '-' : ''}${currency.symbol}${formatted}`
  }

  const formatRawCompact = (amount) => {
    if (amount === null || amount === undefined || isNaN(amount)) return `${currency.symbol}0`
    const num = Number(amount)
    const abs = Math.abs(num)
    if (currency.code === 'INR') {
      if (abs >= 1e7) return `₹${(num / 1e7).toFixed(2)} Cr`
      if (abs >= 1e5) return `₹${(num / 1e5).toFixed(2)} L`
    } else {
      if (abs >= 1e9) return `${currency.symbol}${(num / 1e9).toFixed(2)}B`
      if (abs >= 1e6) return `${currency.symbol}${(num / 1e6).toFixed(2)}M`
      if (abs >= 1e3) return `${currency.symbol}${(num / 1e3).toFixed(1)}K`
    }
    return formatRaw(amount)
  }

  return (
    <CurrencyContext.Provider value={{ currency, currencies: CURRENCIES, setCurrency, formatAmount, formatCompact, formatRaw, formatRawCompact }}>
      {children}
    </CurrencyContext.Provider>
  )
}

export function useCurrency() {
  const ctx = useContext(CurrencyContext)
  if (!ctx) throw new Error('useCurrency must be used within CurrencyProvider')
  return ctx
}
