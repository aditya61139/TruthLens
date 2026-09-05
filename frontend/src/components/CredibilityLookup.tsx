import React, { useEffect, useState } from 'react';
import { Database, Search, ShieldCheck, ShieldAlert, AlertTriangle, ExternalLink } from 'lucide-react';
import { getPublishersList } from '../api/client';
import { PublisherCredibility } from '../types';

export const CredibilityLookup: React.FC = () => {
  const [publishers, setPublishers] = useState<PublisherCredibility[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [loading, setLoading] = useState(true);

  const CATEGORIES = ['All', 'Fact-Checker', 'Mainstream', 'Satire', 'Conspiracy/Fake', 'State-Sponsored'];

  useEffect(() => {
    loadPublishers();
  }, [searchQuery, selectedCategory]);

  const loadPublishers = async () => {
    setLoading(true);
    try {
      const data = await getPublishersList(searchQuery, selectedCategory);
      setPublishers(data.results);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getFactualBadge = (reporting?: string) => {
    switch (reporting) {
      case 'Very High':
      case 'High':
        return <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">{reporting} Factual</span>;
      case 'Mostly Factual':
        return <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-sky-950 text-sky-300 border border-sky-800">{reporting}</span>;
      case 'Mixed':
        return <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-950 text-amber-300 border border-amber-800">{reporting}</span>;
      case 'Low':
      case 'Very Low':
        return <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-rose-950 text-rose-300 border border-rose-800">{reporting}</span>;
      case 'Satire':
        return <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-purple-950 text-purple-300 border border-purple-800">Satire</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-slate-800 text-slate-400 border border-slate-700">Unrated</span>;
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="space-y-2 text-center max-w-2xl mx-auto">
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white flex items-center justify-center space-x-2.5">
          <Database className="w-7 h-7 text-sky-400" />
          <span>Publisher Credibility & Bias Directory</span>
        </h2>
        <p className="text-sm text-slate-400">
          Curated reference database of media organizations, fact-checking desks, and alternative domains rated for reporting standards and editorial bias.
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
              placeholder="Search by publisher name or domain (e.g. reuters.com, snopes, infowars)..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 text-xs sm:text-sm outline-none focus:border-sky-500"
            />
          </div>

          <div className="sm:col-span-1">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full py-2.5 px-3 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs sm:text-sm outline-none focus:border-sky-500"
            >
              {CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>{cat} Outlets</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Directory Table / Cards */}
      {loading ? (
        <div className="py-12 text-center text-sm text-slate-400">Loading publisher directory...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          {publishers.map((pub) => (
            <div
              key={pub.domain}
              className="bg-slate-900/70 border border-slate-800 rounded-xl p-4 space-y-2.5 hover:border-slate-700 transition-all"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-sm text-white">{pub.name}</h3>
                  <span className="text-xs font-mono text-slate-400">{pub.domain}</span>
                </div>
                <div className="text-right">
                  <span className="text-sm font-bold font-mono text-sky-400">{pub.credibility_score}/100</span>
                  <span className="text-[10px] text-slate-400 block">{pub.trust_tier?.split('(')[0]}</span>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-1.5 pt-1">
                {getFactualBadge(pub.factual_reporting)}
                <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                  Bias: {pub.bias_rating}
                </span>
                <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                  {pub.category}
                </span>
              </div>

              {pub.notes && (
                <p className="text-xs text-slate-400 leading-relaxed pt-1">
                  {pub.notes}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
