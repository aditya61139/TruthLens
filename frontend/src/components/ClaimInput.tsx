import React, { useState } from 'react';
import { Search, Link as LinkIcon, Sparkles, X, ArrowRight, RefreshCw, Layers } from 'lucide-react';

interface ClaimInputProps {
  onVerify: (text: string, isUrl: boolean, bypassCache: boolean) => void;
  isLoading: boolean;
}

const SAMPLE_CLAIMS = [
  { label: '🍌 Bananas cure cancer', text: 'Eating ripe bananas with dark spots produces TNF that cures cancer cells.' },
  { label: '🔭 Webb exoplanet water', text: 'NASA James Webb Space Telescope detected atmospheric water vapor on exoplanet WASP-96b.' },
  { label: '📡 5G viral transmission', text: '5G mobile network radiation causes viral respiratory illnesses.' },
  { label: '🚗 EV lifetime emissions', text: 'Electric cars produce more lifetime carbon emissions than conventional gasoline vehicles.' },
  { label: '🇻🇦 Pope political endorsement', text: 'Pope Francis officially endorsed Donald Trump for US President.' }
];

export const ClaimInput: React.FC<ClaimInputProps> = ({ onVerify, isLoading }) => {
  const [inputText, setInputText] = useState('');
  const [isUrlMode, setIsUrlMode] = useState(false);
  const [bypassCache, setBypassCache] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading) return;
    onVerify(inputText.trim(), isUrlMode, bypassCache);
  };

  const handleSampleClick = (text: string) => {
    setInputText(text);
    setIsUrlMode(false);
    onVerify(text, false, bypassCache);
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* Search Container */}
      <div className="glass-panel rounded-2xl p-4 sm:p-6 shadow-2xl relative overflow-hidden">
        {/* Glow accent */}
        <div className="absolute -top-24 -right-24 w-60 h-60 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Input Mode Selector */}
        <div className="flex items-center justify-between mb-4 border-b border-slate-800/80 pb-3">
          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={() => setIsUrlMode(false)}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                !isUrlMode
                  ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Search className="w-3.5 h-3.5" />
              <span>Claim / Headline / Social Post</span>
            </button>

            <button
              type="button"
              onClick={() => setIsUrlMode(true)}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                isUrlMode
                  ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <LinkIcon className="w-3.5 h-3.5" />
              <span>Webpage / Article URL</span>
            </button>
          </div>

          {/* Bypass Cache checkbox */}
          <label className="flex items-center space-x-2 text-xs text-slate-400 cursor-pointer hover:text-slate-200">
            <input
              type="checkbox"
              checked={bypassCache}
              onChange={(e) => setBypassCache(e.target.checked)}
              className="rounded border-slate-700 bg-slate-900 text-sky-500 focus:ring-sky-500/30 h-3.5 w-3.5"
            />
            <span>Fresh Query (Bypass Cache)</span>
          </label>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            {isUrlMode ? (
              <div className="relative flex items-center">
                <LinkIcon className="absolute left-4 w-5 h-5 text-slate-400" />
                <input
                  type="url"
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder="Paste article or social post URL (e.g. https://www.reuters.com/...)"
                  className="w-full pl-12 pr-24 py-3.5 rounded-xl bg-slate-900/90 border border-slate-700 focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 text-white placeholder-slate-500 text-sm font-mono outline-none transition-all"
                  required
                />
                {inputText && (
                  <button
                    type="button"
                    onClick={() => setInputText('')}
                    className="absolute right-14 text-slate-400 hover:text-slate-200 p-1"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            ) : (
              <div className="relative">
                <textarea
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder="Paste a factual claim, viral rumor, tweet, or news headline to verify..."
                  rows={3}
                  className="w-full p-4 rounded-xl bg-slate-900/90 border border-slate-700 focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 text-white placeholder-slate-500 text-sm sm:text-base outline-none resize-none transition-all leading-relaxed"
                  required
                />
                {inputText && (
                  <button
                    type="button"
                    onClick={() => setInputText('')}
                    className="absolute top-3 right-3 text-slate-400 hover:text-slate-200 p-1 bg-slate-800/80 rounded-md"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Action Row */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-1">
            <div className="flex items-center space-x-2 text-xs text-slate-400">
              <Sparkles className="w-3.5 h-3.5 text-sky-400" />
              <span>Multi-layer check: Google Fact Check Tools, News Consensus & Pattern NLP</span>
            </div>

            <button
              type="submit"
              disabled={isLoading || !inputText.trim()}
              className="w-full sm:w-auto flex items-center justify-center space-x-2 px-6 py-3 rounded-xl font-semibold text-sm text-white bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-sky-600/25 transition-all active:scale-[0.98]"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin text-white" />
                  <span>Verifying Evidence...</span>
                </>
              ) : (
                <>
                  <span>Verify with TruthLens</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </form>

        {/* Quick Test Samples */}
        <div className="mt-5 pt-4 border-t border-slate-800/80">
          <p className="text-xs font-medium text-slate-400 mb-2 flex items-center space-x-1.5">
            <Layers className="w-3.5 h-3.5 text-slate-500" />
            <span>Try a verified example:</span>
          </p>
          <div className="flex flex-wrap gap-2">
            {SAMPLE_CLAIMS.map((sample, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSampleClick(sample.text)}
                disabled={isLoading}
                className="text-xs px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800 hover:border-slate-700 hover:text-white transition-all disabled:opacity-50"
              >
                {sample.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
