import http from './http'

export function fetchStockFlow(stockCode) {
  return http.get('/stock/market_flow', { params: { stock_code: stockCode } })
}
