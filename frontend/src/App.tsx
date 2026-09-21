import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { ClaimInput } from './components/ClaimInput';
import { VerdictCard } from './components/VerdictCard';
import { ExplainabilityPanel } from './components/ExplainabilityPanel';
import { PatternChecklist } from './components/PatternChecklist';
import { EvidenceTrail } from './components/EvidenceTrail';
import { QuickSummaryBriefing } from './components/QuickSummaryBriefing';
import { EventBriefingHeader } from './components/EventBriefingHeader';
import { ShareableCard } from './components/ShareableCard';
import { FeedbackModal } from './components/FeedbackModal';
import { ApiKeysModal } from './components/ApiKeysModal';
import { ArticleMode } from './components/ArticleMode';
import { TrendingDashboard } from './components/TrendingDashboard';
import { CredibilityLookup } from './components/CredibilityLookup';
import { ClaimHistoryView } from './components/ClaimHistory';
import { verifySingleClaim, checkBackendHealth } from './api/client';
import { VerificationResult } from './types';
import { Shield, Sparkles, AlertCircle } from 'lucide-react';

export function App() {
  const [activeTab, setActiveTab] = useState<'verify' | 'article' | 'trending' | 'sources' | 'history'>('verify');
  const [isBackendHealthy, setIsBackendHealthy] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [verificationResult, setVerificationResult] = useState<VerificationResult | null>(null);

  // Modals
  const [showShareModal, setShowShareModal] = useState(false);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [showApiKeysModal, setShowApiKeysModal] = useState(false);

  useEffect(() => {
    // Initial health check
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    const ok = await checkBackendHealth();
    setIsBackendHealthy(ok);
  };

  const handleVerify = async (text: string, isUrl: boolean, bypassCache: boolean) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await verifySingleClaim(
        text,
        isUrl ? text : undefined,
        bypassCache
      );
      setVerificationResult(data);
      setActiveTab('verify');
    } catch (err: any) {
      setError(err.message || 'Verification failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectTrendingOrHistoryClaim = (claimText: string) => {
    setActiveTab('verify');
    handleVerify(claimText, false, false);
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col font-sans">
      {/* Top Navigation */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isBackendHealthy={isBackendHealthy}
        onOpenApiKeys={() => setShowApiKeysModal(true)}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Verify Tab */}
        {activeTab === 'verify' && (
          <div className="space-y-8">
            {/* Hero Header */}
            {!verificationResult && (
              <div className="text-center space-y-3 max-w-3xl mx-auto pt-4 pb-2">
                <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-950/80 border border-emerald-800 text-emerald-400 text-xs font-semibold">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Real-Time Multi-Source Fact Checking & Misinformation Defense</span>
                </div>
                <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
                  Transparent, Evidence-Backed <br />
                  <span className="bg-gradient-to-r from-emerald-400 via-teal-300 to-sky-400 bg-clip-text text-transparent">
                    Claim Verification
                  </span>
                </h1>
                <p className="text-sm sm:text-base text-slate-400 max-w-2xl mx-auto leading-relaxed">
                  Verify any factual assertion, social media rumor, or news headline within seconds.
                  TruthLens uncovers the trail of evidence, detects red-flag manipulation heuristics, and cross-references publisher credibility.
                </p>
              </div>
            )}

            {/* Input Component */}
            <ClaimInput onVerify={handleVerify} isLoading={isLoading} />

            {/* Error banner */}
            {error && (
              <div className="max-w-4xl mx-auto bg-rose-950/70 border border-rose-800 text-rose-300 p-4 rounded-xl text-sm flex items-center space-x-2.5">
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Verification Result Display */}
            {verificationResult && (
              <div className="max-w-4xl mx-auto space-y-6 pt-2">
                {/* Mode B: Event Query Header */}
                {verificationResult.mode === 'Event Query' && (
                  <EventBriefingHeader
                    mode={verificationResult.mode}
                    eventMeta={verificationResult.event_meta}
                    extractedQuery={verificationResult.extracted_claim}
                  />
                )}

                {/* Mode A / Mode C: Verdict Card */}
                {verificationResult.mode !== 'Event Query' && (
                  <VerdictCard
                    result={verificationResult}
                    onOpenShareModal={() => setShowShareModal(true)}
                    onOpenFeedbackModal={() => setShowFeedbackModal(true)}
                  />
                )}

                {/* Mode C (Hybrid): Show Event Header alongside Verdict */}
                {verificationResult.mode === 'Hybrid' && (
                  <EventBriefingHeader
                    mode={verificationResult.mode}
                    eventMeta={verificationResult.event_meta}
                    extractedQuery={verificationResult.extracted_claim}
                  />
                )}

                {/* Explainability & Clause Alignment (Mode A & Mode C) */}
                {verificationResult.mode !== 'Event Query' && (
                  <ExplainabilityPanel
                    explanation={verificationResult.explanation}
                    claimText={verificationResult.extracted_claim}
                  />
                )}

                {/* Misinformation Red-Flag Pattern Checklist (Mode A & Mode C) */}
                {verificationResult.mode !== 'Event Query' && (
                  <PatternChecklist patterns={verificationResult.red_flags} />
                )}

                {/* Quick Summary — 360° Incident Briefing (All Modes) */}
                <QuickSummaryBriefing summary={verificationResult.quick_summary} />

                {/* Evidence Trail / Sources & Further Reading (All Modes) */}
                <EvidenceTrail
                  sources={verificationResult.sources}
                  isSettledFact={verificationResult.is_settled_fact}
                  category={verificationResult.category}
                  webSearch={verificationResult.web_search}
                />
              </div>
            )}
          </div>
        )}

        {/* Article Mode Tab */}
        {activeTab === 'article' && <ArticleMode />}

        {/* Trending Tab */}
        {activeTab === 'trending' && (
          <TrendingDashboard onSelectClaim={handleSelectTrendingOrHistoryClaim} />
        )}

        {/* Sources Tab */}
        {activeTab === 'sources' && <CredibilityLookup />}

        {/* History Tab */}
        {activeTab === 'history' && (
          <ClaimHistoryView onSelectClaim={handleSelectTrendingOrHistoryClaim} />
        )}
      </main>

      {/* Shareable Card Modal */}
      {showShareModal && verificationResult && (
        <ShareableCard
          result={verificationResult}
          onClose={() => setShowShareModal(false)}
        />
      )}

      {/* Community Feedback Modal */}
      {showFeedbackModal && verificationResult && (
        <FeedbackModal
          claimText={verificationResult.extracted_claim}
          givenVerdict={verificationResult.verdict}
          onClose={() => setShowFeedbackModal(false)}
        />
      )}

      {/* Google API Keys & Search Modal */}
      {showApiKeysModal && (
        <ApiKeysModal
          onClose={() => setShowApiKeysModal(false)}
          onKeySaved={() => {
            checkHealth();
          }}
        />
      )}

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-[#0b0f19] py-8 text-center text-xs text-slate-500 font-mono">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <Shield className="w-4 h-4 text-emerald-400" />
            <span className="text-slate-300 font-bold font-sans">TruthLens</span>
            <span>— AI Fact-Checking & Misinformation Detection Engine</span>
          </div>
          <div>
            <span>Google Fact Check Tools API • Live News Aggregation • Local NLP Pattern Engine</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
