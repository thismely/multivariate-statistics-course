import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { learningPath,layoutNodes,relationNames } from '../src/lib/graph.js'
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..')
const read=name=>JSON.parse(fs.readFileSync(path.join(root,'src/data',name+'.json'),'utf8'))
const [nodes,edges,resources,cases,comparisons,problems,modules]=['nodes','edges','resources','cases','comparisons','problems','modules'].map(read)
const errors=[]; const check=(v,m)=>{if(!v)errors.push(m)}
for(const [name,rows] of Object.entries({nodes,edges,resources,cases,comparisons,problems})){check(new Set(rows.map(x=>x.id)).size===rows.length,'duplicate '+name)}
const ids=new Set(nodes.map(n=>n.id)),rids=new Set(resources.map(r=>r.id)),locators={}
for(const r of resources){if(r.href){const p=path.join(root,'public',r.href);check(fs.existsSync(p),'missing resource '+r.id);if(fs.existsSync(p))locators[r.id]=JSON.parse(fs.readFileSync(p)).units.length}}
function sources(ss,label){check(ss?.length,'missing evidence '+label);for(const s of ss||[]){check(rids.has(s.resource_id),'bad evidence resource '+label);check(s.start>=1&&s.end>=s.start&&s.end<=locators[s.resource_id],'bad locator '+label)}}
check(nodes.length>=80&&nodes.length<=120,'node budget');check(modules.length===6,'six modules')
for(const n of nodes){check(n.level>=1&&n.level<=5,'bad level '+n.id);check(n.module==='core'||modules.some(m=>m.id===n.module),'bad module');check(n.description&&n.learning_objective&&n.misconception,'missing knowledge card '+n.id);sources(n.sources,n.id);for(const r of n.resource_ids)check(rids.has(r),'bad node resource')}
const seen=new Set()
for(const e of edges){check(ids.has(e.source)&&ids.has(e.target),'dangling '+e.id);check(e.source!==e.target,'self edge');check(e.type in relationNames,'unsupported edge');check(e.rationale&&e.evidence_basis,'unexplained edge');sources(e.sources,e.id);const key=[e.source,e.target,e.type].join(':');check(!seen.has(key),'duplicate edge');seen.add(key)}
for(const n of nodes){try{learningPath(nodes,edges,n.id)}catch(e){errors.push(e.message)}}
for(const collection of [cases,comparisons,problems])for(const item of collection){sources(item.sources,item.id);for(const id of item.method_ids)check(ids.has(id),'dangling method '+item.id)}
for(const c of cases){check(ids.has(c.node_id),'missing case node');check(rids.has(c.data.resource_id),'missing case data reference')}
const positions=layoutNodes(nodes);check(new Set(Object.values(positions).map(p=>p.join(','))).size===nodes.length,'overlapping positions');for(const n of nodes)check(positions[n.id][2]===(n.level-1)*58,'Z semantic mismatch')
const report={status:errors.length?'FAIL':'PASS',nodes:nodes.length,edges:edges.length,resources:resources.length,cases:cases.length,comparisons:comparisons.length,problems:problems.length,byLevel:Object.fromEntries([1,2,3,4,5].map(l=>[l,nodes.filter(n=>n.level===l).length])),byModule:Object.fromEntries(['core',...modules.map(m=>m.id)].map(m=>[m,nodes.filter(n=>n.module===m).length])),byRelation:Object.fromEntries(Object.keys(relationNames).map(t=>[t,edges.filter(e=>e.type===t).length])),errors,scope:'Structural and source locator audit; not independent faculty content approval or empirical reproduction.'}
fs.writeFileSync(path.join(root,'docs/graph-audit.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));if(errors.length)process.exitCode=1
