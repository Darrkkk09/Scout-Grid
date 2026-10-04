import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Search,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  FilterX,
  Tag,
  MapPin,
  Briefcase,
  Layers,
  ArrowRight,
  RefreshCw,
} from 'lucide-react';
import { searchCandidates, fetchCandidates } from '../services/api';
import { CandidateCard } from '../components/candidates/CandidateCard';
import { CandidateFilterToolbar } from '../components/candidates/CandidateFilterToolbar';
import { CandidateCardSkeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { Button } from '../components/ui/Button';

const EXAMPLE_SEARCHES = [
  'Python backend engineers with 3+ years of experience in Bangalore',
  'React developers in Hyderabad',
  'Java Spring Boot engineers with 5 years experience',
  'Senior Full Stack Engineers in Remote',
];

export const Candidates = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  // URL State
  const initialQuery = searchParams.get('q') || '';
  const initialSkill = searchParams.get('skill') || '';
  const initialLocation = searchParams.get('location') || '';
  const initialMinExp = searchParams.get('min_experience') || '';
  const initialPage = parseInt(searchParams.get('page') || '1', 10);

  const [searchInput, setSearchInput] = useState(initialQuery);
  const [activeQuery, setActiveQuery] = useState(initialQuery);

  const [filters, setFilters] = useState({
    skill: initialSkill,
    location: initialLocation,
    min_experience: initialMinExp,
  });

  const [page, setPage] = useState(initialPage);
  const limit = 20;

  // Response & data state
  const [candidates, setCandidates] = useState([]);
  const [parsedRequirements, setParsedRequirements] = useState(null);
  const [pagination, setPagination] = useState({ total: 0, pages: 1 });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasSearched, setHasSearched] = useState(Boolean(initialQuery || initialSkill || initialLocation || initialMinExp));

  // Sync parameters to URL
  const updateUrlParams = (queryVal, filterVals, pageVal) => {
    const params = new URLSearchParams();
    if (queryVal) params.set('q', queryVal);
    if (filterVals.skill) params.set('skill', filterVals.skill);
    if (filterVals.location) params.set('location', filterVals.location);
    if (filterVals.min_experience !== '' && filterVals.min_experience !== undefined) {
      params.set('min_experience', filterVals.min_experience);
    }
    if (pageVal > 1) params.set('page', pageVal.toString());

    setSearchParams(params);
  };

  // Perform search call
  const executeSearch = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      if (activeQuery.trim()) {
        const data = await searchCandidates({
          query: activeQuery.trim(),
          page,
          limit,
          filters: {
            skill: filters.skill || undefined,
            location: filters.location || undefined,
            min_experience: filters.min_experience !== '' ? Number(filters.min_experience) : undefined,
          },
        });

        setCandidates(data.results || []);
        setParsedRequirements(data.parsed_requirements || null);
        setPagination({
          total: data.total || 0,
          pages: data.pages || 1,
        });
        setHasSearched(true);
      } else if (filters.skill || filters.location || filters.min_experience !== '') {
        // Fallback to fetchCandidates if explicit filters are applied without query string
        const data = await fetchCandidates({
          page,
          limit,
          skill: filters.skill,
          location: filters.location,
          min_experience: filters.min_experience,
        });

        setCandidates(data.candidates || []);
        setParsedRequirements(null);
        setPagination({
          total: data.total || 0,
          pages: data.pages || 1,
        });
        setHasSearched(true);
      } else {
        // No search query or explicit filters set
        setCandidates([]);
        setParsedRequirements(null);
        setPagination({ total: 0, pages: 1 });
        setHasSearched(false);
      }
    } catch (err) {
      console.error('Error executing candidate search:', err);
      setError('Unable to search candidates. Please check network connection and try again.');
      setCandidates([]);
    } finally {
      setIsLoading(false);
    }
  }, [activeQuery, filters, page]);

  useEffect(() => {
    executeSearch();
  }, [executeSearch]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (!searchInput.trim() && !filters.skill && !filters.location && filters.min_experience === '') return;

    setActiveQuery(searchInput.trim());
    setPage(1);
    updateUrlParams(searchInput.trim(), filters, 1);
  };

  const handleExampleClick = (queryText) => {
    setSearchInput(queryText);
    setActiveQuery(queryText);
    setPage(1);
    updateUrlParams(queryText, filters, 1);
  };

  const handleFilterChange = (key, value) => {
    const updated = { ...filters, [key]: value };
    setFilters(updated);
    setPage(1);
    updateUrlParams(activeQuery, updated, 1);
  };

  const handleClearSearch = () => {
    const resetFilters = { skill: '', location: '', min_experience: '' };
    setSearchInput('');
    setActiveQuery('');
    setFilters(resetFilters);
    setParsedRequirements(null);
    setPage(1);
    setHasSearched(false);
    updateUrlParams('', resetFilters, 1);
  };

  return (
    <div className="space-y-6 font-sans">
      {/* Top Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-surface-900 tracking-tight flex items-center gap-3">
            <span>Find the right candidates</span>
            {hasSearched && !isLoading && (
              <span className="text-xs font-semibold px-3 py-1 rounded-full bg-brand-50 text-brand-700 border border-brand-200/70">
                {pagination.total.toLocaleString()} found
              </span>
            )}
          </h1>
          <p className="text-xs text-surface-500 mt-1 font-medium">
            AI-powered candidate sourcing and requirement extraction engine.
          </p>
        </div>

        {hasSearched && (
          <Button variant="ghost" size="sm" onClick={handleClearSearch} icon={FilterX}>
            Reset search
          </Button>
        )}
      </div>

      {/* Prominent Search Bar UI */}
      <div className="bg-white rounded-2xl border border-surface-200/90 p-4 shadow-card">
        <form onSubmit={handleSearchSubmit} className="relative">
          <div className="relative flex items-center">
            <Search className="w-5 h-5 text-surface-400 absolute left-4" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Describe the candidate you're looking for... e.g. Python backend engineers with 3+ years in Bangalore"
              className="w-full pl-12 pr-36 py-3.5 text-sm bg-surface-50 border border-surface-200/90 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 text-surface-900 placeholder:text-surface-400 transition-all font-medium"
            />
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={isLoading}
              className="absolute right-2 text-xs font-semibold"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Searching...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Search</span>
                </>
              )}
            </Button>
          </div>
        </form>

        {/* Display Extracted Criteria Badges if present */}
        {parsedRequirements && (
          <div className="mt-3.5 pt-3 border-t border-surface-100 flex flex-wrap items-center gap-2 text-xs text-surface-600">
            <span className="font-semibold text-surface-400 text-[11px] uppercase tracking-wider mr-1">
              Search criteria:
            </span>

            {parsedRequirements.skills.map((skill) => (
              <span
                key={skill}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-brand-50 text-brand-700 border border-brand-200/60 font-semibold"
              >
                <Tag className="w-3 h-3 text-brand-500" />
                {skill}
              </span>
            ))}

            {parsedRequirements.location && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200/60 font-semibold">
                <MapPin className="w-3 h-3 text-emerald-500" />
                {parsedRequirements.location}
              </span>
            )}

            {parsedRequirements.min_experience !== null && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-purple-50 text-purple-700 border border-purple-200/60 font-semibold">
                <Briefcase className="w-3 h-3 text-purple-500" />
                {parsedRequirements.min_experience}+ years
              </span>
            )}

            {parsedRequirements.job_title && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-amber-50 text-amber-700 border border-amber-200/60 font-semibold capitalize">
                <Layers className="w-3 h-3 text-amber-500" />
                {parsedRequirements.job_title}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Manual Filter Controls */}
      <CandidateFilterToolbar
        filters={filters}
        onFilterChange={handleFilterChange}
        onClearFilters={handleClearSearch}
        totalResults={pagination.total}
      />

      {/* Error Alert State */}
      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 flex items-start gap-3 text-xs">
          <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
          <div className="flex-1">
            <div className="font-bold">Unable to search candidates</div>
            <div className="mt-0.5 text-red-600">{error}</div>
            <Button
              variant="outline"
              size="sm"
              onClick={executeSearch}
              className="mt-3 bg-white text-red-700 border-red-200 hover:bg-red-50"
            >
              Retry Connection
            </Button>
          </div>
        </div>
      )}

      {/* Main Content Area: Loading / Zero State / Results */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[...Array(6)].map((_, i) => (
            <CandidateCardSkeleton key={i} />
          ))}
        </div>
      ) : !hasSearched ? (
        /* Initial Empty State before first search */
        <div className="bg-white rounded-2xl border border-surface-200/80 p-8 text-center space-y-6 shadow-sm">
          <div className="max-w-md mx-auto space-y-2">
            <div className="w-12 h-12 rounded-2xl bg-brand-50 text-brand-600 border border-brand-100 flex items-center justify-center mx-auto mb-3">
              <Sparkles className="w-6 h-6" />
            </div>
            <h2 className="text-xl font-bold text-surface-900">Find your next candidate</h2>
            <p className="text-xs text-surface-500 leading-relaxed">
              Describe the role, skills, experience, and location you're looking for in plain English.
            </p>
          </div>

          {/* Preset Example Search Pills */}
          <div className="pt-2">
            <div className="text-[11px] font-semibold text-surface-400 uppercase tracking-wider mb-3">
              Try an example search:
            </div>
            <div className="flex flex-wrap justify-center gap-2 max-w-2xl mx-auto">
              {EXAMPLE_SEARCHES.map((example) => (
                <button
                  key={example}
                  onClick={() => handleExampleClick(example)}
                  className="text-xs text-surface-700 bg-surface-50 hover:bg-brand-50 hover:text-brand-700 border border-surface-200 hover:border-brand-200 px-3.5 py-2 rounded-xl transition-all flex items-center gap-2 group font-medium"
                >
                  <span>{example}</span>
                  <ArrowRight className="w-3.5 h-3.5 text-surface-400 group-hover:text-brand-500 transition-transform group-hover:translate-x-0.5" />
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : candidates.length === 0 && !error ? (
        /* No Results State */
        <EmptyState
          title="No candidates found"
          description="Try changing your search query or removing some filters to broaden your search."
          onClearFilters={handleClearSearch}
        />
      ) : (
        /* Candidates Results Grid */
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {candidates.map((candidate) => (
              <CandidateCard key={candidate.id} candidate={candidate} />
            ))}
          </div>

          {/* Real MongoDB Pagination Controls */}
          {pagination.pages > 1 && (
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-6 border-t border-surface-200/80">
              <div className="text-xs text-surface-500">
                Showing Page <span className="font-bold text-surface-900">{page}</span> of{' '}
                <span className="font-bold text-surface-900">{pagination.pages}</span> ({pagination.total.toLocaleString()} candidates)
              </div>

              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1 || isLoading}
                  onClick={() => {
                    const newPage = Math.max(1, page - 1);
                    setPage(newPage);
                    updateUrlParams(activeQuery, filters, newPage);
                  }}
                  icon={ChevronLeft}
                >
                  Previous
                </Button>

                <div className="flex items-center gap-1 px-2">
                  <span className="text-xs font-semibold text-surface-700 px-2.5 py-1 bg-surface-100 rounded-lg">
                    {page} / {pagination.pages}
                  </span>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= pagination.pages || isLoading}
                  onClick={() => {
                    const newPage = Math.min(pagination.pages, page + 1);
                    setPage(newPage);
                    updateUrlParams(activeQuery, filters, newPage);
                  }}
                >
                  <span>Next</span>
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
