import React from 'react';
import { Compass, Calendar, MapPin, Activity, Tag, Sparkles } from 'lucide-react';
import { EventMeta } from '../types';

interface EventBriefingHeaderProps {
  mode?: string;
  eventMeta?: EventMeta;
  extractedQuery: string;
}

export const EventBriefingHeader: React.FC<EventBriefingHeaderProps> = ({
  mode = 'Event Query',
  eventMeta,
  extractedQuery
}) => {
  const emoji = eventMeta?.category_emoji || '🌊';
  const label = eventMeta?.category_label || 'Natural Disaster — Event Briefing';
  const title = eventMeta?.title || extractedQuery;
  const region = eventMeta?.region || 'Affected Region / Multi-district';
  const dateRange = eventMeta?.date_range || 'Recent / Ongoing';
  const status = eventMeta?.status || '🟡 Developing';

  const getStatusBadge = (st: string) => {
    if (st.includes('Ongoing') || st.includes('🔴')) {
      return (
        <span className="flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-950/90 text-rose-300 border border-rose-700 animate-pulse">
          <span className="w-2 h-2 rounded-full bg-rose-500" />
          <span>🔴 Ongoing Event</span>
        </span>
      );
    }
    if (st.includes('Resolved') || st.includes('🟢')) {
      return (
        <span className="flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-950/90 text-emerald-300 border border-emerald-700">
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
          <span>🟢 Resolved</span>
        </span>
      );
    }
    return (
      <span className="flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-950/90 text-amber-300 border border-amber-700">
        <span className="w-2 h-2 rounded-full bg-amber-500" />
        <span>🟡 Developing Situation</span>
      </span>
    );
  };

  return (
    <div className="w-full rounded-2xl border border-sky-800/80 bg-gradient-to-b from-slate-900 via-slate-900/90 to-slate-950 p-6 sm:p-8 shadow-2xl space-y-5 relative overflow-hidden">
      {/* Top Header Bar: Mode & Category */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-800">
        <div className="flex flex-wrap items-center gap-2">
          {/* Detected Mode Badge */}
          <span className="flex items-center space-x-1 text-xs font-bold px-3 py-1 rounded-md bg-sky-950 text-sky-300 border border-sky-700">
            <Sparkles className="w-3.5 h-3.5 text-sky-400" />
            <span>📌 Mode: {mode}</span>
          </span>

          {/* Event Category Tag */}
          <span className="flex items-center space-x-1.5 text-xs font-semibold px-3 py-1 rounded-md bg-slate-800 text-slate-200 border border-slate-700">
            <span className="text-base">{emoji}</span>
            <span>{label}</span>
          </span>
        </div>

        {/* Live Status Badge */}
        <div>{getStatusBadge(status)}</div>
      </div>

      {/* Main Event Title Banner */}
      <div className="space-y-2">
        <span className="text-[11px] font-bold tracking-widest text-sky-400 uppercase">
          Incident Briefing & Real-Time Intelligence
        </span>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white leading-tight">
          {title}
        </h1>
      </div>

      {/* Metadata Grid: Region, Date Range, Category */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
        <div className="flex items-center space-x-2.5 p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 text-xs">
          <MapPin className="w-4 h-4 text-rose-400 shrink-0" />
          <div>
            <span className="text-[10px] uppercase font-bold text-slate-400 block">Region / Location</span>
            <span className="font-semibold text-slate-200">{region}</span>
          </div>
        </div>

        <div className="flex items-center space-x-2.5 p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 text-xs">
          <Calendar className="w-4 h-4 text-indigo-400 shrink-0" />
          <div>
            <span className="text-[10px] uppercase font-bold text-slate-400 block">Date Range</span>
            <span className="font-semibold text-slate-200">{dateRange}</span>
          </div>
        </div>

        <div className="flex items-center space-x-2.5 p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 text-xs">
          <Activity className="w-4 h-4 text-emerald-400 shrink-0" />
          <div>
            <span className="text-[10px] uppercase font-bold text-slate-400 block">Operational Status</span>
            <span className="font-semibold text-slate-200">{status}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
