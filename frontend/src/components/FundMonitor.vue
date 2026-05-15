<template>
  <div class="card" :class="cardState">
    <div class="card-top">
      <div class="card-id">
        <span class="card-code mono">{{ fundCode }}</span>
        <span class="card-name">{{ fundName }}</span>
      </div>
      <div class="card-nav">
        <span class="nav-label">净值</span>
        <span class="nav-val mono">{{ summary.latest_nav || '--' }}</span>
      </div>
    </div>

    <div class="card-body" v-if="summary.total_records">
      <div class="bar-row">
        <div class="bar-track">
          <div class="bar-fill" :style="{ width: pct + '%' }" :class="barColor"></div>
        </div>
        <span class="bar-pct mono" :class="barColor">{{ pct.toFixed(1) }}%</span>
      </div>

      <div class="range-row">
        <div class="range-item">
          <span class="range-label">低</span>
          <span class="range-val mono">{{ summary.period_low }}</span>
        </div>
        <div class="range-divider"></div>
        <div class="range-item">
          <span class="range-label">高</span>
          <span class="range-val mono">{{ summary.period_high }}</span>
        </div>
      </div>

      <div class="signal" :class="signalClass">
        {{ signalText }}
      </div>
    </div>

    <div class="card-body card-skeleton" v-else-if="loading">
      <div class="sk-line"></div>
      <div class="sk-line short"></div>
    </div>

    <div class="card-foot" v-if="summary.latest_date">
      {{ summary.latest_date }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { fetchEtfHistory } from '../api/fund.js'

const props = defineProps({
  fundCode: { type: String, required: true },
  fundName: { type: String, default: '' },
})

const loading = ref(true)
const summary = ref({})
const pct = ref(0)

const cardState = computed(() => {
  if (pct.value <= 20) return 'state-low'
  if (pct.value >= 80) return 'state-high'
  return ''
})

const barColor = computed(() => {
  if (pct.value <= 20) return 'bar-up'
  if (pct.value >= 80) return 'bar-down'
  return 'bar-neutral'
})

const signalText = computed(() => {
  if (pct.value <= 20) return '适合定投'
  if (pct.value <= 40) return '偏低 · 可关注'
  if (pct.value <= 60) return '适中'
  if (pct.value <= 80) return '偏高'
  return '高位 · 风险'
})

const signalClass = computed(() => {
  if (pct.value <= 20) return 'sig-up'
  if (pct.value <= 40) return 'sig-blue'
  if (pct.value >= 80) return 'sig-down'
  return 'sig-neutral'
})

onMounted(async () => {
  try {
    const data = await fetchEtfHistory(props.fundCode)
    summary.value = data.summary || {}
    pct.value = data.summary?.percentile || 0
  } catch {
    summary.value = {}
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.card {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: 6px;
  overflow: hidden;
}

.card:hover {
  border-color: var(--text-muted);
}

/* 低位状态 - 左侧色条 */
.card.state-low {
  border-left: 2px solid var(--color-up);
}

.card.state-high {
  border-left: 2px solid var(--color-down);
}

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px 16px 0;
}

.card-id {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.card-code {
  font-size: 11px;
  color: var(--text-muted);
  letter-spacing: 0.5px;
}

.card-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.card-nav {
  text-align: right;
}

.nav-label {
  display: block;
  font-size: 10px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 1px;
}

.nav-val {
  font-size: 22px;
  font-weight: 600;
  color: var(--text-primary);
}

.card-body {
  padding: 14px 16px 0;
}

/* 进度条 */
.bar-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.bar-track {
  flex: 1;
  height: 4px;
  background: var(--border-subtle);
  border-radius: 2px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.8s ease;
}

.bar-up {
  background: var(--color-up);
}

.bar-down {
  background: var(--color-down);
}

.bar-neutral {
  background: var(--text-muted);
}

.bar-pct {
  font-size: 13px;
  font-weight: 600;
  min-width: 48px;
  text-align: right;
}

.bar-pct.bar-up {
  color: var(--color-up);
}

.bar-pct.bar-down {
  color: var(--color-down);
}

.bar-pct.bar-neutral {
  color: var(--text-secondary);
}

/* 区间 */
.range-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

.range-item {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.range-label {
  font-size: 11px;
  color: var(--text-muted);
}

.range-val {
  font-size: 13px;
  color: var(--text-secondary);
}

.range-divider {
  flex: 1;
  height: 1px;
  background: var(--border-subtle);
}

/* 信号标签 */
.signal {
  display: inline-block;
  font-size: 12px;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: 3px;
}

.sig-up {
  color: var(--color-up);
  background: rgba(63, 185, 80, 0.1);
}

.sig-blue {
  color: var(--color-accent);
  background: rgba(88, 166, 255, 0.1);
}

.sig-down {
  color: var(--color-down);
  background: rgba(248, 81, 73, 0.1);
}

.sig-neutral {
  color: var(--text-secondary);
  background: var(--bg-hover);
}

/* 骨架屏 */
.card-skeleton .sk-line {
  height: 10px;
  background: var(--bg-hover);
  border-radius: 2px;
  margin-bottom: 8px;
}

.card-skeleton .sk-line.short {
  width: 60%;
}

/* 底部 */
.card-foot {
  padding: 10px 16px;
  margin-top: 14px;
  border-top: 1px solid var(--border-subtle);
  font-size: 11px;
  color: var(--text-muted);
}
</style>
