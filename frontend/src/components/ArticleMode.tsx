import React, { useState } from 'react';
import { Newspaper, Link as LinkIcon, RefreshCw, ArrowRight, ShieldCheck, AlertTriangle, CheckCircle, XCircle, ChevronDown, ChevronUp, Layers } from 'lucide-react';
import { verifyArticleContent } from '../api/client';
import { ArticleAnalysisResult, ArticleClaimItem, VerdictType } from '../types';

export const ArticleMode: React.FC = () => {
  const [inputText, setInputText] = useState('');
  const [urlInput, setUrlInput] = useState('');
  const [isUrlMode, setIsUrlMode] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<ArticleAnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandedClaim, setExpandedClaim] = useState<number | null>(null);

  const sampleArticle = `A viral online post claimed that 5G mobile network radiation causes viral respiratory illnesses across major cities.
Meanwhile, NASA confirmed that the James Webb Space Telescope revealed a steamy atmosphere with water vapor on distant exoplanet WASP-96b.
The European Union officially announced new regulatory safety guidelines for autonomous artificial intelligence models.
Medical researchers continue to study how natural botanical compounds interact with cellular immune receptors.`;

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if ((isUrlMode && !urlInput.trim()) || (!isUrlMode && !inputText.trim())) return;

    setIsLoading(true);
    setError(null);
    try {
      const data = await verifyArticleContent(
        isUrlMode ? undefined : inputText.trim(),
        isUrlMode ? urlInput.trim() : undefined,
        6
      );
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Failed to verify article.');
    } finally {
      setIsLoading(false);
    }
  };

  const getVerdictBadge = (verdict: VerdictType) => {
    switch (verdict) {
      case 'False':
        return <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-rose-950/80 text-rose-300 border border-rose-800">False</span>;
      case 'True':
        return <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-800">True</span>;
      case 'Misleading':
        return <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-950/80 text-amber-300 border border-amber-800">Misleading</span>;
      case 'Satire':
        return <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-purple-950/80 text-purple-300 border border-purple-800">Satire</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-slate-800 text-slate-300 border border-slate-700">Unverified</span>;
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-emerald-400 border-emerald-500/50 bg-emerald-950/30';
    if (score >= 60) return 'text-sky-400 border-sky-500/50 bg-sky-950/30';
    if (score >= 40) return 'text-amber-400 border-amber-500/50 bg-amber-950/30';
    return 'text-rose-400 border-rose-500/50 bg-rose-950/30';
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Introduction Banner */}
      <div className="text-center space-y-2 max-w-2xl mx-auto">
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
          Full Article & Multi-Claim Verification
        </h2>
        <p className="text-sm text-slate-400">
          Paste an entire news article or URL. TruthLens extracts each checkable assertion, verifies them in parallel, and computes an aggregate Article Trust Index.
        </p>
      </div>

      {/* Input Box */}
      <div className="glass-panel rounded-2xl p-6 shadow-2xl space-y-4">
        <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
          <button
            type="button"
            onClick={() => setIsUrlMode(false)}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold ${
              !isUrlMode ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30' : 'text-slate-400'
            }`}
          >
            <Newspaper className="w-3.5 h-3.5" />
            <span>Paste Article Text</span>
          </button>
          <button
            type="button"
            onClick={() => setIsUrlMode(true)}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold ${
              isUrlMode ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30' : 'text-slate-400'
            }`}
          >
            <LinkIcon className="w-3.5 h-3.5" />
            <span>Fetch from URL</span>
          </button>
        </div>

        <form onSubmit={handleVerify} className="space-y-4">
          {isUrlMode ? (
            <input
              type="url"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              placeholder="https://example.com/news/full-article-url"
              className="w-full p-3.5 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 text-sm font-mono outline-none focus:border-sky-500"
              required
            />
          ) : (
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Paste full multi-paragraph article text here..."
              rows={6}
              className="w-full p-4 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 text-sm outline-none focus:border-sky-500 resize-y"
              required
            />
          )}

          <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
            <button
              type="button"
              onClick={() => {
                setIsUrlMode(false);
                setInputText(sampleArticle);
              }}
              className="text-xs text-sky-400 hover:text-sky-300 underline"
            >
              Load Sample 4-Claim Multi-Paragraph Article
            </button>

            <button
              type="submit"
              disabled={isLoading || (isUrlMode ? !urlInput.trim() : !inputText.trim())}
              className="w-full sm:w-auto flex items-center justify-center space-x-2 px-6 py-2.5 rounded-xl text-sm font-semibold text-white bg-sky-600 hover:bg-sky-500 disabled:opacity-50 transition-all shadow-lg shadow-sky-600/20"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Analyzing Article Claims...</span>
                </>
              ) : (
                <>
                  <span>Analyze Full Article</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-rose-950/60 border border-rose-800 text-rose-300 p-4 rounded-xl text-sm">
          {error}
        </div>
      )}

      {/* Analysis Results Display */}
      {result && (
        <div className="space-y-6 animate-fadeIn">
          {/* Article Trust Score Overview Card */}
          <div className="glass-panel rounded-2xl p-6 sm:p-8 border border-slate-800 space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-5">
              <div>
                <span className="text-[11px] font-mono uppercase tracking-widest text-slate-400 block">
                  Article Credibility Audit
                </span>
                <h3 className="text-xl font-bold text-white mt-1">
                  {result.article_title}
                </h3>
                <span className="text-xs text-slate-400">
                  {result.total_claims_analyzed} checkable propositions extracted & verified
                </span>
              </div>

              {/* Big Trust Gauge */}
              <div className={`px-6 py-3 rounded-2xl border ${getScoreColor(result.overall_trust_score)} text-center`}>
                <div className="text-3xl font-extrabold font-mono">
                  {Math.round(result.overall_trust_score)}/100
                </div>
                <div className="text-xs font-bold uppercase tracking-wider mt-0.5">
                  {result.trust_grade}
                </div>
              </div>
            </div>

            {/* Verdict Distribution Bar */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-300">
                <span>Claim Breakdown</span>
                <div className="flex items-center space-x-3">
                  <span className="text-emerald-400">✓ {result.verdict_distribution.True || 0} True</span>
                  <span className="text-amber-400">⚠ {result.verdict_distribution.Misleading || 0} Misleading</span>
                  <span className="text-rose-400">✗ {result.verdict_distribution.False || 0} False</span>
                  <span className="text-slate-400">? {result.verdict_distribution.Unverified || 0} Unverified</span>
                </div>
              </div>

              {/* Stacked bar */}
              <div className="w-full h-3 bg-slate-900 rounded-full overflow-hidden flex border border-slate-800">
                {result.verdict_distribution.True > 0 && (
                  <div
                    style={{ width: `${(result.verdict_distribution.True / result.total_claims_analyzed) * 100}%` }}
                    className="bg-emerald-500 h-full"
                  />
                )}
                {result.verdict_distribution.Misleading > 0 && (
                  <div
                    style={{ width: `${(result.verdict_distribution.Misleading / result.total_claims_analyzed) * 100}%` }}
                    className="bg-amber-500 h-full"
                  />
                )}
                {result.verdict_distribution.False > 0 && (
                  <div
                    style={{ width: `${(result.verdict_distribution.False / result.total_claims_analyzed) * 100}%` }}
                    className="bg-rose-500 h-full"
                  />
                )}
                {result.verdict_distribution.Unverified > 0 && (
                  <div
                    style={{ width: `${(result.verdict_distribution.Unverified / result.total_claims_analyzed) * 100}%` }}
                    className="bg-slate-600 h-full"
                  />
                )}
              </div>
            </div>
          </div>

          {/* List of Verified Claims */}
          <div className="space-y-4">
            <h3 className="text-base font-bold text-white tracking-wide flex items-center space-x-2">
              <Layers className="w-4 h-4 text-sky-400" />
              <span>Individually Verified Claims ({result.claims.length})</span>
            </h3>

            <div className="space-y-3">
              {result.claims.map((claim) => {
                const isExpanded = expandedClaim === claim.claim_index;
                return (
                  <div
                    key={claim.claim_index}
                    className="bg-slate-900/80 rounded-xl border border-slate-800 overflow-hidden transition-all"
                  >
                    <div
                      onClick={() => setExpandedClaim(isExpanded ? null : claim.claim_index)}
                      className="p-4 flex items-start justify-between gap-3 cursor-pointer hover:bg-slate-850"
                    >
                      <div className="flex items-start space-x-3">
                        <span className="flex-shrink-0 w-6 h-6 rounded-full bg-slate-800 text-sky-400 font-mono text-xs flex items-center justify-center font-bold">
                          {claim.claim_index}
                        </span>
                        <div className="space-y-1">
                          <p className="text-sm font-semibold text-white font-serif italic">
                            "{claim.claim_text}"
                          </p>
                          <p className="text-xs text-slate-400 line-clamp-1">{claim.summary}</p>
                        </div>
                      </div>

                      <div className="flex items-center space-x-3 flex-shrink-0">
                        {getVerdictBadge(claim.verdict)}
                        <span className="text-xs font-mono text-slate-400">
                          {Math.round(claim.confidence)}%
                        </span>
                        {isExpanded ? (
                          <ChevronUp className="w-4 h-4 text-slate-400" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-slate-400" />
                        )}
                      </div>
                    </div>

                    {/* Expandable Details */}
                    {isExpanded && (
                      <div className="p-4 bg-slate-950/70 border-t border-slate-800 space-y-3 text-xs">
                        <div className="space-y-1">
                          <strong className="text-slate-300">Why: </strong>
                          <span className="text-slate-300">{claim.summary}</span>
                        </div>

                        {claim.sources.length > 0 && (
                          <div className="space-y-1 pt-1">
                            <strong className="text-slate-400 block uppercase text-[10px] tracking-wider">
                              Cited Sources:
                            </strong>
                            {claim.sources.map((s, idx) => (
                              <div key={idx} className="flex items-center justify-between text-slate-300 bg-slate-900 p-2 rounded-lg border border-slate-800">
                                <span>{s.source_name}: {s.title}</span>
                                {s.source_url && (
                                  <a href={s.source_url} target="_blank" rel="noreferrer" className="text-sky-400 hover:underline ml-2">
                                    View
                                  </a>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
