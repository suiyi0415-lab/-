<template>
  <div class="panel">
    <div class="panel-head">
      <div class="panel-label">
        <span class="panel-tag tag-blue">资金</span>
        <h2>主力资金动向</h2>
      </div>
      <button class="btn-refresh" @click="refreshAll" :disabled="refreshing">
        <span class="btn-icon" :class="{ spin: refreshing }">&#8635;</span>
        {{ refreshing ? '刷新中' : '刷新' }}
      </button>
    </div>

    <!-- 表格 -->
    <div class="table-wrap">
      <table class="tbl" v-if="stockList.length">
        <thead>
          <tr>
            <th class="col-name">个股</th>
            <th class="col-num">收盘价</th>
            <th class="col-num">涨跌幅</th>
            <th class="col-num">主力净流入</th>
            <th class="col-num">超大单</th>
            <th class="col-num">距高点</th>
            <th class="col-num">风险</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="stock in stockList"
            :key="stock.code"
            :class="{ 'row-danger': stock.risk?.near_high_warning }"
          >
            <td class="col-name">
              <div class="stock-info">
                <span class="stock-name">{{ stock.data?.stock_name || '--' }}</span>
                <span class="stock-code mono">{{ stock.code }}</span>
              </div>
            </td>
            <td class="col-num mono">{{ fmtPrice(stock.data?.latest?.close) }}</td>
            <td class="col-num mono" :class="colorCls(stock.data?.latest?.pct_change)">
              {{ fmtPct(stock.data?.latest?.pct_change) }}
            </td>
            <td class="col-num mono" :class="colorCls(stock.data?.latest?.main_net_inflow)">
              {{ fmtMoney(stock.data?.latest?.main_net_inflow) }}
            </td>
            <td class="col-num mono" :class="colorCls(stock.data?.latest?.super_big_net_inflow)">
              {{ fmtMoney(stock.data?.latest?.super_big_net_inflow) }}
            </td>
            <td class="col-num mono" :class="highCls(stock.risk?.current_vs_high_pct)">
              {{ stock.risk?.current_vs_high_pct != null ? stock.risk.current_vs_high_pct + '%' : '--' }}
            </td>
            <td class="col-num">
              <span v-if="stock.risk?.near_high_warning" class="badge-danger">高位</span>
              <span v-else class="badge-safe">正常</span>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="empty" v-else-if="!loading">
        暂无数据
      </div>

      <div class="loading" v-if="loading">
        <a-spin :size="24" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchStockFlow } from '../api/stock.js'

const props = defineProps({
  stocks: { type: Array, default: () => ['300308', '300394'] },
})

const loading = ref(true)
const refreshing = ref(false)
const stockList = ref([])

function fmtMoney(val) {
  if (val == null) return '--'
  const abs = Math.abs(val)
  const sign = val >= 0 ? '' : '-'
  if (abs >= 1e8) return sign + (abs / 1e8).toFixed(2) + '亿'
  if (abs >= 1e4) return sign + (abs / 1e4).toFixed(0) + '万'
  return sign + abs.toFixed(0)
}

function fmtPct(val) {
  if (val == null) return '--'
  return (val >= 0 ? '+' : '') + val.toFixed(2) + '%'
}

function fmtPrice(val) {
  if (val == null) return '--'
  return val.toFixed(2)
}

function colorCls(val) {
  if (val == null) return ''
  return val > 0 ? 'c-up' : val < 0 ? 'c-down' : ''
}

function highCls(val) {
  if (val == null) return ''
  if (val < 5) return 'c-down'
  if (val < 15) return 'c-warn'
  return 'c-up'
}

async function loadAll() {
  const results = await Promise.all(
    props.stocks.map(async (code) => {
      try {
        const data = await fetchStockFlow(code)
        return { code, data, risk: data.risk }
      } catch {
        return { code, data: null, risk: null }
      }
    })
  )
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
.panel {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: 6px;
  overflow: hidden;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-default);
}

.panel-label {
  display: flex;
  align-items: center;
  gap: 10px;
}

.panel-label h2 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.panel-tag {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 3px;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.tag-blue {
  color: var(--color-accent);
  background: rgba(88, 166, 255, 0.12);
  border: 1px solid rgba(88, 166, 255, 0.2);
}

.btn-refresh {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 12px;
  background: transparent;
  border: 1px solid var(--border-default);
  border-radius: 4px;
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  font-family: var(--font-ui);
  transition: all 0.15s;
}

.btn-refresh:hover:not(:disabled) {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--text-muted);
}

.btn-refresh:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-icon {
  font-size: 14px;
  display: inline-block;
}

.btn-icon.spin {
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 表格 */
.table-wrap {
  overflow-x: auto;
}

.tbl {
  width: 100%;
  border-collapse: collapse;
}

.tbl th {
  font-size: 11px;
  font-weight: 500;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 10px 14px;
  text-align: left;
  border-bottom: 1px solid var(--border-default);
  white-space: nowrap;
}

.tbl td {
  padding: 12px 14px;
  font-size: 13px;
  border-bottom: 1px solid var(--border-subtle);
}

.tbl tr:last-child td {
  border-bottom: none;
}

.tbl tr:hover td {
  background: var(--bg-hover);
}

.col-num {
  text-align: right;
  white-space: nowrap;
}

.col-name {
  white-space: nowrap;
}

.stock-info {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.stock-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 13px;
}

.stock-code {
  font-size: 11px;
  color: var(--text-muted);
}

.c-up {
  color: var(--color-up);
}

.c-down {
  color: var(--color-down);
}

.c-warn {
  color: var(--color-warn);
}

/* 高位预警行 */
.row-danger td {
  background: rgba(248, 81, 73, 0.04) !important;
}

.badge-danger {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 3px;
  color: var(--color-down);
  background: rgba(248, 81, 73, 0.1);
}

.badge-safe {
  display: inline-block;
  font-size: 11px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 3px;
  color: var(--text-muted);
  background: var(--bg-hover);
}

.empty {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
  font-size: 13px;
}

.loading {
  display: flex;
  justify-content: center;
  padding: 40px;
}
</style>
