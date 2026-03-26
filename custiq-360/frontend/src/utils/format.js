/**
 * Format a number as Indian currency (₹1,23,456)
 */
export function formatINR(amount) {
  if (amount === null || amount === undefined || isNaN(amount)) return '₹0'
  const num = Number(amount)
  const formatted = new Intl.NumberFormat('en-IN', {
    maximumFractionDigits: 0,
  }).format(Math.abs(num))
  return `${num < 0 ? '-' : ''}₹${formatted}`
}

/**
 * Format a large number in lakhs/crores
 */
export function formatINRCompact(amount) {
  if (amount === null || amount === undefined || isNaN(amount)) return '₹0'
  const num = Number(amount)
  if (Math.abs(num) >= 1e7) {
    return `₹${(num / 1e7).toFixed(2)} Cr`
  }
  if (Math.abs(num) >= 1e5) {
    return `₹${(num / 1e5).toFixed(2)} L`
  }
  return formatINR(num)
}

/**
 * Format a date string
 */
export function formatDate(dateStr) {
  if (!dateStr) return '-'
  try {
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    })
  } catch {
    return dateStr
  }
}

/**
 * Get initials from a name
 */
export function getInitials(name) {
  if (!name) return '?'
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((n) => n[0].toUpperCase())
    .join('')
}

/**
 * Days until a date
 */
export function daysUntil(dateStr) {
  if (!dateStr) return null
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const target = new Date(dateStr)
  target.setHours(0, 0, 0, 0)
  return Math.floor((target - today) / (1000 * 60 * 60 * 24))
}

/**
 * Segment color mapping
 */
export function segmentColor(segment) {
  switch ((segment || '').toLowerCase()) {
    case 'hni':
      return 'bg-amber-100 text-amber-800'
    case 'affluent':
      return 'bg-blue-100 text-blue-800'
    case 'mass':
    default:
      return 'bg-gray-100 text-gray-700'
  }
}

/**
 * Status color for loans/accounts
 */
export function statusColor(status) {
  switch ((status || '').toLowerCase()) {
    case 'active':
      return 'bg-green-100 text-green-800'
    case 'closed':
      return 'bg-gray-100 text-gray-600'
    case 'npa':
    case 'overdue':
      return 'bg-red-100 text-red-800'
    case 'pending':
      return 'bg-yellow-100 text-yellow-800'
    default:
      return 'bg-gray-100 text-gray-700'
  }
}

/**
 * Severity color
 */
export function severityColor(severity) {
  switch ((severity || '').toUpperCase()) {
    case 'HIGH':
      return { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700', badge: 'bg-red-100 text-red-800' }
    case 'MEDIUM':
      return { bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-700', badge: 'bg-amber-100 text-amber-800' }
    case 'LOW':
    default:
      return { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700', badge: 'bg-blue-100 text-blue-800' }
  }
}
