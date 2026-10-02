import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles,
  ArrowRight,
  Search,
  Users,
  Cpu,
  Layers,
  Zap,
  ShieldCheck,
  Database,
  GitBranch,
  BarChart2,
  CheckCircle2,
  ChevronRight
} from 'lucide-react';
import { Button } from '../components/ui/Button';

export const Landing = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-surface-50 text-surface-900 font-sans selection:bg-brand-500/10 selection:text-brand-600">
      {/* Top Navigation */}
      <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-md border-b border-surface-200/70">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-brand-700 to-brand-500 flex items-center justify-center text-white shadow-sm">
              <Layers className="w-4 h-4" />
            </div>
            <span className="font-extrabold text-lg text-surface-900 tracking-tight font-sans">
              ScoutGrid
            </span>
          </div>

          <div className="hidden md:flex items-center gap-8 text-xs font-medium text-surface-600">
            <a href="#product" className="hover:text-surface-900 transition-colors">Product</a>
            <a href="#how-it-works" className="hover:text-surface-900 transition-colors">How it works</a>
            <a href="#infrastructure" className="hover:text-surface-900 transition-colors">Architecture</a>
            <a href="#features" className="hover:text-surface-900 transition-colors">Features</a>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/dashboard')}
            >
              Sign In
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => navigate('/candidates')}
            >
              Explore candidates
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-16 pb-20 md:pt-24 md:pb-28 overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-50 border border-brand-200/80 text-brand-700 text-xs font-semibold mb-6 shadow-2xs">
            <Sparkles className="w-3.5 h-3.5 text-brand-600" />
            <span>AI-Powered Candidate Sourcing Platform</span>
          </div>

          <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold text-surface-900 tracking-tight max-w-4xl mx-auto leading-[1.1] mb-6 font-sans">
            Find the right people, <br className="hidden sm:inline" />
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-brand-600 via-brand-500 to-indigo-600">
              at scale.
            </span>
          </h1>

          <p className="text-base sm:text-lg text-surface-600 max-w-2xl mx-auto mb-8 font-normal leading-relaxed">
            AI-powered candidate sourcing built for modern recruiting teams.
            Streamline profile retrieval, skills evaluation, and talent pipelines seamlessly.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4 mb-16">
            <Button
              variant="primary"
              size="lg"
              icon={ArrowRight}
              onClick={() => navigate('/dashboard')}
              className="w-full sm:w-auto shadow-md hover:shadow-lg transition-all"
            >
              Start sourcing
            </Button>
            <Button
              variant="outline"
              size="lg"
              onClick={() => navigate('/candidates')}
              className="w-full sm:w-auto"
            >
              Explore candidates
            </Button>
          </div>

          {/* Product Preview Mock Dashboard */}
          <div id="product" className="relative mx-auto max-w-5xl rounded-2xl border border-surface-200/80 bg-white p-3 sm:p-4 shadow-floating">
            <div className="rounded-xl border border-surface-200/60 bg-surface-50 p-4 text-left font-sans">
              {/* Mock Header */}
              <div className="flex items-center justify-between pb-3 border-b border-surface-200/80 mb-4">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-400" />
                  <div className="w-3 h-3 rounded-full bg-amber-400" />
                  <div className="w-3 h-3 rounded-full bg-emerald-400" />
                  <span className="text-xs font-mono text-surface-400 ml-2">scoutgrid.app/dashboard</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 font-medium border border-emerald-200">
                    FastAPI MongoDB Live
                  </span>
                </div>
              </div>

              {/* Mock Content */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-4">
                <div className="bg-white p-3 rounded-xl border border-surface-200/80">
                  <div className="text-[11px] text-surface-500 font-medium">Candidates Sourced</div>
                  <div className="text-xl font-bold text-surface-900 mt-1">12,482</div>
                </div>
                <div className="bg-white p-3 rounded-xl border border-surface-200/80">
                  <div className="text-[11px] text-surface-500 font-medium">Active Searches</div>
                  <div className="text-xl font-bold text-surface-900 mt-1">18</div>
                </div>
                <div className="bg-white p-3 rounded-xl border border-surface-200/80">
                  <div className="text-[11px] text-surface-500 font-medium">Shortlisted Talent</div>
                  <div className="text-xl font-bold text-surface-900 mt-1">342</div>
                </div>
                <div className="bg-white p-3 rounded-xl border border-surface-200/80">
                  <div className="text-[11px] font-medium text-surface-500">Pipeline Match</div>
                  <div className="text-xl font-bold text-brand-600 mt-1">87%</div>
                </div>
              </div>

              {/* Mock Candidate Cards preview */}
              <div className="space-y-2">
                <div className="bg-white p-3 rounded-xl border border-surface-200/80 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center font-bold text-xs">
                      RK
                    </div>
                    <div>
                      <div className="font-semibold text-surface-900">Rahul Kumar</div>
                      <div className="text-surface-500 text-[11px]">Backend Engineer • Bangalore • 4.2 yrs</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="hidden sm:inline-block px-2 py-0.5 rounded text-[10px] bg-surface-100 text-surface-700">
                      Python, FastAPI, MongoDB
                    </span>
                    <ChevronRight className="w-4 h-4 text-surface-400" />
                  </div>
                </div>

                <div className="bg-white p-3 rounded-xl border border-surface-200/80 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-xs">
                      AS
                    </div>
                    <div>
                      <div className="font-semibold text-surface-900">Ananya Sharma</div>
                      <div className="text-surface-500 text-[11px]">Frontend Architect • Remote • 6.5 yrs</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="hidden sm:inline-block px-2 py-0.5 rounded text-[10px] bg-surface-100 text-surface-700">
                      React, TypeScript, Tailwind
                    </span>
                    <ChevronRight className="w-4 h-4 text-surface-400" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Why ScoutGrid Section */}
      <section className="py-16 bg-white border-y border-surface-200/70">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-surface-900 tracking-tight">
              Why talent teams choose ScoutGrid
            </h2>
            <p className="text-sm text-surface-500 mt-2">
              Designed specifically for speed, precision, and enterprise candidate management.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 rounded-2xl bg-surface-50 border border-surface-200/80 space-y-3">
              <div className="w-10 h-10 rounded-xl bg-brand-100 text-brand-700 flex items-center justify-center">
                <Search className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-surface-900">Precision Filters</h3>
              <p className="text-xs text-surface-600 leading-relaxed">
                Instantly query candidates by exact skills, location parameters, and experience thresholds powered by indexing.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-surface-50 border border-surface-200/80 space-y-3">
              <div className="w-10 h-10 rounded-xl bg-brand-100 text-brand-700 flex items-center justify-center">
                <Zap className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-surface-900">Sub-Second Response</h3>
              <p className="text-xs text-surface-600 leading-relaxed">
                Built on high-performance FastAPI backends and optimized MongoDB aggregations for zero latency.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-surface-50 border border-surface-200/80 space-y-3">
              <div className="w-10 h-10 rounded-xl bg-brand-100 text-brand-700 flex items-center justify-center">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-surface-900">Verified Profiles</h3>
              <p className="text-xs text-surface-600 leading-relaxed">
                Structured candidate records with work experience histories, skill taxonomy, and verified education.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="py-16 bg-surface-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-surface-900 tracking-tight">
              How ScoutGrid works
            </h2>
            <p className="text-sm text-surface-500 mt-2">
              Three simple steps to evaluate and source top-tier engineering talent.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-white p-6 rounded-2xl border border-surface-200/80 shadow-card text-center relative">
              <div className="w-10 h-10 rounded-full bg-surface-900 text-white font-bold text-sm flex items-center justify-center mx-auto mb-4">
                1
              </div>
              <h3 className="text-base font-bold text-surface-900 mb-2">1. Define Sourcing Criteria</h3>
              <p className="text-xs text-surface-500 leading-relaxed">
                Filter by technical skills, geographical locations, and required years of hands-on experience.
              </p>
            </div>

            <div className="bg-white p-6 rounded-2xl border border-surface-200/80 shadow-card text-center relative">
              <div className="w-10 h-10 rounded-full bg-brand-600 text-white font-bold text-sm flex items-center justify-center mx-auto mb-4">
                2
              </div>
              <h3 className="text-base font-bold text-surface-900 mb-2">2. Scout Candidates</h3>
              <p className="text-xs text-surface-500 leading-relaxed">
                Review candidate profiles fetched in real time directly from our MongoDB candidate service backend.
              </p>
            </div>

            <div className="bg-white p-6 rounded-2xl border border-surface-200/80 shadow-card text-center relative">
              <div className="w-10 h-10 rounded-full bg-surface-900 text-white font-bold text-sm flex items-center justify-center mx-auto mb-4">
                3
              </div>
              <h3 className="text-base font-bold text-surface-900 mb-2">3. Evaluate & Shortlist</h3>
              <p className="text-xs text-surface-500 leading-relaxed">
                Inspect complete experience timelines, education details, and export candidate data for outreach.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Scale / Infrastructure Section */}
      <section id="infrastructure" className="py-16 bg-surface-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-surface-800 text-brand-300 text-xs font-semibold mb-4 border border-surface-700">
              <Cpu className="w-3.5 h-3.5" />
              <span>Distributed Architecture Roadmap</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight mb-4 font-sans">
              Engineered for distributed scale
            </h2>
            <p className="text-sm text-surface-400 leading-relaxed mb-8">
              ScoutGrid is designed from the ground up for massive throughput. Our architecture foundation combines high-concurrency backend microservices with robust data stores.
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-surface-800/80 border border-surface-700">
              <Database className="w-5 h-5 text-brand-400 mb-2" />
              <div className="text-sm font-bold">MongoDB Store</div>
              <div className="text-[11px] text-surface-400 mt-1">Active profile storage & indexed queries</div>
            </div>

            <div className="p-4 rounded-xl bg-surface-800/80 border border-surface-700">
              <Search className="w-5 h-5 text-purple-400 mb-2" />
              <div className="text-sm font-bold">OpenSearch</div>
              <div className="text-[11px] text-surface-400 mt-1">Vector embeddings & semantic search (Phase 2)</div>
            </div>

            <div className="p-4 rounded-xl bg-surface-800/80 border border-surface-700">
              <GitBranch className="w-5 h-5 text-emerald-400 mb-2" />
              <div className="text-sm font-bold">Redis & Kafka</div>
              <div className="text-[11px] text-surface-400 mt-1">High-throughput task queueing & cache</div>
            </div>

            <div className="p-4 rounded-xl bg-surface-800/80 border border-surface-700">
              <Cpu className="w-5 h-5 text-amber-400 mb-2" />
              <div className="text-sm font-bold">Kubernetes</div>
              <div className="text-[11px] text-surface-400 mt-1">Auto-scaling distributed worker cluster</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-16 bg-white border-b border-surface-200/70">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-surface-900 tracking-tight">
              Powerful sourcing features
            </h2>
            <p className="text-sm text-surface-500 mt-2">
              Everything your talent acquisition team needs to move fast.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="p-5 rounded-2xl bg-surface-50 border border-surface-200/80">
              <CheckCircle2 className="w-5 h-5 text-brand-600 mb-2" />
              <h4 className="text-sm font-bold text-surface-900 mb-1">FastAPI Backend</h4>
              <p className="text-xs text-surface-600">Direct integration with production REST endpoint for zero fake data.</p>
            </div>

            <div className="p-5 rounded-2xl bg-surface-50 border border-surface-200/80">
              <CheckCircle2 className="w-5 h-5 text-brand-600 mb-2" />
              <h4 className="text-sm font-bold text-surface-900 mb-1">Real-Time Pagination</h4>
              <p className="text-xs text-surface-600">Effortlessly navigate through thousands of candidates with page limits.</p>
            </div>

            <div className="p-5 rounded-2xl bg-surface-50 border border-surface-200/80">
              <CheckCircle2 className="w-5 h-5 text-brand-600 mb-2" />
              <h4 className="text-sm font-bold text-surface-900 mb-1">Multi-Filter Queries</h4>
              <p className="text-xs text-surface-600">Combine skill, location, and minimum experience filters simultaneously.</p>
            </div>

            <div className="p-5 rounded-2xl bg-surface-50 border border-surface-200/80">
              <CheckCircle2 className="w-5 h-5 text-brand-600 mb-2" />
              <h4 className="text-sm font-bold text-surface-900 mb-1">Deep Profile Views</h4>
              <p className="text-xs text-surface-600">View complete employment timelines, start/end dates, and job details.</p>
            </div>

            <div className="p-5 rounded-2xl bg-surface-50 border border-surface-200/80">
              <CheckCircle2 className="w-5 h-5 text-brand-600 mb-2" />
              <h4 className="text-sm font-bold text-surface-900 mb-1">Responsive SaaS UI</h4>
              <p className="text-xs text-surface-600">Desktop-optimized with drawer navigation on mobile and tablet.</p>
            </div>

            <div className="p-5 rounded-2xl bg-surface-50 border border-surface-200/80">
              <CheckCircle2 className="w-5 h-5 text-brand-600 mb-2" />
              <h4 className="text-sm font-bold text-surface-900 mb-1">Shimmer Loaders</h4>
              <p className="text-xs text-surface-600">Polished skeleton loaders and empty states for exceptional UX.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-16 bg-surface-50 text-center">
        <div className="max-w-4xl mx-auto px-4 sm:px-6">
          <h2 className="text-3xl font-extrabold text-surface-900 tracking-tight mb-4">
            Ready to find your next candidate?
          </h2>
          <p className="text-sm text-surface-600 max-w-lg mx-auto mb-8">
            Access the candidate database now and start building your talent pipeline.
          </p>
          <div className="flex items-center justify-center gap-4">
            <Button variant="primary" size="lg" icon={ArrowRight} onClick={() => navigate('/candidates')}>
              Browse Candidates Now
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-white border-t border-surface-200/80 py-8 text-xs text-surface-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-brand-600" />
            <span className="font-bold text-surface-900">ScoutGrid</span>
            <span>© 2026 ScoutGrid Inc. All rights reserved.</span>
          </div>

          <div className="flex items-center gap-6">
            <span className="hover:text-surface-900 cursor-pointer">Privacy Policy</span>
            <span className="hover:text-surface-900 cursor-pointer">Terms of Service</span>
            <span className="hover:text-surface-900 cursor-pointer font-medium text-brand-600">FastAPI REST Docs</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
