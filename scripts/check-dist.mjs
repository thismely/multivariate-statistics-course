import fs from 'node:fs'
import path from 'node:path'
import assert from 'node:assert/strict'
const root=path.resolve(import.meta.dirname,'..')
const rows=JSON.parse(fs.readFileSync(path.join(root,'src/data/course-resources.json')))
const dist=path.join(root,'dist')
const manifest=[]
for(const r of rows){
 for(const field of ['path','preview']){
  if(!r[field])continue
  assert(!r[field].startsWith('/')&&!r[field].includes('..'),`unsafe ${r.id}`)
  const file=path.join(dist,r[field]);assert(fs.existsSync(file),`not deployed: ${r.id} ${field}`)
  assert(fs.statSync(file).size>0,`empty: ${r.id} ${field}`)
  manifest.push({id:r.id,field,path:r[field],bytes:fs.statSync(file).size})
 }
}
const index=fs.readFileSync(path.join(dist,'index.html'),'utf8')
for(const match of index.matchAll(/(?:src|href)="([^"]+)"/g)){
 if(match[1].startsWith('http'))continue
 assert(match[1].startsWith('./'),`not relative: ${match[1]}`)
 assert(fs.existsSync(path.join(dist,match[1])),`missing bundle: ${match[1]}`)
}
fs.writeFileSync(path.join(root,'docs/dist-audit.json'),JSON.stringify({status:'PASS',resourceFiles:manifest.length,scope:'Built-file and relative URL validation; browser interaction is separately verified.',files:manifest},null,2)+'\n')
console.log(`PASS: ${manifest.length} deployed course file links and entry assets`)
