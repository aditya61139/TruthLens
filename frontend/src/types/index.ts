export type VerdictType = 'True' | 'False' | 'Misleading' | 'Unverified' | 'Satire' | 'Error';

export interface PublisherCredibility {
  name?: string;
  domain?: string;
  category?: string;
  bias_rating?: string;
  factual_reporting?: string;
  credibility_score?: number;
  trust_tier?: string;
  country?: string;
  notes?: string;
  matched?: boolean;
}

export interface EventMeta {
  category_emoji?: string;
  category_label?: string;
  title?: string;
  region?: string;
  date_range?: string;
  status?: '🔴 Ongoing' | '🟡 Developing' | '🟢 Resolved' | string;
}

export interface ImpactNumbers {
  deaths?: string;
  displaced?: string;
  areas_affected?: string;
  damage?: string;
  rescue?: string;
}

export interface QuickSummary {
  what_happened: string;
  full_context: string;
  timeline?: string[];
  impact_numbers?: ImpactNumbers;
  key_parties?: Array<{ name: string; role: string }>;
  key_data?: string[];
  perspectives?: Array<{ party: string; stance: string }>;
  current_status?: string;
  key_takeaway: string;
}

export interface SourceEvidence {
  source_name: string;
  source_site?: string;
  source_url?: string;
  title: string;
  raw_rating?: string;
  normalized_verdict: VerdictType;
  stance?: 'ENTAILS' | 'CONTRADICTS' | 'NEUTRAL';
  stance_reason?: string;
  source_type?: '[🟢 Primary Source]' | '[🔵 Major News Outlet]' | '[🟡 Fact-Checker]' | '[🟠 Domain Expert / Academic]' | '[⚪ Other / General]' | string;
  date_published?: string;
  review_date?: string;
  paywall?: boolean;
  archive_url?: string;
  claim_text?: string;
  claimant?: string;
  confidence_contribution?: number;
  explanation?: string;
  publisher_credibility?: PublisherCredibility;
}

export interface RedFlagItem {
  category: string;
  pattern: string;
  severity: 'Low' | 'Medium' | 'High' | 'Critical';
  impact: number;
  explanation: string;
  detected_instances?: string[];
}

export interface MisinformationAnalysis {
  red_flag_score: number;
  risk_level: string;
  risk_color: 'green' | 'yellow' | 'amber' | 'red';
  total_flags: number;
  flags: RedFlagItem[];
  checklist: {
    clickbait_detected: boolean;
    emotional_manipulation: boolean;
    vague_sourcing: boolean;
    conspiracy_cues: boolean;
    dubious_statistics: boolean;
    excessive_sensationalism: boolean;
  };
}

export interface ClaimClauseBreakdown {
  clause: string;
  status: 'debunked' | 'verified' | 'misleading' | 'unverified' | 'satire' | 'accurate' | 'unsupported';
  note: string;
}

export interface ExplainabilityData {
  why_bullets: string[];
  claim_breakdown: ClaimClauseBreakdown[];
  unverified_aspects: string;
  plain_english_takeaway?: string;
}

export interface VerificationResult {
  cached: boolean;
  is_fuzzy_match?: boolean;
  fuzzy_similarity?: number;
  input_text: string;
  extracted_claim: string;
  mode?: 'Claim Verification' | 'Event Query' | 'Hybrid' | string;
  event_meta?: EventMeta;
  page_title?: string | null;
  url?: string | null;
  verdict: VerdictType;
  truth_value?: 'True' | 'False' | 'Likely True' | 'Likely False' | 'Misleading' | 'Satire' | 'Unverifiable' | string;
  knowledge_certainty?: 'Settled Knowledge' | 'Under Active Debate' | 'Emerging / Current Event' | 'Insufficient Evidence' | string;
  final_verdict_display?: string;
  claim_type?: 'SETTLED_FACT' | 'CURRENT_EVENT' | 'OPINION' | 'CONTESTED' | string;
  is_settled_fact?: boolean;
  fact_type?: string;
  is_time_sensitive?: boolean;
  web_search?: {
    attempted: boolean;
    query_used: string;
    provider: string;
    results_count: number;
  };
  confidence: number;
  confidence_factors: string[];
  category: string;
  summary: string;
  plain_english_takeaway?: string;
  llm_enhanced?: boolean;
  llm_warning?: string | null;
  gemini_calls_made?: number;
  error?: {
    code: string;
    message: string;
    status_code?: number;
    details?: string;
  } | null;
  explanation: ExplainabilityData;
  quick_summary?: QuickSummary;
  red_flags: MisinformationAnalysis;
  credibility: PublisherCredibility;
  sources: SourceEvidence[];
  verified_at?: string;
}

export interface ArticleClaimItem {
  claim_index: number;
  claim_text: string;
  context: string;
  verdict: VerdictType;
  confidence: number;
  summary: string;
  sources_count: number;
  sources: SourceEvidence[];
  red_flags: MisinformationAnalysis;
}

export interface ArticleAnalysisResult {
  article_title: string;
  url?: string;
  total_claims_analyzed: number;
  overall_trust_score: number;
  trust_grade: string;
  verdict_distribution: Record<VerdictType, number>;
  overall_red_flags: MisinformationAnalysis;
  publisher_credibility: PublisherCredibility;
  claims: ArticleClaimItem[];
}

export interface TrendingClaimItem {
  id: number;
  claim_text: string;
  verdict: VerdictType;
  confidence: number;
  category: string;
  summary: string;
  source_name: string;
  source_url: string;
  search_volume: number;
  last_checked?: string;
}

export interface HistoryItem {
  id: number;
  input_text: string;
  extracted_claim: string;
  verdict: VerdictType;
  confidence: number;
  category: string;
  sources_count: number;
  red_flag_score: number;
  summary: string;
  created_at?: string;
}

export interface SystemStats {
  total_verifications: number;
  cache_entries: number;
  total_cache_hits: number;
  total_publishers_tracked: number;
  user_satisfaction_rate: number;
  feedback_counts: {
    helpful: number;
    incorrect: number;
  };
  verdict_distribution: Record<string, number>;
  category_distribution: Record<string, number>;
}
