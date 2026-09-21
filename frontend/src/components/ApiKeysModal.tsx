import React, { useState, useEffect } from 'react';
import { Key, Shield, CheckCircle2, AlertCircle, Sparkles, ExternalLink, X, Save } from 'lucide-react';

interface ApiKeysModalProps {
  onClose: () => void;
  onKeySaved: () => void;
}

export const ApiKeysModal: React.FC<ApiKeysModalProps> = ({ onClose, onKeySaved }) => {
  const [apiKey, setApiKey] = useState('');
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/config/status');
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleSaveKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey.trim()) return;

    setLoading(true);
    setErrorMsg('');
    setSuccessMsg('');

    try {
      const res = await fetch('/api/config/set-key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ google_api_key: apiKey.trim() })
      });

      if (!res.ok) {
        throw new Error('Failed to configure API key');
      }

      const data = await res.json();
      setSuccessMsg(data.message || 'Google API Key saved and active!');
      setApiKey('');
      await fetchStatus();
      onKeySaved();
    } catch (err: any) {
      setErrorMsg(err.message || 'Error saving API Key');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="w-full max-w-xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 space-y-5 text-white">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <Key className="w-5 h-5 text-sky-400" />
            <h3 className="text-base font-bold text-white">Google Web Search & API Configuration</h3>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Info Banner */}
        <div className="bg-sky-950/40 border border-sky-800/60 p-4 rounded-xl space-y-1.5 text-xs text-sky-200">
          <div className="flex items-center space-x-2 font-bold text-sky-300">
            <Sparkles className="w-4 h-4" />
            <span>Enable Real-Time Google Web Search & Gemini Grounding</span>
          </div>
          <p className="text-slate-300 leading-relaxed">
            Supplying a single Google API key activates <strong>Live Google Search Grounding</strong>, <strong>Gemini AI Synthesis</strong>, and the <strong>Google Fact Check Tools API</strong> for real-time verification of breaking events.
          </p>
          <a
            href="https://aistudio.google.com/app/apikey"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center space-x-1 text-sky-400 hover:underline font-semibold pt-1"
          >
            <span>Get a free Google API Key from Google AI Studio</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>

        {/* Status Indicators */}
        {status && (
          <div className="space-y-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
              Active Verification Capabilities:
            </span>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="flex items-center space-x-2 bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Settled Knowledge Engine</span>
              </div>
              <div className="flex items-center space-x-2 bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>News Consensus Engine</span>
              </div>
              <div className="flex items-center space-x-2 bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                {status.capabilities.google_search_grounding ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-slate-500" />
                )}
                <span className={status.capabilities.google_search_grounding ? 'text-white' : 'text-slate-500'}>
                  Google Search Grounding
                </span>
              </div>
              <div className="flex items-center space-x-2 bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                {status.capabilities.gemini_fact_synthesis ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-slate-500" />
                )}
                <span className={status.capabilities.gemini_fact_synthesis ? 'text-white' : 'text-slate-500'}>
                  Gemini 3 Flash Live Synthesis
                </span>
              </div>
            </div>
            {status.model && (
              <div className="flex items-center justify-between px-3 py-1.5 bg-slate-950 rounded-lg border border-slate-800 text-[11px] text-slate-400">
                <span>Active Model:</span>
                <span className="font-mono text-sky-400 font-semibold">{status.model}</span>
              </div>
            )}
          </div>
        )}

        {/* Input Form */}
        <form onSubmit={handleSaveKey} className="space-y-3 pt-1">
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">
              Enter Google AI Studio API Key:
            </label>
            <p className="text-[11px] text-slate-400 mb-2">
              Valid Gemini API keys start with <code className="text-sky-300 bg-slate-950 px-1 py-0.5 rounded font-mono">AIzaSy...</code> (OAuth tokens starting with <code className="text-rose-300 bg-slate-950 px-1 py-0.5 rounded font-mono">AQ...</code> are not accepted by Google AI Studio).
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="AIzaSy..."
              className="flex-1 bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs text-white outline-none focus:border-sky-500 font-mono"
            />
            <button
              type="submit"
              disabled={loading || !apiKey.trim()}
              className="flex items-center space-x-1.5 px-4 py-2.5 rounded-xl text-xs font-semibold text-white bg-sky-600 hover:bg-sky-500 disabled:opacity-50 transition-all shadow-md shadow-sky-600/20"
            >
              <Save className="w-3.5 h-3.5" />
              <span>{loading ? 'Saving...' : 'Activate Key'}</span>
            </button>
          </div>
        </form>

        {successMsg && (
          <div className="p-3 bg-emerald-950/60 border border-emerald-800 text-emerald-300 rounded-xl text-xs flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {errorMsg && (
          <div className="p-3 bg-rose-950/60 border border-rose-800 text-rose-300 rounded-xl text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <div className="flex justify-end pt-2 border-t border-slate-800">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white bg-slate-800"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
