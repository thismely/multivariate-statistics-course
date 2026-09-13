import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import nodes from './data/nodes.json'
import edges from './data/edges.json'
import resources from './data/resources.json'
import cases from './data/cases.json'
import comparisons from './data/comparisons.json'
import problems from './data/problems.json'
import modules from './data/modules.json'
import {learningPath,comparisonContext,searchNodes} from './lib/graph.js'
export const useUniverse=defineStore('universe',()=>{
 const mode=ref('universe'),selectedId=ref('pca'),query=ref(''),moduleFilter=ref('all'),levelFilter=ref(0),relationFilter=ref('all'),comparisonId=ref('pca-fa'),problemId=ref('reduce'),caseId=ref('case_pca'),pathTarget=ref('case_pca'),pathDirection=ref('before'),flight=ref(0),sceneReset=ref(0),quality=ref('balanced'),tourIndex=ref(-1),resource=ref(null),presentation=ref(false)
 const byId=Object.fromEntries(nodes.map(n=>[n.id,n]))
 const selected=computed(()=>byId[selectedId.value]);const searchResults=computed(()=>searchNodes(nodes,query.value))
 const comparison=computed(()=>comparisons.find(c=>c.id===comparisonId.value));const problem=computed(()=>problems.find(p=>p.id===problemId.value));const caseItem=computed(()=>cases.find(c=>c.id===caseId.value));const path=computed(()=>learningPath(nodes,edges,pathTarget.value,pathDirection.value));const context=computed(()=>comparisonContext(nodes,edges,comparison.value.method_ids))
 const focusIds=computed(()=>mode.value==='path'?path.value:mode.value==='compare'?context.value.ids:mode.value==='cases'?[caseItem.value.node_id,...caseItem.value.method_ids]:mode.value==='problems'?problem.value.method_ids:[])
 const filtered=computed(()=>nodes.filter(n=>(moduleFilter.value==='all'||n.module===moduleFilter.value)&&(Number(levelFilter.value)===0||n.level===Number(levelFilter.value))))
 function select(id){if(!byId[id])return;selectedId.value=id;flight.value++;query.value=''}
 function focus(id){moduleFilter.value='all';levelFilter.value=0;select(id)}
 function setMode(value){mode.value=value;tourIndex.value=-1;moduleFilter.value='all';levelFilter.value=0}
 function makePath(id){pathTarget.value=id;pathDirection.value='before';setMode('path');focus(id)}
 function reset(){moduleFilter.value='all';levelFilter.value=0;relationFilter.value='all';sceneReset.value++}
 function openResource(id,source){resource.value={...resources.find(r=>r.id===id),start:source?.start||1,end:source?.end||1}}
 return {nodes,edges,resources,cases,comparisons,problems,modules,byId,mode,selectedId,selected,query,searchResults,moduleFilter,levelFilter,relationFilter,comparisonId,comparison,problemId,problem,caseId,caseItem,pathTarget,pathDirection,path,context,flight,sceneReset,quality,tourIndex,resource,presentation,focusIds,filtered,select,focus,setMode,makePath,reset,openResource}
})
