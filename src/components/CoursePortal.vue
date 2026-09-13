<script setup>
import { computed, ref } from 'vue'
import { ArrowLeft, ArrowRight, ArrowUpRight, BookOpen, Boxes, ChartNoAxesCombined, ChevronRight, Code2, Database, Download, ExternalLink, FileText, FlaskConical, Github, Info, Library, ListFilter, Orbit, Search, Sparkles, Table2, Target, UsersRound } from 'lucide-vue-next'
import { useUniverse } from '../store'
import CourseResource from './CourseResource.vue'

const props = defineProps({
  route: { type: Object, required: true },
  resources: { type: Array, default: () => [] },
  chapters: { type: Array, default: () => [] },
})
const emit = defineEmits(['navigate'])
const store = useUniverse()
const resourceQuery = ref('')
const resourceType = ref('all')
const labType = ref('all')

const navItems = [
  { path: '/', label: '首页', icon: Sparkles },
  { path: '/space', label: '三维空间', icon: Orbit },
  { path: '/chapters', label: '课程章节', icon: BookOpen },
  { path: '/methods', label: '方法导航', icon: ChartNoAxesCombined },
  { path: '/labs', label: 'Python 实验', icon: FlaskConical },
  { path: '/cases', label: '案例库', icon: Boxes },
  { path: '/datasets', label: '数据集', icon: Database },
  { path: '/resources', label: '资源库', icon: Library },
]
const typeLabels = { notes: '讲义', slides: '课件', notebook: 'Notebook', code: '代码', data: '数据', case: '案例', exercise: '练习', reference: '参考' }
const resourceTypes = [{ id: 'all', label: '全部资源' }, ...Object.entries(typeLabels).map(([id, label]) => ({ id, label }))]

const routeName = computed(() => props.route?.name ?? 'home')
const currentResource = computed(() => props.resources.find((resource) => resource.id === props.route?.id))
const currentChapter = computed(() => props.chapters.find((chapter) => chapter.id === props.route?.id))
const methods = computed(() => store.nodes.filter((node) => node.type === 'method'))
/* A lab is counted once, by its runnable Notebook. Companion code is shown
 * on the lab page but is intentionally excluded from the experiment total. */
const reproducibleLabs = computed(() => props.resources.filter((resource) => resource.type === 'notebook' && (String(resource.status).toLowerCase() === 'verified' || resource.id.startsWith('lab-'))))
const referenceNotebooks = computed(() => props.resources.filter((resource) => resource.type === 'notebook' && !reproducibleLabs.value.some((lab) => lab.id === resource.id)))
const labCodes = computed(() => props.resources.filter((resource) => resource.type === 'code' && (resource.id.startsWith('lab-') || String(resource.status).toLowerCase() === 'verified')))
const labs = reproducibleLabs
const datasets = computed(() => props.resources.filter((resource) => resource.type === 'data'))
const cases = computed(() => store.cases)
const simulatedCases = computed(() => props.resources.filter((resource) => resource.type === 'case' && resource.id.startsWith('lab-')))
const filteredResources = computed(() => {
  const query = resourceQuery.value.trim().toLowerCase()
  return props.resources.filter((resource) => {
    const matchesType = resourceType.value === 'all' || resource.type === resourceType.value
    const haystack = [resource.title, resource.description, resource.chapter, resource.type].join(' ').toLowerCase()
    return matchesType && (!query || haystack.includes(query))
  })
})
const filteredLabs = computed(() => {
  if (labType.value === 'reference') return referenceNotebooks.value
  if (labType.value === 'code') return labCodes.value
  return reproducibleLabs.value
})
const chapterNodes = computed(() => currentChapter.value ? store.nodes.filter((node) => String(node.chapter ?? '') === currentChapter.value.id) : [])
const chapterResources = computed(() => currentChapter.value ? props.resources.filter((resource) => resource.chapter === currentChapter.value.id) : [])

function go(path) {
  emit('navigate', path)
}

function goResource(id) {
  if (id) go(`/resource/${encodeURIComponent(id)}`)
}

function goChapter(id) {
  go(`/chapter/${encodeURIComponent(id)}`)
}

function goSpace(id = '') {
  go(id ? `/space?node=${encodeURIComponent(id)}` : '/space')
}

function resourcesForNode(node) {
  const ids = new Set([...(node.resource_ids ?? []), ...props.resources.filter((resource) => resource.knowledge_nodes.includes(node.id)).map((resource) => resource.id)])
  return props.resources.filter((resource) => ids.has(resource.id)).slice(0, 5)
}

function chapterTitle(id) {
  return props.chapters.find((chapter) => chapter.id === id)?.title ?? id
}

function typeLabel(type) {
  return typeLabels[type] ?? '资源'
}

function assetUrl(path) {
  const raw = String(path ?? '').trim()
  if (!raw) return ''
  if (/^(?:https?:|data:|blob:)/i.test(raw)) return raw
  const base = import.meta.env.BASE_URL || '/'
  const cleanBase = base.endsWith('/') ? base : `${base}/`
  return `${cleanBase}${raw.replace(/^\.\//, '').replace(/^\/+/, '')}`
}
</script>

<template>
  <div class="course-portal" :class="{ 'course-portal-space': routeName === 'space' }">
    <header v-if="routeName !== 'space'" class="course-header">
      <a href="#/" class="course-brand" @click.prevent="go('/')">
        <span class="course-brand-mark"><Orbit :size="21" /></span>
        <span><strong>多元统计分析</strong><small>DIGITAL COURSE · OPEN LEARNING SPACE</small></span>
      </a>
      <nav class="course-nav" aria-label="课程导航">
        <button v-for="item in navItems" :key="item.path" :class="{ active: (item.path === '/' ? routeName === 'home' : routeName === item.path.slice(1)) }" @click="go(item.path)">
          <component :is="item.icon" :size="15" />{{ item.label }}
        </button>
      </nav>
      <button class="course-header-about" @click="go('/about')"><Info :size="16" />关于课程</button>
    </header>

    <div v-if="routeName === 'space'" class="space-route-bar">
      <a href="#/" class="course-brand course-brand-compact" @click.prevent="go('/')"><span class="course-brand-mark"><Orbit :size="18" /></span><strong>多元统计分析 · 数字课程</strong></a>
      <div class="space-route-actions"><button @click="go('/')"><ArrowLeft :size="15" />课程首页</button><button @click="go('/resources')"><Library :size="15" />资源库</button></div>
    </div>

    <div v-if="routeName === 'space'" class="space-route-content">
      <slot name="space" />
    </div>

    <main v-else class="course-main">
      <section v-if="routeName === 'home'" class="course-home">
        <div class="course-hero">
          <div class="course-hero-copy">
            <span class="course-kicker">MULTIVARIATE STATISTICAL ANALYSIS · DIGITAL COURSE</span>
            <h1>从数据出发，<br /><em>理解多元世界。</em></h1>
            <p>以三维知识空间为入口，串联章节、方法、Python 实验、案例与数据。沿着问题找到方法，也沿着方法回到真实材料。</p>
            <div class="course-hero-actions"><button class="course-button course-button-primary" @click="goSpace()"><Orbit :size="17" />进入三维知识空间</button><button class="course-button" @click="go('/chapters')">浏览课程章节<ArrowRight :size="16" /></button></div>
          </div>
          <div class="course-hero-map" aria-hidden="true"><div class="hero-orbit hero-orbit-one"></div><div class="hero-orbit hero-orbit-two"></div><div class="hero-core"><Orbit :size="34" /><span>KNOWLEDGE<br />UNIVERSE</span></div><i class="hero-node hero-node-one"></i><i class="hero-node hero-node-two"></i><i class="hero-node hero-node-three"></i></div>
        </div>

        <div class="course-stat-grid">
          <div><strong>{{ props.chapters.length || 12 }}</strong><span>课程章节</span></div><div><strong>{{ store.nodes.length }}</strong><span>知识节点</span></div><div><strong>{{ props.resources.length }}</strong><span>公开资源</span></div><div><strong>{{ labs.length }}</strong><span>Python 实验</span></div>
        </div>

        <section class="course-section home-section"><div class="section-heading"><div><span class="course-kicker">LEARNING ROUTES</span><h2>选择你的学习入口</h2></div><p>三维探索与传统章节导航互相补充。</p></div><div class="entry-grid"><button @click="goSpace()"><span class="entry-icon entry-icon-green"><Orbit :size="21" /></span><span><strong>知识空间</strong><small>从节点、方法与关系开始探索</small></span><ArrowUpRight :size="17" /></button><button @click="go('/methods')"><span class="entry-icon entry-icon-gold"><ChartNoAxesCombined :size="21" /></span><span><strong>方法导航</strong><small>按统计问题理解方法边界</small></span><ArrowUpRight :size="17" /></button><button @click="go('/labs')"><span class="entry-icon entry-icon-blue"><FlaskConical :size="21" /></span><span><strong>Python 实验</strong><small>从 Notebook 走到可复核代码</small></span><ArrowUpRight :size="17" /></button></div></section>

        <section class="course-section"><div class="section-heading"><div><span class="course-kicker">COURSE MAP</span><h2>12 章课程入口</h2></div><button class="course-text-link" @click="go('/chapters')">查看全部<ArrowRight :size="15" /></button></div><div class="chapter-mini-grid"><button v-for="(chapter, index) in props.chapters.slice(0, 12)" :key="chapter.id" @click="goChapter(chapter.id)"><span>{{ String(index + 1).padStart(2, '0') }}</span><strong>{{ chapter.title }}</strong><small>{{ chapter.description || '进入本章学习路径' }}</small><ChevronRight :size="15" /></button></div></section>

        <section class="course-section home-lab-section"><div class="section-heading"><div><span class="course-kicker">CORE LABS</span><h2>核心实验入口</h2></div><button class="course-text-link" @click="go('/labs')">实验目录<ArrowRight :size="15" /></button></div><div class="resource-strip"><button v-for="resource in labs.slice(0, 4)" :key="resource.id" @click="goResource(resource.id)"><span class="resource-type-pill">{{ typeLabel(resource.type) }}</span><strong>{{ resource.title }}</strong><small>{{ chapterTitle(resource.chapter) }}</small><ArrowUpRight :size="15" /></button><p v-if="!labs.length" class="course-empty">课程实验资源正在整理中。</p></div></section>
      </section>

      <section v-else-if="routeName === 'chapters'" class="course-page"><div class="page-intro"><span class="course-kicker">COURSE CHAPTERS</span><h1>课程章节</h1><p>从数据处理、探索与可视化出发，逐步进入降维、分群、分类、关联与综合应用。</p></div><div class="chapter-card-grid"><button v-for="(chapter, index) in props.chapters" :key="chapter.id" class="chapter-card" @click="goChapter(chapter.id)"><span class="chapter-number">{{ String(index + 1).padStart(2, '0') }}</span><div><h2>{{ chapter.title }}</h2><p>{{ chapter.description || '围绕本章核心问题组织知识、方法与实验。' }}</p><small>{{ chapter.objectives?.length || 0 }} 项学习目标 · {{ props.resources.filter((resource) => resource.chapter === chapter.id).length }} 项资源</small></div><ArrowRight :size="17" /></button></div></section>

      <section v-else-if="routeName === 'chapter'" class="course-page chapter-detail-page"><div v-if="currentChapter" class="chapter-detail"><div class="page-intro"><button class="course-back-link" @click="go('/chapters')"><ArrowLeft :size="15" />返回章节</button><span class="course-kicker">{{ currentChapter.id }} · COURSE CHAPTER</span><h1>{{ currentChapter.title }}</h1><p>{{ currentChapter.description || '本章围绕多元数据分析中的关键问题组织学习。' }}</p></div><div class="chapter-detail-grid"><section class="detail-content-card"><span class="course-kicker">LEARNING OBJECTIVES</span><h2>学习目标</h2><ol v-if="currentChapter.objectives?.length"><li v-for="objective in currentChapter.objectives" :key="objective">{{ objective }}</li></ol><p v-else class="course-empty-inline">学习目标将随课程材料完善。</p><span class="course-kicker detail-kicker">KNOWLEDGE NODES</span><h2>知识结构</h2><div class="node-chip-list"><button v-for="node in chapterNodes" :key="node.id" @click="goSpace(node.id)">{{ node.name }}<Orbit :size="13" /></button><p v-if="!chapterNodes.length" class="course-empty-inline">本章的知识节点正在整理中。</p></div></section><section class="detail-resource-card"><div class="section-heading"><div><span class="course-kicker">CHAPTER RESOURCES</span><h2>本章资源</h2></div><span class="detail-count">{{ chapterResources.length }}</span></div><div class="compact-resource-list"><button v-for="resource in chapterResources" :key="resource.id" @click="goResource(resource.id)"><span class="resource-type-pill">{{ typeLabel(resource.type) }}</span><span><strong>{{ resource.title }}</strong><small>{{ resource.description }}</small></span><ArrowUpRight :size="15" /></button><p v-if="!chapterResources.length" class="course-empty">本章暂无登记资源。</p></div></section></div></div><div v-else class="course-empty-page"><FileText :size="26" /><h1>找不到这个章节</h1><button class="course-button" @click="go('/chapters')">返回章节目录</button></div></section>

      <section v-else-if="routeName === 'methods'" class="course-page"><div class="page-intro"><span class="course-kicker">METHOD NAVIGATION</span><h1>方法导航</h1><p>先说清楚问题，再选择方法。每个方法都连接到相应的知识节点、课程材料与 Python 实验。</p></div><div class="method-card-grid"><article v-for="method in methods" :key="method.id" class="method-card"><div class="method-card-top"><span class="method-symbol"><ChartNoAxesCombined :size="18" /></span><span>{{ method.chapter }}</span></div><h2>{{ method.name }}</h2><p>{{ method.description }}</p><div class="method-resource-links"><button @click="goSpace(method.id)"><Orbit :size="14" />查看知识节点</button><button v-for="resource in resourcesForNode(method).slice(0, 2)" :key="resource.id" @click="goResource(resource.id)"><ArrowUpRight :size="13" />{{ typeLabel(resource.type) }}</button></div></article><p v-if="!methods.length" class="course-empty">暂无方法节点。</p></div></section>

      <section v-else-if="routeName === 'labs'" class="course-page"><div class="page-intro"><span class="course-kicker">PYTHON LABS</span><h1>Python 实验</h1><p>Notebook 用于阅读与实验，代码用于核对实现路径；所有结果都应回到数据、假设与诊断。</p></div><div class="lab-summary-grid"><div><strong>{{ reproducibleLabs.length }}</strong><span>可重跑实验</span><small>已核验 Notebook</small></div><div><strong>{{ referenceNotebooks.length }}</strong><span>原 Notebook 参考</span><small>用于课程阅读</small></div><div><strong>{{ labCodes.length }}</strong><span>配套代码</span><small>不重复计入实验</small></div></div><div class="filter-toolbar"><div class="filter-tabs"><button :class="{ active: labType === 'all' }" @click="labType = 'all'">可重跑实验</button><button :class="{ active: labType === 'reference' }" @click="labType = 'reference'">原 Notebook 参考</button><button :class="{ active: labType === 'code' }" @click="labType = 'code'">配套代码</button></div><span>{{ filteredLabs.length }} 项当前资源</span></div><div class="lab-card-grid"><article v-for="resource in filteredLabs" :key="resource.id" class="lab-card"><div class="lab-card-label"><Code2 :size="15" />{{ typeLabel(resource.type) }}<span>{{ resource.chapter }}</span></div><h2>{{ resource.title }}</h2><p>{{ resource.description }}</p><div class="lab-card-actions"><button class="course-button course-button-primary" @click="goResource(resource.id)">{{ resource.type === 'notebook' ? '查看 Notebook' : '查看代码' }}<ArrowRight :size="15" /></button><button class="course-icon-button" :aria-label="`在图谱中查看 ${resource.title}`" @click="resource.knowledge_nodes?.[0] && goSpace(resource.knowledge_nodes[0])"><Orbit :size="16" /></button></div></article><p v-if="!filteredLabs.length" class="course-empty">当前筛选下没有实验资源。</p></div></section>

      <section v-else-if="routeName === 'cases'" class="course-page">
        <div class="page-intro"><span class="course-kicker">CASE LIBRARY</span><h1>案例库</h1><p>案例从真实任务出发，连接方法选择、数据文件、实验代码与有边界的结果解释。</p></div>
        <section class="case-section case-simulated-section"><div class="section-heading"><div><span class="course-kicker">REPRODUCIBLE TEACHING CASES</span><h2>可复核模拟教学案例</h2></div><span class="case-section-note">{{ simulatedCases.length }} 项</span></div><p class="case-boundary-note">这些案例使用公开课程项目中的模拟数据，用于复现方法流程；它们不是原课程案例的原始数据。</p><div class="case-card-grid"><article v-for="resource in simulatedCases" :key="resource.id" class="case-card"><div class="case-card-top"><span>模拟教学实验</span><span>{{ resource.chapter }}</span></div><h2>{{ resource.title }}</h2><p>{{ resource.description }}</p><div class="case-methods"><button v-for="nodeId in resource.knowledge_nodes?.slice(0, 3)" :key="nodeId" @click="goSpace(nodeId)">{{ store.byId[nodeId]?.name || nodeId }}</button></div><div class="case-resource-list"><button @click="goResource(resource.id)"><span class="resource-type-pill">案例</span>查看模拟案例说明<ArrowUpRight :size="14" /></button><button v-for="item in props.resources.filter((candidate) => candidate.chapter === resource.chapter && ['notebook', 'code', 'data'].includes(candidate.type) && candidate.id !== resource.id).slice(0, 3)" :key="item.id" @click="goResource(item.id)"><span class="resource-type-pill">{{ typeLabel(item.type) }}</span>{{ item.title }}<ArrowUpRight :size="14" /></button></div></article><p v-if="!simulatedCases.length" class="course-empty">暂无模拟教学案例。</p></div></section>
        <section class="case-section case-history-section"><div class="section-heading"><div><span class="course-kicker">ORIGINAL COURSE CASES</span><h2>原课程案例参考</h2></div><span class="case-section-note">{{ cases.length }} 项</span></div><p class="case-boundary-note">原课程案例参考，原数据未迁移/未重跑。下面仅保留课程问题、方法与阅读入口，避免与模拟数据混淆。</p><div class="case-card-grid"><article v-for="item in cases" :key="item.id" class="case-card case-history-card"><div class="case-card-top"><span>{{ item.domain }}</span><span>原课程案例参考</span></div><h2>{{ item.title }}</h2><p>{{ item.description }}</p><div class="case-methods"><button v-for="methodId in item.method_ids" :key="methodId" @click="goSpace(methodId)">{{ store.byId[methodId]?.name || methodId }}</button></div><div class="case-reference-note">原数据未迁移 · 未重跑</div></article><p v-if="!cases.length" class="course-empty">暂无原课程案例记录。</p></div></section>
      </section>

      <section v-else-if="routeName === 'datasets'" class="course-page"><div class="page-intro"><span class="course-kicker">DATASETS</span><h1>数据集</h1><p>数据文件服务于课堂案例与方法练习。请先阅读字段说明、样本范围与使用边界，再进行分析。</p></div><div class="dataset-card-grid"><article v-for="resource in datasets" :key="resource.id" class="dataset-card"><div class="dataset-card-top"><span class="resource-type-pill">DATA</span><span>{{ resource.chapter }}</span></div><h2>{{ resource.title }}</h2><p>{{ resource.description }}</p><div class="dataset-actions"><button class="course-button course-button-primary" @click="goResource(resource.id)"><Table2 :size="15" />查看数据说明</button><a v-if="resource.path" class="course-button" :href="assetUrl(resource.path)" download><Download :size="15" />下载</a></div></article><p v-if="!datasets.length" class="course-empty">暂无公开数据集。</p></div></section>

      <section v-else-if="routeName === 'resources'" class="course-page"><div class="page-intro"><span class="course-kicker">COURSE RESOURCE LIBRARY</span><h1>课程资源</h1><p>按类型、章节或关键词查找课件、讲义、Notebook、代码、数据与练习。</p></div><div class="resource-library-toolbar"><label class="resource-search"><Search :size="17" /><input v-model="resourceQuery" placeholder="搜索资源名称、章节或简介" aria-label="搜索课程资源" /></label><label class="resource-select"><ListFilter :size="15" /><select v-model="resourceType" aria-label="按资源类型筛选"><option v-for="option in resourceTypes" :key="option.id" :value="option.id">{{ option.label }}</option></select></label></div><div class="library-summary"><span>{{ filteredResources.length }} / {{ props.resources.length }} 项公开资源</span><button v-if="resourceQuery || resourceType !== 'all'" class="course-text-link" @click="resourceQuery = ''; resourceType = 'all'">清除筛选</button></div><div class="library-resource-grid"><article v-for="resource in filteredResources" :key="resource.id" class="library-resource-card"><div class="library-card-top"><span class="resource-type-pill">{{ typeLabel(resource.type) }}</span><span>{{ resource.chapter }}</span></div><h2>{{ resource.title }}</h2><p>{{ resource.description }}</p><div class="library-card-bottom"><small>{{ resource.status || '可在线查看或下载' }}</small><button @click="goResource(resource.id)">查看资源<ArrowUpRight :size="14" /></button></div></article><p v-if="!filteredResources.length" class="course-empty">当前筛选下没有资源。</p></div></section>

      <section v-else-if="routeName === 'about'" class="course-page about-page"><div class="page-intro"><span class="course-kicker">ABOUT THIS COURSE</span><h1>关于课程</h1><p>《多元统计分析》开放式数字课程，以三维知识空间为核心导航，将课程内容、Python 实验、案例数据与可追溯资源连接起来。</p></div><div class="about-grid"><article><span class="about-icon"><Target :size="20" /></span><h2>学习目标</h2><p>理解多元数据中的结构、关系与不确定性，能够在问题、数据、方法和解释之间建立清晰的分析链条。</p></article><article><span class="about-icon"><UsersRound :size="20" /></span><h2>适用对象</h2><p>适合正在学习多元统计分析、希望用 Python 完成数据分析练习，或需要从方法边界出发阅读案例的学习者。</p></article><article><span class="about-icon"><Github :size="20" /></span><h2>开放项目</h2><p>课程采用 Vue、Vite、Three.js 与 Pinia 构建，适合在 GitHub Pages 上持续维护与公开访问。</p><a class="course-text-link" href="https://github.com" target="_blank" rel="noopener">查看 GitHub 项目<ExternalLink :size="14" /></a></article><article><span class="about-icon"><Info :size="20" /></span><h2>资源说明</h2><p>公开清单仅收录适合发布的课程资源。版权不明确的材料保留书目信息或本地阅读提示，学生信息和系统敏感信息不进入公开站点。</p></article></div></section>

      <CourseResource v-else-if="routeName === 'resource'" :resource="currentResource" :resources="props.resources" @navigate="go" />
      <section v-else class="course-empty-page"><FileText :size="26" /><h1>页面不存在</h1><p>请从课程导航重新选择入口。</p><button class="course-button" @click="go('/')">回到首页</button></section>
    </main>

    <footer v-if="routeName !== 'space'" class="course-footer"><span>《多元统计分析》数字课程</span><span>三维知识空间 · Python 实验 · 案例与数据</span><button @click="go('/about')">关于课程 <ArrowRight :size="13" /></button></footer>
  </div>
</template>
