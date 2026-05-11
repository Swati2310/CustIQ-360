import axios from 'axios'

// In dev: Vite proxies /api → localhost:8000 (vite.config.js)
// In production: set VITE_API_BASE_URL to your Render backend URL
const BASE = import.meta.env.VITE_API_BASE_URL || ''

const api = axios.create({
  baseURL: `${BASE}/api`,
  headers: { 'Content-Type': 'application/json' },
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'An error occurred'
    return Promise.reject(new Error(message))
  }
)

// Customers
export const getCustomers = (search = '', page = 1, limit = 20) =>
  api.get('/customers', { params: { search, page, limit } })

export const getCustomer = (id) => api.get(`/customers/${id}`)

export const getCustomerAccounts = (id) => api.get(`/customers/${id}/accounts`)

export const getCustomerLoans = (id) => api.get(`/customers/${id}/loans`)

export const getCustomerWealth = (id) => api.get(`/customers/${id}/wealth`)

export const getCustomerKYC = (id) => api.get(`/customers/${id}/kyc`)

export const getRecommendations = (id) => api.get(`/recommendations/${id}`)

export const searchCustomers = (query) =>
  api.get('/customers', { params: { search: query, limit: 8 } })

// Chat (streaming SSE)
export const sendChat = (message, customerId = null, history = []) => {
  const params = new URLSearchParams()
  params.set('message', message)
  if (customerId) params.set('customer_id', customerId)
  if (history.length > 0) params.set('history', JSON.stringify(history))

  return fetch(`${BASE}/api/chat?${params.toString()}`, {
    method: 'GET',
    headers: { Accept: 'text/event-stream' },
  })
}

export const sendChatPost = async (message, customerId = null, history = []) => {
  const body = { message, history }
  if (customerId) body.customer_id = customerId

  return fetch(`${BASE}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify(body),
  })
}

// Alerts
export const getAlerts = () => api.get('/alerts')

// Simulators
export const simulateEMI = (principal, rate, tenure) =>
  api.post('/simulate/emi', { principal, rate_percent: rate, tenure_months: tenure })

export const simulateFD = (principal, rate, tenure_days) =>
  api.post('/simulate/fd', { principal, rate_percent: rate, tenure_days })

// Document extraction
export const extractDocument = async (file, docType) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('doc_type', docType)
  return api.post('/documents/extract', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const applyExtraction = (customerId, docType, extractedData) =>
  api.patch(`/customers/${customerId}/apply-extraction`, {
    doc_type: docType,
    extracted_data: extractedData,
  })

export default api
