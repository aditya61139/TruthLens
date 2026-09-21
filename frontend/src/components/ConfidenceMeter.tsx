import React from 'react';
import { Gauge, CheckCircle, Info } from 'lucide-react';

interface ConfidenceMeterProps {
  score: number;
  factors?: string[];
}

export const ConfidenceMeter: React.FC<ConfidenceMeterProps> = ({ score, factors = [] }) => {
  // Determine color and label
  let strokeColor = '#64748b'; // unverified / slate
  let ratingLabel = 'Low Evidence Base';
  let badgeBg = 'bg-slate-800 text-slate-300 border-slate-700';

  if (score >= 85) {
    strokeColor = '#10b981'; // emerald
    ratingLabel = 'High Confidence';
    badgeBg = 'bg-emerald-950/80 text-emerald-300 border-emerald-800';
  } else if (score >= 65) {
    strokeColor = '#14b8a6'; // teal
    ratingLabel = 'Moderate-High Confidence';
    badgeBg = 'bg-teal-950/80 text-teal-300 border-teal-800';
  } else if (score >= 45) {
    strokeColor = '#f59e0b'; // amber
    ratingLabel = 'Moderate Confidence';
    badgeBg = 'bg-amber-950/80 text-amber-300 border-amber-800';
  } else {
    strokeColor = '#ef4444'; // crimson red
    ratingLabel = 'Low Confidence / Uncorroborated';
    badgeBg = 'bg-rose-950/80 text-rose-300 border-rose-800';
  }

  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="bg-slate-900/60 rounded-xl p-4 border border-slate-800/80 flex flex-col justify-between">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-400">
          <Gauge className="w-4 h-4 text-emerald-400" />
          <span>CONFIDENCE INDEX</span>
        </div>
        <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full border ${badgeBg}`}>
          {ratingLabel}
        </span>
      </div>

      <div className="flex items-center space-x-4 my-2">
        {/* Radial SVG Meter */}
        <div className="relative flex items-center justify-center w-24 h-24 flex-shrink-0">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
            {/* Background circle */}
            <circle
              cx="50"
              cy="50"
              r={radius}
              className="text-slate-800"
              strokeWidth="8"
              stroke="currentColor"
              fill="transparent"
            />
            {/* Progress circle */}
            <circle
              cx="50"
              cy="50"
              r={radius}
              stroke={strokeColor}
              strokeWidth="8"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              fill="transparent"
              className="transition-all duration-1000 ease-out"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-xl font-extrabold font-mono text-white">{Math.round(score)}%</span>
            <span className="text-[9px] uppercase tracking-wider text-slate-400 font-semibold">Certainty</span>
          </div>
        </div>

        {/* Factors Breakdown */}
        <div className="flex-1 space-y-1 text-xs">
          {factors.length > 0 ? (
            factors.slice(0, 3).map((factor, idx) => (
              <div key={idx} className="flex items-start space-x-1.5 text-slate-300">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0 mt-0.5" />
                <span className="leading-tight text-[11px]">{factor}</span>
              </div>
            ))
          ) : (
            <p className="text-[11px] text-slate-400">Confidence calculated from fact-check consensus and source authority.</p>
          )}
        </div>
      </div>
    </div>
  );
};
