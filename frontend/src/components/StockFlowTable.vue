<template>
  <div class="flow-panel">
    <div class="panel-header">
      <div class="panel-title-group">
        <h3 class="panel-title">主力资金动向</h3>
        <span class="panel-subtitle">实时追踪板块资金流入流出</span>
      </div>
      <button class="refresh-btn" @click="refreshAll" :disabled="refreshing">
        <span class="refresh-icon" :class="{ spinning: refreshing }">&#8635;</span>
        {{ refreshing ? '刷新中' : '刷新数据' }}
      </button>
    </div>

    <div class="stock-grid">
      <div
        v-for="stock in stockList"
        :key="stock.code"
        class="stock-row"
        :class="{ 'row-warning': stock.risk?.near_high_warning }"
      >
        <div class="stock-identity">
          <span class="stock-code">{{ stock.code }}</span>
          <span class="stock-name">{{ stock.data?.stock_name || '--' }}</span>
        </div>

        <div class="stock-metrics">
          <div class="metric-cell">
            <span class="cell-label">主力净流入</span>
            <span class="cell-value" :class="flowClass(stock.data?.latest?.main_net_inflow)">
              {{ formatMoney(stock.data?.latest?.main_net_inflow) }}
            </span>
          </div>

          <div class="metric-cell">
            <span class="cell-label">主力占比</span>
            <span class="cell-value" :class="flowClass(stock.data?.latest?.main_net_ratio)">
              {{ formatPercent(stock.data?.latest?.main_net_ratio) }}
            </span>
          </div>

          <div class="metric-cell">
            <span class="cell-label">超大单净流入</span>
            <span class="cell-value" :class="flowClass(stock.data?.latest?.super_big_net_inflow)">
              {{ formatMoney(stock.data?.latest?.super_big_net_inflow) }}
            </span>
          </div>

          <div class="metric-cell">
            <span class="cell-label">距年内高点</span>
            <span
              class="cell-value"
              :class="highClass(stock.risk?.current_vs_high_pct)"
              :style="{ fontWeight: stock.risk?.near_high_warning ? '700' : '500' }"
            >
              {{ stock.risk?.current_vs_high_pct != null ? stock.risk.current_vs_high_pct + '%' : '--' }}
            </span>
          </div>

          <div class="metric-cell">
            <span class="cell-label">年内最高</span>
            <span class="cell-value neutral">
              {{ stock.risk?.year_high || '--' }}
            </span>
          </div>
        </div>

        <div class="risk-indicator" v-if="stock.risk?.near_high_warning">
          <span class="risk-badge">高位预警</span>
        </div>
      </div>

      <div class="loading-state" v-if="loading">
        <a-spin :size="28" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchStockFlow } from '../api/stock.js'

const props = defineProps({
  stocks: {
    type: Array,
    default: () => ['300308', '300394'],
  },
})

const loading = ref(true)
const refreshing = ref(false)
const stockList = ref([])

function formatMoney(val) {
  if (val == null) return '--'
  const abs = Math.abs(val)
  if (abs >= 1e8) return (val / 1e8).toFixed(2) + '亿'
  if (abs >= 1e4) return (val / 1e4).toFixed(2) + '万'
  return val.toFixed(0)
}

function formatPercent(val) {
  if (val == null) return '--'
  return val.toFixed(2) + '%'
}

function flowClass(val) {
  if (val == null) return 'neutral'
  return val > 0 ? 'positive' : val < 0 ? 'negative' : 'neutral'
}

function highClass(val) {
  if (val == null) return 'neutral'
  if (val < 5) return 'negative'
  if (val < 15) return 'warning'
  return 'positive'
}

async function loadStockData(code) {
  try {
    const data = await fetchStockFlow(code)
    return { code, data, risk: data.risk }
  } catch {
    return { code, data: null, risk: null }
  }
}

async function loadAll() {
  const results = await Promise.all(props.stocks.map(loadStockData))
  stockList.value = results
}

async function refreshAll() {
  refreshing.value = true
  try {
    await loadAll()
  } finally {
    refreshing.value = false
  }
}

onMounted(async () => {
  try {
    await loadAll()
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.flow-panel {
  background: #1e1e2e;
  border: 1px solid #2a2a3e;
  border-radius: 12px;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #2a2a3e;
  background: linear-gradient(180deg, #22223a 0%, #1e1e2e 100%);
}

.panel-title-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.panel-title {
  font-size: 18px;
  font-weight: 600;
  color: #e5e7eb;
  margin: 0;
  letter-spacing: 0.3px;
}

.panel-subtitle {
  font-size: 12px;
  color: #6b7280;
  letter-spacing: 0.3px;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 8px;
  color: #60a5fa;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
}

.refresh-btn:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.18);
  border-color: rgba(59, 130, 246, 0.4);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.refresh-icon {
  font-size: 16px;
  display: inline-block;
  transition: transform 0.3s ease;
}

.refresh-icon.spinning {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.stock-grid {
  padding: 0;
}

.stock-row {
  display: flex;
  align-items: center;
  padding: 18px 24px;
  border-bottom: 1px solid #2a2a3e;
  transition: background 0.2s ease;
  position: relative;
}

.stock-row:last-child {
  border-bottom: none;
}

.stock-row:hover {
  background: rgba(255, 255, 255, 0.02);
}

.stock-row.row-warning {
  background: rgba(239, 68, 68, 0.04);
  border-left: 3px solid #ef4444;
}

.stock-identity {
  min-width: 140px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stock-code {
  font-size: 11px;
  color: #6b7280;
  font-family: 'SF Mono', 'Cascadia Code', 'Consolas', monospace;
  letter-spacing: 0.5px;
}

.stock-name {
  font-size: 15px;
  font-weight: 600;
  color: #e5e7eb;
}

.stock-metrics {
  display: flex;
  flex: 1;
  gap: 4px;
}

.metric-cell {
  flex: 1;
  text-align: right;
  padding: 8px 12px;
}

.cell-label {
  display: block;
  font-size: 10px;
  color: #4b5563;
  margin-bottom: 4px;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.cell-value {
  font-size: 14px;
  font-weight: 500;
  font-family: 'SF Mono', 'Cascadia Code', 'Consolas', monospace;
}

.cell-value.positive {
  color: #10b981;
}

.cell-value.negative {
  color: #ef4444;
}

.cell-value.warning {
  color: #f59e0b;
}

.cell-value.neutral {
  color: #9ca3af;
}

.risk-indicator {
  position: absolute;
  top: 10px;
  right: 16px;
}

.risk-badge {
  display: inline-block;
  padding: 3px 10px;
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
  font-size: 11px;
  font-weight: 600;
  border-radius: 4px;
  letter-spacing: 0.5px;
  animation: pulse-badge 2s ease-in-out infinite;
}

@keyframes pulse-badge {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.loading-state {
  display: flex;
  justify-content: center;
  padding: 48px 0;
}
</style>
