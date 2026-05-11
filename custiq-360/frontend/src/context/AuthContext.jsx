import React, { createContext, useContext, useState } from 'react'

// ID format: RM-[ISO3 country code]-[sequence]
const MOCK_USERS = [
  // APAC
  { id: 'RM-IND-001', name: 'Arjun Sharma',    email: 'arjun.sharma@custiq.com',    region: 'APAC', country: 'India',        branch: 'Mumbai – Bandra Kurla Complex', password: 'rm@1234' },
  { id: 'RM-SGP-001', name: 'Wei Ling Tan',    email: 'weiling.tan@custiq.com',     region: 'APAC', country: 'Singapore',    branch: 'Singapore – Raffles Place',     password: 'rm@1234' },
  { id: 'RM-HKG-001', name: 'James Wong',      email: 'james.wong@custiq.com',      region: 'APAC', country: 'Hong Kong',    branch: 'Hong Kong – Central',           password: 'rm@1234' },
  { id: 'RM-AUS-001', name: 'Claire Thompson', email: 'claire.thompson@custiq.com', region: 'APAC', country: 'Australia',    branch: 'Sydney – CBD',                  password: 'rm@1234' },
  // EMEA
  { id: 'RM-GBR-001', name: 'Sarah Mitchell',  email: 'sarah.mitchell@custiq.com',  region: 'EMEA', country: 'United Kingdom', branch: 'London – Canary Wharf',       password: 'rm@1234' },
  { id: 'RM-UAE-001', name: 'Fatima Al-Rashid',email: 'fatima.alrashid@custiq.com', region: 'EMEA', country: 'UAE',           branch: 'Dubai – DIFC',                  password: 'rm@1234' },
  { id: 'RM-DEU-001', name: 'Klaus Müller',    email: 'klaus.muller@custiq.com',    region: 'EMEA', country: 'Germany',       branch: 'Frankfurt – Bankenviertel',     password: 'rm@1234' },
  // AMER
  { id: 'RM-USA-001', name: 'Michael Carter',  email: 'michael.carter@custiq.com',  region: 'AMER', country: 'United States', branch: 'New York – Manhattan',          password: 'rm@1234' },
  { id: 'RM-BRA-001', name: 'Ana Oliveira',    email: 'ana.oliveira@custiq.com',    region: 'AMER', country: 'Brazil',        branch: 'São Paulo – Faria Lima',        password: 'rm@1234' },
]

const SESSION_KEY = 'custiq_rm_session'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const raw = sessionStorage.getItem(SESSION_KEY)
      return raw ? JSON.parse(raw) : null
    } catch {
      return null
    }
  })

  function login(employeeId, password) {
    const match = MOCK_USERS.find(
      (u) => u.id.toLowerCase() === employeeId.trim().toLowerCase() && u.password === password
    )
    if (!match) return { ok: false, error: 'Invalid Employee ID or password.' }
    const { password: _, ...safeUser } = match
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(safeUser))
    setUser(safeUser)
    return { ok: true }
  }

  function logout() {
    sessionStorage.removeItem(SESSION_KEY)
    setUser(null)
  }

  return <AuthContext.Provider value={{ user, login, logout }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
