import React, { useRef, useState } from 'react';
import { toPng } from 'html-to-image';
import { Shield, Download, Copy, Check, X, Sparkles, ExternalLink } from 'lucide-react';
import { VerificationResult } from '../types';

interface ShareableCardProps {
  result: VerificationResult;
  onClose: () => void;
}

export const ShareableCard: React.FC<ShareableCardProps> = ({ result, onClose }) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const [downloading, setDownloading] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleDownload = async () => {
    if (!cardRef.current) return;
    setDownloading(true);
    try {
      const dataUrl = await toPng(cardRef.current, { quality: 0.95, pixelRatio: 2 });
      const link = document.createElement('a');
      link.download = `truthlens-${result.verdict.toLowerCase()}-${Date.now()}.png`;
      link.href = dataUrl;
      link.click();
    } catch (err) {
      console.error('Failed to export image', err);
    } finally {
      setDownloading(false);
    }
  };

  const handleCopyCard = async () => {
    if (!cardRef.current) return;
    try {
      const dataUrl = await toPng(cardRef.current, { quality: 0.95, pixelRatio: 2 });
      const blob = await (await fetch(dataUrl)).blob();
      await navigator.clipboard.write([
        new ClipboardItem({ 'image/png': blob })
      ]);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      // Fallback text copy
      navigator.clipboard.writeText(`TruthLens Verdict [${result.verdict}]: "${result.extracted_claim}" - ${result.summary}`);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getVerdictTheme = () => {
    switch (result.verdict) {
      case 'False':
        return { bg: 'bg-rose-950/90 border-rose-500', text: 'text-rose-400', badge: 'bg-rose-500 text-white' };
      case 'True':
        return { bg: 'bg-emerald-950/90 border-emerald-500', text: 'text-emerald-400', badge: 'bg-emerald-500 text-white' };
      case 'Misleading':
        return { bg: 'bg-amber-950/90 border-amber-500', text: 'text-amber-400', badge: 'bg-amber-500 text-white' };
      case 'Satire':
        return { bg: 'bg-purple-950/90 border-purple-500', text: 'text-purple-400', badge: 'bg-purple-500 text-white' };
      default:
        return { bg: 'bg-slate-900 border-slate-700', text: 'text-slate-400', badge: 'bg-slate-700 text-white' };
    }
  };

  const theme = getVerdictTheme();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden space-y-4 p-6">
        {/* Modal Top Bar */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-bold text-white">Shareable Verdict Card</h3>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* The Visual Card to be Exported */}
        <div
          ref={cardRef}
          className={`w-full rounded-2xl border-2 ${theme.bg} p-6 sm:p-8 space-y-4 shadow-2xl relative overflow-hidden text-white font-sans`}
          style={{ minHeight: '340px' }}
        >
          {/* Top Brand Bar */}
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center text-slate-950">
                <Shield className="w-5 h-5 fill-slate-950" />
              </div>
              <div>
                <span className="font-bold text-lg tracking-tight">Truth<span className="text-emerald-400">Lens</span></span>
                <span className="text-[10px] text-slate-400 ml-2 tracking-widest uppercase font-mono">Fact Check Unit</span>
              </div>
            </div>
            <span className="text-xs text-slate-400 font-mono">{new Date().toISOString().split('T')[0]}</span>
          </div>

          {/* Verdict and Confidence */}
          <div className="flex items-center justify-between">
            <span className={`px-4 py-1.5 rounded-xl font-extrabold text-sm sm:text-base tracking-wider uppercase ${theme.badge} shadow-lg`}>
              Verdict: {result.verdict}
            </span>
            <span className="text-sm font-mono font-bold text-slate-300">
              Confidence: <strong className="text-white text-base">{Math.round(result.confidence)}%</strong>
            </span>
          </div>

          {/* Core Claim */}
          <div className="bg-slate-950/60 p-4 rounded-xl border border-white/10">
            <span className="text-[10px] uppercase font-mono tracking-widest text-slate-400 block mb-1">Claim Statement:</span>
            <p className="text-base sm:text-lg font-medium text-white italic font-serif leading-snug">
              "{result.extracted_claim}"
            </p>
          </div>

          {/* Plain English Takeaway */}
          {result.plain_english_takeaway && (
            <div className="p-3 rounded-xl bg-emerald-950/50 border border-emerald-500/40 text-emerald-100 text-xs sm:text-sm font-medium">
              <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-300 block mb-0.5">Plain English Takeaway:</span>
              {result.plain_english_takeaway}
            </div>
          )}

          {/* Summary */}
          <p className="text-xs sm:text-sm text-slate-200 leading-relaxed font-sans">
            {result.summary}
          </p>

          {/* Footer watermark */}
          <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-white/10 font-mono">
            <span>Verified with cited independent evidence</span>
            <span className="text-emerald-400 font-bold">truthlens.ai</span>
          </div>
        </div>

        {/* Modal Action Buttons */}
        <div className="flex items-center justify-end space-x-3 pt-2">
          <button
            onClick={handleCopyCard}
            className="flex items-center space-x-1.5 px-4 py-2 rounded-xl text-sm font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4 text-slate-400" />}
            <span>{copied ? 'Copied to Clipboard' : 'Copy Card Image'}</span>
          </button>

          <button
            onClick={handleDownload}
            disabled={downloading}
            className="flex items-center space-x-1.5 px-5 py-2 rounded-xl text-sm font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/20 transition-all"
          >
            <Download className="w-4 h-4" />
            <span>{downloading ? 'Exporting...' : 'Download PNG Card'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
