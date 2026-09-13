<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useUniverse } from './store'
import LegacyKnowledgeSpace from './App.vue'
import CoursePortal from './components/CoursePortal.vue'

/*
 * The course manifests are deliberately loaded from src/data.  import.meta.glob
 * keeps the shell buildable while the manifest is being prepared and lets Vite
 * bundle the JSON into a single static artifact for GitHub Pages.
 */
const manifestModules = import.meta.glob('./data/course-resources.json', { eager: true, import: 'default' })
const chapterModules = import.meta.glob('./data/chapters.json', { eager: true, import: 'default' })
const store = useUniverse()

const firstManifest = (modules) => Object.values(modules)[0] ?? []
const rawResourceManifest = ref(firstManifest(manifestModules))
const rawChapterManifest = ref(firstManifest(chapterModules))

const typeMap = {
  ppt: 'slides',
  slide: 'slides',
  lecture: 'notes',
  book: 'reference',
  python: 'code',
  dataset: 'data',
  exercise: 'exercise',
}

function listFromManifest(value, keys = []) {
  if (Array.isArray(value)) return value
  for (const key of keys) {
    if (Array.isArray(value?.[key])) return value[key]
  }
  return []
}

function chapterId(value, fallback = '') {
  if (value && typeof value === 'object') return chapterId(value.id ?? value.chapter ?? value.title, fallback)
  if (typeof value === 'number') return `CH${String(value).padStart(2, '0')}`
  const text = String(value ?? '').trim()
  const match = text.match(/(?:CH|chapter|第)\s*0*(\d{1,2})/i)
  return match ? `CH${String(match[1]).padStart(2, '0')}` : (text || fallback)
}

function inferredChapter(resource) {
  const direct = chapterId(resource.chapter ?? resource.chapter_id ?? resource.chapterId)
  if (direct) return direct
  const text = `${resource.id ?? ''} ${resource.title ?? ''}`
  const match = text.match(/(?:ch(?:apter)?|第)\s*0*(\d{1,2})/i)
  return match ? `CH${String(match[1]).padStart(2, '0')}` : ''
}

function normalizedType(resource) {
  const original = String(resource.type ?? resource.kind ?? '').toLowerCase()
  if (typeMap[original]) return typeMap[original]
  if (['notes', 'slides', 'notebook', 'code', 'data', 'case', 'exercise', 'reference'].includes(original)) return original
  const path = String(resource.path ?? resource.href ?? '').toLowerCase()
  if (path.endsWith('.ipynb')) return 'notebook'
  if (path.endsWith('.csv') || path.endsWith('.xlsx') || path.endsWith('.xls')) return 'data'
  if (path.endsWith('.ppt') || path.endsWith('.pptx')) return 'slides'
  if (path.endsWith('.pdf') || path.endsWith('.md') || path.endsWith('.txt')) return 'notes'
  return 'reference'
}

function normalizeResource(resource = {}) {
  const legacyIds = Array.isArray(resource.resource_ids) ? resource.resource_ids : []
  const nodeIds = Array.isArray(resource.knowledge_nodes)
    ? resource.knowledge_nodes
    : (Array.isArray(resource.knowledge_node_ids) ? resource.knowledge_node_ids : [])
  return {
    ...resource,
    id: String(resource.id ?? resource.resource_id ?? ''),
    title: resource.title ?? resource.name ?? '未命名课程资源',
    type: normalizedType(resource),
    chapter: inferredChapter(resource),
    knowledge_nodes: [...new Set(nodeIds.map(String))],
    path: resource.path ?? resource.href ?? '',
    description: resource.description ?? resource.summary ?? '课程资源，详情以原始文件为准。',
    public: resource.public !== false,
    related_resource_ids: resource.related_resource_ids ?? resource.related_ids ?? [],
    legacy_resource_ids: legacyIds,
  }
}

function normalizeChapter(chapter = {}) {
  const id = chapterId(chapter.id ?? chapter.chapter ?? chapter.title)
  return {
    ...chapter,
    id: id || String(chapter.id ?? ''),
    title: chapter.title ?? chapter.name ?? id,
    objectives: Array.isArray(chapter.objectives) ? chapter.objectives : [],
    description: chapter.description ?? chapter.summary ?? '',
  }
}

const resources = computed(() => {
  const manifest = listFromManifest(rawResourceManifest.value, ['resources', 'items', 'data'])
  const source = manifest.length ? manifest : store.resources
  return source.map(normalizeResource).filter((resource) => resource.id && resource.public)
})

const chapters = computed(() => {
  const manifest = listFromManifest(rawChapterManifest.value, ['chapters', 'items', 'data'])
  if (manifest.length) return manifest.map(normalizeChapter).filter((chapter) => chapter.id)

  const ids = new Set()
  for (const node of store.nodes) if (node.chapter) ids.add(chapterId(node.chapter))
  for (const resource of resources.value) if (resource.chapter) ids.add(resource.chapter)
  const fallbackIds = [...ids].filter(Boolean).sort()
  const twelve = fallbackIds.length ? fallbackIds : Array.from({ length: 12 }, (_, index) => `CH${String(index + 1).padStart(2, '0')}`)
  return twelve.map((id) => {
    const node = store.nodes.find((item) => chapterId(item.chapter) === id)
    return normalizeChapter({
      id,
      title: node?.name ?? `第${Number(id.slice(2))}章`,
      description: node?.description ?? '本章围绕多元数据分析中的核心问题展开。',
      objectives: node?.learning_objective ? [node.learning_objective] : [],
    })
  })
})

function parseHash(hash = '') {
  const raw = hash.replace(/^#/, '') || '/'
  const [pathname, queryString = ''] = raw.split('?')
  const path = pathname.startsWith('/') ? pathname : `/${pathname}`
  const segments = path.split('/').filter(Boolean).map((segment) => {
    try { return decodeURIComponent(segment) } catch { return segment }
  })
  const query = Object.fromEntries(new URLSearchParams(queryString))
  if (!segments.length) return { name: 'home', path: '/', query }
  if (segments[0] === 'resource') return { name: 'resource', path, id: segments[1] ?? '', query }
  if (segments[0] === 'chapter') return { name: 'chapter', path, id: chapterId(segments[1]), query }
  const known = new Set(['space', 'chapters', 'methods', 'labs', 'cases', 'datasets', 'resources', 'about'])
  return { name: known.has(segments[0]) ? segments[0] : 'home', path, query }
}

const route = ref(parseHash(typeof window === 'undefined' ? '/' : window.location.hash))

function syncHash() {
  route.value = parseHash(window.location.hash)
}

function navigate(path) {
  const next = String(path || '/')
  window.location.hash = next.startsWith('#') ? next.slice(1) : (next.startsWith('/') ? next : `/${next}`)
}

watch(
  () => [route.value.name, route.value.query?.node],
  ([name, node]) => {
    if (name !== 'space') return
    store.setMode('universe')
    if (node && store.byId[node]) store.focus(node)
    else store.reset()
  },
  { immediate: true },
)

watch(
  () => route.value.name,
  (name) => {
    if (typeof document === 'undefined') return
    document.body.classList.add('course-page-active')
    document.body.classList.toggle('course-space-active', name === 'space')
  },
  { immediate: true },
)

onMounted(() => window.addEventListener('hashchange', syncHash))
onBeforeUnmount(() => {
  window.removeEventListener('hashchange', syncHash)
  document.body.classList.remove('course-page-active', 'course-space-active')
})
</script>

<template>
  <div class="course-app">
    <CoursePortal :route="route" :resources="resources" :chapters="chapters" @navigate="navigate">
      <template #space>
        <div class="course-space-frame">
          <LegacyKnowledgeSpace />
        </div>
      </template>
    </CoursePortal>
  </div>
</template>
