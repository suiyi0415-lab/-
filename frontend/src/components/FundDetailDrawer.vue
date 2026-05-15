<template>
  <a-drawer
    :visible="visible"
    :width="600"
    :footer="false"
    unmount-on-close
    @cancel="emit('update:visible', false)"
  >
    <template #title>
      <div class="drawer-title">
        <span class="drawer-code mono">{{ fundCode }}</span>
        <span class="drawer-name">{{ fundName }}</span>
        <span class="drawer-pct mono" :class="estPct >= 0 ? 'c-up' : 'c-down'">
          {{ estPct >= 0 ? '+' : '' }}{{ estPct.toFixed(2) }}%
        </span>
      </div>
    </template>

    <!-- 分时走势图 -->
    <div class="section">
      <div class="section-label">分时走势</div>
      <div ref="chartRef" class="chart-box"></div>
    </div>

    <!-- 重仓股透视 -->
    <div class="section">
      <div class="section-label">重仓股透视 <span class="section-hint">{{ quarter }}</span></div>
      <a-table
        :data="holdings"
        :loading="holdingsLoading"
        :pagination="false"
        :bordered="false"
        size="small"
        class="holdings-table"
      >
        <template #columns>
          <a-table-column title="股票" data-index="stock_name" :width="120">
            <template #cell="{ record }">
              <div class="stock-cell">
                <span class="stock-name">{{ record.stock_name }}</span>
                <span class="stock-code mono">{{ record.stock_code }}</span>
              </div>
            </template>
          </a-table-column>
          <a-table-column title="权重" data-index="weight" align="right" :width="80">
            <template #cell="{ record }">
              <span class="mono">{{ record.weight.toFixed(2) }}%</span>
            </template>
          </a-table-column>
          <a-table-column title="涨跌幅" data-index="pct_change" align="right" :width="90">
            <template #cell="{ record }">
              <span class="mono" :class="record.pct_change >= 0 ? 'c-up' : 'c-down'">
                {{ record.pct_change >= 0 ? '+' : '' }}{{ record.pct_change.toFixed(2) }}%
              </span>
            </template>
          </a-table-column>
          <a-table-column title="主力净流入" data-index="main_net_inflow" align="right" :width="110">
            <template #cell="{ record }">
              <span
                v-if="record.main_net_inflow != null"
                class="mono"
                :class="record.main_net_inflow >= 0 ? 'c-up' : 'c-down'"
              >
                {{ fmtInflow(record.main_net_inflow) }}
              </span>
              <span v-else class="c-muted">--</span>
            </template>
          </a-table-column>
        </template>
      </a-table>
    </div>
  </a-drawer>
</template>

<script setup>
import { ref, watch, nextTick, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { fetchFundIntraday, fetchHoldingsRadar } from '../api/fund.js'

const props = defineProps({
  visible: { type: Boolean, default: false },
  fundCode: { type: String, required: true },
  fundName: { type: String, default: '' },
})

const emit = defineEmits(['update:visible'])

// 分时图
const chartRef = ref(null)
let chartInstance = null
const estPct = ref(0)
const quarter = ref('')

// 重仓股
const holdings = ref([])
const holdingsLoading = ref(false)

function fmtInflow(val) {
  const abs = Math.abs(val)
  const sign = val >= 0 ? '+' : '-'
  if (abs >= 1e8) return sign + (abs / 1e8).toFixed(2) + '亿'
  if (abs >= 1e4) return sign + (abs / 1e4).toFixed(0) + '万'
  return sign + abs.toFixed(0)
}

// ECharts 暗黑主题配置
function getChartOption(records) {
  const times = records.map(r => r.time)
  const prices = records.map(r => r.price)
  const avgPrices = records.map(r => r.avg_price)

  // 计算昨收价参考线（用第一条数据的 price 近似）
  const basePrice = prices.length > 0 ? prices[0] : 0

  return {
    animation: true,
    animationDuration: 600,
    grid: {
      top: 24,
      right: 16,
      bottom: 28,
      left: 52,
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1c2128',
      borderColor: '#30363d',
      textStyle: { color: '#f0f6fc', fontSize: 12, fontFamily: 'JetBrains Mono, monospace' },
      axisPointer: {
        type: 'cross',
        crossStyle: { color: '#30363d' },
        lineStyle: { color: '#30363d' },
      },
      formatter(params) {
        const time = params[0].axisValue
        let html = `<div style="margin-bottom:4px;color:#8b949e">${time}</div>`
        params.forEach(p => {
          const color = p.color
          const val = p.value
          const diff = val - basePrice
          const diffPct = basePrice > 0 ? ((diff / basePrice) * 100).toFixed(2) : '0.00'
          const sign = diff >= 0 ? '+' : ''
          html += `<div style="display:flex;justify-content:space-between;gap:16px">`
          html += `<span><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${color};margin-right:6px"></span>${p.seriesName}</span>`
          html += `<span style="font-weight:600">${val.toFixed(4)} <span style="color:${diff >= 0 ? '#3fb950' : '#f85149'}">${sign}${diffPct}%</span></span>`
          html += `</div>`
        })
        return html
      },
    },
    xAxis: {
      type: 'category',
      data: times,
      axisLine: { lineStyle: { color: '#21262d' } },
      axisTick: { show: false },
      axisLabel: {
        color: '#484f58',
        fontSize: 10,
        fontFamily: 'JetBrains Mono, monospace',
        interval: Math.floor(times.length / 6),
      },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: '#484f58',
        fontSize: 10,
        fontFamily: 'JetBrains Mono, monospace',
        formatter: v => v.toFixed(3),
      },
      splitLine: {
        lineStyle: { color: '#161b22', type: 'dashed' },
      },
    },
    series: [
      {
        name: '最新价',
        type: 'line',
        data: prices,
        symbol: 'none',
        lineStyle: { width: 1.5, color: '#58a6ff' },
        itemStyle: { color: '#58a6ff' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(88,166,255,0.12)' },
            { offset: 1, color: 'rgba(88,166,255,0)' },
          ]),
        },
      },
      {
        name: '均价',
        type: 'line',
        data: avgPrices,
        symbol: 'none',
        lineStyle: { width: 1, color: '#d29922', type: 'dashed' },
        itemStyle: { color: '#d29922' },
      },
    ],
  }
}

async function loadIntraday() {
  try {
    const data = await fetchFundIntraday(props.fundCode)
    await nextTick()
    if (!chartRef.value) return

    if (!chartInstance) {
      chartInstance = echarts.init(chartRef.value, null, { renderer: 'canvas' })
    }
    chartInstance.setOption(getChartOption(data.records), true)
  } catch {
    // 静默失败，抽屉内不弹错误
  }
}

async function loadHoldings() {
  holdingsLoading.value = true
  try {
    const data = await fetchHoldingsRadar(props.fundCode)
    holdings.value = data.holdings || []
    estPct.value = data.estimated_pct || 0
    quarter.value = data.quarter || ''
  } catch {
    holdings.value = []
  } finally {
    holdingsLoading.value = false
  }
}

function handleResize() {
  chartInstance?.resize()
}

// 监听 visible 变化，打开时加载数据
watch(() => props.visible, (val) => {
  if (val && props.fundCode) {
    loadIntraday()
    loadHoldings()
    window.addEventListener('resize', handleResize)
  } else {
    window.removeEventListener('resize', handleResize)
  }
})

onUnmounted(() => {
  chartInstance?.dispose()
  chartInstance = null
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.drawer-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.drawer-code {
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 0.5px;
}

.drawer-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.drawer-pct {
  font-size: 16px;
  font-weight: 700;
  margin-left: auto;
}

.c-up { color: #3fb950; }
.c-down { color: #f85149; }
.c-muted { color: #484f58; }

.section {
  margin-bottom: 24px;
}

.section-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 10px;
  letter-spacing: 0.3px;
}

.section-hint {
  font-size: 11px;
  font-weight: 400;
  color: var(--text-muted);
  margin-left: 6px;
}

.chart-box {
  width: 100%;
  height: 250px;
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: 6px;
}

/* 表格样式覆盖 */
.holdings-table :deep(.arco-table) {
  background: transparent;
}

.holdings-table :deep(.arco-table-th) {
  background: var(--bg-surface) !important;
  color: var(--text-muted) !important;
  font-size: 11px !important;
  letter-spacing: 0.5px;
  border-bottom-color: var(--border-default) !important;
}

.holdings-table :deep(.arco-table-td) {
  background: transparent !important;
  color: var(--text-primary) !important;
  border-bottom-color: var(--border-subtle) !important;
  font-size: 13px;
}

.holdings-table :deep(.arco-table-tr:hover .arco-table-td) {
  background: var(--bg-hover) !important;
}

.stock-cell {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.stock-cell .stock-name {
  font-weight: 600;
  font-size: 13px;
  color: var(--text-primary);
}

.stock-cell .stock-code {
  font-size: 11px;
  color: var(--text-muted);
}

.mono {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}
</style>
