import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  withCredentials: true,
  timeout: 120_000,
})

export interface NewsItem { title: string; url: string; sources: string[] }

export interface AnalysisReport {
  symbol: string; name?: string; signal: string; confidence: string
  core_conclusion: string; drivers: string[]; risks: string[]; action: string
  price: number; currency: string
  change_1d_pct: number | null; change_1w_pct: number | null; change_1m_pct: number | null
  change_1d_vs_index?: number | null; change_1d_pct_rank?: number | null
  sector?: string | null; industry?: string | null
  pe_ratio?: number | null; forward_pe?: number | null; price_to_book?: number | null
  roe?: number | null; debt_to_equity?: number | null; profit_margin?: number | null
  revenue_growth?: number | null; market_cap?: number | null; dividend_yield?: number | null
  analyst_target_mean?: number | null; recommendation?: string | null; next_earnings_date?: string | null
  rsi_14?: number | null; macd?: { macd_line: number; signal_line: number; histogram: number } | null
  avg_volume_20d?: number | null; volatility_20d?: number | null
  beta?: number | null; beta_vs_index?: number | null
  sparkline?: number[]; news?: NewsItem[]
  error?: string
}

export interface AnalyzeResponse {
  run_id: string; symbol: string; region: string; report: AnalysisReport; gaps: GapSummary
}

export interface GapSummary {
  project: string; run_id: string; total: number
  by_severity: Record<string, number>; entries: GapEntry[]
}

export interface GapEntry { subject: string; category: string; severity: string; note: string }

export interface HistoryItem {
  run_id: string; symbol: string; region: string | null
  signal: string | null; confidence: string | null; action: string | null
  core_conclusion: string | null; created_at: string
}

export interface StockSearchResult { symbol: string; name: string; region: string }
