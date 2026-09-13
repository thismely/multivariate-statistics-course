<script setup>
import {ref,onMounted,onBeforeUnmount,watch} from 'vue'
import * as THREE from 'three'
import {OrbitControls} from 'three/addons/controls/OrbitControls.js'
import {CSS2DRenderer,CSS2DObject} from 'three/addons/renderers/CSS2DRenderer.js'
import {useUniverse} from '../store'
import {layoutNodes,typeColors,levels} from '../lib/graph'
const store=useUniverse(),host=ref(),failed=ref(false),fps=ref(0),hovered=ref(''),positions=layoutNodes(store.nodes)
let renderer,labels,scene,camera,controls,observer,raf,flight,lastFrame=0,frameCount=0,frameTime=0,disposed=false,dirty=true,atHome=true,pointerStart,gridObjects=[],meshMap=new Map(),edgeObjects=[],edgeLines,edgeArrows,edgePositions,edgeColors,nodeLabels=[],moduleLabels=[]
const reduceMotion=window.matchMedia('(prefers-reduced-motion: reduce)').matches
const homePosition=new THREE.Vector3(450,-690,500),homeTarget=new THREE.Vector3(0,0,95)
function responsiveHome(){return homeTarget.clone().add(homePosition.clone().sub(homeTarget).multiplyScalar(Math.max(1,1.22/(camera?.aspect||1))))}
const emit=defineEmits(['ready'])
function label(text,position,cls){const el=document.createElement('div');el.className=cls;el.textContent=text;el.title=text;const obj=new CSS2DObject(el);obj.position.fromArray(position);scene.add(obj);return obj}
function fly(id,home=false){
 if(!camera)return;atHome=home
 let target=home?homeTarget.clone():new THREE.Vector3(...positions[id]);let delta=home?responsiveHome().sub(target):new THREE.Vector3(205,-300,220)
 const fitGroup=!home&&((store.mode==='compare'&&store.comparison.method_ids.includes(id))||(store.mode==='cases'&&id===store.caseItem.node_id)||(store.mode==='path'&&id===store.pathTarget&&store.tourIndex<0))
 if(fitGroup&&store.focusIds.length){const box=new THREE.Box3().setFromPoints(store.focusIds.map(id=>new THREE.Vector3(...positions[id])));target=box.getCenter(new THREE.Vector3());const radius=box.getSize(new THREE.Vector3()).length()/2;const halfFov=Math.atan(Math.tan(THREE.MathUtils.degToRad(camera.fov/2))*Math.min(1,camera.aspect));const distance=Math.max(360,radius/Math.sin(halfFov)*1.13);delta.set(.45,-.69,.405).normalize().multiplyScalar(distance)}
 flight={start:performance.now(),from:camera.position.clone(),fromTarget:controls.target.clone(),to:target.clone().add(delta),target,duration:reduceMotion?0:1150};dirty=true
}
function updateVisibility(){
 const visible=new Set(store.filtered.map(n=>n.id)),focus=new Set(store.focusIds)
 for(const n of store.nodes){const mesh=meshMap.get(n.id);if(!mesh)continue;mesh.visible=visible.has(n.id);const active=!focus.size||focus.has(n.id);mesh.material.opacity=active?1:.13;mesh.scale.setScalar(n.id===store.selectedId?1.7:1);mesh.material.emissiveIntensity=n.id===store.selectedId?.35:.12}
 for(const item of edgeObjects){const {edge,index,points,offset,color,matrix}=item;const show=visible.has(edge.source)&&visible.has(edge.target)&&(store.relationFilter==='all'||store.relationFilter===edge.type);const active=focus.size?focus.has(edge.source)&&focus.has(edge.target):edge.source===store.selectedId||edge.target===store.selectedId;const tint=color.clone().lerp(new THREE.Color('#f3f7fc'),active?0:.84);
  for(let i=0;i<points.length;i++){const at=offset+i;edgePositions.setXYZ(at,show?points[i].x:0,show?points[i].y:0,show?points[i].z:0);edgeColors.setXYZ(at,tint.r,tint.g,tint.b)}
  const transform=matrix.clone();if(!show||edge.type==='compare_with')transform.scale(new THREE.Vector3(0,0,0));edgeArrows.setMatrixAt(index,transform);edgeArrows.setColorAt(index,tint)
 }
 if(edgeLines){edgePositions.needsUpdate=true;edgeColors.needsUpdate=true;edgeArrows.instanceMatrix.needsUpdate=true;if(edgeArrows.instanceColor)edgeArrows.instanceColor.needsUpdate=true}
 dirty=true
}
function ray(event){const bounds=host.value.getBoundingClientRect();const pointer=new THREE.Vector2((event.clientX-bounds.left)/bounds.width*2-1,-(event.clientY-bounds.top)/bounds.height*2+1);const r=new THREE.Raycaster();r.params.Points.threshold=8;r.setFromCamera(pointer,camera);return r.intersectObjects([...meshMap.values()].filter(m=>m.visible),false)[0]?.object.userData.nodeId}
function down(e){pointerStart={x:e.clientX,y:e.clientY};flight=null;atHome=false}
function up(e){if(pointerStart&&Math.hypot(e.clientX-pointerStart.x,e.clientY-pointerStart.y)<5){const id=ray(e);if(id)store.select(id)}pointerStart=null}
function move(e){const id=ray(e);hovered.value=id?store.byId[id].name:'';renderer.domElement.style.cursor=id?'pointer':'grab'}
function loop(now){
 if(disposed)return;raf=requestAnimationFrame(loop)
 if(document.hidden)return
 if(now-lastFrame<(store.quality==='low'?32:16))return
 const elapsed=now-lastFrame;lastFrame=now
 frameTime+=elapsed;if(frameTime>1500){fps.value=Math.round(frameCount*1000/frameTime);frameCount=0;frameTime=0}
 if(flight){const t=flight.duration?Math.min((now-flight.start)/flight.duration,1):1;const ease=t*t*(3-2*t);camera.position.lerpVectors(flight.from,flight.to,ease);controls.target.lerpVectors(flight.fromTarget,flight.target,ease);if(t===1)flight=null;dirty=true}
 const changed=controls.update();if(changed)dirty=true
 if(!dirty)return
 const dist=camera.position.distanceTo(controls.target),focus=new Set(store.focusIds),compMethods=store.mode==='compare'?store.comparison.method_ids:[];const occupied=[]
 for(const {obj,node} of nodeLabels.sort((a,b)=>(b.node.id===store.selectedId?10:b.node.importance)-(a.node.id===store.selectedId?10:a.node.importance))){
  const mesh=meshMap.get(node.id),forced=node.id===store.selectedId||compMethods.includes(node.id),labelOffset=compMethods.includes(node.id)?(compMethods.indexOf(node.id)===0?-75:75):0;obj.element.style.marginLeft=labelOffset+'px';let show=mesh.visible&&(!focus.size||focus.has(node.id)||node.id==='course')&&(node.id==='course'||forced||focus.has(node.id)||(dist<1000&&node.importance>=5)||dist<340)
  const v=obj.position.clone().project(camera);show=show&&Math.abs(v.x)<.92&&Math.abs(v.y)<.92&&v.z<1
  if(show){const x=v.x*host.value.clientWidth/2+labelOffset,y=v.y*host.value.clientHeight/2;if(!forced&&occupied.some(p=>Math.abs(p[0]-x)<105&&Math.abs(p[1]-y)<30))show=false;else occupied.push([x,y])}
  obj.visible=show;obj.element.classList.toggle('selected',node.id===store.selectedId)
 }
 for(const obj of moduleLabels)obj.visible=dist>340
 renderer.render(scene,camera);labels.render(scene,camera);frameCount++;host.value.dataset.drawCalls=String(renderer.info.render.calls);host.value.dataset.triangles=String(renderer.info.render.triangles);dirty=false
}
onMounted(()=>{
 if(new URLSearchParams(location.search).get('graphics')==='off'){failed.value=true;emit('ready',false);return}
 scene=new THREE.Scene();scene.fog=new THREE.FogExp2('#f3f7fc',.00055)
 camera=new THREE.PerspectiveCamera(43,1,1,4000);camera.up.set(0,0,1);camera.position.copy(homePosition)
 try{renderer=new THREE.WebGLRenderer({alpha:true,antialias:true,powerPreference:'high-performance'})}catch{failed.value=true;emit('ready',false);return}
 renderer.setClearColor(0xf3f7fc,0);renderer.setPixelRatio(Math.min(devicePixelRatio,1.7));host.value.appendChild(renderer.domElement)
 labels=new CSS2DRenderer();labels.domElement.className='scene-label-layer';host.value.appendChild(labels.domElement)
 controls=new OrbitControls(camera,renderer.domElement);controls.target.copy(homeTarget);controls.enableDamping=true;controls.dampingFactor=.09;controls.minDistance=85;controls.maxDistance=1450;controls.maxPolarAngle=Math.PI*.89;controls.addEventListener('change',()=>dirty=true);controls.addEventListener('start',()=>{flight=null;atHome=false})
 scene.add(new THREE.AmbientLight('#ccddec',2));const light=new THREE.DirectionalLight('#eaf9ff',3);light.position.set(100,-200,700);scene.add(light)
 // Horizontal XY rings at literal Z heights. These are semantic guides, not graph edges.
 for(let level=0;level<5;level++){
  const pts=[];for(let i=0;i<=128;i++){let a=i/128*Math.PI*2;pts.push(new THREE.Vector3(Math.cos(a)*365,Math.sin(a)*365,level*58))}
  const ring=new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),new THREE.LineBasicMaterial({color:'#5d778d',transparent:true,opacity:level===0?.30:.16}));scene.add(ring);gridObjects.push(ring)
  label(`L${level+1}  ${levels[level]}`,[-360,-235,level*58],'height-label')
 }
 const axis=new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(-360,-235,0),new THREE.Vector3(-360,-235,255)]),new THREE.LineDashedMaterial({color:'#8fabbc',dashSize:3,gapSize:5,transparent:true,opacity:.35}));axis.computeLineDistances();scene.add(axis)
 const centers={A:[-190,-190],B:[-265,70],C:[-90,250],D:[190,190],E:[265,-70],F:[90,-250]}
 for(const module of store.modules){const [x,y]=centers[module.id];
  const shape=new THREE.Mesh(new THREE.CircleGeometry(88,64),new THREE.MeshBasicMaterial({color:module.color,transparent:true,opacity:.035,side:THREE.DoubleSide,depthWrite:false}));shape.position.set(x,y,-6);scene.add(shape)
  const ringPts=Array.from({length:65},(_,i)=>new THREE.Vector3(x+Math.cos(i/64*Math.PI*2)*91,y+Math.sin(i/64*Math.PI*2)*91,-5));scene.add(new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(ringPts),new THREE.LineBasicMaterial({color:module.color,transparent:true,opacity:.25})))
  const obj=label(`${module.id}  ${module.name}`,[x,y,-18],'module-label');obj.element.style.color=module.color;moduleLabels.push(obj)
  const column=new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(x,y,0),new THREE.Vector3(x,y,232)]),new THREE.LineDashedMaterial({color:module.color,dashSize:2,gapSize:8,transparent:true,opacity:.16}));column.computeLineDistances();scene.add(column)
 }
 const sphere=new THREE.IcosahedronGeometry(1,2)
 for(const node of store.nodes){const isCore=node.id==='course',material=new THREE.MeshStandardMaterial({color:isCore?'#f97316':typeColors[node.type],emissive:isCore?'#c45a08':typeColors[node.type],emissiveIntensity:.12,metalness:.25,roughness:.4,transparent:true});const mesh=new THREE.Mesh(sphere,material);mesh.position.fromArray(positions[node.id]);mesh.geometry=sphere;mesh.userData.nodeId=node.id
  // Use a parent scale to preserve highlight scaling independently of semantic size.
  const base=new THREE.Group();base.position.copy(mesh.position);mesh.position.set(0,0,0);mesh.scale.setScalar(1);base.scale.setScalar(isCore?13:node.importance>=5?7.2:4.2);base.add(mesh);scene.add(base);meshMap.set(node.id,mesh)
  const obj=label(isCore?'多元统计分析':node.name,[...positions[node.id].slice(0,2),positions[node.id][2]+13],'node-label');nodeLabels.push({obj,node})
 }
 const relationColors={prerequisite:'#087c62',derived_from:'#7042b6',part_of:'#64748b',compare_with:'#c05a08',used_for:'#bd3748',assessed_by:'#4d7514'}
 const segmentVertices=store.edges.length*36;edgePositions=new THREE.BufferAttribute(new Float32Array(segmentVertices*3),3);edgeColors=new THREE.BufferAttribute(new Float32Array(segmentVertices*3),3)
 const edgeGeometry=new THREE.BufferGeometry().setAttribute('position',edgePositions).setAttribute('color',edgeColors)
 edgeLines=new THREE.LineSegments(edgeGeometry,new THREE.LineBasicMaterial({vertexColors:true,transparent:true,opacity:.75,depthWrite:false}));edgeLines.frustumCulled=false;scene.add(edgeLines)
 edgeArrows=new THREE.InstancedMesh(new THREE.ConeGeometry(2.1,6,5),new THREE.MeshBasicMaterial({transparent:true,opacity:.8,depthWrite:false}),store.edges.length);edgeArrows.frustumCulled=false;scene.add(edgeArrows)
 store.edges.forEach((edge,index)=>{const start=new THREE.Vector3(...positions[edge.source]),end=new THREE.Vector3(...positions[edge.target]);const mid=start.clone().lerp(end,.5);mid.z+=Math.min(35,start.distanceTo(end)*.08);const curve=new THREE.QuadraticBezierCurve3(start,mid,end),curvePoints=curve.getPoints(18),points=[]
  for(let i=0;i<18;i++)points.push(curvePoints[i],curvePoints[i+1]);const dummy=new THREE.Object3D();dummy.position.copy(curve.getPoint(.79));dummy.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),curve.getTangent(.79));dummy.updateMatrix();edgeObjects.push({edge,index,points,offset:index*36,color:new THREE.Color(relationColors[edge.type]),matrix:dummy.matrix.clone()})
 })
 // Fixed deterministic star field, purely decorative; no knowledge positions are randomized.
 const coords=[];for(let i=0;i<650;i++){const a=i*2.399963,rad=450+(i%151)*3;coords.push(Math.cos(a)*rad,Math.sin(a)*rad,-80+(i%71)*9)}
 scene.add(new THREE.Points(new THREE.BufferGeometry().setAttribute('position',new THREE.Float32BufferAttribute(coords,3)),new THREE.PointsMaterial({color:'#cbd6e2',size:1.25,transparent:true,opacity:.35,sizeAttenuation:true})))
 function resize(){const w=host.value.clientWidth,h=host.value.clientHeight;if(!w||!h)return;camera.aspect=w/h;camera.updateProjectionMatrix();if(atHome){flight=null;camera.position.copy(responsiveHome());controls.target.copy(homeTarget);}renderer.setSize(w,h);labels.setSize(w,h);dirty=true}
 observer=new ResizeObserver(resize);observer.observe(host.value);resize();updateVisibility();renderer.domElement.addEventListener('pointerdown',down);renderer.domElement.addEventListener('pointerup',up);renderer.domElement.addEventListener('pointermove',move);renderer.domElement.addEventListener('webglcontextlost',e=>{e.preventDefault();failed.value=true})
 raf=requestAnimationFrame(loop);emit('ready',true)
})
watch(()=>[store.selectedId,store.filtered,store.focusIds,store.relationFilter],updateVisibility,{deep:true})
watch(()=>store.flight,()=>fly(store.selectedId));watch(()=>store.sceneReset,()=>fly(null,true));watch(()=>store.quality,()=>{renderer?.setPixelRatio(store.quality==='low'?1:Math.min(devicePixelRatio,1.7));dirty=true})
onBeforeUnmount(()=>{disposed=true;cancelAnimationFrame(raf);observer?.disconnect();controls?.dispose();renderer?.domElement.removeEventListener('pointerdown',down);renderer?.domElement.removeEventListener('pointerup',up);renderer?.domElement.removeEventListener('pointermove',move);scene?.traverse(o=>{if(o.isInstancedMesh)o.dispose();o.geometry?.dispose();if(o.material)for(const m of [].concat(o.material))m.dispose();if(o.isCSS2DObject)o.element.remove()});renderer?.dispose();renderer?.domElement.remove();labels?.domElement.remove()})
</script>
<template>
 <div ref="host" class="universe-scene" aria-label="六大知识星系与五层认知高度三维场景">
  <div v-if="failed" class="scene-fallback"><strong>当前设备无法呈现 WebGL 2 场景</strong><p>请继续使用左侧节点目录、搜索与学习导航，所有知识和资源仍然可用。</p><button @click="store.setMode('directory')">打开知识目录</button></div>
  <div class="scene-status"><span class="status-dot"></span>{{ failed ? '目录模式可用' : '3D 空间已就绪' }}<span v-if="!failed">{{ fps ? fps+' FPS' : '按需渲染' }}</span></div>
  <div class="scene-axis-mobile">Z ↑ 认知高度 · 五层递进</div>
  <div v-if="hovered" class="hover-label">{{ hovered }} · 点击查看</div>
 </div>
</template>
