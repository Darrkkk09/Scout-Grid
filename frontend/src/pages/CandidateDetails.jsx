import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  MapPin,
  Mail,
  Briefcase,
  GraduationCap,
  Calendar,
  Award,
  AlertCircle,
  Building2,
  BookmarkCheck,
  Share2,
  Sparkles
} from 'lucide-react';
import { fetchCandidateById } from '../services/api';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Skeleton } from '../components/ui/Skeleton';

export const CandidateDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const [candidate, setCandidate] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [shortlisted, setShortlisted] = useState(false);

  useEffect(() => {
    const getCandidate = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await fetchCandidateById(id);
        setCandidate(data);
      } catch (err) {
        console.error('Failed to fetch candidate profile:', err);
        setError('Candidate profile not found or server error.');
      } finally {
        setIsLoading(false);
      }
    };

    if (id) {
      getCandidate();
    }
  }, [id]);

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6 font-sans">
        <Skeleton className="h-8 w-36 rounded-lg" />
        <div className="bg-white rounded-2xl border border-surface-200/80 p-8 shadow-card space-y-6">
          <div className="flex justify-between items-start">
            <div className="space-y-3">
              <Skeleton className="h-7 w-60" />
              <Skeleton className="h-4 w-40" />
              <Skeleton className="h-4 w-48" />
            </div>
            <Skeleton className="h-10 w-28 rounded-xl" />
          </div>
          <div className="space-y-3 pt-6 border-t border-surface-100">
            <Skeleton className="h-5 w-32" />
            <div className="flex gap-2">
              <Skeleton className="h-7 w-20" />
              <Skeleton className="h-7 w-24" />
              <Skeleton className="h-7 w-16" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !candidate) {
    return (
      <div className="max-w-xl mx-auto text-center py-16 font-sans">
        <div className="w-14 h-14 bg-red-50 text-red-600 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-red-100">
          <AlertCircle className="w-7 h-7" />
        </div>
        <h2 className="text-xl font-bold text-surface-900 mb-2">Candidate Not Found</h2>
        <p className="text-sm text-surface-500 mb-6">
          The requested candidate profile could not be found or has been removed.
        </p>
        <Button variant="primary" icon={ArrowLeft} onClick={() => navigate('/candidates')}>
          Back to candidates
        </Button>
      </div>
    );
  }

  const primaryRole = candidate.experience && candidate.experience.length > 0
    ? candidate.experience[0].title
    : 'Candidate Profile';

  return (
    <div className="max-w-4xl mx-auto space-y-6 font-sans">
      {/* Back Button */}
      <div className="flex items-center justify-between">
        <Button
          variant="outline"
          size="sm"
          icon={ArrowLeft}
          onClick={() => navigate('/candidates')}
        >
          Back to candidates
        </Button>

        <div className="flex items-center gap-2">
          <Button
            variant={shortlisted ? 'primary' : 'outline'}
            size="sm"
            icon={BookmarkCheck}
            onClick={() => setShortlisted(!shortlisted)}
          >
            {shortlisted ? 'Shortlisted' : 'Shortlist'}
          </Button>
        </div>
      </div>

      {/* Hero Header Card */}
      <div className="bg-white rounded-2xl border border-surface-200/80 p-6 sm:p-8 shadow-card space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-surface-900 tracking-tight">
                {candidate.name}
              </h1>
              <Badge variant="brand" size="lg">
                {candidate.experience_years} Years Experience
              </Badge>
            </div>

            <p className="text-base font-medium text-surface-700 flex items-center gap-2">
              <Briefcase className="w-4 h-4 text-surface-400 shrink-0" />
              <span>{primaryRole}</span>
            </p>

            <div className="flex flex-wrap items-center gap-y-1 gap-x-5 text-xs text-surface-500 pt-1">
              <div className="flex items-center gap-1.5">
                <MapPin className="w-4 h-4 text-surface-400 shrink-0" />
                <span>{candidate.location}</span>
              </div>

              {candidate.email && (
                <div className="flex items-center gap-1.5">
                  <Mail className="w-4 h-4 text-surface-400 shrink-0" />
                  <a href={`mailto:${candidate.email}`} className="text-brand-600 hover:underline">
                    {candidate.email}
                  </a>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Skills Section */}
        {candidate.skills && candidate.skills.length > 0 && (
          <div className="pt-6 border-t border-surface-100">
            <h3 className="text-xs font-bold text-surface-500 uppercase tracking-wider mb-3">
              Technical Skills & Competencies
            </h3>
            <div className="flex flex-wrap gap-2">
              {candidate.skills.map((skill, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 rounded-lg text-xs font-semibold bg-brand-50 text-brand-700 border border-brand-200/70"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Experience Timeline Section */}
      <div className="bg-white rounded-2xl border border-surface-200/80 p-6 sm:p-8 shadow-card space-y-6">
        <div className="flex items-center justify-between pb-4 border-b border-surface-100">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-surface-100 text-surface-700">
              <Briefcase className="w-5 h-5" />
            </div>
            <h2 className="text-lg font-bold text-surface-900">Work Experience</h2>
          </div>
          <span className="text-xs font-semibold text-surface-500">
            {candidate.experience ? candidate.experience.length : 0} Positions
          </span>
        </div>

        {candidate.experience && candidate.experience.length > 0 ? (
          <div className="relative pl-6 space-y-8 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-surface-200">
            {candidate.experience.map((exp, idx) => (
              <div key={idx} className="relative group">
                {/* Timeline Dot */}
                <div className="absolute -left-[27px] top-1.5 w-3 h-3 rounded-full bg-white border-2 border-brand-600 ring-4 ring-white" />

                <div className="space-y-1">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                    <h3 className="text-base font-bold text-surface-900">
                      {exp.title}
                    </h3>
                    <div className="flex items-center gap-1.5 text-xs text-surface-500 font-medium">
                      <Calendar className="w-3.5 h-3.5 text-surface-400" />
                      <span>
                        {exp.start_date} — {exp.end_date ? exp.end_date : 'Present'}
                      </span>
                    </div>
                  </div>

                  <div className="text-xs font-semibold text-brand-600 flex items-center gap-1">
                    <Building2 className="w-3.5 h-3.5 text-brand-500" />
                    <span>{exp.company}</span>
                  </div>

                  {exp.description && (
                    <p className="text-xs text-surface-600 leading-relaxed pt-2">
                      {exp.description}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-surface-500 italic">No explicit experience timeline listed.</p>
        )}
      </div>

      {/* Education Section */}
      <div className="bg-white rounded-2xl border border-surface-200/80 p-6 sm:p-8 shadow-card space-y-4">
        <div className="flex items-center gap-2.5 pb-3 border-b border-surface-100">
          <div className="p-2 rounded-xl bg-surface-100 text-surface-700">
            <GraduationCap className="w-5 h-5" />
          </div>
          <h2 className="text-lg font-bold text-surface-900">Education</h2>
        </div>

        <div className="text-sm font-semibold text-surface-900">
          {candidate.education || 'Educational background not specified'}
        </div>
      </div>
    </div>
  );
};
