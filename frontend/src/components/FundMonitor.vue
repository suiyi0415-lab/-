<template>
  <div class="fund-card" :class="cardClass">
    <div class="card-header">
      <div class="fund-info">
        <span class="fund-code">{{ fundCode }}</span>
        <h3 class="fund-name">{{ fundName }}</h3>
      </div>
      <div class="fund-nav">
        <span class="nav-label">单位净值</span>
        <span class="nav-value">{{ summary.latest_nav || '--' }}</span>
      </div>
    </div>

    <div class="card-body" v-if="summary.total_records">
      <div class="metric-row">
        <div class="metric">
          <span class="metric-label">估值分位</span>
          <span class="metric-value" :style="{ color: percentileColor }">
            {{ percentileText }}
          </span>
        </div>
        <div class="metric">
          <span class="metric-label">区间最高</span>
          <span class="metric-value">{{ summary.period_high }}</span>
        </div>
        <div class="metric">
          <span class="metric-label">区间最低</span>
          <span class="metric-value">{{ summary.period_low }}</span>
        </div>
      </div>

      <div class="range-bar">
        <div class="range-track">
          <div class="range-fill" :style="{ width: percentile + '%' }"></div>
          <div class="range-thumb" :style="{ left: percentile + '%' }"></div>
        </div>
        <div class="range-labels">
          <span>低估</span>
          <span>适中</span>
          <span>高估</span>
        </div>
      </div>

      <div class="signal-tag" :class="signalClass">
        {{ signalText }}
      </div>
    </div>

    <div class="card-loading" v-else-if="loading">
      <a-spin :size="24" />
    </div>

    <div class="card-footer">
      <span class="update-time" v-if="summary.latest_date">
        更新于 {{ summary.latest_date }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { fetchEtfHistory } from '../api/fund.js'

const props = defineProps({
  fundCode: { type: String, required: true },
  fundName: { type: String, default: 'ETF基金' },
})

const loading = ref(true)
const summary = ref({})
const percentile = ref(0)

const percentileText = computed(() => {
  if (!summary.value.total_records) return '--'
  return percentile.value.toFixed(1) + '%'
})

const percentileColor = computed(() => {
  if (percentile.value <= 20) return '#10b981'
  if (percentile.value <= 50) return '#f59e0b'
  return '#ef4444'
})

const signalText = computed(() => {
  if (percentile.value <= 20) return '低位区间 · 适合定投'
  if (percentile.value <= 40) return '合理偏低 · 可关注'
  if (percentile.value <= 60) return '估值适中 · 观望'
  if (percentile.value <= 80) return '估值偏高 · 谨慎操作'
  return '高位区间 · 注意风险'
})

const signalClass = computed(() => {
  if (percentile.value <= 20) return 'signal-buy'
  if (percentile.value <= 40) return 'signal-watch'
  if (percentile.value <= 60) return 'signal-neutral'
  return 'signal-warn'
})

const cardClass = computed(() => {
  if (percentile.value <= 20) return 'card-undervalued'
  if (percentile.value >= 50) return 'card-overvalued'
  return ''
})

onMounted(async () => {
  try {
    const data = await fetchEtfHistory(props.fundCode)
    summary.value = data.summary || {}
    percentile.value = data.summary?.percentile || 0
  } catch {
    summary.value = {}
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.fund-card {
  background: #1e1e2e;
  border: 1px solid #2a2a3e;
  border-radius: 12px;
  padding: 24px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.fund-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: #3b3b5c;
  transition: background 0.3s ease;
}

.fund-card:hover {
  border-color: #3b3b5c;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.fund-card.card-undervalued::before {
  background: linear-gradient(90deg, #10b981, #34d399);
}

.fund-card.card-overvalued::before {
  background: linear-gradient(90deg, #ef4444, #f87171);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.fund-info {
  flex: 1;
}

.fund-code {
  font-size: 12px;
  color: #6b7280;
  font-family: 'SF Mono', 'Cascadia Code', 'Consolas', monospace;
  letter-spacing: 0.5px;
}

.fund-name {
  font-size: 18px;
  font-weight: 600;
  color: #e5e7eb;
  margin: 4px 0 0 0;
  letter-spacing: 0.3px;
}

.fund-nav {
  text-align: right;
}

.nav-label {
  display: block;
  font-size: 11px;
  color: #6b7280;
  margin-bottom: 2px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.nav-value {
  font-size: 26px;
  font-weight: 700;
  color: #f9fafb;
  font-family: 'SF Mono', 'Cascadia Code', 'Consolas', monospace;
}

.card-body {
  border-top: 1px solid #2a2a3e;
  padding-top: 16px;
}

.metric-row {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.metric {
  flex: 1;
  background: #16162a;
  border-radius: 8px;
  padding: 10px 12px;
}

.metric-label {
  display: block;
  font-size: 11px;
  color: #6b7280;
  margin-bottom: 4px;
  letter-spacing: 0.5px;
}

.metric-value {
  font-size: 16px;
  font-weight: 600;
  font-family: 'SF Mono', 'Cascadia Code', 'Consolas', monospace;
  color: #e5e7eb;
}

.range-bar {
  margin: 16px 0;
}

.range-track {
  height: 6px;
  background: #2a2a3e;
  border-radius: 3px;
  position: relative;
  overflow: visible;
}

.range-fill {
  height: 100%;
  border-radius: 3px;
  background: linear-gradient(90deg, #10b981 0%, #f59e0b 50%, #ef4444 100%);
  transition: width 0.6s ease;
}

.range-thumb {
  position: absolute;
  top: 50%;
  width: 14px;
  height: 14px;
  background: #f9fafb;
  border: 2px solid #3b3b5c;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  transition: left 0.6s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.range-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 6px;
  font-size: 10px;
  color: #4b5563;
  letter-spacing: 0.5px;
}

.signal-tag {
  display: inline-block;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  letter-spacing: 0.3px;
}

.signal-buy {
  background: rgba(16, 185, 129, 0.12);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.signal-watch {
  background: rgba(59, 130, 246, 0.12);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.signal-neutral {
  background: rgba(107, 114, 128, 0.12);
  color: #9ca3af;
  border: 1px solid rgba(107, 114, 128, 0.2);
}

.signal-warn {
  background: rgba(239, 68, 68, 0.12);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.card-loading {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}

.card-footer {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #2a2a3e;
}

.update-time {
  font-size: 11px;
  color: #4b5563;
  letter-spacing: 0.3px;
}
</style>
