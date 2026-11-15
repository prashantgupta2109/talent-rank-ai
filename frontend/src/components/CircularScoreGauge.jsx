import React from 'react';

export default function CircularScoreGauge({ score, size = 120, strokeWidth = 10 }) {
  const normalizedScore = Math.max(0, Math.min(100, score || 0));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (normalizedScore / 100) * circumference;

  let colorClass = 'text-emerald-500';
  let bgClass = 'text-emerald-100';
  let badgeLabel = 'Strong Fit';

  if (normalizedScore < 60) {
    colorClass = 'text-rose-500';
    bgClass = 'text-rose-100';
    badgeLabel = 'Weak Fit';
  } else if (normalizedScore < 80) {
    colorClass = 'text-amber-500';
    bgClass = 'text-amber-100';
    badgeLabel = 'Moderate Fit';
  }

  return (
    <div className="flex flex-col items-center justify-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg className="w-full h-full transform -rotate-90" viewBox={`0 0 ${size} ${size}`}>
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="currentColor"
            strokeWidth={strokeWidth}
            className={bgClass}
            fill="transparent"
          />
          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="currentColor"
            strokeWidth={strokeWidth}
            className={`${colorClass} transition-all duration-1000 ease-out`}
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-extrabold text-slate-800">
            {Math.round(normalizedScore)}%
          </span>
          <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-500">
            Match
          </span>
        </div>
      </div>
      <span className={`mt-2 text-xs font-medium px-2 py-0.5 rounded-full ${
        normalizedScore >= 80 ? 'bg-emerald-100 text-emerald-800' :
        normalizedScore >= 60 ? 'bg-amber-100 text-amber-800' : 'bg-rose-100 text-rose-800'
      }`}>
        {badgeLabel}
      </span>
    </div>
  );
}
