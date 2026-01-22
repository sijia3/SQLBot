<script setup lang="ts">
import ChartComponent from '@/views/chat/component/ChartComponent.vue'
import type { ChatMessage } from '@/api/chat.ts'
import { computed, nextTick, ref, watch } from 'vue'
import type { ChartTypes } from '@/views/chat/component/BaseChart.ts'
import { useI18n } from 'vue-i18n'
// 引入 Element Plus 的图标
import { Loading } from '@element-plus/icons-vue'

const props = defineProps<{
  id?: number | string
  chartType: ChartTypes
  message: ChatMessage
  data: Array<{ [key: string]: any }>
  loadingData?: boolean
}>()

const { t } = useI18n()

const chartObject = computed<{
  type: ChartTypes
  title: string
  axis: {
    x: { name: string; value: string }
    y: { name: string; value: string } | Array<{ name: string; value: string }>
    series: { name: string; value: string }
    'multi-quota': {
      name: string
      value: Array<string>
    }
  }
  columns: Array<{ name: string; value: string }>
}>(() => {
  if (props.message?.record?.chart) {
    return JSON.parse(props.message.record.chart)
  }
  return {}
})

const xAxis = computed(() => {
  const axis = chartObject.value?.axis
  if (axis?.x) {
    return [axis.x]
  }
  return []
})
const yAxis = computed(() => {
  const axis = chartObject.value?.axis
  if (!axis?.y) {
    return []
  }

  const y = axis.y
  const multiQuotaValues = axis['multi-quota']?.value || []

  // 统一处理为数组
  const yArray = Array.isArray(y) ? [...y] : [{ ...y }]

  // 标记 multi-quota
  return yArray.map((item) => ({
    ...item,
    'multi-quota': multiQuotaValues.includes(item.value),
  }))
})
const series = computed(() => {
  const axis = chartObject.value?.axis
  if (axis?.series) {
    return [axis.series]
  }
  return []
})

const multiQuotaName = computed(() => {
  return chartObject.value?.axis?.['multi-quota']?.name
})

const chartRef = ref()
const chartOpacity = ref(1)
const chartTransition = ref('none')
// 新增：专门控制渲染中的 loading 状态
const isRendering = ref(false)

// 开始渲染过渡：显示 Loading，隐藏图表
function startTransition() {
  isRendering.value = true // 立即显示加载图标
  chartTransition.value = 'none' // 关闭动画，瞬间隐藏
  chartOpacity.value = 0 // 隐藏图表（防止看到布局调整的丑样子）
}

// 结束渲染过渡：隐藏 Loading，淡入图表
function endTransition() {
  // 稍微延迟一点点，确保 Loading 图标至少闪现一下，给用户明确反馈
  setTimeout(() => {
    isRendering.value = false
    chartTransition.value = 'opacity 0.4s ease-in-out' // 开启平滑动画
    chartOpacity.value = 1
  }, 300) // 300ms 足够完成布局计算，且不会让用户觉得太久
}

// 监听数据变化（点击刷新或新数据到达）
watch(
  () => props.data,
  (newData) => {
    if (newData && newData.length > 0) {
      startTransition()
      // 等待 DOM 更新后重新渲染
      nextTick(() => {
        // 如果需要手动触发子组件更新，可以在这里调用，通常 props 变化会自动触发
        // 这里主要为了配合视觉过渡
        endTransition()
      })
    }
  },
  { immediate: true }
)

// 监听图表类型切换（点击表格/图表按钮）
function onTypeChange() {
  startTransition()

  nextTick(() => {
    chartRef.value?.destroyChart()
    chartRef.value?.renderChart()
    endTransition()
  })
}
function getViewInfo() {
  return {
    chart: {
      columns: chartObject.value?.columns,
      type: props.chartType,
      xAxis: xAxis.value,
      yAxis: yAxis.value,
      series: series.value,
      title: chartObject.value.title,
    },
    data: { data: props.data },
  }
}
function getExcelData() {
  return chartRef.value?.getExcelData()
}

defineExpose({
  onTypeChange,
  getViewInfo,
  getExcelData,
})
</script>

<template>
  <div v-if="message.record?.chart" class="chart-base-container">
    <div v-if="isRendering" class="rendering-loader">
      <div class="loader-content">
        <el-icon class="is-loading" :size="24"><Loading /></el-icon>
        <span class="loading-text">加载中...</span>
      </div>
    </div>

    <div
      v-if="message.record.id && data?.length > 0"
      style="height: 100%; width: 100%"
      :style="{
        opacity: chartOpacity,
        transition: chartTransition
      }"
    >
      <ChartComponent
        :id="id ?? 'default_chat_id'"
        ref="chartRef"
        :type="chartType"
        :columns="chartObject?.columns"
        :x="xAxis"
        :y="yAxis"
        :series="series"
        :data="data"
        :multi-quota-name="multiQuotaName"
      />
    </div>
    <el-empty v-else :description="loadingData ? t('chat.loading_data') : t('chat.no_data')" />
  </div>
</template>

<style scoped lang="less">
.chart-base-container {
  height: 100%;
  width: 100%;
  border-radius: 12px;
  background: rgba(224, 224, 226, 0.29);
  overflow: hidden;
  position: relative; // 确保 loader 绝对定位相对于此容器
}

.rendering-loader {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.5); // 半透明背景，让用户知道还是在当前卡片里
  backdrop-filter: blur(2px); // 可选：轻微模糊背景增加质感

  .loader-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;

    .loading-text {
      font-size: 12px;
      color: #909399;
    }
  }
}
</style>
