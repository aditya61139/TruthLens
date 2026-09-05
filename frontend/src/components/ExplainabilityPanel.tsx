import React from 'react';
import { Lightbulb, CheckCircle2, XCircle, AlertCircle, HelpCircle, FileText, Info } from 'lucide-react';
import { ExplainabilityData, ClaimClauseBreakdown } from '../types';

interface ExplainabilityPanelProps {
  explanation: ExplainabilityData;
  claimText: string;
}

export const ExplainabilityPanel: React.FC<ExplainabilityPanelProps> = ({
  explanation,
  claimText
}) => {
  const getClauseBadge = (status: ClaimClauseBreakdown['status']) => {
    switch (status) {
      case 'debunked':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-rose-900/60 text-rose-300 border border-rose-700">Debunked</span>;
      case 'verified':
      case 'accurate':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-900/60 text-emerald-300 border border-emerald-700">Accurate</span>;
      case 'misleading':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-amber-900/60 text-amber-300 border border-amber-700">Misleading / Distorted</span>;
      case 'satire':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-purple-900/60 text-purple-300 border border-purple-700">Satire</span>;
      default:
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700">Unverified</span>;
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
        <Lightbulb className="w-5 h-5 text-amber-400" />
        <h2 className="text-base font-bold text-white tracking-wide">
          Explainability & Evidence Alignment
        </h2>
      </div>

      {/* Why Bullets */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Factual Breakdown & Key Findings
        </h3>
        <div className="space-y-2.5">
          {explanation.why_bullets.map((bullet, idx) => (
            <div key={idx} className="flex items-start space-x-2.5 bg-slate-900/60 p-3 rounded-xl border border-slate-800/80">
              <span className="flex-shrink-0 w-5 h-5 rounded-full bg-sky-950 border border-sky-800 text-sky-400 text-xs flex items-center justify-center font-mono font-bold mt-0.5">
                {idx + 1}
              </span>
              <p className="text-sm text-slate-200 leading-relaxed">{bullet}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Clause-by-Clause Highlighting */}
      {explanation.claim_breakdown && explanation.claim_breakdown.length > 0 && (
        <div className="space-y-3 pt-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
            <FileText className="w-3.5 h-3.5 text-slate-400" />
            <span>Clause-by-Clause Assertion Mapping</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {explanation.claim_breakdown.map((item, idx) => (
              <div key={idx} className="bg-slate-900/80 rounded-xl p-3.5 border border-slate-800/80 flex flex-col justify-between space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-slate-400 font-semibold">Clause {idx + 1}</span>
                  {getClauseBadge(item.status)}
                </div>
                <p className="text-sm font-medium text-slate-100 italic font-serif">"{item.clause}"</p>
                <p className="text-xs text-slate-400 leading-normal">{item.note}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Unverified Details / Limitations */}
      {explanation.unverified_aspects && explanation.unverified_aspects !== 'None' && (
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-3.5 flex items-start space-x-2.5">
          <Info className="w-4 h-4 text-sky-400 flex-shrink-0 mt-0.5" />
          <div className="text-xs text-slate-400">
            <strong className="text-slate-300 font-semibold">Scope & Evidence Limits: </strong>
            {explanation.unverified_aspects}
          </div>
        </div>
      )}
    </div>
  );
};
