import React, { useEffect, useState } from 'react';
import { History, Search, Trash2, Calendar, CheckCircle2, XCircle, AlertTriangle, ExternalLink } from 'lucide-react';
import { getClaimHistory, deleteHistoryItem } from '../api/client';
import { HistoryItem, VerdictType } from '../types';

interface ClaimHistoryProps {
  onSelectClaim: (claimText: string) => void;
}

export const ClaimHistoryView: React.FC<ClaimHistoryProps> = ({ onSelectClaim }) => {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [verdictFilter, setVerdictFilter] = useState('All');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadHistory();
  }, [searchQuery, verdictFilter]);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const data = await getClaimHistory(searchQuery, verdictFilter);
      setHistory(data.history);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await deleteHistoryItem(id);
      setHistory((prev) => prev.filter((item) => item.id !== id));
    } catch (err) {
      console.error(err);
    }
  };

  const getVerdictBadge = (verdict: VerdictType) => {
    switch (verdict) {
      case 'False':
        return <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-rose-950 text-rose-300 border border-rose-800">False</span>;
      case 'True':
        return <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">True</span>;
      case 'Misleading':
        return <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-amber-950 text-amber-300 border border-amber-800">Misleading</span>;
      case 'Satire':
        return <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-purple-950 text-purple-300 border border-purple-800">Satire</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-slate-800 text-slate-300 border border-slate-700">Unverified</span>;
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="space-y-2 text-center max-w-2xl mx-auto">
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white flex items-center justify-center space-x-2.5">
          <History className="w-7 h-7 text-sky-400" />
          <span>Verification History</span>
        </h2>
        <p className="text-sm text-slate-400">
          Search and revisit previously verified claims, headlines, and analysis records.
        </p>
      </div>

      {/* Filter / Search Bar */}
      <div className="glass-panel rounded-2xl p-4 sm:p-5 border border-slate-800 space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="sm:col-span-2 relative">
            <Search className="absolute left-3.5 top-3.5 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search previous checks..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 text-xs sm:text-sm outline-none focus:border-sky-500"
            />
          </div>

          <div className="sm:col-span-1">
            <select
              value={verdictFilter}
              onChange={(e) => setVerdictFilter(e.target.value)}
              className="w-full py-2.5 px-3 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs sm:text-sm outline-none focus:border-sky-500"
            >
              <option value="All">All Verdicts</option>
              <option value="False">False</option>
              <option value="True">True</option>
              <option value="Misleading">Misleading</option>
              <option value="Satire">Satire</option>
              <option value="Unverified">Unverified</option>
            </select>
          </div>
        </div>
      </div>

      {/* History List */}
      {loading ? (
        <div className="py-12 text-center text-sm text-slate-400">Loading history...</div>
      ) : history.length === 0 ? (
        <div className="bg-slate-900/40 p-8 rounded-2xl border border-slate-800 text-center text-slate-400 text-sm">
          No verification records match your filter criteria.
        </div>
      ) : (
        <div className="space-y-3">
          {history.map((item) => (
            <div
              key={item.id}
              onClick={() => onSelectClaim(item.extracted_claim)}
              className="bg-slate-900/70 hover:bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl p-4 sm:p-5 transition-all cursor-pointer space-y-2"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {getVerdictBadge(item.verdict)}
                  <span className="text-xs font-mono text-slate-400 font-semibold">{Math.round(item.confidence)}% Confidence</span>
                  <span className="text-[11px] font-mono text-slate-400 px-2 py-0.5 rounded bg-slate-800 border border-slate-700">
                    {item.category}
                  </span>
                </div>

                <div className="flex items-center space-x-3">
                  {item.created_at && (
                    <span className="text-[11px] text-slate-500 font-mono">
                      {new Date(item.created_at).toLocaleString()}
                    </span>
                  )}
                  <button
                    onClick={(e) => handleDelete(item.id, e)}
                    className="p-1 rounded text-slate-500 hover:text-rose-400 hover:bg-slate-800 transition-all"
                    title="Delete record"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              <p className="text-sm font-semibold text-white font-serif italic">
                "{item.extracted_claim}"
              </p>

              {item.summary && (
                <p className="text-xs text-slate-400 line-clamp-2">
                  {item.summary}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
