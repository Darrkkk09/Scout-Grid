import React from 'react';
import { MapPin, Briefcase, GraduationCap, ChevronRight, Mail, Calendar } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

export const CandidateCard = ({ candidate }) => {
  const navigate = useNavigate();

  // Extract latest title if experience entries exist
  const currentRole = candidate.experience && candidate.experience.length > 0
    ? candidate.experience[0].title
    : 'Candidate Profile';

  const currentCompany = candidate.experience && candidate.experience.length > 0
    ? candidate.experience[0].company
    : null;

  return (
    <div className="bg-white rounded-2xl border border-surface-200/80 p-5 shadow-card hover:shadow-floating transition-all duration-200 group flex flex-col justify-between">
      <div>
        {/* Header section: Name, Title, Experience badge */}
        <div className="flex items-start justify-between gap-4 mb-3">
          <div>
            <h3 className="text-base font-bold text-surface-900 group-hover:text-brand-600 transition-colors font-sans flex items-center gap-2">
              <span>{candidate.name}</span>
            </h3>
            <p className="text-xs font-medium text-surface-600 flex items-center gap-1.5 mt-0.5">
              <span>{currentRole}</span>
              {currentCompany && (
                <>
                  <span className="text-surface-300">•</span>
                  <span className="text-surface-500">{currentCompany}</span>
                </>
              )}
            </p>
          </div>

          <Badge variant="brand" size="md" className="shrink-0 font-medium">
            {candidate.experience_years} yrs exp
          </Badge>
        </div>

        {/* Location & Contact Info */}
        <div className="flex flex-wrap items-center gap-y-1 gap-x-4 text-xs text-surface-500 mb-4">
          <div className="flex items-center gap-1">
            <MapPin className="w-3.5 h-3.5 text-surface-400 shrink-0" />
            <span>{candidate.location}</span>
          </div>

          {candidate.email && (
            <div className="flex items-center gap-1 text-surface-500">
              <Mail className="w-3.5 h-3.5 text-surface-400 shrink-0" />
              <span className="truncate max-w-[180px]">{candidate.email}</span>
            </div>
          )}
        </div>

        {/* Skills list */}
        {candidate.skills && candidate.skills.length > 0 && (
          <div className="mb-4">
            <div className="flex flex-wrap gap-1.5">
              {candidate.skills.slice(0, 6).map((skill, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium bg-surface-100 text-surface-700 border border-surface-200/60"
                >
                  {skill}
                </span>
              ))}
              {candidate.skills.length > 6 && (
                <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium bg-surface-50 text-surface-500 border border-surface-200/60">
                  +{candidate.skills.length - 6} more
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Footer: Education & Profile Link */}
      <div className="pt-3 border-t border-surface-100 flex items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-1.5 text-surface-500 truncate max-w-[60%]">
          <GraduationCap className="w-4 h-4 text-surface-400 shrink-0" />
          <span className="truncate font-medium text-surface-600">{candidate.education || 'Degree not specified'}</span>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate(`/candidates/${candidate.id}`)}
          className="group-hover:border-brand-300 group-hover:bg-brand-50/50 group-hover:text-brand-700 shrink-0"
        >
          <span>View profile</span>
          <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
        </Button>
      </div>
    </div>
  );
};
