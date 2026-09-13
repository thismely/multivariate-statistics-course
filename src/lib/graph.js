export const relationNames = { prerequisite:'推荐先修', derived_from:'理论构造', part_of:'组成部分', compare_with:'方法比较', used_for:'应用于', assessed_by:'练习检验' }
export const levels = ['基础概念','统计原理','Python 实现','方法诊断与解释','综合应用']
export const typeNames = {concept:'概念',theory:'原理',method:'方法',python:'Python',case:'案例',assessment:'练习'}
export const typeColors = {concept:'#1263bd',theory:'#7042b6',method:'#00816d',python:'#b45309',case:'#bd3748',assessment:'#4d7514'}
/** All predecessor branches in deterministic topological order. No arbitrary shortest-path branch loss. */
export function learningPath(nodes,edges,target,direction='before') {
  if(!nodes.some(n=>n.id===target)) return []
  const links=edges.filter(e=>e.type==='prerequisite'); const visited=new Set(),active=new Set(),result=[]
  function visit(id) {
    if(active.has(id)) throw new Error('先修关系存在环路：'+id)
    if(visited.has(id)) return
    active.add(id)
    const adjacent=links.filter(e=>direction==='before'?e.target===id:e.source===id).map(e=>direction==='before'?e.source:e.target).sort()
    for(const next of adjacent) visit(next)
    active.delete(id);visited.add(id);result.push(id)
  }
  visit(target)
  // Stable Kahn order among reachable nodes puts available foundations before higher levels.
  const reachable=new Set(result),ordered=[],remaining=new Set(result)
  const byId=Object.fromEntries(nodes.map(n=>[n.id,n]))
  while(remaining.size){
    const available=[...remaining].filter(id=>!links.some(e=>e.target===id&&remaining.has(e.source)&&reachable.has(e.source)))
    available.sort((a,b)=>(byId[a]?.level||0)-(byId[b]?.level||0)||a.localeCompare(b))
    if(!available.length)throw new Error('先修关系存在环路')
    ordered.push(available[0]);remaining.delete(available[0])
  }
  return ordered
}
export function comparisonContext(nodes,edges,ids) {
 const branches=ids.map(id=>new Set(learningPath(nodes,edges,id)))
 const common=[...branches[0]].filter(id=>branches.slice(1).every(b=>b.has(id)))
 const parts=new Set(ids)
 // Expand the compared methods, not every ancestor's unrelated sibling topics.
 let changed=true
 while(changed){changed=false;for(const e of edges)if(e.type==='part_of'&&parts.has(e.target)&&!parts.has(e.source)){parts.add(e.source);changed=true}}
 return {common,ids:[...new Set([...parts,...branches.flatMap(b=>[...b])])]}
}
export function searchNodes(nodes,query) {
 const q=query.trim().toLowerCase().replace(/\s+/g,'')
 if(!q)return []
 return nodes.map(n=>({n,score:n.name.toLowerCase().replace(/\s+/g,'').includes(q)?2:([n.id,n.chapter,...n.keywords,n.description].join(' ').toLowerCase().replace(/\s+/g,'').includes(q)?1:0)})).filter(x=>x.score).sort((a,b)=>b.score-a.score||b.n.importance-a.n.importance).map(x=>x.n)
}
/** Z is literally cognitive height; XY positions are deterministic module cells. */
export function layoutNodes(nodes) {
 const centers={A:[-190,-190],B:[-265,70],C:[-90,250],D:[190,190],E:[265,-70],F:[90,-250],core:[0,0]}
 const buckets={}; const result={}
 for(const n of nodes){const key=n.module+':'+n.level;(buckets[key]??=[]).push(n)}
 for(const group of Object.values(buckets))group.sort((a,b)=>a.id.localeCompare(b.id)).forEach((n,i)=>{
  const c=centers[n.module],cols=Math.ceil(Math.sqrt(group.length)),row=Math.floor(i/cols),col=i%cols
  result[n.id]=n.id==='course'?[0,0,0]:[c[0]+(col-(cols-1)/2)*28,c[1]+(row-(Math.ceil(group.length/cols)-1)/2)*28,(n.level-1)*58]
 })
 return result
}
