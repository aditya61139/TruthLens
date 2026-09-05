import React from 'react';
import { Shield, Sparkles, Newspaper, TrendingUp, Database, History, CheckCircle2, AlertTriangle } from 'lucide-react';

interface NavbarProps {
  activeTab: 'verify' | 'article' | 'trending' | 'sources' | 'history';
  setActiveTab: (tab: 'verify' | 'article' | 'trending' | 'sources' | 'history') => void;
  isBackendHealthy: boolean;
  onOpenApiKeys: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  isBackendHealthy,
  onOpenApiKeys
}) => {
  return (
    <header className="sticky top-0 z-50 border-b border-slate-800 bg-slate-950/85 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('verify')}>
            <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 via-indigo-500 to-emerald-400 p-[2px] shadow-lg shadow-sky-500/20">
              <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                <Shield className="w-5 h-5 text-sky-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-xl tracking-tight text-white font-sans">
                  Truth<span className="text-sky-400">Lens</span>
                </span>
                <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-sky-950/80 border border-sky-800 text-sky-300">
                  AI Verifier
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">Fact-Checking & Misinformation Detection</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex items-center space-x-1 sm:space-x-2">
            <button
              onClick={() => setActiveTab('verify')}
              className={`flex items-center space-x-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'verify'
                  ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
              }`}
            >
              <Sparkles className="w-4 h-4" />
              <span>Verify Claim</span>
            </button>

            <button
              onClick={() => setActiveTab('article')}
              className={`flex items-center space-x-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'article'
                  ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
              }`}
            >
              <Newspaper className="w-4 h-4" />
              <span>Article Mode</span>
            </button>

            <button
              onClick={() => setActiveTab('trending')}
              className={`flex items-center space-x-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'trending'
                  ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
              }`}
            >
              <TrendingUp className="w-4 h-4" />
              <span className="hidden md:inline">Trending Debunks</span>
              <span className="md:hidden">Trending</span>
            </button>

            <button
              onClick={() => setActiveTab('sources')}
              className={`flex items-center space-x-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'sources'
                  ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
              }`}
            >
              <Database className="w-4 h-4" />
              <span className="hidden lg:inline">Publisher Directory</span>
              <span className="lg:hidden">Sources</span>
            </button>

            <button
              onClick={() => setActiveTab('history')}
              className={`flex items-center space-x-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'history'
                  ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
              }`}
            >
              <History className="w-4 h-4" />
              <span>History</span>
            </button>
          </nav>

          {/* Action & Status */}
          <div className="flex items-center space-x-2.5">
            <button
              onClick={onOpenApiKeys}
              className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-900 border border-slate-700 hover:border-sky-500 text-slate-300 hover:text-white transition-all shadow-sm"
              title="Configure Google API Key & Search Grounding"
            >
              <Sparkles className="w-3.5 h-3.5 text-sky-400" />
              <span className="hidden sm:inline">Google API Keys</span>
            </button>

            {/* Engine Status Indicator */}
            <div className="hidden sm:flex items-center space-x-2 pl-2 border-l border-slate-800">
              <div className={`w-2 h-2 rounded-full ${isBackendHealthy ? 'bg-emerald-400 shadow-sm shadow-emerald-400/50 animate-pulse-subtle' : 'bg-rose-500'}`} />
              <span className="text-xs text-slate-400 font-mono">
                {isBackendHealthy ? 'Online' : 'Connecting...'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
