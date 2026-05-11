import React, { useState } from 'react'
import { Landmark, Eye, EyeOff, LogIn, Globe2, ShieldCheck } from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'

export default function LoginPage() {
  const { login } = useAuth()
  const [employeeId, setEmployeeId] = useState('')
  const [password, setPassword]     = useState('')
  const [showPass, setShowPass]     = useState(false)
  const [error, setError]           = useState('')
  const [loading, setLoading]       = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    if (!employeeId.trim() || !password) {
      setError('Please enter both Employee ID and password.')
      return
    }
    setLoading(true)
    await new Promise((r) => setTimeout(r, 700))
    const result = login(employeeId, password)
    if (!result.ok) setError(result.error)
    setLoading(false)
  }

  return (
    <div className="min-h-screen relative flex items-center justify-center p-4 overflow-hidden bg-[#0f0c29]">

      {/* Animated gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#0f0c29] via-[#302b63] to-[#24243e]" />

      {/* Animated blobs */}
      <div className="absolute top-[-10%] left-[-10%] w-[480px] h-[480px] rounded-full opacity-20 animate-blob"
        style={{ background: 'radial-gradient(circle, #6366f1, #8b5cf6)', filter: 'blur(60px)' }} />
      <div className="absolute bottom-[-15%] right-[-5%] w-[520px] h-[520px] rounded-full opacity-15 animate-blob-slow"
        style={{ background: 'radial-gradient(circle, #4f46e5, #7c3aed)', filter: 'blur(80px)', animationDelay: '3s' }} />
      <div className="absolute top-[40%] right-[20%] w-[300px] h-[300px] rounded-full opacity-10 animate-float-slow"
        style={{ background: 'radial-gradient(circle, #818cf8, #6366f1)', filter: 'blur(50px)' }} />

      {/* Floating particles */}
      {[...Array(6)].map((_, i) => (
        <div
          key={i}
          className="absolute w-1 h-1 bg-white/30 rounded-full animate-float"
          style={{
            left: `${15 + i * 14}%`,
            top: `${20 + (i % 3) * 25}%`,
            animationDelay: `${i * 0.8}s`,
            animationDuration: `${4 + i}s`,
          }}
        />
      ))}

      {/* Card */}
      <div className="relative w-full max-w-md animate-slide-up" style={{ animationDelay: '100ms' }}>
        {/* Glow ring behind card */}
        <div className="absolute -inset-0.5 bg-gradient-to-r from-primary-600 to-violet-600 rounded-3xl opacity-40 blur-sm" />

        <div className="relative bg-white/10 backdrop-blur-xl rounded-3xl overflow-hidden border border-white/20 shadow-2xl">

          {/* Header */}
          <div className="px-8 pt-8 pb-6 text-center">
            {/* Logo */}
            <div className="flex items-center justify-center mb-6">
              <div className="relative">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-violet-600 flex items-center justify-center shadow-glow animate-float">
                  <Landmark className="w-8 h-8 text-white" />
                </div>
                <div className="absolute -top-1 -right-1 w-5 h-5 bg-emerald-400 rounded-full border-2 border-white/20 flex items-center justify-center">
                  <ShieldCheck className="w-2.5 h-2.5 text-white" />
                </div>
              </div>
            </div>

            <h1 className="text-2xl font-bold text-white mb-1">CustIQ 360°</h1>
            <p className="text-sm text-white/60 mb-1">Banking Intelligence Platform</p>
            <div className="flex items-center justify-center gap-1.5 text-xs text-white/40">
              <Globe2 className="w-3 h-3" />
              <span>Global Relationship Manager Portal</span>
            </div>
          </div>

          {/* Divider */}
          <div className="mx-8 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent mb-6" />

          {/* Form */}
          <form onSubmit={handleSubmit} className="px-8 pb-8 space-y-4">
            {/* Employee ID */}
            <div className="animate-slide-up stagger-2">
              <label className="block text-xs font-semibold text-white/70 uppercase tracking-wider mb-2">
                Employee ID
              </label>
              <input
                type="text"
                value={employeeId}
                onChange={(e) => setEmployeeId(e.target.value)}
                placeholder="e.g. RM-IND-001"
                autoComplete="username"
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-sm text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all backdrop-blur-sm"
              />
            </div>

            {/* Password */}
            <div className="animate-slide-up stagger-3">
              <label className="block text-xs font-semibold text-white/70 uppercase tracking-wider mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPass ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  className="w-full px-4 py-3 pr-11 bg-white/10 border border-white/20 rounded-xl text-sm text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all backdrop-blur-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowPass((p) => !p)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/80 transition-colors"
                  tabIndex={-1}
                >
                  {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="animate-scale-in bg-red-500/20 border border-red-400/30 rounded-xl px-4 py-3">
                <p className="text-sm text-red-300">{error}</p>
              </div>
            )}

            {/* Submit */}
            <div className="animate-slide-up stagger-4 pt-2">
              <button
                type="submit"
                disabled={loading}
                className="w-full relative flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold text-white transition-all duration-200 active:scale-95 disabled:opacity-60 overflow-hidden group"
                style={{ background: 'linear-gradient(135deg, #4f46e5, #7c3aed)' }}
              >
                {/* Shimmer overlay on hover */}
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
                {loading ? (
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <LogIn className="w-4 h-4" />
                )}
                {loading ? 'Authenticating…' : 'Sign In to Portal'}
              </button>
            </div>

            <p className="text-center text-xs text-white/30 pt-1">
              Forgot credentials? Contact{' '}
              <span className="text-primary-300 font-medium cursor-pointer hover:text-primary-200 transition-colors">
                IT Support
              </span>
            </p>
          </form>
        </div>
      </div>

      {/* Footer */}
      <p className="absolute bottom-5 text-xs text-white/20 tracking-wide">
        © 2025 CustIQ 360° · Secure · Encrypted · Global
      </p>
    </div>
  )
}
