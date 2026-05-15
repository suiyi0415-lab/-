<template>
  <div class="shell">
    <!-- 顶部栏 - Bloomberg 风格紧凑头部 -->
    <header class="topbar">
      <div class="topbar-left">
        <span class="topbar-logo">QB</span>
        <span class="topbar-title">QuantBoard</span>
        <span class="topbar-sep">/</span>
        <span class="topbar-page">监控面板</span>
      </div>
      <div class="topbar-right">
        <span class="topbar-status">
          <span class="status-dot"></span>
          API 在线
        </span>
        <span class="topbar-time mono">{{ currentTime }}</span>
      </div>
    </header>

    <main class="main">
      <!-- 低位定投区 -->
      <div class="panel">
        <div class="panel-head">
          <div class="panel-label">
            <span class="panel-tag tag-green">定投</span>
            <h2>低位定投池</h2>
          </div>
          <span class="panel-hint">估值分位 &lt; 20% 适合加仓</span>
        </div>
        <div class="grid-3">
          <FundMonitor fund-code="512010" fund-name="医药ETF" />
          <FundMonitor fund-code="159915" fund-name="创业板ETF" />
          <FundMonitor fund-code="513180" fund-name="恒生科技ETF" />
        </div>
      </div>

      <!-- 资金流向区 -->
      <div class="panel">
        <StockFlowTable :stocks="['300308', '300394']" />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import FundMonitor from './components/FundMonitor.vue'
import StockFlowTable from './components/StockFlowTable.vue'

const currentTime = ref('')
let timer = null

function updateTime() {
  const d = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  currentTime.value = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  clearInterval(timer)
})
</script>

<style scoped>
.shell {
  min-height: 100vh;
  background: var(--bg-base);
}

/* 顶部栏 */
.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 48px;
  padding: 0 20px;
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border-default);
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.topbar-logo {
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: 13px;
  color: var(--bg-base);
  background: var(--text-primary);
  padding: 2px 6px;
  border-radius: 3px;
  letter-spacing: -0.5px;
}

.topbar-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
}

.topbar-sep {
  color: var(--text-muted);
  font-size: 14px;
}

.topbar-page {
  font-size: 13px;
  color: var(--text-secondary);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.topbar-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}

.status-dot {
  width: 6px;
  height: 6px;
  background: var(--color-up);
  border-radius: 50%;
}

.topbar-time {
  font-size: 12px;
  color: var(--text-muted);
}

/* 主内容 */
.main {
  max-width: 1280px;
  margin: 0 auto;
  padding: 20px;
}

/* 面板 */
.panel {
  margin-bottom: 24px;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 0 2px;
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

.tag-green {
  color: var(--color-up);
  background: rgba(63, 185, 80, 0.12);
  border: 1px solid rgba(63, 185, 80, 0.2);
}

.panel-hint {
  font-size: 12px;
  color: var(--text-muted);
}

.grid-3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

@media (max-width: 960px) {
  .grid-3 {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .grid-3 {
    grid-template-columns: 1fr;
  }
}
</style>
