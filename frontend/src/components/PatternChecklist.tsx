import React from 'react';
import { AlertTriangle, CheckCircle, XCircle, ShieldAlert, Zap, AlertCircle } from 'lucide-react';
import { MisinformationAnalysis } from '../types';

interface PatternChecklistProps {
  patterns: MisinformationAnalysis;
}

export const PatternChecklist: React.FC<PatternChecklistProps> = ({ patterns }) => {
  const getRiskBadge = () => {
    switch (patterns.risk_color) {
      case 'red':
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-rose-950/80 text-rose-300 border border-rose-800">High Risk ({patterns.red_flag_score}/100)</span>;
      case 'amber':
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-950/80 text-amber-300 border border-amber-800">Moderate Risk ({patterns.red_flag_score}/100)</span>;
      case 'yellow':
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-yellow-950/80 text-yellow-300 border border-yellow-800">Low Risk ({patterns.red_flag_score}/100)</span>;
      default:
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-800">Clean / Neutral ({patterns.red_flag_score}/100)</span>;
    }
  };

  const checklistItems = [
    { label: 'Clickbait & Curiosity Gap', flagged: patterns.checklist.clickbait_detected },
    { label: 'Emotional & Outrage Language', flagged: patterns.checklist.emotional_manipulation },
    { label: 'Vague / Anonymous Attribution', flagged: patterns.checklist.vague_sourcing },
    { label: 'Conspiracy & Pseudoscience Cues', flagged: patterns.checklist.conspiracy_cues },
    { label: 'Unverified Extreme Statistics', flagged: patterns.checklist.dubious_statistics },
    { label: 'Sensational Punctuation / Shouting', flagged: patterns.checklist.excessive_sensationalism },
  ];

  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2">
          <ShieldAlert className="w-5 h-5 text-rose-400" />
          <h2 className="text-base font-bold text-white tracking-wide">
            Misinformation Pattern Heuristics
          </h2>
        </div>
        {getRiskBadge()}
      </div>

      <p className="text-xs text-slate-400 leading-relaxed">
        Local rule-based NLP analyzer flags common manipulation tactics, sensationalist cues, and psychological triggers.
      </p>

      {/* Checklist Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        {checklistItems.map((item, idx) => (
          <div
            key={idx}
            className={`flex items-center justify-between p-3 rounded-xl border text-xs font-medium transition-all ${
              item.flagged
                ? 'bg-rose-950/20 border-rose-800/50 text-rose-300'
                : 'bg-slate-900/50 border-slate-800 text-slate-400'
            }`}
          >
            <span>{item.label}</span>
            {item.flagged ? (
              <span className="flex items-center space-x-1 text-rose-400 font-bold text-[11px]">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Detected</span>
              </span>
            ) : (
              <span className="flex items-center space-x-1 text-emerald-400 text-[11px]">
                <CheckCircle className="w-3.5 h-3.5" />
                <span>Passed</span>
              </span>
            )}
          </div>
        ))}
      </div>

      {/* Flag Details List */}
      {patterns.flags && patterns.flags.length > 0 && (
        <div className="space-y-2 pt-2">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
            Detected Triggers ({patterns.flags.length}):
          </span>
          <div className="space-y-2">
            {patterns.flags.map((flag, idx) => (
              <div key={idx} className="bg-slate-900/80 p-3 rounded-xl border border-slate-800 text-xs space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-rose-300">{flag.pattern}</span>
                  <span className="text-[10px] uppercase font-bold text-slate-400 px-2 py-0.5 rounded bg-slate-800 border border-slate-700">
                    {flag.severity} Severity
                  </span>
                </div>
                <p className="text-slate-400">{flag.explanation}</p>
                {flag.detected_instances && flag.detected_instances.length > 0 && (
                  <div className="flex flex-wrap gap-1 pt-1">
                    {flag.detected_instances.map((inst, i) => (
                      <span key={i} className="px-1.5 py-0.5 rounded bg-rose-950/60 text-rose-300 font-mono text-[10px] border border-rose-800/60">
                        "{inst}"
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
