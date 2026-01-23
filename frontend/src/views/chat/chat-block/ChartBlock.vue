<script setup lang="ts">
import type { ChatMessage } from '@/api/chat.ts'
import DisplayChartBlock from '@/views/chat/component/DisplayChartBlock.vue'
import ChartPopover from '@/views/chat/chat-block/ChartPopover.vue'
import { computed, ref, watch } from 'vue'
import { useClipboard } from '@vueuse/core'
import { concat } from 'lodash-es'
import type { ChartTypes } from '@/views/chat/component/BaseChart.ts'
import ICON_BAR from '@/assets/svg/chart/icon_bar_outlined.svg'
import ICON_COLUMN from '@/assets/svg/chart/icon_dashboard_outlined.svg'
import ICON_LINE from '@/assets/svg/chart/icon_chart-line.svg'
import ICON_PIE from '@/assets/svg/chart/icon_pie_outlined.svg'
import ICON_TABLE from '@/assets/svg/chart/icon_form_outlined.svg'
import icon_sql_outlined from '@/assets/svg/icon_sql_outlined.svg'
import icon_export_outlined from '@/assets/svg/icon_export_outlined.svg'
import icon_file_image_colorful from '@/assets/svg/icon_file-image_colorful.svg'
import icon_file_excel_colorful from '@/assets/svg/icon_file-excel_colorful.svg'
import icon_into_item_outlined from '@/assets/svg/icon_into-item_outlined.svg'
import icon_window_max_outlined from '@/assets/svg/icon_window-max_outlined.svg'
import icon_window_mini_outlined from '@/assets/svg/icon_window-mini_outlined.svg'
import icon_copy_outlined from '@/assets/svg/icon_copy_outlined.svg'
import { useI18n } from 'vue-i18n'
import SQLComponent from '@/views/chat/component/SQLComponent.vue'
import { useAssistantStore } from '@/stores/assistant'
import AddViewDashboard from '@/views/dashboard/common/AddViewDashboard.vue'
import html2canvas from 'html2canvas'
import { chatApi } from '@/api/chat'

const props = withDefaults(
  defineProps<{
    recordId?: number
    message: ChatMessage
    isPredict?: boolean
    chatType?: ChartTypes
    enlarge?: boolean
    loadingData?: boolean
    // 新增分页相关 Props
    total?: number
    currentPage?: number
    pageSize?: number
  }>(),
  {
    recordId: undefined,
    isPredict: false,
    chatType: undefined,
    enlarge: false,
    loadingData: false,
    // 默认值
    total: 0,
    currentPage: 1,
    pageSize: 20,
  }
)

const { copy } = useClipboard({ legacy: true })
const loading = ref<boolean>(false)
const { t } = useI18n()
const addViewRef = ref(null)
// 新增分页相关 Emits
const emits = defineEmits([
  'exitFullScreen',
  'update:currentPage',
  'update:pageSize',
  'page-change',
])

const dataObject = computed<{
  fields: Array<string>
  data: Array<{ [key: string]: any }>
  limit: number | undefined
}>(() => {
  if (props.message?.record?.data) {
    if (typeof props.message?.record?.data === 'string') {
      return JSON.parse(props.message.record.data)
    } else {
      return props.message.record.data
    }
  }
  return {}
})
const assistantStore = useAssistantStore()
const isCompletePage = computed(() => !assistantStore.getAssistant || assistantStore.getEmbedded)

const isAssistant = computed(() => assistantStore.getAssistant)

const chartId = computed(() => props.message?.record?.id + (props.enlarge ? '-fullscreen' : ''))

const data = computed(() => {
  if (props.isPredict) {
    let _list = []
    if (
      props.message?.record?.predict_data &&
      typeof props.message?.record?.predict_data === 'string'
    ) {
      if (
        props.message?.record?.predict_data.length > 0 &&
        props.message?.record?.predict_data.trim().startsWith('[') &&
        props.message?.record?.predict_data.trim().endsWith(']')
      ) {
        try {
          _list = JSON.parse(props.message?.record?.predict_data)
        } catch (e) {
          console.error(e)
        }
      }
    } else {
      if (props.message?.record?.predict_data?.length > 0) {
        _list = props.message?.record?.predict_data
      }
    }
    if (_list.length == 0) {
      return _list
    }

    if (dataObject.value.data && dataObject.value.data?.length > 0) {
      return concat(dataObject.value.data, _list)
    }
    return _list
  } else {
    return dataObject.value.data
  }
})

const chartRef = ref()

const chartObject = computed<{
  type: ChartTypes
  title: string
  axis: {
    x: { name: string; value: string }
    y: { name: string; value: string }
    series: { name: string; value: string }
  }
  columns: Array<{ name: string; value: string }>
}>(() => {
  if (props.message?.record?.chart) {
    return JSON.parse(props.message.record.chart)
  }
  return {}
})

const currentChartType = ref<ChartTypes | undefined>(
  props.chatType ?? chartObject.value.type ?? 'table'
)

const chartType = computed<ChartTypes>({
  get() {
    if (currentChartType.value) {
      return currentChartType.value
    }
    return props.chatType ?? chartObject.value.type ?? 'table'
  },
  set(v) {
    currentChartType.value = v
  },
})

const chartTypeList = computed(() => {
  const _list = []
  if (chartObject.value) {
    switch (chartObject.value.type) {
      case 'table':
        break
      case 'column':
      case 'bar':
      case 'line':
        _list.push({
          value: 'column',
          name: t('chat.chart_type.column'),
          icon: ICON_COLUMN,
        })
        _list.push({
          value: 'bar',
          name: t('chat.chart_type.bar'),
          icon: ICON_BAR,
        })
        _list.push({
          value: 'line',
          name: t('chat.chart_type.line'),
          icon: ICON_LINE,
        })
        break
      case 'pie':
        _list.push({
          value: 'pie',
          name: t('chat.chart_type.pie'),
          icon: ICON_PIE,
        })
    }
  }

  return _list
})

function changeTable() {
  onTypeChange('table')
}

function onTypeChange(val: any) {
  chartType.value = val
  chartRef.value?.onTypeChange()
}

function reloadChart() {
  chartRef.value?.onTypeChange()
}

const dialogVisible = ref(false)

function openFullScreen() {
  dialogVisible.value = true
}

function closeFullScreen() {
  emits('exitFullScreen')
}

function onExitFullScreen() {
  dialogVisible.value = false
}

const sqlShow = ref(false)

function showSql() {
  sqlShow.value = true
}

function addToDashboard() {
  const recordeInfo = {
    id: '1-1',
    data: {
      data: data.value,
    },
    chart: {},
  }
  // @ts-expect-error eslint-disable-next-line @typescript-eslint/ban-ts-comment
  const chartBaseInfo = JSON.parse(props.message?.record?.chart)
  recordeInfo['chart'] = {
    type: currentChartType.value,
    title: chartBaseInfo.title,
    columns: chartBaseInfo.columns,
    xAxis: chartBaseInfo.axis?.x ? [chartBaseInfo.axis.x] : [],
    yAxis: chartBaseInfo.axis?.y ? [chartBaseInfo.axis.y] : [],
    series: chartBaseInfo.axis?.series ? [chartBaseInfo.axis.series] : [],
  }
  // @ts-expect-error eslint-disable-next-line @typescript-eslint/ban-ts-comment
  addViewRef.value?.optInit(recordeInfo)
}

function copyText() {
  if (props.message?.record?.sql) {
    copy(props.message.record.sql).then(() => {
      ElMessage.success(t('embedded.copy_successful'))
    })
  }
}

const exportRef = ref()

function exportToExcel() {
  if (chartRef.value && props.recordId) {
    loading.value = true
    chatApi
      .export2Excel(props.recordId, props.message?.record?.chat_id || 0)
      .then((res) => {
        const blob = new Blob([res], {
          type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        const link = document.createElement('a')
        link.href = URL.createObjectURL(blob)
        link.download = `${chartObject.value.title ?? 'Excel'}.xlsx`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      })
      .catch(async (error) => {
        if (error.response) {
          try {
            let text = await error.response.data.text()
            try {
              text = JSON.parse(text)
            } finally {
              ElMessage({
                message: text,
                type: 'error',
                showClose: true,
              })
            }
          } catch (e) {
            console.error('Error processing error response:', e)
          }
        } else {
          console.error('Other error:', error)
          ElMessage({
            message: error,
            type: 'error',
            showClose: true,
          })
        }
      })
      .finally(() => {
        loading.value = false
      })
    exportRef.value?.hide()
  }
}

function exportToImage() {
  const obj = document.getElementById('chart-component-' + chartId.value)
  if (obj) {
    html2canvas(obj).then((canvas) => {
      canvas.toBlob(function (blob) {
        if (blob) {
          const link = document.createElement('a')
          link.download = (chartObject.value.title ?? 'chart') + '.png' // Specify filename
          link.href = URL.createObjectURL(blob)
          document.body.appendChild(link) // Append to body to make it clickable
          link.click() // Programmatically click the link
          document.body.removeChild(link) // Clean up
          URL.revokeObjectURL(link.href) // Release the object URL
        }
      }, 'image/png')
    })
  }
  exportRef.value?.hide()
}

defineExpose({
  reloadChart,
})

watch(
  () => chartObject.value?.type,
  (val) => {
    if (val) {
      currentChartType.value = val
    }
  }
)

// ✅ 新增：监听数据变化，强制刷新图表/表格
// 这一步至关重要，解决分页后数据变了但界面不刷新的问题
watch(
  () => data.value,
  () => {
    // 当分页数据变化时，调用子组件的刷新方法
    if (chartRef.value) {
      reloadChart()
    }
  },
  { deep: true } // 深度监听，确保捕获对象内部变化
)

// ✅ 分页处理函数
const handleSizeChange = (val: number) => {
  emits('update:pageSize', val)
  emits('page-change')
}
const handleCurrentChange = (val: number) => {
  emits('update:currentPage', val)
  emits('page-change')
}
</script>

<template>
  <div
    v-if="
      !message.isTyping &&
      ((!isPredict && (message?.record?.sql || message?.record?.chart)) ||
        (isPredict && message?.record?.chart && data.length > 0))
    "
    v-loading.fullscreen.lock="loading"
    class="chart-component-container"
    :class="{ 'full-screen': enlarge }"
  >
    <div class="header-bar">
      <div class="title">
        {{ chartObject.title }}
      </div>
      <div class="buttons-bar">
        <div class="chart-select-container">
          <el-tooltip effect="dark" :offset="8" :content="t('chat.type')" placement="top">
            <ChartPopover
              v-if="chartTypeList.length > 0"
              :chart-type-list="chartTypeList"
              :chart-type="chartType"
              :title="t('chat.type')"
              @type-change="onTypeChange"
            ></ChartPopover>
          </el-tooltip>

          <el-tooltip
            effect="dark"
            :offset="8"
            :content="t('chat.chart_type.table')"
            placement="top"
          >
            <el-button
              class="tool-btn"
              :class="{ 'chart-active': currentChartType === 'table' }"
              text
              @click="changeTable"
            >
              <el-icon size="16">
                <ICON_TABLE />
              </el-icon>
            </el-button>
          </el-tooltip>
        </div>

        <div v-if="message?.record?.sql">
          <el-tooltip effect="dark" :offset="8" :content="t('chat.show_sql')" placement="top">
            <el-button class="tool-btn" text @click="showSql">
              <el-icon size="16">
                <icon_sql_outlined />
              </el-icon>
            </el-button>
          </el-tooltip>
        </div>
        <div v-if="message?.record?.chart">
          <el-popover
            ref="exportRef"
            trigger="click"
            popper-class="export_to_select"
            placement="bottom"
          >
            <template #reference>
              <div>
                <el-tooltip
                  effect="dark"
                  :offset="8"
                  :content="t('chat.export_to')"
                  placement="top"
                >
                  <el-button class="tool-btn" text>
                    <el-icon size="16">
                      <icon_export_outlined />
                    </el-icon>
                  </el-button>
                </el-tooltip>
              </div>
            </template>
            <div class="popover">
              <div class="popover-content">
                <div class="title">{{ t('chat.export_to') }}</div>
                <div class="popover-item" @click="exportToExcel">
                  <el-icon size="16">
                    <icon_file_excel_colorful />
                  </el-icon>
                  <div class="model-name">{{ t('chat.excel') }}</div>
                </div>
                <div
                  v-if="currentChartType !== 'table'"
                  class="popover-item"
                  @click="exportToImage"
                >
                  <el-icon size="16">
                    <icon_file_image_colorful />
                  </el-icon>
                  <div class="model-name">{{ t('chat.picture') }}</div>
                </div>
              </div>
            </div>
          </el-popover>
        </div>
        <div v-if="message?.record?.chart && !isAssistant">
          <el-tooltip effect="dark" :content="t('chat.add_to_dashboard')" placement="top">
            <el-button class="tool-btn" text @click="addToDashboard">
              <el-icon size="16">
                <icon_into_item_outlined />
              </el-icon>
            </el-button>
          </el-tooltip>
        </div>
        <div class="divider" />
        <div v-if="!enlarge">
          <el-tooltip
            effect="dark"
            :offset="8"
            :content="!isCompletePage ? $t('common.zoom_in') : t('chat.full_screen')"
            placement="top"
          >
            <el-button class="tool-btn" text @click="openFullScreen">
              <el-icon size="16">
                <icon_window_max_outlined />
              </el-icon>
            </el-button>
          </el-tooltip>
        </div>
        <div v-else>
          <el-tooltip
            effect="dark"
            :offset="8"
            :content="!isCompletePage ? $t('common.zoom_out') : t('chat.exit_full_screen')"
            placement="top"
          >
            <el-button class="tool-btn" text @click="closeFullScreen">
              <el-icon size="16">
                <icon_window_mini_outlined />
              </el-icon>
            </el-button>
          </el-tooltip>
        </div>
      </div>
    </div>

    <template v-if="message?.record?.chart">
      <div class="chart-block">
        <DisplayChartBlock
          :id="chartId"
          ref="chartRef"
          :chart-type="chartType"
          :message="message"
          :data="data"
          :loading-data="loadingData"
        />
      </div>

      <div v-if="currentChartType === 'table' && total > 0" class="pagination-container">
        <el-pagination
          :current-page="props.currentPage"
          :page-size="props.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          size="small"
          layout="total, prev, pager, next, sizes"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          :disabled="loadingData"
        />
      </div>

      <div v-if="dataObject.limit" class="over-limit-hint">
        {{ t('chat.data_over_limit', [dataObject.limit]) }}
      </div>
    </template>

    <AddViewDashboard ref="addViewRef"></AddViewDashboard>
    <el-dialog
      v-if="!enlarge"
      v-model="dialogVisible"
      fullscreen
      :show-close="false"
      class="chart-fullscreen-dialog"
      header-class="chart-fullscreen-dialog-header"
      body-class="chart-fullscreen-dialog-body"
    >
      <ChartBlock
        v-if="dialogVisible"
        :message="message"
        :record-id="recordId"
        :is-predict="isPredict"
        :chat-type="chartType"
        :loading-data="loadingData"
        enlarge
        :total="total"
        :current-page="currentPage"
        :page-size="pageSize"
        @update:current-page="(val) => emits('update:currentPage', val)"
        @update:page-size="(val) => emits('update:pageSize', val)"
        @page-change="() => emits('page-change')"
        @exit-full-screen="onExitFullScreen"
      />
    </el-dialog>

    <el-drawer
      v-model="sqlShow"
      :size="!isCompletePage ? '100%' : '600px'"
      :title="t('chat.show_sql')"
      direction="rtl"
      body-class="chart-sql-drawer-body"
    >
      <div class="sql-block">
        <SQLComponent
          v-if="message.record?.sql"
          :sql="message.record?.sql"
          style="margin-top: 12px"
        />
        <el-button v-if="message.record?.sql" circle class="input-icon" @click="copyText">
          <el-icon size="16">
            <icon_copy_outlined />
          </el-icon>
        </el-button>
      </div>
    </el-drawer>
  </div>
</template>

<style scoped lang="less">
.chart-component-container {
  width: 100%;
  padding: 16px;
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(222, 224, 227, 1);
  border-radius: 12px;
  background-color: var(--el-bg-color); // 确保背景色
  height: fit-content;
  position: relative; // ✅ 确保 v-loading 能够正确遮罩

  &.full-screen {
    border: none;
    height: 100%;
    padding: 0;
  }

  .header-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px; // 底部留白

    .title {
      font-size: 16px;
      font-weight: 500;
      color: var(--el-text-color-primary);
    }

    .buttons-bar {
      display: flex;
      align-items: center;
      gap: 4px; // 按钮间距

      .chart-select-container {
        display: flex;
        background-color: var(--el-fill-color-light);
        border-radius: 6px;
        padding: 2px;
        margin-right: 8px;

        .tool-btn {
          height: 24px;
          padding: 0 8px;
          border-radius: 4px;

          &.chart-active {
            background-color: var(--el-bg-color);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
          }
        }
      }

      .divider {
        width: 1px;
        height: 16px;
        background-color: var(--el-border-color);
        margin: 0 8px;
      }
    }
  }

  .chart-block {
    flex: 1;
    overflow: hidden; // 防止图表溢出
    min-height: 300px;
  }

  // ✅ 分页样式优化
  .pagination-container {
    display: flex;
    justify-content: flex-end;
    margin-top: 12px;
    padding-top: 8px;
    border-top: 1px dashed var(--el-border-color-lighter);
  }

  .over-limit-hint {
    margin-top: 8px;
    font-size: 12px;
    color: var(--el-text-color-secondary);
    text-align: right;
  }
}
</style>
