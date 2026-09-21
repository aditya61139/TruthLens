import React, { useState } from 'react';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  HelpCircle,
  Sparkles,
  Share2,
  ThumbsUp,
  ThumbsDown,
  Copy,
  Check,
  Zap,
  Tag,
  Clock,
  BookOpen
} from 'lucide-react';
import { VerificationResult, VerdictType } from '../types';
import { ConfidenceMeter } from './ConfidenceMeter';

interface VerdictCardProps {
  result: VerificationResult;
  onOpenShareModal: () => void;
  onOpenFeedbackModal: () => void;
}

const VERDICT_THEMES: Record<
  VerdictType,
  {
    bgGradient: string;
    borderColor: string;
    badgeBg: string;
    textColor: string;
    icon: React.ReactNode;
    title: string;
    description: string;
  }
> = {
  False: {
    bgGradient: 'from-rose-950/40 via-slate-900/90 to-[#0b0f19]',
    borderColor: 'border-rose-500/40',
    badgeBg: 'bg-rose-500/20 text-rose-300 border-rose-500/50 shadow-rose-500/10',
    textColor: 'text-rose-400',
    icon: <XCircle className="w-8 h-8 text-rose-400" />,
    title: 'FALSE',
    description: 'This claim is demonstrably inaccurate or fabricated.'
  },
  True: {
    bgGradient: 'from-emerald-950/40 via-slate-900/90 to-[#0b0f19]',
    borderColor: 'border-emerald-500/40',
    badgeBg: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50 shadow-emerald-500/10',
    textColor: 'text-emerald-400',
    icon: <CheckCircle2 className="w-8 h-8 text-emerald-400" />,
    title: 'TRUE / VERIFIED',
    description: 'This claim aligns with established facts and authoritative evidence.'
  },
  Misleading: {
    bgGradient: 'from-amber-950/40 via-slate-900/90 to-[#0b0f19]',
    borderColor: 'border-amber-500/40',
    badgeBg: 'bg-amber-500/20 text-amber-300 border-amber-500/50 shadow-amber-500/10',
    textColor: 'text-amber-400',
    icon: <AlertTriangle className="w-8 h-8 text-amber-400" />,
    title: 'MISLEADING',
    description: 'Contains selective truth or missing context that creates a false impression.'
  },
  Satire: {
    bgGradient: 'from-purple-950/40 via-slate-900/90 to-[#0b0f19]',
    borderColor: 'border-purple-500/40',
    badgeBg: 'bg-purple-500/20 text-purple-300 border-purple-500/50 shadow-purple-500/10',
    textColor: 'text-purple-400',
    icon: <Sparkles className="w-8 h-8 text-purple-400" />,
    title: 'SATIRE / PARODY',
    description: 'Originated from a known satirical publication; not factual reporting.'
  },
  Unverified: {
    bgGradient: 'from-slate-900/60 via-slate-900/90 to-[#0b0f19]',
    borderColor: 'border-slate-700/60',
    badgeBg: 'bg-slate-800 text-slate-300 border-slate-700',
    textColor: 'text-slate-400',
    icon: <HelpCircle className="w-8 h-8 text-slate-400" />,
    title: 'UNVERIFIED',
    description: 'Insufficient independent documentation to confirm or refute.'
  },
  Error: {
    bgGradient: 'from-amber-950/70 via-slate-900/90 to-[#0b0f19]',
    borderColor: 'border-amber-600/70',
    badgeBg: 'bg-amber-900/50 text-amber-200 border-amber-600',
    textColor: 'text-amber-300',
    icon: <AlertTriangle className="w-8 h-8 text-amber-400" />,
    title: 'SERVICE RATE-LIMITED / ERROR',
    description: 'The verification service encountered an upstream API rate limit or outage. Please retry in a few moments.'
  }
};

export const VerdictCard: React.FC<VerdictCardProps> = ({
  result,
  onOpenShareModal,
  onOpenFeedbackModal
}) => {
  const [copied, setCopied] = useState(false);
  const truthValueKey = (result.truth_value || result.verdict || 'Unverified') as VerdictType;
  const theme = VERDICT_THEMES[truthValueKey] || (result.verdict ? VERDICT_THEMES[result.verdict] : VERDICT_THEMES.Unverified);

  const displayTitle = result.final_verdict_display || theme.title;

  const handleCopySummary = () => {
    let textToCopy = `TruthLens Verification Report\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🏷️ Category: ${result.category} | 📚 Certainty: ${result.knowledge_certainty || 'Standard'}\n🔎 Verdict: [${(result.final_verdict_display || result.verdict).toUpperCase()}] (${Math.round(result.confidence)}% Confidence)\n\nCheckable Claim Analyzed:\n"${result.extracted_claim}"\n`;

    if (result.plain_english_takeaway) {
      textToCopy += `\n💡 Plain English Takeaway:\n${result.plain_english_takeaway}\n`;
    }

    textToCopy += `\nSummary:\n${result.summary}\n`;

    if (result.quick_summary) {
      textToCopy += `\n📋 Quick Summary — 360° Briefing\n──────────────────────────────────\n🔍 What Happened\n   ${result.quick_summary.what_happened}\n\n📖 Full Context & Background\n   ${result.quick_summary.full_context}\n`;
      if (result.quick_summary.timeline && result.quick_summary.timeline.length > 0) {
        textToCopy += `\n⏱️ Timeline of Key Events\n` + result.quick_summary.timeline.map(t => `   - ${t}`).join('\n') + `\n`;
      }
      if (result.quick_summary.current_status) {
        textToCopy += `\n📌 Current Status\n   ${result.quick_summary.current_status}\n`;
      }
      if (result.quick_summary.key_takeaway) {
        textToCopy += `\n🔑 Key Takeaway\n   ${result.quick_summary.key_takeaway}\n`;
      }
    }

    if (result.sources && result.sources.length > 0) {
      textToCopy += `\n📚 Sources & Further Reading\n─────────────────────────────\n`;
      result.sources.forEach((s, idx) => {
        textToCopy += `${idx + 1}. ${s.source_type || '[⚪ Other / General]'} **${s.source_name}**\n   📰 "${s.title}"\n   🔗 ${s.source_url || 'URL not available'}\n   📅 Published: ${s.date_published || s.review_date || 'Date not available'}${s.paywall ? ' (🔒 Paywall)' : ''}\n\n`;
      });
    }

    textToCopy += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nVerified via TruthLens AI`;

    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`w-full rounded-2xl border ${theme.borderColor} bg-gradient-to-b ${theme.bgGradient} p-6 sm:p-8 shadow-2xl transition-all relative overflow-hidden`}>
      {/* Header bar: Metadata & Badges */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-800/80">
        <div className="flex flex-wrap items-center gap-2">
          {/* Mode Badge */}
          <span className="flex items-center space-x-1 text-xs font-bold px-2.5 py-1 rounded-md bg-sky-950 text-sky-300 border border-sky-700">
            <Sparkles className="w-3 h-3 text-sky-400" />
            <span>📌 Mode: {result.mode || 'Claim Verification'}</span>
          </span>

          {/* Category */}
          <span className="flex items-center space-x-1 text-xs font-semibold px-2.5 py-1 rounded-md bg-slate-800/90 text-slate-300 border border-slate-700">
            <Tag className="w-3 h-3 text-sky-400" />
            <span>{result.category}</span>
          </span>

          {/* Knowledge Certainty Badge */}
          {result.knowledge_certainty && (
            <span className={`flex items-center space-x-1 text-xs font-semibold px-2.5 py-0.5 rounded-md border ${
              result.knowledge_certainty === 'Settled Knowledge'
                ? 'bg-indigo-950/80 text-indigo-300 border-indigo-700/70'
                : result.knowledge_certainty === 'Under Active Debate'
                ? 'bg-amber-950/80 text-amber-300 border-amber-700/70'
                : 'bg-slate-800/90 text-slate-300 border-slate-700'
            }`}>
              <span>📚 {result.knowledge_certainty}</span>
            </span>
          )}

          {/* Cache / Speed Badge */}
          {result.cached && (
            <span className="flex items-center space-x-1 text-xs font-semibold px-2 py-0.5 rounded-md bg-sky-950/80 text-sky-300 border border-sky-800">
              <Zap className="w-3 h-3 text-sky-400" />
              <span>
                {result.is_fuzzy_match ? `Fuzzy Match (${result.fuzzy_similarity}%)` : 'Cache Hit (<5ms)'}
              </span>
            </span>
          )}

          {result.is_time_sensitive && (
            <span className="flex items-center space-x-1 text-xs font-semibold px-2 py-0.5 rounded-md bg-amber-950/80 text-amber-300 border border-amber-800 animate-pulse-subtle">
              <span>⚡ Breaking / Current Event</span>
            </span>
          )}

          {result.web_search?.attempted && (
            <span className="flex items-center space-x-1 text-xs font-semibold px-2 py-0.5 rounded-md bg-sky-950/80 text-sky-300 border border-sky-800" title={`Query: ${result.web_search.query_used} via ${result.web_search.provider}`}>
              <span>🌐 Web Search: "{result.web_search.query_used}" ({result.web_search.results_count})</span>
            </span>
          )}

          {result.llm_enhanced && (
            <span className="flex items-center space-x-1 text-xs font-semibold px-2 py-0.5 rounded-md bg-indigo-950/80 text-indigo-300 border border-indigo-800" title="Gemini 3 Flash Live synthesis verified">
              <Sparkles className="w-3 h-3 text-indigo-400" />
              <span>Gemini 3 Flash Live</span>
            </span>
          )}

          {result.gemini_calls_made === 0 && !result.cached && (
            <span className="text-[11px] font-mono text-slate-400 px-2 py-0.5 rounded bg-slate-900 border border-slate-800" title="0 Gemini API calls consumed">
              ⚡ Local Verified (0 AI Calls)
            </span>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-2">
          <button
            onClick={handleCopySummary}
            className="flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all"
            title="Copy verification summary"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-slate-400" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>

          <button
            onClick={onOpenShareModal}
            className="flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-medium bg-sky-600 hover:bg-sky-500 text-white shadow-sm transition-all"
          >
            <Share2 className="w-3.5 h-3.5" />
            <span>Share Card</span>
          </button>

          <button
            onClick={onOpenFeedbackModal}
            className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-slate-200 border border-slate-700 transition-all"
            title="Submit Feedback"
          >
            <ThumbsUp className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main Verdict Display Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 my-6 items-center">
        {/* Left 2 Cols: Claim & Verdict Banner */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center space-x-3">
            {theme.icon}
            <div>
              <span className="text-[11px] font-bold tracking-widest text-slate-400 uppercase">
                TruthLens Final Verdict
              </span>
              <div className="flex items-center space-x-3">
                <h1 className={`text-2xl sm:text-3xl font-extrabold tracking-tight ${theme.textColor}`}>
                  {displayTitle}
                </h1>
                {result.is_settled_fact && (
                  <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${
                    result.truth_value === 'False' || result.verdict === 'False'
                      ? 'bg-rose-950 text-rose-300 border-rose-700'
                      : 'bg-emerald-950 text-emerald-300 border-emerald-700'
                  }`}>
                    {result.truth_value === 'False' || result.verdict === 'False' ? 'Contradiction' : 'Undisputed Fact'}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Extracted Claim Box */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
            <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold block mb-1">
              Checkable Claim Analyzed:
            </span>
            <p className="text-base sm:text-lg font-medium text-white italic font-serif leading-snug">
              "{result.extracted_claim}"
            </p>
            {result.page_title && (
              <span className="text-xs text-slate-400 block mt-2">
                Source Page: <strong className="text-slate-300 font-normal">{result.page_title}</strong>
              </span>
            )}
          </div>

          {/* Plain-English Takeaway Callout Box */}
          {result.plain_english_takeaway && (
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/20 p-4 border-l-4 border-l-emerald-500 space-y-1.5 shadow-lg shadow-emerald-950/20">
              <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-emerald-400">
                <BookOpen className="w-4 h-4" />
                <span>Plain English Takeaway</span>
              </div>
              <p className="text-sm sm:text-base font-medium text-emerald-100 leading-relaxed">
                {result.plain_english_takeaway}
              </p>
            </div>
          )}

          {/* Verdict Summary takeaway */}
          <p className="text-sm sm:text-base text-slate-200 leading-relaxed font-sans">
            {result.summary}
          </p>

          {/* Upstream Warning Banner */}
          {result.llm_warning && (
            <div className="flex items-center space-x-2 p-3 rounded-xl bg-amber-950/40 border border-amber-800/60 text-amber-300 text-xs">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <span>{result.llm_warning}</span>
            </div>
          )}

          {/* Service Error Details */}
          {result.error && (
            <div className="space-y-2 p-3.5 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-200 text-xs">
              <div className="flex items-center space-x-2 font-bold text-rose-300">
                <AlertTriangle className="w-4 h-4" />
                <span>Service Diagnostic Details: [{result.error.code}]</span>
              </div>
              <p className="font-mono text-[11px] text-rose-300/90 leading-relaxed">
                {result.error.details || result.error.message}
              </p>
            </div>
          )}
        </div>

        {/* Right 1 Col: Confidence Meter */}
        <div className="lg:col-span-1">
          <ConfidenceMeter score={result.confidence} factors={result.confidence_factors} />
        </div>
      </div>
    </div>
  );
};
