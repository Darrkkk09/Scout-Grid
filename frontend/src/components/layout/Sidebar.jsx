import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Search,
  BookmarkCheck,
  BarChart3,
  Settings,
  X,
  Layers,
  Sparkles
} from 'lucide-react';

export const Sidebar = ({ mobileOpen, onMobileClose }) => {
  const location = useLocation();

  const navItems = [
    { name: 'Overview', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Candidates', path: '/candidates', icon: Users, badge: 'Live' },
    { name: 'Searches', path: '#searches', icon: Search, disabled: true },
    { name: 'Shortlists', path: '#shortlists', icon: BookmarkCheck, disabled: true },
    { name: 'Analytics', path: '#analytics', icon: BarChart3, disabled: true },
  ];

  const bottomNavItems = [
    { name: 'Settings', path: '#settings', icon: Settings, disabled: true },
  ];

  const renderNavLink = (item) => {
    const isActive = location.pathname === item.path || (item.path === '/candidates' && location.pathname.startsWith('/candidates'));
    const Icon = item.icon;

    if (item.disabled) {
      return (
        <div
          key={item.name}
          className="flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium text-surface-400 cursor-not-allowed group transition-colors"
          title="Coming soon in future AI release"
        >
          <div className="flex items-center gap-2.5">
            <Icon className="w-4 h-4 text-surface-400 group-hover:text-surface-500" />
            <span>{item.name}</span>
          </div>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-surface-100 text-surface-400 border border-surface-200">
            Phase 2
          </span>
        </div>
      );
    }

    return (
      <NavLink
        key={item.name}
        to={item.path}
        onClick={onMobileClose}
        className={({ isActive }) =>
          `flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all ${
            isActive
              ? 'bg-brand-50 text-brand-700 font-semibold shadow-2xs'
              : 'text-surface-600 hover:text-surface-900 hover:bg-surface-100'
          }`
        }
      >
        <div className="flex items-center gap-2.5">
          <Icon className={`w-4 h-4 ${isActive ? 'text-brand-600' : 'text-surface-500'}`} />
          <span>{item.name}</span>
        </div>
        {item.badge && (
          <span className="text-[10px] px-1.5 py-0.5 font-semibold rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
            {item.badge}
          </span>
        )}
      </NavLink>
    );
  };

  const sidebarContent = (
    <div className="h-full flex flex-col justify-between p-4">
      <div>
        {/* Brand Header */}
        <div className="flex items-center justify-between px-2 mb-8">
          <NavLink to="/" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-brand-700 to-brand-500 flex items-center justify-center text-white shadow-sm ring-1 ring-brand-600/20">
              <Layers className="w-4 h-4" />
            </div>
            <div>
              <span className="font-extrabold text-base tracking-tight text-surface-900 font-sans group-hover:text-brand-600 transition-colors">
                ScoutGrid
              </span>
              <span className="text-[10px] font-semibold text-brand-600 block -mt-1 tracking-wider uppercase">
                Enterprise
              </span>
            </div>
          </NavLink>

          {/* Close button for mobile */}
          <button
            onClick={onMobileClose}
            className="lg:hidden p-1.5 text-surface-400 hover:text-surface-700 rounded-lg hover:bg-surface-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Section Label */}
        <div className="px-3 mb-2 text-[10px] font-bold text-surface-400 uppercase tracking-wider">
          Platform
        </div>

        {/* Navigation Links */}
        <nav className="space-y-1">
          {navItems.map(renderNavLink)}
        </nav>
      </div>

      <div>
        {/* Bottom Nav */}
        <div className="pt-2 border-t border-surface-200/80 space-y-1">
          {bottomNavItems.map(renderNavLink)}
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Persistent Sidebar */}
      <aside className="hidden lg:block w-60 bg-white border-r border-surface-200/80 shrink-0 h-screen sticky top-0 z-40">
        {sidebarContent}
      </aside>

      {/* Mobile Drawer Overlay */}
      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-surface-950/40 backdrop-blur-xs transition-opacity"
            onClick={onMobileClose}
          />
          {/* Content */}
          <div className="relative w-64 max-w-full bg-white h-full shadow-2xl z-10 flex-1">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
};
