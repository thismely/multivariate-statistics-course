<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { ArrowLeft, ArrowUpRight, BookOpen, Download, ExternalLink, FileCode2, FileText, Link2, Orbit, Table2 } from 'lucide-vue-next'
import { useUniverse } from '../store'

const props = defineProps({
  resource: { type: Object, default: null },
  resources: { type: Array, default: () => [] },
})
const emit = defineEmits(['navigate'])
const store = useUniverse()

const loading = ref(false)
const error = ref('')
const textPreview = ref('')
const csvRows = ref([])
const csvTotalRows = ref(0)
const notebookCells = ref([])
const iframeSrc = ref('')
let controller

const typeLabels = {
  notes: '讲义',
  slides: '课件',
  notebook: 'Notebook',
  code: 'Python 代码',
  data: '数据集',
  case: '案例',
  exercise: '练习',
  reference: '参考资料',
}

const resource = computed(() => props.resource)
const typeLabel = computed(() => typeLabels[resource.value?.type] ?? '课程资源')
const extension = computed(() => {
  const path = String(resource.value?.path ?? '').split('?')[0].toLowerCase()
  return path.includes('.') ? path.split('.').pop() : ''
})
const previewPath = computed(() => {
  const preview = resource.value?.preview
  if (typeof preview === 'string') return preview
  if (preview && typeof preview === 'object') return preview.path ?? preview.href ?? ''
  return ''
})

function assetUrl(path) {
  const raw = String(path ?? '').trim()
  if (!raw) return ''
  if (/^(?:https?:|data:|blob:)/i.test(raw)) return raw
  const base = import.meta.env.BASE_URL || '/'
  const cleanBase = base.endsWith('/') ? base : `${base}/`
  const cleanPath = raw.replace(/^\.\//, '').replace(/^\/+/, '')
  return `${cleanBase}${cleanPath}`
}

const downloadUrl = computed(() => assetUrl(resource.value?.path || previewPath.value))
const previewKind = computed(() => {
  const r = resource.value
  if (!r) return 'none'
  if (previewPath.value && /\.html?($|\?)/i.test(previewPath.value)) return 'html'
  if (extension.value === 'html' || extension.value === 'htm') return 'html'
  if (extension.value === 'pdf') return 'pdf'
  if (r.type === 'notebook' && previewPath.value) return 'html'
  if (r.type === 'notebook' || extension.value === 'ipynb') return 'notebook'
  if (r.type === 'data' && ['csv', 'tsv'].includes(extension.value)) return 'csv'
  if (r.type === 'slides' && ['ppt', 'pptx'].includes(extension.value)) return 'download'
  if (r.type === 'data') return 'data'
  if (r.type === 'slides') return 'text'
  if (r.type === 'code' || r.type === 'notes' || r.type === 'exercise' || r.type === 'reference') return 'text'
  return 'text'
})

function parseCsvLine(line, delimiter = ',') {
  const cells = []
  let cell = ''
  let quoted = false
  for (let index = 0; index < line.length; index += 1) {
    const char = line[index]
    if (char === '"' && line[index + 1] === '"' && quoted) {
      cell += '"'
      index += 1
    } else if (char === '"') {
      quoted = !quoted
    } else if (char === delimiter && !quoted) {
      cells.push(cell)
      cell = ''
    } else {
      cell += char
    }
  }
  cells.push(cell)
  return cells
}

function parseCsv(text) {
  const lines = String(text).split(/\r?\n/).filter((line) => line.trim())
  const delimiter = extension.value === 'tsv' ? '\t' : ','
  csvTotalRows.value = lines.length
  csvRows.value = lines.slice(0, 11).map((line) => parseCsvLine(line, delimiter))
}

function notebookSource(cell) {
  return Array.isArray(cell?.source) ? cell.source.join('') : String(cell?.source ?? '')
}

function notebookOutput(cell) {
  if (!Array.isArray(cell?.outputs) || !cell.outputs.length) return ''
  return cell.outputs.map((output) => {
    if (typeof output.text === 'string') return output.text
    if (Array.isArray(output.text)) return output.text.join('')
    if (output.data?.['text/plain']) {
      return Array.isArray(output.data['text/plain']) ? output.data['text/plain'].join('') : output.data['text/plain']
    }
    return ''
  }).filter(Boolean).join('\n')
}

async function loadPreview() {
  controller?.abort()
  textPreview.value = ''
  csvRows.value = []
  csvTotalRows.value = 0
  notebookCells.value = []
  iframeSrc.value = ''
  error.value = ''
  const current = resource.value
  if (!current) return

  if (previewKind.value === 'html' && previewPath.value) {
    iframeSrc.value = assetUrl(previewPath.value)
    return
  }
  if (previewKind.value === 'pdf' || previewKind.value === 'download' || previewKind.value === 'data') return
  const path = current.path
  if (!path) return

  loading.value = true
  controller = new AbortController()
  try {
    const response = await fetch(assetUrl(path), { signal: controller.signal })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    if (previewKind.value === 'notebook' || extension.value === 'json' && current.type === 'notebook') {
      const notebook = await response.json()
      notebookCells.value = (notebook.cells ?? []).map((cell, index) => ({
        index: index + 1,
        cell_type: cell.cell_type ?? 'code',
        source: notebookSource(cell),
        output: notebookOutput(cell),
      }))
    } else {
      const text = await response.text()
      if (previewKind.value === 'csv') parseCsv(text)
      else {
        try {
          const parsed = JSON.parse(text)
          textPreview.value = JSON.stringify(parsed, null, 2)
        } catch {
          textPreview.value = text
        }
      }
    }
  } catch (caught) {
    if (caught?.name !== 'AbortError') error.value = '在线预览暂时不可用，请下载原件或检查静态资源路径。'
  } finally {
    loading.value = false
  }
}

watch(() => resource.value?.id, loadPreview, { immediate: true })
onBeforeUnmount(() => controller?.abort())

const relatedResources = computed(() => {
  const current = resource.value
  if (!current) return []
  const explicit = new Set([...(current.related_resource_ids ?? []), ...(current.data_ids ?? []), current.code_id, current.notebook_id].filter(Boolean))
  return props.resources.filter((item) => item.id !== current.id && (explicit.has(item.id) || item.chapter === current.chapter)).sort((a,b)=>Number(explicit.has(b.id))-Number(explicit.has(a.id))).slice(0, 10)
})

const knowledgeNodes = computed(() => (resource.value?.knowledge_nodes ?? []).map((id) => ({
  id,
  name: store.byId[id]?.name ?? id,
})))

function navigate(path) {
  emit('navigate', path)
}

function back() {
  navigate(resource.value?.chapter ? `/chapter/${encodeURIComponent(resource.value.chapter)}` : '/resources')
}

function openResource(id) {
  navigate(`/resource/${encodeURIComponent(id)}`)
}

function openSpace(id) {
  navigate(`/space?node=${encodeURIComponent(id)}`)
}

function provenanceText(value) {
  if (!value) return ''
  return typeof value === 'string' ? value : JSON.stringify(value)
}
</script>

<template>
  <section v-if="resource" class="course-resource-detail" aria-labelledby="course-resource-title">
    <div class="course-breadcrumbs">
      <button class="course-link-button" @click="back"><ArrowLeft :size="15" />返回资源库</button>
      <span>/</span>
      <span>{{ typeLabel }}</span>
      <span v-if="resource.chapter">/ {{ resource.chapter }}</span>
    </div>

    <header class="resource-detail-header">
      <div class="resource-detail-heading">
        <span class="course-kicker">COURSE RESOURCE · {{ typeLabel.toUpperCase() }}</span>
        <h1 id="course-resource-title">{{ resource.title }}</h1>
        <p>{{ resource.description }}</p>
        <div class="resource-meta-row">
          <span v-if="resource.chapter">{{ resource.chapter }}</span>
          <span>{{ resource.public ? '公开课程资源' : '限制访问' }}</span>
          <span v-if="resource.status">{{ resource.status }}</span>
        </div>
      </div>
      <div class="resource-detail-actions">
        <a v-if="downloadUrl" class="course-button course-button-primary" :href="downloadUrl" download>
          <Download :size="16" />下载原件
        </a>
        <a v-if="downloadUrl && previewKind === 'pdf'" class="course-button" :href="downloadUrl" target="_blank" rel="noopener">
          <ExternalLink :size="16" />新窗口打开
        </a>
      </div>
    </header>

    <div class="resource-detail-layout">
      <main class="resource-preview-card">
        <div class="resource-preview-title"><span>在线查看</span><span v-if="loading" class="resource-loading">正在读取…</span></div>
        <p v-if="error" class="course-empty course-error" role="alert">{{ error }}</p>
        <div v-else-if="loading" class="resource-loading-block">正在载入课程资源…</div>

        <div v-else-if="previewKind === 'html' && iframeSrc" class="html-preview-wrap">
          <iframe :src="iframeSrc" :title="`${resource.title} HTML 预览`" sandbox="" loading="lazy"></iframe>
          <small>HTML 预览运行在受限 sandbox 中，页面脚本不会执行。</small>
        </div>
        <div v-else-if="previewKind === 'pdf' && downloadUrl" class="pdf-preview-wrap">
          <iframe :src="downloadUrl" :title="`${resource.title} PDF 预览`" loading="lazy"></iframe>
        </div>
        <div v-else-if="previewKind === 'notebook'" class="notebook-preview">
          <article v-for="cell in notebookCells" :key="cell.index" class="notebook-cell" :class="`cell-${cell.cell_type}`">
            <div class="notebook-cell-label">{{ cell.cell_type === 'markdown' ? '说明' : '代码' }} · {{ String(cell.index).padStart(2, '0') }}</div>
            <pre>{{ cell.source }}</pre>
            <pre v-if="cell.output" class="notebook-output">{{ cell.output }}</pre>
          </article>
          <p v-if="!notebookCells.length" class="course-empty">该 Notebook 尚无可读取的单元，请下载原件查看。</p>
        </div>
        <div v-else-if="previewKind === 'csv'" class="csv-preview">
          <div class="table-scroll"><table><tbody><tr v-for="(row, index) in csvRows" :key="index"><th v-if="index === 0" v-for="cell in row" :key="cell">{{ cell }}</th><td v-else v-for="(cell, cellIndex) in row" :key="cellIndex">{{ cell }}</td></tr></tbody></table></div>
          <small v-if="csvTotalRows > csvRows.length">显示前 {{ csvRows.length }} 行，共 {{ csvTotalRows }} 行；下载原件查看完整数据。</small>
          <p v-if="!csvRows.length" class="course-empty">尚未读取到 CSV 行。</p>
        </div>
        <div v-else-if="previewKind === 'download'" class="download-only-preview">
          <div class="preview-icon"><BookOpen :size="28" /></div>
          <h2>课件原件</h2>
          <p>PowerPoint 文件保留原始排版，请下载后使用本地演示软件查看。</p>
          <a v-if="downloadUrl" class="course-button course-button-primary" :href="downloadUrl" download><Download :size="16" />下载 PPTX</a>
        </div>
        <div v-else-if="previewKind === 'data'" class="download-only-preview">
          <div class="preview-icon"><Table2 :size="28" /></div>
          <h2>数据集说明</h2>
          <p>{{ resource.description }}</p>
          <a v-if="downloadUrl" class="course-button course-button-primary" :href="downloadUrl" download><Download :size="16" />下载数据文件</a>
        </div>
        <div v-else class="text-preview">
          <pre v-if="textPreview">{{ textPreview }}</pre>
          <p v-else class="course-empty">当前资源没有可在线提取的文本，请下载原件查看。</p>
        </div>
      </main>

      <aside class="resource-detail-aside">
        <section v-if="knowledgeNodes.length" class="resource-side-section">
          <h2><Orbit :size="16" />关联知识节点</h2>
          <button v-for="node in knowledgeNodes" :key="node.id" class="resource-side-link" @click="openSpace(node.id)">
            <span>{{ node.name }}</span><ArrowUpRight :size="14" />
          </button>
        </section>
        <section v-if="relatedResources.length" class="resource-side-section">
          <h2><Link2 :size="16" />关联资源</h2>
          <button v-for="item in relatedResources" :key="item.id" class="resource-side-link" @click="openResource(item.id)">
            <span><small>{{ typeLabels[item.type] ?? '资源' }}</small>{{ item.title }}</span><ArrowUpRight :size="14" />
          </button>
        </section>
        <section v-if="resource.provenance" class="resource-side-section resource-provenance">
          <h2><FileText :size="16" />来源说明</h2>
          <p>{{ provenanceText(resource.provenance) }}</p><p v-if="resource.source_label">原材料：{{resource.source_label}}</p><p v-if="resource.transformation">{{resource.transformation}}</p>
        </section>
        <section v-if="resource.path" class="resource-side-section resource-path">
          <h2><FileCode2 :size="16" />文件路径</h2>
          <code>{{ resource.path }}</code>
        </section>
      </aside>
    </div>
  </section>
  <section v-else class="course-empty-page"><FileText :size="26" /><h1>找不到这项资源</h1><p>资源清单中没有登记该条目。</p></section>
</template>
