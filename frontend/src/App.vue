<template>
  <div class="app-shell">
    <header class="app-header">
      <div class="header-left">
        <div class="logo-mark"></div>
        <div class="header-text">
          <h1 class="app-title">QuantBoard</h1>
          <span class="app-subtitle">ETF 估值 &amp; 资金监控</span>
        </div>
      </div>
      <div class="header-right">
        <span class="header-badge">v1.0</span>
        <span class="header-time">{{ currentTime }}</span>
      </div>
    </header>

    <main class="app-main">
      <section class="section">
        <div class="section-header">
          <div class="section-title-group">
            <h2 class="section-title">低位定投池</h2>
            <span class="section-desc">估值分位低于 20% 为适合定投区间</span>
          </div>
        </div>
        <div class="card-grid">
          <FundMonitor fund-code="512010" fund-name="医药ETF" />
          <FundMonitor fund-code="159915" fund-name="创业板ETF" />
          <FundMonitor fund-code="513180" fund-name="恒生科技ETF" />
        </div>
      </section>

      <section class="section">
        <StockFlowTable :stocks="['300308', '300394']" />
      </section>
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
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
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
.app-shell {
  min-height: 100vh;
  background: #13131f;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 32px;
  background: rgba(30, 30, 46, 0.8);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid #2a2a3e;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.logo-mark {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  border-radius: 8px;
  flex-shrink: 0;
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.app-title {
  font-size: 18px;
  font-weight: 700;
  color: #f9fafb;
  margin: 0;
  letter-spacing: 1px;
}

.app-subtitle {
  font-size: 11px;
  color: #6b7280;
  letter-spacing: 0.5px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-badge {
  padding: 4px 10px;
  background: rgba(59, 130, 246, 0.12);
  color: #60a5fa;
  font-size: 11px;
  font-weight: 600;
  border-radius: 6px;
  letter-spacing: 0.5px;
}

.header-time {
  font-size: 13px;
  color: #9ca3af;
  font-family: 'SF Mono', 'Cascadia Code', 'Consolas', monospace;
  letter-spacing: 0.5px;
}

.app-main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px 24px;
}

.section {
  margin-bottom: 40px;
}

.section-header {
  margin-bottom: 20px;
}

.section-title-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  color: #e5e7eb;
  margin: 0;
  letter-spacing: 0.3px;
}

.section-desc {
  font-size: 13px;
  color: #6b7280;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 20px;
}
</style>
