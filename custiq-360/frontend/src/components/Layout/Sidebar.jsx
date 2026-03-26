import React from 'react'
import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Bell, Calculator, Landmark } from 'lucide-react'
import clsx from 'clsx'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', exact: true },
  { to: '/alerts', icon: Bell, label: 'Alerts' },
  { to: '/simulator', icon: Calculator, label: 'Simulator' },
]

export default function Sidebar() {
  return (
    <aside className="w-60 flex-shrink-0 bg-white border-r border-gray-200 flex flex-col h-screen">
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-gray-100">
        <div className="w-9 h-9 rounded-lg bg-primary-600 flex items-center justify-center shadow-sm">
          <Landmark className="w-5 h-5 text-white" />
        </div>
        <div>
          <p className="text-sm font-bold text-primary-700 leading-tight">CustIQ 360°</p>
          <p className="text-xs text-gray-400 leading-tight">Banking Intelligence</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider px-3 mb-3">
          Main Menu
        </p>
        {navItems.map(({ to, icon: Icon, label, exact }) => (
          <NavLink
            key={to}
            to={to}
            end={exact}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150',
                isActive
                  ? 'bg-primary-50 text-primary-700 border border-primary-100'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              )
            }
          >
            {({ isActive }) => (
              <>
                <Icon
                  className={clsx(
                    'w-4.5 h-4.5',
                    isActive ? 'text-primary-600' : 'text-gray-400'
                  )}
                  size={18}
                />
                {label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Bottom info */}
      <div className="px-5 py-4 border-t border-gray-100">
        <div className="bg-primary-50 rounded-lg p-3">
          <p className="text-xs font-semibold text-primary-700">CustIQ 360°</p>
          <p className="text-xs text-primary-500 mt-0.5">RM Portal v1.0.0</p>
          <p className="text-xs text-gray-400 mt-1">AI-Powered Banking Suite</p>
        </div>
      </div>
    </aside>
  )
}
