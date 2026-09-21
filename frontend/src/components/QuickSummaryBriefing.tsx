import React from 'react';
import { 
  FileText, 
  Search, 
  BookOpen, 
  Clock, 
  Users, 
  BarChart3, 
  Scale, 
  Compass, 
  Key 
} from 'lucide-react';
import { QuickSummary } from '../types';

interface QuickSummaryBriefingProps {
  summary?: QuickSummary;
}

export const QuickSummaryBriefing: React.FC<QuickSummaryBriefingProps> = ({ summary }) => {
  if (!summary) return null;

  const isFieldMeaningful = (val?: string) => {
    if (!val) return false;
    const clean = val.trim().toLowerCase();
    return clean !== 'n/a' && clean !== 'none' && !clean.startsWith('n/a') && clean !== 'not applicable';
  };

  const hasImpactData = summary.impact_numbers && (
    isFieldMeaningful(summary.impact_numbers.deaths) ||
    isFieldMeaningful(summary.impact_numbers.displaced) ||
    isFieldMeaningful(summary.impact_numbers.areas_affected) ||
    isFieldMeaningful(summary.impact_numbers.damage) ||
    isFieldMeaningful(summary.impact_numbers.rescue)
  );

  return (
    <div className="w-full rounded-2xl border border-slate-800 bg-slate-900/90 p-6 sm:p-8 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg sm:text-xl font-bold text-white flex items-center gap-2">
              <span>📋 Quick Summary</span>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-sky-950 text-sky-300 border border-sky-800">
                360° Incident Briefing
              </span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Comprehensive journalistic synthesis across all documented primary and secondary records.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 🔍 What Happened */}
        <div className="space-y-2 bg-slate-950/60 border border-slate-800/80 rounded-xl p-4">
          <div className="flex items-center space-x-2 text-sky-400 font-semibold text-sm">
            <Search className="w-4 h-4" />
            <span>🔍 What Happened</span>
          </div>
          <p className="text-sm text-slate-200 leading-relaxed">
            {summary.what_happened}
          </p>
        </div>

        {/* 📖 Full Context & Background */}
        <div className="space-y-2 bg-slate-950/60 border border-slate-800/80 rounded-xl p-4">
          <div className="flex items-center space-x-2 text-indigo-400 font-semibold text-sm">
            <BookOpen className="w-4 h-4" />
            <span>📖 Full Context & Background</span>
          </div>
          <p className="text-sm text-slate-200 leading-relaxed">
            {summary.full_context}
          </p>
        </div>
      </div>

      {/* ⏱️ Timeline of Key Events (if present) */}
      {summary.timeline && summary.timeline.length > 0 && (
        <div className="space-y-3 bg-slate-950/60 border border-slate-800/80 rounded-xl p-4">
          <div className="flex items-center space-x-2 text-amber-400 font-semibold text-sm">
            <Clock className="w-4 h-4" />
            <span>⏱️ Timeline of Key Events</span>
          </div>
          <ul className="space-y-2">
            {summary.timeline.map((item, idx) => (
              <li key={idx} className="flex items-start space-x-2.5 text-xs sm:text-sm text-slate-300">
                <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
                <span className="leading-relaxed">{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 📊 Impact & Key Numbers */}
      {hasImpactData && summary.impact_numbers && (
        <div className="space-y-3 bg-slate-950/60 border border-slate-800/80 rounded-xl p-4 sm:p-5">
          <div className="flex items-center space-x-2 text-emerald-400 font-semibold text-sm">
            <BarChart3 className="w-4 h-4" />
            <span>📊 Impact & Key Numbers</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {isFieldMeaningful(summary.impact_numbers.deaths) && (
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                <span className="text-[11px] font-bold uppercase tracking-wider text-rose-400 flex items-center gap-1.5">
                  <span>💀 Deaths / Casualties</span>
                </span>
                <p className="text-xs font-semibold text-slate-200">{summary.impact_numbers.deaths}</p>
              </div>
            )}
            {isFieldMeaningful(summary.impact_numbers.displaced) && (
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                <span className="text-[11px] font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
                  <span>🏠 Displaced Populations</span>
                </span>
                <p className="text-xs font-semibold text-slate-200">{summary.impact_numbers.displaced}</p>
              </div>
            )}
            {isFieldMeaningful(summary.impact_numbers.areas_affected) && (
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                <span className="text-[11px] font-bold uppercase tracking-wider text-sky-400 flex items-center gap-1.5">
                  <span>🏘️ Areas Affected</span>
                </span>
                <p className="text-xs font-semibold text-slate-200">{summary.impact_numbers.areas_affected}</p>
              </div>
            )}
            {isFieldMeaningful(summary.impact_numbers.damage) && (
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                <span className="text-[11px] font-bold uppercase tracking-wider text-orange-400 flex items-center gap-1.5">
                  <span>🌾 Damage & Loss</span>
                </span>
                <p className="text-xs font-semibold text-slate-200">{summary.impact_numbers.damage}</p>
              </div>
            )}
            {isFieldMeaningful(summary.impact_numbers.rescue) && (
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1 sm:col-span-2 lg:col-span-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                  <span>🚑 Rescue Operations</span>
                </span>
                <p className="text-xs font-semibold text-slate-200">{summary.impact_numbers.rescue}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 👥 Key Parties Involved & 📊 Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 👥 Key Parties */}
        {summary.key_parties && summary.key_parties.length > 0 && (
          <div className="space-y-3 bg-slate-950/60 border border-slate-800/80 rounded-xl p-4">
            <div className="flex items-center space-x-2 text-purple-400 font-semibold text-sm">
              <Users className="w-4 h-4" />
              <span>👥 Key Parties Involved</span>
            </div>
            <div className="space-y-2">
              {summary.key_parties.map((party, idx) => (
                <div key={idx} className="flex items-start justify-between gap-2 p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                  <span className="text-xs font-bold text-purple-300 shrink-0">{party.name}</span>
                  <span className="text-xs text-slate-400 text-right">{party.role}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 📊 Key Data Points */}
        {summary.key_data && summary.key_data.length > 0 && (
          <div className="space-y-3 bg-slate-950/60 border border-slate-800/80 rounded-xl p-4">
            <div className="flex items-center space-x-2 text-emerald-400 font-semibold text-sm">
              <BarChart3 className="w-4 h-4" />
              <span>📊 Key Data Points</span>
            </div>
            <ul className="space-y-2">
              {summary.key_data.map((dataItem, idx) => (
                <li key={idx} className="flex items-start space-x-2 text-xs sm:text-sm text-slate-300">
                  <span className="text-emerald-400 font-mono font-bold">•</span>
                  <span className="leading-relaxed">{dataItem}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* ⚖️ Multiple Perspectives (if present) */}
      {summary.perspectives && summary.perspectives.length > 0 && (
        <div className="space-y-3 bg-slate-950/60 border border-slate-800/80 rounded-xl p-4">
          <div className="flex items-center space-x-2 text-teal-400 font-semibold text-sm">
            <Scale className="w-4 h-4" />
            <span>⚖️ Multiple Perspectives</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {summary.perspectives.map((p, idx) => (
              <div key={idx} className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                <span className="text-xs font-bold text-teal-300 block">{p.party}</span>
                <p className="text-xs text-slate-300 italic">"{p.stance}"</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 📌 Current Status */}
      {summary.current_status && (
        <div className="flex items-start space-x-3 bg-slate-950/60 border border-slate-800/80 rounded-xl p-4">
          <Compass className="w-4 h-4 text-cyan-400 mt-0.5 shrink-0" />
          <div className="space-y-0.5">
            <span className="text-xs font-bold uppercase tracking-wider text-cyan-400">
              📌 Current Status
            </span>
            <p className="text-xs sm:text-sm text-slate-200 leading-relaxed">
              {summary.current_status}
            </p>
          </div>
        </div>
      )}

      {/* 🔑 Key Takeaway Banner */}
      {summary.key_takeaway && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 sm:p-5 flex items-start space-x-3">
          <Key className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <span className="text-xs font-bold uppercase tracking-widest text-amber-400 block mb-1">
              🔑 Key Takeaway
            </span>
            <p className="text-sm sm:text-base font-semibold text-white leading-snug">
              {summary.key_takeaway}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
