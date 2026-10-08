import React, { useState } from 'react';
import { MapPin, GraduationCap, ChevronRight, Mail, CheckCircle2, AlertTriangle, Send, Copy, Check } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

export const CandidateCard = ({ candidate: candObj, verification, outreach }) => {
  const navigate = useNavigate();
  const [copied, setCopied] = useState(false);
  const [showOutreach, setShowOutreach] = useState(false);

  // Extract candidate object if wrapped in VerifiedCandidateResult structure
  const candidate = candObj.candidate ? candObj.candidate : candObj;
  const ver = verification || candObj.verification;
  const out = outreach || candObj.outreach;

  // Extract latest title if experience entries exist
  const currentRole = candidate.experience && candidate.experience.length > 0
    ? candidate.experience[0].title
    : 'Candidate Profile';

  const currentCompany = candidate.experience && candidate.experience.length > 0
    ? candidate.experience[0].company
    : null;

  const handleCopyOutreach = () => {
    if (!out) return;
    const fullText = `Subject: ${out.subject}\n\n${out.body}`;
    navigator.clipboard.writeText(fullText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-white rounded-2xl border border-surface-200/80 p-5 shadow-card hover:shadow-floating transition-all duration-200 group flex flex-col justify-between relative">
      <div>
        {/* Header section: Name, Title, Experience badge, Fit Score */}
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

          <div className="flex items-center gap-2">
            {ver?.fit_score !== undefined && (
              <span className={`text-xs font-extrabold px-2.5 py-1 rounded-full border ${
                ver.fit_score >= 85
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : ver.fit_score >= 70
                  ? 'bg-brand-50 text-brand-700 border-brand-200'
                  : 'bg-amber-50 text-amber-700 border-amber-200'
              }`}>
                {ver.fit_score}% Fit
              </span>
            )}

            <Badge variant="brand" size="md" className="shrink-0 font-medium">
              {candidate.experience_years} yrs exp
            </Badge>
          </div>
        </div>

        {/* Location & Contact Info */}
        <div className="flex flex-wrap items-center gap-y-1 gap-x-4 text-xs text-surface-500 mb-3">
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

        {/* Multi-Agent Fit Verification Strengths & Gaps */}
        {ver && (
          <div className="mb-4 p-3 rounded-xl bg-surface-50 border border-surface-200/60 text-xs space-y-1.5">
            {ver.strengths && ver.strengths.length > 0 && (
              <div className="space-y-1">
                {ver.strengths.map((str, idx) => (
                  <div key={idx} className="flex items-start gap-1.5 text-emerald-700 font-medium leading-tight">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
                    <span>{str}</span>
                  </div>
                ))}
              </div>
            )}

            {ver.gaps && ver.gaps.length > 0 && (
              <div className="space-y-1 pt-1 border-t border-surface-200/50">
                {ver.gaps.map((gap, idx) => (
                  <div key={idx} className="flex items-start gap-1.5 text-amber-700 font-medium leading-tight">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" />
                    <span>{gap}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Skills list */}
        {candidate.skills && candidate.skills.length > 0 && (
          <div className="mb-4">
            <div className="flex flex-wrap gap-1.5">
              {candidate.skills.slice(0, 6).map((skill, idx) => {
                const isMatched = ver?.matching_skills?.some(
                  (ms) => ms.toLowerCase() === skill.toLowerCase()
                );
                return (
                  <span
                    key={idx}
                    className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium border ${
                      isMatched
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200/80 font-semibold'
                        : 'bg-surface-100 text-surface-700 border-surface-200/60'
                    }`}
                  >
                    {skill}
                  </span>
                );
              })}
              {candidate.skills.length > 6 && (
                <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium bg-surface-50 text-surface-500 border border-surface-200/60">
                  +{candidate.skills.length - 6} more
                </span>
              )}
            </div>
          </div>
        )}

        {/* Outreach Draft Accordion / Preview */}
        {out && (
          <div className="mb-4 pt-2 border-t border-surface-100">
            <button
              onClick={() => setShowOutreach(!showOutreach)}
              className="text-xs font-semibold text-brand-600 hover:text-brand-700 flex items-center gap-1.5 py-1"
            >
              <Send className="w-3.5 h-3.5" />
              <span>{showOutreach ? 'Hide Outreach Draft' : 'View Personal Outreach Draft'}</span>
            </button>

            {showOutreach && (
              <div className="mt-2 p-3 rounded-xl bg-brand-50/40 border border-brand-100 text-xs text-surface-800 relative space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-brand-900 text-[11px] uppercase tracking-wider">
                    {out.tone || 'Professional'} Draft
                  </span>
                  <button
                    onClick={handleCopyOutreach}
                    className="inline-flex items-center gap-1 text-[11px] font-semibold text-brand-700 bg-white hover:bg-brand-50 border border-brand-200 px-2 py-0.5 rounded-md transition-colors"
                  >
                    {copied ? (
                      <>
                        <Check className="w-3 h-3 text-emerald-600" />
                        <span>Copied!</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3 h-3 text-brand-600" />
                        <span>Copy Draft</span>
                      </>
                    )}
                  </button>
                </div>
                <div className="font-semibold text-surface-900">Subject: {out.subject}</div>
                <div className="whitespace-pre-wrap text-surface-700 font-sans leading-relaxed text-[11px] max-h-40 overflow-y-auto pr-1">
                  {out.body}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer: Education & Profile Link */}
      <div className="pt-3 border-t border-surface-100 flex items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-1.5 text-surface-500 truncate max-w-[60%]">
          <GraduationCap className="w-4 h-4 text-surface-400 shrink-0" />
          <span className="truncate font-medium text-surface-600">
            {candidate.education || 'Degree not specified'}
          </span>
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
