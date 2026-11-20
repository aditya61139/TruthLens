import {
  VerificationResult,
  ArticleAnalysisResult,
  TrendingClaimItem,
  HistoryItem,
  SystemStats,
  PublisherCredibility
} from '../types';

const API_BASE = '/api';

async function handleApiError(response: Response, defaultMessage: string): Promise<never> {
  const errorText = await response.text().catch(() => '');
  let detail = defaultMessage;
  try {
    const parsed = JSON.parse(errorText);
    detail = parsed.detail || parsed.message || defaultMessage;
  } catch {
    if (errorText.includes('ECONNREFUSED') || response.status === 504 || response.status === 502 || response.status === 500) {
      detail = 'Cannot connect to TruthLens backend server (127.0.0.1:8000). Please ensure the backend is running using start.bat or run_backend.bat.';
    } else if (errorText) {
      detail = errorText;
    }
  }
  throw new Error(detail);
}

export async function verifySingleClaim(
  text: string,
  url?: string,
  bypassCache = false
): Promise<VerificationResult> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text,
        url,
        bypass_cache: bypassCache
      })
    });
  } catch {
    throw new Error('Cannot connect to TruthLens backend server (127.0.0.1:8000). Please ensure the backend is running using start.bat or run_backend.bat.');
  }

  if (!response.ok) {
    await handleApiError(response, 'Verification failed.');
  }

  return response.json();
}

export async function verifyArticleContent(
  text?: string,
  url?: string,
  maxClaims = 6
): Promise<ArticleAnalysisResult> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/verify/article`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text,
        url,
        max_claims: maxClaims
      })
    });
  } catch {
    throw new Error('Cannot connect to TruthLens backend server (127.0.0.1:8000). Please ensure the backend is running using start.bat or run_backend.bat.');
  }

  if (!response.ok) {
    await handleApiError(response, 'Article analysis failed.');
  }

  return response.json();
}

export async function getTrendingClaims(category?: string): Promise<{
  trending: TrendingClaimItem[];
  stats: {
    categories: Record<string, number>;
    verdicts: Record<string, number>;
    total_monitored: number;
  };
}> {
  const params = new URLSearchParams();
  if (category && category !== 'All') params.append('category', category);

  const response = await fetch(`${API_BASE}/trending?${params.toString()}`);
  if (!response.ok) throw new Error('Failed to load trending claims');
  return response.json();
}

export async function getClaimHistory(query?: string, verdict?: string): Promise<{
  total: number;
  history: HistoryItem[];
}> {
  const params = new URLSearchParams();
  if (query) params.append('q', query);
  if (verdict && verdict !== 'All') params.append('verdict', verdict);

  const response = await fetch(`${API_BASE}/history?${params.toString()}`);
  if (!response.ok) throw new Error('Failed to load history');
  return response.json();
}

export async function deleteHistoryItem(id: number): Promise<void> {
  const response = await fetch(`${API_BASE}/history/${id}`, { method: 'DELETE' });
  if (!response.ok) throw new Error('Failed to delete history entry');
}

export async function getPublishersList(
  q?: string,
  category?: string,
  bias?: string
): Promise<{ total: number; results: PublisherCredibility[] }> {
  const params = new URLSearchParams();
  if (q) params.append('q', q);
  if (category && category !== 'All') params.append('category', category);
  if (bias && bias !== 'All') params.append('bias', bias);

  const response = await fetch(`${API_BASE}/sources?${params.toString()}`);
  if (!response.ok) throw new Error('Failed to load publishers');
  return response.json();
}

export async function submitFeedback(data: {
  claim_text: string;
  given_verdict: string;
  feedback_type: 'helpful' | 'incorrect';
  suggested_verdict?: string;
  comments?: string;
}): Promise<{ status: string; message: string }> {
  const response = await fetch(`${API_BASE}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });

  if (!response.ok) throw new Error('Failed to submit feedback');
  return response.json();
}

export async function getSystemStats(): Promise<SystemStats> {
  const response = await fetch(`${API_BASE}/stats`);
  if (!response.ok) throw new Error('Failed to fetch stats');
  return response.json();
}

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const res = await fetch('/health', { method: 'GET' });
    if (!res.ok) return false;
    const data = await res.json().catch(() => null);
    return Boolean(data && (data.status === 'healthy' || data.status === 'online'));
  } catch {
    return false;
  }
}
