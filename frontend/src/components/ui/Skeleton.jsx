import React from 'react';

export const Skeleton = ({ className = '' }) => {
  return (
    <div className={`animate-shimmer bg-surface-200/80 rounded-lg ${className}`} />
  );
};

export const CandidateCardSkeleton = () => {
  return (
    <div className="bg-white rounded-xl border border-surface-200/80 p-5 shadow-card space-y-4">
      <div className="flex justify-between items-start">
        <div className="space-y-2">
          <Skeleton className="h-5 w-44" />
          <Skeleton className="h-4 w-32" />
        </div>
        <Skeleton className="h-6 w-24 rounded-full" />
      </div>

      <div className="flex items-center gap-4 pt-1">
        <Skeleton className="h-4 w-28" />
        <Skeleton className="h-4 w-24" />
      </div>

      <div className="flex flex-wrap gap-2 pt-2">
        <Skeleton className="h-6 w-16" />
        <Skeleton className="h-6 w-20" />
        <Skeleton className="h-6 w-14" />
        <Skeleton className="h-6 w-18" />
      </div>

      <div className="pt-3 border-t border-surface-100 flex justify-between items-center">
        <Skeleton className="h-4 w-48" />
        <Skeleton className="h-8 w-28 rounded-lg" />
      </div>
    </div>
  );
};
