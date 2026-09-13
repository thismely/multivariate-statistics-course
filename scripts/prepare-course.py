"""Prepare safe previews and resource mappings; never execute uploaded notebooks."""
from pathlib import Path
import json,html,shutil,re,xml.etree.ElementTree as ET,zipfile,subprocess,sys
root=Path(__file__).resolve().parents[1]
def read(p):return json.loads((root/p).read_text())
if (root/'course/labs.json').exists():
 subprocess.run([sys.executable,str(root/'scripts/build-labs.py')],cwd=root,check=True,stdout=subprocess.DEVNULL)
resources=read('src/data/imported-resources.json')
head='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{font:16px/1.8 system-ui;max-width:960px;margin:24px auto;padding:20px;color:#192b3b}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f2f5f7;padding:20px}article{border-bottom:1px solid #ccc}h2{font-size:18px}</style>'
for r in resources:
 p=root/r['path']
 if r['type']=='notebook':
  nb=json.loads(p.read_text());out=head+'<h1>'+html.escape(r['title'])+'</h1><p>'+html.escape(r['description'])+'</p>'
  for i,c in enumerate(nb['cells'],1):out+='<article><h2>单元 '+str(i)+' · '+c['cell_type']+'</h2><pre>'+html.escape(''.join(c['source']))+'</pre></article>'
  (root/r['preview']).write_text(out+'</html>')
 if r['type']=='slides':
  out=head+'<h1>'+html.escape(r['title'])+'</h1><p>文本预览；图像、公式和版式请下载课件核对。</p>'
  with zipfile.ZipFile(p) as z:
   names=sorted([n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+.xml',n)],key=lambda x:int(re.search(r'(\d+)\.xml',x)[1]))
   for i,name in enumerate(names,1):
    t=ET.fromstring(z.read(name));text='\n'.join(e.text or '' for e in t.iter() if e.tag.endswith('}t'))
    out+='<article><h2>第 '+str(i)+' 页</h2><pre>'+html.escape(text)+'</pre></article>'
  (root/r['preview']).write_text(out+'</html>')
if (root/'course/labs.json').exists():
 for lab in read('course/labs.json'):
  ids={kind:'lab-'+lab['id']+'-'+kind for kind in ['code','notebook','data','case']}
  for kind in ids:
   val=lab.get(kind)
   if not val:continue
   if not isinstance(val,str):raise ValueError('lab path must be a string: '+lab['id'])
   r=dict(id=ids[kind],title=lab['title']+' · '+{'code':'Python代码','notebook':'可重跑实验','data':'模拟数据','case':'教学案例'}[kind],type=kind,chapter=lab['chapter'],knowledge_nodes=lab['knowledge_nodes'],path=val,description=lab['description'],public=True,status=lab.get('execution_status','待运行'),provenance='新编教学实验；固定种子模拟数据',data_ids=[ids['data']],code_id=ids['code'],notebook_id=ids['notebook'])
   if kind=='notebook' and lab.get('preview'):r['preview']=lab['preview']
   resources.append(r)
  if lab.get('dictionary'):
   resources.append(dict(id='lab-'+lab['id']+'-dictionary',title=lab['title']+' · 字段说明',type='notes',chapter=lab['chapter'],knowledge_nodes=lab['knowledge_nodes'],path=lab['dictionary'],description='模拟数据字段、单位和生成含义；与同名实验的数据下载配套。',public=True,data_ids=[ids['data']],code_id=ids['code'],notebook_id=ids['notebook'],provenance='新编教学实验字段说明'))
# data dictionaries and lab guides are first-class resources, never unregistered downloads.
registered={r['path'] for r in resources}|{r.get('preview') for r in resources}
for file in sorted((root/'course').rglob('*.md')):
 rel=file.relative_to(root).as_posix()
 if rel not in registered:
  resources.append(dict(id='guide-'+re.sub('[^a-zA-Z0-9]+','-',rel),title=file.stem,type='notes',chapter='CH01',knowledge_nodes=['course'],path=rel,description='教学实验运行或字段说明。',public=True,provenance='课程建设文档'))
(root/'src/data/course-resources.json').write_text(json.dumps(resources,ensure_ascii=False,indent=2)+'\n')
# Course source is canonical; generated public copy supports Vite dev/build without filesystem APIs.
dst=root/'public/course'
if dst.exists():shutil.rmtree(dst)
shutil.copytree(root/'course',dst,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
print('Prepared',len(resources),'course resources')
