import { api, type AnalyzeResponse, type HistoryItem, type StockSearchResult } from './client'

export const analysisApi = {
  analyze: (symbol: string, region?: string) =>
    api.post<AnalyzeResponse>('/analysis/analyze', { symbol, region }).then(r => r.data),
  history: (limit = 50, symbol?: string) =>
    api.get<HistoryItem[]>('/analysis/history', { params: { limit, symbol } }).then(r => r.data),
  getRun: (runId: string) =>
    api.get<{ run_id: string; symbol: string; region: string; payload: any }>(`/analysis/history/${runId}`).then(r => r.data),
  searchStocks: (q: string) =>
    api.get<StockSearchResult[]>('/stocks/search', { params: { q } }).then(r => r.data),
}
