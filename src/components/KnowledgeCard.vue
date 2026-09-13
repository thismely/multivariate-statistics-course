<script setup>
import {computed,ref,watch} from 'vue'
import {ArrowUpRight,Route,BookOpen,Code2,AlertCircle,ArrowRight,Target,Layers,ChevronRight} from 'lucide-vue-next'
import {useUniverse} from '../store'
import courseResources from '../data/course-resources.json'
import {levels,typeNames,relationNames} from '../lib/graph'
const s=useUniverse(),card=ref()
watch(()=>s.selectedId,()=>{if(card.value)card.value.scrollTop=0})
const n=computed(()=>s.selected)
const courseLinks=computed(()=>courseResources.filter(r=>r.knowledge_nodes.includes(n.value.id)))
const parents=computed(()=>s.edges.filter(e=>e.type==='prerequisite'&&e.target===n.value.id))
const children=computed(()=>s.edges.filter(e=>e.type==='prerequisite'&&e.source===n.value.id))
const linkedCases=computed(()=>s.cases.filter(c=>c.method_ids.includes(n.value.id)||c.node_id===n.value.id))
const exercises=computed(()=>s.edges.filter(e=>e.type==='assessed_by'&&e.source===n.value.id))
const relations=computed(()=>s.edges.filter(e=>e.source===n.value.id||e.target===n.value.id))
</script>
<template><aside ref="card" class="knowledge-card" aria-label="知识卡片" v-if="n">
 <div class="card-topline"><span class="eyebrow">KNOWLEDGE CARD</span><span class="tag">{{n.chapter}}</span></div>
 <div class="card-heading"><div class="node-symbol"><Layers :size="23"/></div><p>{{s.modules.find(m=>m.id===n.module)?.name||'课程核心'}}</p><h2>{{n.name}}</h2><div class="chips"><span>{{typeNames[n.type]}}</span><span>L{{n.level}} · {{levels[n.level-1]}}</span></div></div>
 <p class="definition">{{n.description}}</p>
 <button class="primary wide" @click="s.makePath(n.id)"><Route :size="16"/>生成学习路径<ArrowUpRight :size="16"/></button>
 <section v-if="n.formula" class="method-io"><div class="formula">{{n.formula}}</div><p><b>输入</b>{{n.inputs}}</p><p><b>输出</b>{{n.outputs}}</p></section>
 <section><h3><Target :size="14"/>学习目标</h3><p>{{n.learning_objective}}</p></section>
 <section><h3>推荐先修 <span>{{parents.length}}</span></h3><div class="link-chips"><button v-for="e in parents" :key="e.id" @click="s.focus(e.source)">{{s.byId[e.source].name}}<ChevronRight :size="12"/></button><p class="muted" v-if="!parents.length">本图谱未设额外先修，可从此处开始。</p></div></section>
 <section class="caution"><h3><AlertCircle :size="14"/>理解边界</h3><p>{{n.misconception}}</p></section>
 <section v-if="linkedCases.length"><h3>关联案例</h3><button v-for="c in linkedCases" :key="c.id" class="resource-link" @click="s.caseId=c.id;s.setMode('cases');s.focus(c.node_id)">{{c.title}}<ArrowUpRight :size="14"/></button></section>
 <section><h3>完整课程资源</h3><a class="resource-link" :href="'#/chapter/'+n.chapter">进入 {{n.chapter}} 章节学习 →</a><a v-for="r in courseLinks" :key="r.id" class="resource-link" :href="'#/resource/'+r.id">{{r.title}} ↗</a></section>
 <section><h3><BookOpen :size="14"/>课程来源</h3><button v-for="source in n.sources" :key="source.resource_id+source.start" class="source-button" @click="s.openResource(source.resource_id,source)"><span>{{s.resources.find(r=>r.id===source.resource_id)?.title}}</span><small>{{source.locator}} <ArrowUpRight :size="12"/></small></button>
 <div class="resource-types"><button v-for="id in n.resource_ids" :key="id" @click="s.openResource(id)"><Code2 v-if="id.startsWith('nb')" :size="13"/><BookOpen v-else :size="13"/>{{id.startsWith('nb')?'Python':id.startsWith('ppt')?'课件':id.startsWith('lecture')?'讲义':'数据表'}}</button></div></section>
 <section v-if="n.reading_suggestions?.length"><h3>教材阅读</h3><button class="source-button" v-for="r in n.reading_suggestions" :key="r.resource_id" @click="s.openResource(r.resource_id,{start:r.page,end:r.page})"><span>{{s.resources.find(x=>x.id===r.resource_id).title}}</span><small>PDF 第 {{r.page}} 页 · 本地原书 <ArrowUpRight :size="12"/></small></button></section>
 <section v-if="exercises.length"><h3>练习入口</h3><button v-for="e in exercises" :key="e.id" class="resource-link" @click="s.focus(e.target)">{{s.byId[e.target].name}}<ArrowRight :size="13"/></button></section>
 <section v-if="children.length"><h3>继续探索</h3><div class="link-chips"><button v-for="e in children" :key="e.id" @click="s.focus(e.target)">{{s.byId[e.target].name}}</button></div></section>
 <details class="relation-detail"><summary>查看 {{relations.length}} 条关系与依据</summary><article v-for="e in relations" :key="e.id"><b>{{s.byId[e.source].name}} {{e.type==='compare_with'?'↔':'→'}} {{s.byId[e.target].name}}</b><small>{{relationNames[e.type]}} · {{e.evidence_basis==='teaching_inference'?'教学整理':'材料依据'}}</small><p>{{e.rationale}}</p><button @click="s.openResource(e.sources[0].resource_id,e.sources[0])">核对来源 {{e.sources[0].locator}}</button></article></details>
 <footer>课程内容导航 · 教师可核对来源<br>AI Tutor 与个性化掌握度接口已预留</footer>
</aside></template>
