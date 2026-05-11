import React from 'react'
import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Bell, Calculator, Landmark, Sparkles } from 'lucide-react'
import clsx from 'clsx'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', exact: true },
  { to: '/alerts', icon: Bell, label: 'Alerts' },
  { to: '/simulator', icon: Calculator, label: 'Simulator' },
]

export default function Sidebar() {
  return (
    <aside className="w-60 flex-shrink-0 flex flex-col h-screen animate-slide-in-left"
      style={{ background: 'linear-gradient(180deg, #1e1b4b 0%, #1e1b4b 60%, #16133a 100%)' }}>

      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-white/10">
        <div className="relative w-9 h-9 rounded-xl flex items-center justify-center shadow-glow flex-shrink-0"
          style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}>
          <Landmark className="w-4.5 h-4.5 text-white" size={18} />
          <div className="absolute -top-0.5 -right-0.5 w-3 h-3 bg-emerald-400 rounded-full border-2 border-[#1e1b4b]" />
        </div>
        <div>
          <p className="text-sm font-bold text-white leading-tight">CustIQ 360°</p>
          <p className="text-[10px] text-indigo-300/70 leading-tight">Banking Intelligence</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-5 space-y-1">
        <p className="text-[10px] font-bold text-indigo-300/40 uppercase tracking-widest px-3 mb-3">
          Navigation
        </p>

        {navItems.map(({ to, icon: Icon, label, exact }, i) => (
          <NavLink
            key={to}
            to={to}
            end={exact}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group relative overflow-hidden',
                'animate-slide-in-left',
                isActive
                  ? 'text-white'
                  : 'text-indigo-200/60 hover:text-white hover:bg-white/5'
              )
            }
            style={{ animationDelay: `${i * 60}ms` }}
          >
            {({ isActive }) => (
              <>
                {/* Active glow background */}
                {isActive && (
                  <div className="absolute inset-0 rounded-xl"
                    style={{ background: 'linear-gradient(135deg, rgba(99,102,241,0.35), rgba(139,92,246,0.20))' }} />
                )}
                {/* Active left bar */}
                {isActive && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-6 rounded-r-full bg-primary-400" />
                )}

                <div className={clsx(
                  'relative w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 transition-all duration-200',
                  isActive
                    ? 'shadow-glow-sm'
                    : 'group-hover:bg-white/10'
                )} style={isActive ? { background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' } : {}}>
                  <Icon className={clsx('w-4 h-4', isActive ? 'text-white' : 'text-indigo-300/70 group-hover:text-white')} />
                </div>

                <span className="relative">{label}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* AI badge at bottom */}
      <div className="px-4 py-4 border-t border-white/10">
        <div className="rounded-xl p-3.5 relative overflow-hidden"
          style={{ background: 'linear-gradient(135deg, rgba(99,102,241,0.25), rgba(139,92,246,0.15))' }}>
          <div className="absolute inset-0 border border-white/10 rounded-xl" />
          <div className="flex items-center gap-2 mb-1">
            <Sparkles className="w-3.5 h-3.5 text-primary-300 animate-pulse" />
            <p className="text-xs font-semibold text-white">AI-Powered</p>
          </div>
          <p className="text-[10px] text-indigo-300/60 leading-relaxed">
            Gemini 2.5 · LangGraph · RAG
          </p>
          <p className="text-[10px] text-indigo-300/40 mt-1">RM Portal v1.0.0</p>
        </div>
      </div>
    </aside>
  )
}
