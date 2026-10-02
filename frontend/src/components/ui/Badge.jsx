import React from 'react';

export const Badge = ({
  children,
  variant = 'neutral',
  size = 'md',
  className = ''
}) => {
  const baseStyles = 'inline-flex items-center font-medium rounded-md tracking-wide';

  const variants = {
    neutral: 'bg-surface-100 text-surface-700 border border-surface-200/80',
    brand: 'bg-brand-50 text-brand-700 border border-brand-200/70',
    success: 'bg-emerald-50 text-emerald-700 border border-emerald-200/70',
    warning: 'bg-amber-50 text-amber-700 border border-amber-200/70',
    purple: 'bg-purple-50 text-purple-700 border border-purple-200/70',
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-[11px]',
    md: 'px-2.5 py-1 text-xs',
    lg: 'px-3 py-1 text-sm',
  };

  return (
    <span className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}>
      {children}
    </span>
  );
};
