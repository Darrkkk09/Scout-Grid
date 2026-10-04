import React from 'react';
import { Search, HelpCircle, Bell, Menu, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const Header = ({ onMobileMenuToggle }) => {
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-30 h-16 bg-white/90 backdrop-blur-md border-b border-surface-200/80 px-4 sm:px-6 flex items-center justify-between transition-all">
      <div className="flex items-center gap-4">
        <button
          onClick={onMobileMenuToggle}
          className="lg:hidden p-2 text-surface-600 hover:text-surface-900 hover:bg-surface-100 rounded-lg transition-colors"
          aria-label="Toggle navigation drawer"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Global Search Quick Launcher */}
        <div className="relative hidden md:block w-72 lg:w-96">
          <div
            onClick={() => navigate('/candidates')}
            className="w-full bg-surface-50 border border-surface-200/90 hover:border-surface-300 rounded-xl py-2 px-3.5 pl-10 text-xs text-surface-400 cursor-pointer flex items-center justify-between transition-colors shadow-subtle"
          >
            <span className="flex items-center gap-2">
              <Search className="w-4 h-4 text-surface-400 absolute left-3 top-2.5" />
              <span>Search candidates by skill, location...</span>
            </span>
            <kbd className="hidden lg:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-medium text-surface-400 bg-white border border-surface-200 rounded shadow-2xs">
              ⌘K
            </kbd>
          </div>
        </div>
      </div>

      {/* Right side items */}
      <div className="flex items-center gap-3">
        <div className="hidden sm:flex items-center gap-1 px-2.5 py-1 rounded-full bg-brand-50 border border-brand-200/70 text-brand-700 text-xs font-medium">
          <Sparkles className="w-3.5 h-3.5 text-brand-600 animate-pulse" />
          <span>Search System Active</span>
        </div>

        <button
          className="p-2 text-surface-500 hover:text-surface-800 hover:bg-surface-100 rounded-lg transition-colors"
          title="Help & Documentation"
        >
          <HelpCircle className="w-5 h-5" />
        </button>

        <button
          className="p-2 text-surface-500 hover:text-surface-800 hover:bg-surface-100 rounded-lg transition-colors relative"
          title="Notifications"
        >
          <Bell className="w-5 h-5" />
          <span className="absolute top-2 right-2 w-2 h-2 bg-brand-600 rounded-full ring-2 ring-white"></span>
        </button>

        <div className="h-5 w-px bg-surface-200 mx-1 hidden sm:block" />

        {/* User Avatar */}
        <div className="flex items-center gap-3 pl-1">
          <div className="w-8 h-8 rounded-full bg-surface-900 text-white flex items-center justify-center font-semibold text-xs ring-2 ring-surface-200/60 shadow-sm">
            SG
          </div>
          <div className="hidden xl:block text-left">
            <div className="text-xs font-semibold text-surface-900 leading-tight">Recruiting Admin</div>
            <div className="text-[11px] text-surface-500">Enterprise Sourcing</div>
          </div>
        </div>
      </div>
    </header>
  );
};
