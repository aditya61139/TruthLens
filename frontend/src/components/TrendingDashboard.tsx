import React, { useEffect, useState } from 'react';
import { TrendingUp, Flame, ShieldAlert, CheckCircle2, XCircle, AlertTriangle, ExternalLink, Filter, BarChart3 } from 'lucide-react';
import { getTrendingClaims } from '../api/client';
import { TrendingClaimItem, VerdictType } from '../types';

interface TrendingDashboardProps {
  onSelectClaim: (claimText: string) => void;
}

const CATEGORIES = ['All', 'Health & Medicine', 'Science & Space', 'Technology', 'Politics', 'Climate & Energy', 'Satire & Humor'];

export const TrendingDashboard: React.FC<TrendingDashboardProps> = ({ onSelectClaim }) => {
  const [trendingList, setTrendingList] = useState<TrendingClaimItem[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTrending();
  }, [selectedCategory]);

  const loadTrending = async () => {
    setLoading(true);
    try {
      const data = await getTrendingClaims(selectedCategory);
      setTrendingList(data.trending);
      setStats(data.stats);
    } catch (err) {
      console.error('Failed to load trending claims', err);
    } finally {
      setLoading(false);
    }
  };

  const getVerdictBadge = (verdict: VerdictType) => {
    switch (verdict) {
      case 'False':
        return <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-950/80 text-rose-300 border border-rose-800">False</span>;
      case 'True':
        return <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-800">True</span>;
      case 'Misleading':
        return <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-950/80 text-amber-300 border border-amber-800">Misleading</span>;
      case 'Satire':
        return <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-purple-950/80 text-purple-300 border border-purple-800">Satire</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-slate-800 text-slate-300 border border-slate-700">Unverified</span>;
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header & Stats Strip */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white flex items-center space-x-2.5">
              <Flame className="w-7 h-7 text-amber-400" />
              <span>Trending Misinformation & Verified Claims</span>
            </h2>
            <p className="text-sm text-slate-400 mt-1">
              Real-time feed of viral claims, health myths, and high-interest online assertions tracked across fact-checking databases.
            </p>
          </div>
        </div>

        {/* Quick Stats Grid */}
        {stats && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
              <span className="text-[11px] font-mono uppercase text-slate-400 block">Claims Monitored</span>
              <span className="text-2xl font-bold font-mono text-white mt-1 block">{stats.total_monitored}</span>
            </div>
            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
              <span className="text-[11px] font-mono uppercase text-slate-400 block">Debunked False</span>
              <span className="text-2xl font-bold font-mono text-rose-400 mt-1 block">{stats.verdicts?.False || 0}</span>
            </div>
            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
              <span className="text-[11px] font-mono uppercase text-slate-400 block">Misleading / Context</span>
              <span className="text-2xl font-bold font-mono text-amber-400 mt-1 block">{stats.verdicts?.Misleading || 0}</span>
            </div>
            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
              <span className="text-[11px] font-mono uppercase text-slate-400 block">Verified True</span>
              <span className="text-2xl font-bold font-mono text-emerald-400 mt-1 block">{stats.verdicts?.True || 0}</span>
            </div>
          </div>
        )}
      </div>

      {/* Category Pills */}
      <div className="flex items-center space-x-2 overflow-x-auto pb-2 scrollbar-none">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
              selectedCategory === cat
                ? 'bg-sky-500 text-white shadow-md shadow-sky-500/20'
                : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Trending Cards Grid */}
      {loading ? (
        <div className="py-12 text-center text-sm text-slate-400">Loading trending claims...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {trendingList.map((item) => (
            <div
              key={item.id}
              className="bg-slate-900/70 hover:bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-2xl p-5 space-y-3 transition-all flex flex-col justify-between"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
                    {item.category}
                  </span>
                  <div className="flex items-center space-x-2">
                    {getVerdictBadge(item.verdict)}
                    <span className="text-xs font-mono text-slate-400">{Math.round(item.confidence)}%</span>
                  </div>
                </div>

                <h3 className="text-sm sm:text-base font-bold text-white font-serif leading-snug">
                  "{item.claim_text}"
                </h3>

                <p className="text-xs text-slate-300 leading-relaxed line-clamp-3">
                  {item.summary}
                </p>
              </div>

              {/* Action Bar */}
              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
                <span className="text-[11px] text-slate-400">
                  Primary Source: <strong className="text-slate-300 font-normal">{item.source_name}</strong>
                </span>

                <button
                  onClick={() => onSelectClaim(item.claim_text)}
                  className="text-sky-400 hover:text-sky-300 font-semibold hover:underline flex items-center space-x-1"
                >
                  <span>Verify Now</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
