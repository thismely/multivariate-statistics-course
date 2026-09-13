<script setup>
import {ref,watch,nextTick,onBeforeUnmount} from 'vue'
import {X,ExternalLink,FileText,ChevronDown,Download} from 'lucide-vue-next'
import {useUniverse} from '../store'
const store=useUniverse(),units=ref([]),loading=ref(false),error=ref(''),showAll=ref(false),dialog=ref(),originalFocus=ref(null)
const localSources=false
let controller
function close(){store.resource=null;nextTick(()=>originalFocus.value?.focus())}
function key(e){if(e.key==='Escape'){e.stopPropagation();close()}if(e.key==='Tab'){const els=[...dialog.value.querySelectorAll('button,a[href],select,input')].filter(el=>!el.disabled);const first=els[0],last=els.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus()}}}
watch(()=>store.resource,async r=>{
 controller?.abort();units.value=[];error.value='';showAll.value=false
 if(!r)return
 originalFocus.value=document.activeElement;await nextTick();dialog.value?.focus()
 if(!r.href)return
 loading.value=true;controller=new AbortController()
 try{const res=await fetch(import.meta.env.BASE_URL+r.href,{signal:controller.signal});if(!res.ok)throw new Error('资源加载失败');const data=await res.json();units.value=data.units;loading.value=false;await nextTick();dialog.value?.querySelector('.source-highlight')?.scrollIntoView({block:'center'})}
 catch(e){if(e.name!=='AbortError'){error.value='无法读取资源。请检查静态资源是否完整部署。';loading.value=false}}
})
function download(){const r=store.resource;const blob=new Blob([units.value.map(u=>`${u.locator}\n${u.text}`).join('\n\n')],{type:'text/plain;charset=utf-8'});const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=r.title+'-文本摘录.txt';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
onBeforeUnmount(()=>controller?.abort())
</script>
<template><Teleport to="body"><div v-if="store.resource" class="modal-backdrop" @click.self="close"><section class="resource-modal" ref="dialog" role="dialog" aria-modal="true" aria-labelledby="resource-title" tabindex="-1" @keydown="key">
 <header><div><span class="eyebrow">COURSE RESOURCE · 来源定位</span><h2 id="resource-title">{{store.resource.title}}</h2></div><button class="icon-button" aria-label="关闭资源" @click="close"><X :size="20"/></button></header>
 <div class="resource-meta"><span>{{store.resource.title}}</span><span class="tag">{{store.resource.kind==='python'?'源代码已检查 · 未执行':store.resource.kind==='ppt'?'文本层 · 图片未 OCR':'课程原始材料'}}</span></div>
 <p class="notice" v-if="store.resource.kind==='ppt'">此处展示课件文本层；图片、公式与排版请在本机原始 PPT 中核对。</p>
 <p class="notice" v-if="store.resource.kind==='python'">原 Notebook 代码按单元展示，未运行代码及输出。旧路径、数据泄漏与历史接口问题请参阅开发报告。</p>
 <div class="resource-toolbar"><a v-if="store.resource.course_id" :href="'#/resource/'+store.resource.course_id" @click="close">进入课程资源页 · 预览与下载 ↗</a><button v-if="units.length" @click="showAll=!showAll"><ChevronDown :size="14"/>{{showAll?'只看定位附近':'查看完整文本'}}</button><button v-if="units.length" @click="download"><Download :size="14"/>下载文本</button><a v-if="localSources" :href="'/course-source/'+store.resource.id+(store.resource.kind==='book'?'#page='+store.resource.start:'')" target="_blank" rel="noopener"><ExternalLink :size="14"/>打开本机原文件</a></div>
 <div class="resource-content"><p v-if="loading">正在读取课程资源…</p><p v-if="error" role="alert">{{error}}</p><p v-if="!store.resource.href" class="empty">教材保留为本地阅读资料，系统没有打包整本 PDF。{{localSources?'可使用上方入口打开本机原文件。':'请在课程资源页面检索相应参考资料。'}}</p>
 <template v-for="unit in units" :key="unit.index"><article v-if="showAll||(unit.index>=Math.max(1,store.resource.start-3)&&unit.index<=store.resource.end+12)" :class="{'source-highlight':unit.index>=store.resource.start&&unit.index<=store.resource.end}"><small>{{unit.locator}}<span v-if="unit.images"> · 含 {{unit.images}} 张图片（需原件核对）</span></small><pre>{{unit.text||'（此处无可提取文本）'}}</pre></article></template></div>
</section></div></Teleport></template>
