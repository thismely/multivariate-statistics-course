import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import {learningPath,comparisonContext,searchNodes,layoutNodes} from '../src/lib/graph.js'
const nodes=JSON.parse(fs.readFileSync(new URL('../src/data/nodes.json',import.meta.url))),edges=JSON.parse(fs.readFileSync(new URL('../src/data/edges.json',import.meta.url)))
test('PCA case path retains every prerequisite branch, and is topological',()=>{const p=learningPath(nodes,edges,'case_pca');assert(p.includes('corrmat'));assert(p.includes('eigen'));assert(p.indexOf('pca')<p.indexOf('case_pca'));assert.equal(new Set(p).size,p.length);for(const e of edges.filter(e=>e.type==='prerequisite'&&p.includes(e.target)))assert(p.indexOf(e.source)<p.indexOf(e.target))})
test('diamond prerequisites do not lose a branch',()=>{const n=['a','b','c','d'].map(id=>({id})),e=[['a','b'],['a','c'],['b','d'],['c','d']].map(([source,target])=>({source,target,type:'prerequisite'}));assert.deepEqual(learningPath(n,e,'d'),['a','b','c','d'])})
test('cycles fail explicitly and missing goals return empty',()=>{const n=[{id:'a'},{id:'b'}];assert.throws(()=>learningPath(n,[{source:'a',target:'b',type:'prerequisite'},{source:'b',target:'a',type:'prerequisite'}],'b'),/环路/);assert.deepEqual(learningPath(nodes,edges,'does-not-exist'),[])})
test('comparison edges never become required steps',()=>{const p=learningPath(nodes,edges,'fa');assert(!p.includes('pca'));const c=comparisonContext(nodes,edges,['pca','fa']);assert(c.common.includes('corrmat'));assert(c.ids.includes('pcaload'));assert(c.ids.includes('rotation'))})
test('downstream order preserves dependency and excludes comparison-only neighbors',()=>{const p=learningPath(nodes,edges,'pca','after');assert.equal(p[0],'pca');assert(p.includes('case_pca'));assert(!p.includes('fa'));for(const e of edges.filter(e=>e.type==='prerequisite'&&p.includes(e.source)&&p.includes(e.target)))assert(p.indexOf(e.source)<p.indexOf(e.target))})
test('Chinese, English case-insensitive, whitespace, and no-result searches',()=>{assert(searchNodes(nodes,'PCA').some(n=>n.id==='pca'));assert(searchNodes(nodes,'因子').some(n=>n.id==='fa'));assert(searchNodes(nodes,' Logistic ').some(n=>n.id==='logistic'));assert.equal(searchNodes(nodes,'zzzz不存在').length,0)})
test('fixed XY layout survives input ordering and Z equals semantic height',()=>{const a=layoutNodes(nodes),b=layoutNodes([...nodes].reverse());for(const n of nodes){assert.deepEqual(a[n.id],b[n.id]);assert.equal(a[n.id][2],(n.level-1)*58)}assert.equal(new Set(Object.values(a).map(p=>p.join(','))).size,nodes.length)})

test('PCA case spans concepts, principles, Python, interpretation, application',()=>{const p=learningPath(nodes,edges,'case_pca');assert.deepEqual([...new Set(p.map(id=>nodes.find(n=>n.id===id).level))].sort(),[1,2,3,4,5]);assert(p.indexOf('standard')<p.indexOf('pca'))})

test('comparison does not expand unrelated siblings of a shared foundation',()=>{const c=comparisonContext(nodes,edges,['pca','fa']);assert(!c.ids.includes('numpy'));assert(!c.ids.includes('pandas'));assert(c.ids.includes('pcaload'))})
