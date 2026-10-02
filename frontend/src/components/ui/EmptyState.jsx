import React from 'react';
import { SearchX, FilterX } from 'lucide-react';
import { Button } from './Button';

export const EmptyState = ({
  title = "No candidates found",
  description = "Try removing some filters or searching for another skill or location.",
  onClearFilters,
  icon: Icon = SearchX
}) => {
  return (
    <div className="bg-white border border-surface-200/80 rounded-2xl p-12 text-center shadow-card max-w-xl mx-auto my-8">
      <div className="w-14 h-14 bg-surface-100 text-surface-600 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-surface-200/50">
        <Icon className="w-7 h-7" />
      </div>
      <h3 className="text-lg font-semibold text-surface-900 mb-2">{title}</h3>
      <p className="text-sm text-surface-500 max-w-md mx-auto mb-6 leading-relaxed">
        {description}
      </p>
      {onClearFilters && (
        <Button variant="outline" icon={FilterX} onClick={onClearFilters}>
          Clear filters
        </Button>
      )}
    </div>
  );
};
