import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users,
  Search,
  BookmarkCheck,
  TrendingUp,
  Plus,
  ArrowUpRight,
  Sparkles,
  ChevronRight,
  CheckCircle2,
  ListFilter,
  FileSearch,
  Briefcase
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { checkHealth } from '../services/api';

export const Dashboard = () => {
  const navigate = useNavigate();
  const [backendStatus, setBackendStatus] = useState('checking');

  useEffect(() => {
    checkHealth()
      .then((res) => setBackendStatus(res.status === 'ok' ? 'online' : 'offline'))
      .catch(() => setBackendStatus('offline'));
  }, []);

  // Structured metrics state ready for future API binding
  const metrics = [
    {
      id: 'candidates_sourced',
      label: 'Candidates sourced',
      value: '12,482',
      change: '+14% from last month',
      icon: Users,
      color: 'text-brand-600',
      bgColor: 'bg-brand-50',
    },
    {
      id: 'active_searches',
      label: 'Active searches',
      value: '18',
      change: '4 pending review',
      icon: Search,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
    {
      id: 'shortlisted',
      label: 'Shortlisted',
      value: '342',
      change: '32 this week',
      icon: BookmarkCheck,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
    },
    {
      id: 'average_match',
      label: 'Average match',
      value: '87%',
      change: '+2.4% match quality',
      icon: TrendingUp,
      color: 'text-amber-600',
      bgColor: 'bg-amber-50',
    },
  ];

  // Recent searches sample cards
  const recentSearches = [
    {
      title: 'Backend Engineer',
      query: 'Python, FastAPI, MongoDB',
      candidatesCount: 342,
      location: 'Bangalore / Remote',
      minExp: '3+ yrs',
    },
    {
      title: 'Frontend Engineer',
      query: 'React, TypeScript, Tailwind',
      candidatesCount: 521,
      location: 'Remote',
      minExp: '2+ yrs',
    },
    {
      title: 'Machine Learning Engineer',
      query: 'Python, PyTorch, OpenSearch',
      candidatesCount: 128,
      location: 'Hyderabad / Bangalore',
      minExp: '4+ yrs',
    },
  ];

  const handleQuickSearch = (searchItem) => {
    const params = new URLSearchParams();
    if (searchItem.title.includes('Backend')) {
      params.append('skill', 'Python');
    } else if (searchItem.title.includes('Frontend')) {
      params.append('skill', 'React');
    } else {
      params.append('skill', 'Python');
    }
    navigate(`/candidates?${params.toString()}`);
  };

  return (
    <div className="space-y-8 font-sans">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-surface-900 tracking-tight">
              Good morning
            </h1>
          </div>
          <p className="text-sm text-surface-500 mt-1 font-medium">
            Find and evaluate the right candidates faster.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="md"
            onClick={() => navigate('/candidates')}
            icon={ListFilter}
          >
            All Candidates
          </Button>
          <Button
            variant="primary"
            size="md"
            icon={Plus}
            onClick={() => navigate('/candidates')}
          >
            New search
          </Button>
        </div>
      </div>

      {/* Sourcing Banner */}
      <div className="bg-gradient-to-r from-brand-900 via-surface-900 to-indigo-950 rounded-2xl p-5 text-white shadow-card flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="p-2.5 rounded-xl bg-white/10 text-brand-300 backdrop-blur-xs">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold tracking-wide text-white">AI-Powered Talent Sourcing Engine Active</h3>
            </div>
            <p className="text-xs text-surface-300 mt-0.5 max-w-xl">
              Query candidates by natural language requirements, skills, location, and experience with instant search.
            </p>
          </div>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate('/candidates')}
          className="bg-white/10 border-white/20 text-white hover:bg-white/20 shrink-0"
        >
          <span>Launch Sourcing Engine</span>
          <ArrowUpRight className="w-4 h-4" />
        </Button>
      </div>

      {/* Metrics Section */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((m) => {
          const Icon = m.icon;
          return (
            <div
              key={m.id}
              className="bg-white rounded-2xl border border-surface-200/80 p-5 shadow-card hover:shadow-floating transition-all duration-200"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-surface-500 uppercase tracking-wider">
                  {m.label}
                </span>
                <div className={`p-2 rounded-xl ${m.bgColor} ${m.color}`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <div className="text-2xl font-extrabold text-surface-900 tracking-tight">
                {m.value}
              </div>
              <div className="text-[11px] font-medium text-surface-500 mt-2 flex items-center gap-1">
                <span className="text-emerald-600 font-semibold">{m.change}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Recent Searches Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-surface-900 tracking-tight">Recent searches</h2>
            <p className="text-xs text-surface-500">Quick access to active candidate sourcing pipelines</p>
          </div>
          <button
            onClick={() => navigate('/candidates')}
            className="text-xs font-semibold text-brand-600 hover:text-brand-700 flex items-center gap-1"
          >
            <span>View all</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {recentSearches.map((search, idx) => (
            <div
              key={idx}
              onClick={() => handleQuickSearch(search)}
              className="bg-white rounded-2xl border border-surface-200/80 p-5 shadow-card hover:shadow-floating transition-all duration-200 cursor-pointer group flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-surface-900 group-hover:text-brand-600 transition-colors">
                    {search.title}
                  </span>
                  <span className="text-[11px] font-semibold text-brand-700 bg-brand-50 px-2 py-0.5 rounded-full border border-brand-200/60">
                    {search.candidatesCount} candidates
                  </span>
                </div>
                <div className="text-xs text-surface-500 font-mono mb-3 bg-surface-50 p-2 rounded-lg border border-surface-200/50">
                  {search.query}
                </div>
              </div>

              <div className="flex items-center justify-between text-xs text-surface-400 pt-2 border-t border-surface-100">
                <span>{search.location}</span>
                <span className="font-medium text-surface-600">{search.minExp}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Start Section */}
      <div className="bg-white rounded-2xl border border-surface-200/80 p-6 shadow-card space-y-4">
        <div>
          <h2 className="text-base font-bold text-surface-900 tracking-tight">Quick start guide</h2>
          <p className="text-xs text-surface-500">Follow these steps to quickly source candidates for your open roles</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
          <div className="flex items-start gap-3.5">
            <div className="w-8 h-8 rounded-xl bg-surface-900 text-white font-bold text-xs flex items-center justify-center shrink-0">
              1
            </div>
            <div>
              <h4 className="text-xs font-bold text-surface-900 mb-1">1. Describe the role</h4>
              <p className="text-xs text-surface-500 leading-relaxed">
                Specify key skills (e.g. Python, React), preferred locations (e.g. Bangalore), and required years of experience.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3.5">
            <div className="w-8 h-8 rounded-xl bg-brand-600 text-white font-bold text-xs flex items-center justify-center shrink-0">
              2
            </div>
            <div>
              <h4 className="text-xs font-bold text-surface-900 mb-1">2. Scout candidates</h4>
              <p className="text-xs text-surface-500 leading-relaxed">
                Execute natural language queries to search through thousands of structured candidate profiles.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3.5">
            <div className="w-8 h-8 rounded-xl bg-surface-900 text-white font-bold text-xs flex items-center justify-center shrink-0">
              3
            </div>
            <div>
              <h4 className="text-xs font-bold text-surface-900 mb-1">3. Review matches</h4>
              <p className="text-xs text-surface-500 leading-relaxed">
                Inspect complete work experiences, background histories, and contact information.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
