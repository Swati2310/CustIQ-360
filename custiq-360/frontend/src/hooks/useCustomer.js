import { useState, useEffect, useCallback } from 'react'
import {
  getCustomer,
  getCustomerAccounts,
  getCustomerLoans,
  getCustomerWealth,
  getCustomerKYC,
} from '../utils/api.js'

export default function useCustomer(customerId) {
  const [customer, setCustomer] = useState(null)
  const [accounts, setAccounts] = useState([])
  const [loans, setLoans] = useState([])
  const [wealth, setWealth] = useState([])
  const [kyc, setKYC] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchAll = useCallback(async () => {
    if (!customerId) return
    setLoading(true)
    setError(null)
    try {
      const [custRes, accRes, loanRes, wealthRes, kycRes] = await Promise.allSettled([
        getCustomer(customerId),
        getCustomerAccounts(customerId),
        getCustomerLoans(customerId),
        getCustomerWealth(customerId),
        getCustomerKYC(customerId),
      ])

      if (custRes.status === 'fulfilled') setCustomer(custRes.value.data)
      else throw new Error(custRes.reason?.message || 'Failed to load customer')

      if (accRes.status === 'fulfilled') setAccounts(accRes.value.data || [])
      if (loanRes.status === 'fulfilled') setLoans(loanRes.value.data || [])
      if (wealthRes.status === 'fulfilled') setWealth(wealthRes.value.data || [])
      if (kycRes.status === 'fulfilled') setKYC(kycRes.value.data)
    } catch (err) {
      setError(err.message || 'Failed to load customer data')
    } finally {
      setLoading(false)
    }
  }, [customerId])

  useEffect(() => {
    fetchAll()
  }, [fetchAll])

  return {
    customer,
    accounts,
    loans,
    wealth,
    kyc,
    loading,
    error,
    refetch: fetchAll,
  }
}
