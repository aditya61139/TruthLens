import React from 'react';
import { ExternalLink, Calendar, BookOpen, User, Award, Info, Lock, Archive } from 'lucide-react';
import { SourceEvidence, VerdictType } from '../types';

interface EvidenceTrailProps {
  sources: SourceEvidence[];
  isSettledFact?: boolean;
  category?: string;
  webSearch?: {
    attempted: boolean;
    query_used: string;
    provider: string;
    results_count: number;
  };
}

export const EvidenceTrail: React.FC<EvidenceTrailProps> = ({
  sources,
  isSettledFact = false,
  category = 'General',
  webSearch
}) => {
  const getSourceTypeBadge = (sourceType?: string) => {
    const typeStr = sourceType || '[⚪ Other / General]';
    if (typeStr.includes('Primary')) {
      return (
        <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-emerald-950/90 text-emerald-300 border border-emerald-700/80 flex items-center gap-1">
          <span>🟢 Primary Source</span>
        </span>
      );
    }
    if (typeStr.includes('Major News')) {
      return (
        <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-sky-950/90 text-sky-300 border border-sky-700/80 flex items-center gap-1">
          <span>🔵 Major News Outlet</span>
        </span>
      );
    }
    if (typeStr.includes('Fact-Checker') || typeStr.includes('Fact-Check')) {
      return (
        <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-amber-950/90 text-amber-300 border border-amber-700/80 flex items-center gap-1">
          <span>🟡 Fact-Checker</span>
        </span>
      );
    }
    if (typeStr.includes('Academic') || typeStr.includes('Domain Expert')) {
      return (
        <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-orange-950/90 text-orange-300 border border-orange-700/80 flex items-center gap-1">
          <span>🟠 Domain Expert / Academic</span>
        </span>
      );
    }
    return (
      <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-slate-800 text-slate-300 border border-slate-700 flex items-center gap-1">
        <span>⚪ Other / General</span>
      </span>
    );
  };

  const getRatingBadge = (verdict: VerdictType, rawRating?: string) => {
    switch (verdict) {
      case 'False':
        return <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-rose-950/80 text-rose-300 border border-rose-800">{rawRating || 'False'}</span>;
      case 'True':
        return <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-800">{rawRating || 'True'}</span>;
      case 'Misleading':
        return <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-amber-950/80 text-amber-300 border border-amber-800">{rawRating || 'Misleading'}</span>;
      case 'Satire':
        return <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-purple-950/80 text-purple-300 border border-purple-800">{rawRating || 'Satire'}</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-slate-800 text-slate-300 border border-slate-700">{rawRating || 'Unverified'}</span>;
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2">
          <BookOpen className="w-5 h-5 text-sky-400" />
          <h2 className="text-base sm:text-lg font-bold text-white tracking-wide flex items-center gap-2">
            <span>📚 Sources & Further Reading</span>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">
              {sources.length} Cited
            </span>
          </h2>
        </div>
        <span className="text-xs text-slate-400 font-mono">
          {isSettledFact ? 'Educational & Academic References' : 'Ranked by Relevance'}
        </span>
      </div>

      {/* Web Search Execution Metadata Bar */}
      {webSearch?.attempted && (
        <div className="flex flex-wrap items-center justify-between gap-2 p-2.5 rounded-lg bg-slate-900/90 border border-slate-800 text-xs font-mono text-slate-300">
          <div className="flex items-center space-x-2">
            <span className="text-sky-400 font-bold">🌐 Live Web Search:</span>
            <span>Query: <strong className="text-white">"{webSearch.query_used}"</strong></span>
          </div>
          <div className="flex items-center space-x-3 text-[11px] text-slate-400">
            <span>Provider: <span className="text-sky-300">{webSearch.provider}</span></span>
            <span>Matched: <span className="text-emerald-400 font-bold">{webSearch.results_count} sources</span></span>
          </div>
        </div>
      )}

      {sources.length === 0 ? (
        isSettledFact ? (
          <div className="bg-emerald-950/20 p-6 rounded-xl border border-emerald-800/60 space-y-2">
            <div className="flex items-center space-x-2 text-emerald-400 font-bold text-sm">
              <Award className="w-5 h-5" />
              <span>Settled Scientific & Educational Knowledge ({category})</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed font-sans">
              This statement is an established, non-controversial factual reality verified across fundamental educational and academic reference standards.
            </p>
          </div>
        ) : (
          <div className="bg-slate-900/40 p-6 rounded-xl border border-slate-800 text-center space-y-1.5">
            <div className="flex items-center justify-center space-x-1.5 text-slate-400 text-sm font-semibold">
              <Info className="w-4 h-4 text-slate-500" />
              <span>No directly relevant fact-check investigations or news citations found.</span>
            </div>
            <p className="text-xs text-slate-400">
              TruthLens enforces strict relevance filtering and does not pad the evidence trail with loosely related keyword matches.
            </p>
          </div>
        )
      ) : (
        <div className="space-y-4">
          {sources.map((source, idx) => (
            <div
              key={idx}
              className="bg-slate-900/80 hover:bg-slate-900 transition-all rounded-xl p-4 sm:p-5 border border-slate-800 hover:border-slate-700 space-y-3"
            >
              {/* Top row: Number, Source Type Badge, Publisher & Rating badge */}
              <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-slate-800/60">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="w-6 h-6 rounded-full bg-slate-800 text-slate-300 text-xs font-mono font-bold flex items-center justify-center">
                    {idx + 1}
                  </span>
                  {getSourceTypeBadge(source.source_type)}
                  <span className="font-bold text-sm text-white">{source.source_name}</span>
                  {source.paywall && (
                    <span className="flex items-center space-x-1 text-[11px] font-semibold px-2 py-0.5 rounded bg-amber-950/80 text-amber-300 border border-amber-800">
                      <Lock className="w-3 h-3" />
                      <span>Paywall</span>
                    </span>
                  )}
                </div>

                <div className="flex items-center space-x-2">
                  {source.stance && (
                    <span className={`px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider border ${
                      source.stance === 'ENTAILS'
                        ? 'bg-emerald-950/90 text-emerald-300 border-emerald-700/80'
                        : source.stance === 'CONTRADICTS'
                        ? 'bg-rose-950/90 text-rose-300 border-rose-700/80'
                        : 'bg-slate-800 text-slate-400 border-slate-700'
                    }`}>
                      Stance: {source.stance}
                    </span>
                  )}
                  {getRatingBadge(source.normalized_verdict, source.raw_rating)}
                </div>
              </div>

              {/* Title & Stance Assessment */}
              <div className="space-y-1.5">
                <h4 className="text-sm sm:text-base font-semibold text-slate-100 leading-snug">
                  📰 "{source.title}"
                </h4>
                {source.stance_reason && (
                  <div className="text-[11px] font-mono text-slate-400 flex items-center space-x-1">
                    <span className="text-sky-400 font-semibold">Stance Assessment:</span>
                    <span>{source.stance_reason}</span>
                  </div>
                )}
                {source.explanation && (
                  <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-slate-800/80 font-sans">
                    {source.explanation}
                  </p>
                )}
              </div>

              {/* Bottom Row: Direct Link, Publication Date & Archive */}
              <div className="pt-1 flex flex-wrap items-center justify-between gap-2 text-xs">
                <div className="flex items-center space-x-3">
                  {source.source_url && (
                    <a
                      href={source.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center space-x-1.5 text-sky-400 hover:text-sky-300 font-medium underline underline-offset-4 decoration-sky-500/40 hover:decoration-sky-400 transition-all font-mono"
                    >
                      <span>🔗 {source.source_url.length > 50 ? source.source_url.slice(0, 50) + '...' : source.source_url}</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}

                  {source.archive_url && (
                    <a
                      href={source.archive_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center space-x-1 text-slate-400 hover:text-slate-200"
                    >
                      <Archive className="w-3 h-3" />
                      <span>Archive</span>
                    </a>
                  )}
                </div>

                <div className="flex items-center space-x-3 text-slate-400 text-[11px]">
                  <span className="flex items-center space-x-1">
                    <Calendar className="w-3 h-3 text-slate-500" />
                    <span>Published: {source.date_published || source.review_date || 'Date not available'}</span>
                  </span>

                  {source.claimant && source.claimant !== 'Unknown' && (
                    <span className="flex items-center space-x-1">
                      <User className="w-3 h-3 text-slate-500" />
                      <span>Claimed by: {source.claimant}</span>
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
