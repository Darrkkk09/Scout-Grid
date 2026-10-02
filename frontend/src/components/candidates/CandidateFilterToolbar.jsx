import React from 'react';
import { Filter, X, Search, MapPin, Award, RotateCcw } from 'lucide-react';
import { Button } from '../ui/Button';

export const CandidateFilterToolbar = ({
  filters,
  onFilterChange,
  onClearFilters,
  totalResults
}) => {
  const activeCount = [
    filters.skill,
    filters.location,
    filters.min_experience !== '' && filters.min_experience !== null && filters.min_experience !== undefined ? true : false
  ].filter(Boolean).length;

  return (
    <div className="bg-white rounded-2xl border border-surface-200/80 p-4 mb-6 shadow-card space-y-4">
      {/* Top row: Section title & Clear filters button */}
      <div className="flex items-center justify-between pb-3 border-b border-surface-100">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-surface-100 text-surface-600">
            <Filter className="w-4 h-4" />
          </div>
          <span className="text-sm font-semibold text-surface-900">Filter Candidates</span>
          {activeCount > 0 && (
            <span className="ml-1 px-2 py-0.5 rounded-full text-xs font-bold bg-brand-100 text-brand-700">
              {activeCount} active
            </span>
          )}
        </div>

        {activeCount > 0 && (
          <button
            onClick={onClearFilters}
            className="text-xs font-medium text-surface-500 hover:text-brand-600 flex items-center gap-1.5 transition-colors px-2 py-1 rounded-md hover:bg-surface-100"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset filters</span>
          </button>
        )}
      </div>

      {/* Filter Inputs Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {/* Skill Filter */}
        <div className="relative">
          <label className="block text-[11px] font-semibold text-surface-500 mb-1 uppercase tracking-wider">
            Skill
          </label>
          <div className="relative">
            <Search className="w-4 h-4 text-surface-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="e.g. Python, FastAPI, React..."
              value={filters.skill || ''}
              onChange={(e) => onFilterChange('skill', e.target.value)}
              className="w-full pl-9 pr-8 py-2 text-xs bg-surface-50 border border-surface-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all text-surface-900 placeholder:text-surface-400"
            />
            {filters.skill && (
              <button
                onClick={() => onFilterChange('skill', '')}
                className="absolute right-2.5 top-2.5 text-surface-400 hover:text-surface-600"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>

        {/* Location Filter */}
        <div className="relative">
          <label className="block text-[11px] font-semibold text-surface-500 mb-1 uppercase tracking-wider">
            Location
          </label>
          <div className="relative">
            <MapPin className="w-4 h-4 text-surface-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="e.g. Bangalore, Remote, Delhi..."
              value={filters.location || ''}
              onChange={(e) => onFilterChange('location', e.target.value)}
              className="w-full pl-9 pr-8 py-2 text-xs bg-surface-50 border border-surface-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all text-surface-900 placeholder:text-surface-400"
            />
            {filters.location && (
              <button
                onClick={() => onFilterChange('location', '')}
                className="absolute right-2.5 top-2.5 text-surface-400 hover:text-surface-600"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>

        {/* Min Experience Filter */}
        <div className="relative">
          <label className="block text-[11px] font-semibold text-surface-500 mb-1 uppercase tracking-wider">
            Min Experience (Years)
          </label>
          <div className="relative">
            <Award className="w-4 h-4 text-surface-400 absolute left-3 top-2.5" />
            <input
              type="number"
              min="0"
              max="30"
              step="0.5"
              placeholder="e.g. 3"
              value={filters.min_experience ?? ''}
              onChange={(e) => onFilterChange('min_experience', e.target.value)}
              className="w-full pl-9 pr-8 py-2 text-xs bg-surface-50 border border-surface-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all text-surface-900 placeholder:text-surface-400"
            />
            {filters.min_experience !== '' && filters.min_experience !== undefined && (
              <button
                onClick={() => onFilterChange('min_experience', '')}
                className="absolute right-2.5 top-2.5 text-surface-400 hover:text-surface-600"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
