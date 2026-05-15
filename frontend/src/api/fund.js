import http from './http'

export function fetchFundHistory(fundCode, period = '1y') {
  return http.get('/fund/history', { params: { fund_code: fundCode, period } })
}

export function fetchEtfHistory(code) {
  return http.get('/etf/history', { params: { code } })
}

export function fetchFundIntraday(code) {
  return http.get('/fund/intraday', { params: { code } })
}

export function fetchHoldingsRadar(fundCode) {
  return http.get('/fund/holdings_radar', { params: { fund_code: fundCode } })
}
