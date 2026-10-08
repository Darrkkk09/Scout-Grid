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
  Cpu,
  Bot,
  UserCheck,
  Send,
} from 'lucide-react';
import { searchCandidates, fetchCandidates, sourceCandidates } from '../services/api';
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
  const initialUseMas = searchParams.get('mas') === 'true' || true; // Default to Multi-Agent Sourcing

  const [searchInput, setSearchInput] = useState(initialQuery);
  const [activeQuery, setActiveQuery] = useState(initialQuery);
  const [useMas, setUseMas] = useState(initialUseMas);
  const [outreachTone, setOutreachTone] = useState('professional');

  const [filters, setFilters] = useState({
    skill: initialSkill,
    location: initialLocation,
    min_experience: initialMinExp,
  });

  const [page, setPage] = useState(initialPage);
  const limit = 20;

  // Response & data state
  const [candidates, setCandidates] = useState([]);
  const [expandedReqs, setExpandedReqs] = useState(null);
  const [parsedRequirements, setParsedRequirements] = useState(null);
  const [pagination, setPagination] = useState({ total: 0, pages: 1 });
  const [isLoading, setIsLoading] = useState(false);
  const [masStep, setMasStep] = useState('');
  const [error, setError] = useState(null);
  const [hasSearched, setHasSearched] = useState(Boolean(initialQuery || initialSkill || initialLocation || initialMinExp));

  // Sync parameters to URL
  const updateUrlParams = (queryVal, filterVals, pageVal, masVal) => {
    const params = new URLSearchParams();
    if (queryVal) params.set('q', queryVal);
    if (filterVals.skill) params.set('skill', filterVals.skill);
    if (filterVals.location) params.set('location', filterVals.location);
    if (filterVals.min_experience !== '' && filterVals.min_experience !== undefined) {
      params.set('min_experience', filterVals.min_experience);
    }
    if (pageVal > 1) params.set('page', pageVal.toString());
    if (masVal !== undefined) params.set('mas', masVal.toString());

    setSearchParams(params);
  };

  // Perform search call
  const executeSearch = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    setExpandedReqs(null);
    setParsedRequirements(null);

    try {
      if (activeQuery.trim()) {
        if (useMas) {
          // Multi-Agent System Sourcing Flow
          setMasStep('Expanding technical requirements with QueryExpansionAgent...');
          const data = await sourceCandidates({
            query: activeQuery.trim(),
            generateOutreach: true,
            outreachTone,
            topK: 20,
          });

          setMasStep('Auditing candidate fits with CandidateVerifierAgent & OutreachAgent...');
          setCandidates(data.candidates || []);
          setExpandedReqs(data.expanded_requirements || null);
          setParsedRequirements({
            skills: data.expanded_requirements?.primary_skills || [],
            location: data.expanded_requirements?.location,
            min_experience: data.expanded_requirements?.min_experience,
            job_title: data.expanded_requirements?.job_title,
          });
          setPagination({
            total: data.total_found || (data.candidates ? data.candidates.length : 0),
            pages: 1,
          });
          setHasSearched(true);
        } else {
          // OpenSearch Direct Hybrid Flow
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
        }
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
      console.error('Error executing candidate sourcing request:', err);
      setError('Unable to complete the sourcing request. Please try again.');
      setCandidates([]);
    } finally {
      setIsLoading(false);
      setMasStep('');
    }
  }, [activeQuery, filters, page, useMas, outreachTone]);

  useEffect(() => {
    executeSearch();
  }, [executeSearch]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (!searchInput.trim() && !filters.skill && !filters.location && filters.min_experience === '') return;

    setActiveQuery(searchInput.trim());
    setPage(1);
    updateUrlParams(searchInput.trim(), filters, 1, useMas);
  };

  const handleExampleClick = (queryText) => {
    setSearchInput(queryText);
    setActiveQuery(queryText);
    setPage(1);
    updateUrlParams(queryText, filters, 1, useMas);
  };

  const handleFilterChange = (key, value) => {
    const updated = { ...filters, [key]: value };
    setFilters(updated);
    setPage(1);
    updateUrlParams(activeQuery, updated, 1, useMas);
  };

  const handleClearSearch = () => {
    const resetFilters = { skill: '', location: '', min_experience: '' };
    setSearchInput('');
    setActiveQuery('');
    setFilters(resetFilters);
    setParsedRequirements(null);
    setExpandedReqs(null);
    setPage(1);
    setHasSearched(false);
    updateUrlParams('', resetFilters, 1, useMas);
  };

  return (
    <div className="space-y-6 font-sans">
      {/* Top Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-surface-900 tracking-tight flex items-center gap-3">
            <span>AI Multi-Agent Candidate Sourcing</span>
            {hasSearched && !isLoading && (
              <span className="text-xs font-semibold px-3 py-1 rounded-full bg-brand-50 text-brand-700 border border-brand-200/70">
                {pagination.total.toLocaleString()} candidates
              </span>
            )}
          </h1>
          <p className="text-xs text-surface-500 mt-1 font-medium">
            Powered by 4 Autonomous Agents: Query Expansion, Search Coordinator, Fit Auditor & Outreach Drafts.
          </p>
        </div>

        {hasSearched && (
          <Button variant="ghost" size="sm" onClick={handleClearSearch} icon={FilterX}>
            Reset search
          </Button>
        )}
      </div>

      {/* Search Input & MAS Configuration Bar */}
      <div className="bg-white rounded-2xl border border-surface-200/90 p-4 shadow-card space-y-3">
        <form onSubmit={handleSearchSubmit} className="relative">
          <div className="relative flex items-center">
            <Search className="w-5 h-5 text-surface-400 absolute left-4" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Describe the candidate you're looking for... e.g. Python backend engineers in Bangalore with 3+ years"
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
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Agent Source</span>
                </>
              )}
            </Button>
          </div>
        </form>

        {/* MAS Settings Controls: Toggle & Tone selection */}
        <div className="flex flex-wrap items-center justify-between text-xs text-surface-600 pt-2 border-t border-surface-100 gap-3">
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 cursor-pointer font-semibold text-surface-700">
              <input
                type="checkbox"
                checked={useMas}
                onChange={(e) => setUseMas(e.target.checked)}
                className="w-4 h-4 rounded text-brand-600 focus:ring-brand-500 border-surface-300"
              />
              <span className="flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-brand-600" />
                Enable Multi-Agent Pipeline (MAS)
              </span>
            </label>
          </div>

          {useMas && (
            <div className="flex items-center gap-2">
              <span className="text-surface-400 font-medium">Outreach Tone:</span>
              <select
                value={outreachTone}
                onChange={(e) => setOutreachTone(e.target.value)}
                className="px-2.5 py-1 bg-surface-50 border border-surface-200 rounded-lg font-medium text-surface-800 focus:outline-none"
              >
                <option value="professional">Professional</option>
                <option value="casual">Casual</option>
                <option value="technical">Technical Lead</option>
              </select>
            </div>
          )}
        </div>

        {/* Display Skill Taxonomy Expansion Criteria Badges if present */}
        {expandedReqs && (
          <div className="mt-3.5 pt-3 border-t border-surface-100 flex flex-wrap items-center gap-2 text-xs text-surface-600">
            <span className="font-semibold text-brand-700 text-[11px] uppercase tracking-wider mr-1 flex items-center gap-1">
              <Bot className="w-3.5 h-3.5 text-brand-600" />
              Taxonomy Expanded Skills:
            </span>

            {expandedReqs.expanded_skills?.map((skill) => {
              const isPrimary = expandedReqs.primary_skills?.includes(skill);
              return (
                <span
                  key={skill}
                  className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md font-semibold border ${
                    isPrimary
                      ? 'bg-brand-50 text-brand-700 border-brand-200/80'
                      : 'bg-emerald-50 text-emerald-700 border-emerald-200/80'
                  }`}
                >
                  <Tag className="w-3 h-3" />
                  {skill} {isPrimary ? '(Direct)' : '(Taxonomy)'}
                </span>
              );
            })}
          </div>
        )}
      </div>

      {/* Manual Filter Controls */}
      {!useMas && (
        <CandidateFilterToolbar
          filters={filters}
          onFilterChange={handleFilterChange}
          onClearFilters={handleClearSearch}
          totalResults={pagination.total}
        />
      )}

      {/* Loading Progress State */}
      {isLoading && (
        <div className="p-4 rounded-xl bg-brand-50/60 border border-brand-200 text-brand-900 flex items-center gap-3 text-xs shadow-sm animate-pulse">
          <RefreshCw className="w-4 h-4 text-brand-600 animate-spin shrink-0" />
          <div className="font-medium">
            {masStep || 'Understanding requirements, auditing fit scores, and generating outreach...'}
          </div>
        </div>
      )}

      {/* Error Alert State */}
      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 flex items-start gap-3 text-xs">
          <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
          <div className="flex-1">
            <div className="font-bold">Unable to complete the sourcing request</div>
            <div className="mt-0.5 text-red-600">{error}</div>
            <Button
              variant="outline"
              size="sm"
              onClick={executeSearch}
              className="mt-3 bg-white text-red-700 border-red-200 hover:bg-red-50"
            >
              Please try again
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
            <h2 className="text-xl font-bold text-surface-900">Multi-Agent Sourcing Engine</h2>
            <p className="text-xs text-surface-500 leading-relaxed">
              Submit natural-language requirements. Autonomous sub-agents expand tech terms, search candidates, audit fit scores, and draft outreach emails.
            </p>
          </div>

          {/* Preset Example Search Pills */}
          <div className="pt-2">
            <div className="text-[11px] font-semibold text-surface-400 uppercase tracking-wider mb-3">
              Try an example sourcing prompt:
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
            {candidates.map((candResult, idx) => (
              <CandidateCard
                key={candResult.candidate?.id || candResult.id || idx}
                candidate={candResult}
              />
            ))}
          </div>

          {/* Pagination Controls */}
          {pagination.pages > 1 && !useMas && (
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
                    updateUrlParams(activeQuery, filters, newPage, useMas);
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
                    updateUrlParams(activeQuery, filters, newPage, useMas);
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
