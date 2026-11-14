// @ts-nocheck
// Ported unchanged from the HTML prototype (the Earth / ISS / helmet scene), wrapped as a function.
export function initScene(THREE:any,st:HTMLElement,cv:HTMLCanvasElement,env:any):any{const {D,M,stat,col}=env;let fx=true,dead=false;
const gl=(()=>{try{const c=document.createElement('canvas');return !!(c.getContext('webgl')||c.getContext('experimental-webgl'))}catch(e){return false}})();
if(!gl||matchMedia('(prefers-reduced-motion:reduce)').matches)return null;
const T=THREE,R=new T.WebGLRenderer({canvas:cv,antialias:true,alpha:true});let dpr=Math.min(devicePixelRatio||1,1.75);R.setPixelRatio(dpr);
const S=new T.Scene(),C=new T.PerspectiveCamera(38,1,.1,100);C.position.set(0,.5,16);
S.add(new T.AmbientLight(0x7f9cff,.55));const sun=new T.DirectionalLight(0xffffff,1.7);sun.position.set(6,2.5,5);S.add(sun);const rim=new T.PointLight(0x4c86ff,1.2,30);rim.position.set(-6,-2,-3);S.add(rim);
const rnd=Math.random,cvs=(w,h,f)=>{const c=document.createElement('canvas');c.width=w;c.height=h;f(c.getContext('2d'),w,h);return new T.CanvasTexture(c)};
const earthTex=cvs(1024,512,(g,w,h)=>{const o=g.createLinearGradient(0,0,0,h);o.addColorStop(0,'#1b56d6');o.addColorStop(.5,'#0a3fb8');o.addColorStop(1,'#1b56d6');g.fillStyle=o;g.fillRect(0,0,w,h);
for(let i=0;i<110;i++){const x=rnd()*w,y=h*.12+rnd()*h*.76,r=12+rnd()*46;g.fillStyle='rgba('+(46+rnd()*70|0)+','+(150+rnd()*60|0)+','+(96+rnd()*60|0)+',.9)';g.beginPath();g.ellipse(x,y,r,r*(.4+rnd()*.5),rnd()*3,0,7);g.fill();g.fillStyle='rgba(196,170,110,.35)';g.beginPath();g.ellipse(x+r*.2,y,r*.5,r*.25,rnd()*3,0,7);g.fill()}
g.fillStyle='rgba(235,245,255,.9)';g.fillRect(0,0,w,h*.05);g.fillRect(0,h*.95,w,h*.05)});
const cloudTex=cvs(1024,512,(g,w,h)=>{for(let i=0;i<150;i++){g.fillStyle='rgba(255,255,255,'+(.12+rnd()*.28)+')';g.beginPath();g.ellipse(rnd()*w,rnd()*h,20+rnd()*60,4+rnd()*12,rnd()*.5,0,7);g.fill()}});
const glowTex=cvs(128,128,g=>{const r=g.createRadialGradient(64,64,0,64,64,64);r.addColorStop(0,'rgba(255,255,255,1)');r.addColorStop(.25,'rgba(160,200,255,.5)');r.addColorStop(1,'rgba(160,200,255,0)');g.fillStyle=r;g.fillRect(0,0,128,128)});
const earth=new T.Mesh(new T.SphereGeometry(2,96,96),new T.MeshStandardMaterial({map:earthTex,roughness:.75,metalness:.05}));earth.rotation.z=.41;
const clouds=new T.Mesh(new T.SphereGeometry(2.045,64,64),new T.MeshStandardMaterial({map:cloudTex,transparent:true,opacity:.65,depthWrite:false}));
const atm=new T.Mesh(new T.SphereGeometry(2.35,64,64),new T.ShaderMaterial({transparent:true,side:T.BackSide,blending:T.AdditiveBlending,depthWrite:false,vertexShader:'varying vec3 n;void main(){n=normalize(normalMatrix*normal);gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',fragmentShader:'varying vec3 n;void main(){float i=pow(max(0.,.72-dot(n,vec3(0.,0.,1.))),4.);gl_FragColor=vec4(.3,.55,1.,1.)*i*.55;}'}));
const grp=new T.Group();grp.add(earth,clouds);S.add(grp);S.add(atm);
const sg=new T.Sprite(new T.SpriteMaterial({map:glowTex,blending:T.AdditiveBlending,transparent:true,depthWrite:false,opacity:.9}));sg.position.set(4.6,2.3,-3);sg.scale.set(7,7,1);S.add(sg);
const rings=[0,1,2].map(()=>{const m=new T.Mesh(new T.RingGeometry(2.3,2.34,128),new T.MeshBasicMaterial({color:0xe4ff3a,transparent:true,opacity:0,side:T.DoubleSide,depthWrite:false,blending:T.AdditiveBlending}));S.add(m);return m});
const orb=new T.Group();orb.rotation.set(Math.PI/2.4,.3,0);S.add(orb);orb.add(new T.Mesh(new T.TorusGeometry(3.1,.014,8,220),new T.MeshBasicMaterial({color:0xe4ff3a})));
const orb2=new T.Mesh(new T.TorusGeometry(3.9,.008,8,220),new T.MeshBasicMaterial({color:0x6fa0ff,transparent:true,opacity:.5}));orb2.rotation.set(Math.PI/2.9,-.6,0);S.add(orb2);
const sta=new T.Group(),m1=new T.MeshStandardMaterial({color:0xdce6ff,metalness:.4,roughness:.4}),m2=new T.MeshStandardMaterial({color:0x2d6bff,metalness:.6,roughness:.3,emissive:0x0a2a8f});
sta.add(new T.Mesh(new T.BoxGeometry(.5,.12,.12),m1),new T.Mesh(new T.CylinderGeometry(.09,.09,.3,12),m1));[-.55,.55].forEach(x=>{const p=new T.Mesh(new T.BoxGeometry(.5,.02,.32),m2);p.position.x=x;sta.add(p)});
const blink=new T.Mesh(new T.SphereGeometry(.035,8,8),new T.MeshBasicMaterial({color:0xff5a5f}));blink.position.set(.25,.08,0);sta.add(blink);orb.add(sta);
const TR=36,tp=new Float32Array(TR*3),tc=new Float32Array(TR*3);for(let i=0;i<TR;i++){const f=1-i/TR;tc[i*3]=.9*f;tc[i*3+1]=f;tc[i*3+2]=.23*f}
const tg=new T.BufferGeometry();tg.setAttribute('position',new T.BufferAttribute(tp,3));tg.setAttribute('color',new T.BufferAttribute(tc,3));orb.add(new T.Line(tg,new T.LineBasicMaterial({vertexColors:true,transparent:true,blending:T.AdditiveBlending,depthWrite:false})));
const hm=new T.Group(),shell=new T.Mesh(new T.SphereGeometry(.62,40,40),new T.MeshStandardMaterial({color:0xeaf0ff,roughness:.35,metalness:.1})),visor=new T.Mesh(new T.SphereGeometry(.5,40,40),new T.MeshStandardMaterial({color:0x0b1b4a,roughness:.06,metalness:.95}));visor.scale.set(1,.85,.55);visor.position.set(0,-.02,.34);
const stripe=new T.Mesh(new T.TorusGeometry(.5,.03,12,48),new T.MeshBasicMaterial({color:0xe4ff3a}));stripe.rotation.x=Math.PI/2;stripe.position.y=-.5;
const ant=new T.Mesh(new T.CylinderGeometry(.018,.018,.32,8),new T.MeshStandardMaterial({color:0xdce6ff}));ant.position.set(.3,.62,0);ant.rotation.z=-.3;
const knob=new T.Mesh(new T.SphereGeometry(.05,12,12),new T.MeshBasicMaterial({color:0xff5a5f}));knob.position.set(.34,.78,0);
const hl=new T.Mesh(new T.SphereGeometry(.07,12,12),new T.MeshBasicMaterial({color:0xffffff,transparent:true,opacity:.7}));hl.position.set(-.18,.14,.58);
hm.add(shell,visor,stripe,ant,knob,hl);hm.position.set(-3.1,-1.7,2.4);hm.scale.setScalar(1.1);S.add(hm);
const NS=1400,sp=new Float32Array(NS*3),sc=new Float32Array(NS*3);for(let i=0;i<NS;i++){const r=18+rnd()*18,th=rnd()*6.283,ph=Math.acos(2*rnd()-1);sp[i*3]=r*Math.sin(ph)*Math.cos(th);sp[i*3+1]=r*Math.sin(ph)*Math.sin(th);sp[i*3+2]=r*Math.cos(ph);const c=.6+rnd()*.4,b=rnd()<.2;sc[i*3]=b?.7:c;sc[i*3+1]=b?.8:c;sc[i*3+2]=1}
const sgm=new T.BufferGeometry();sgm.setAttribute('position',new T.BufferAttribute(sp,3));sgm.setAttribute('color',new T.BufferAttribute(sc,3));const stars=new T.Points(sgm,new T.PointsMaterial({size:.09,vertexColors:true,transparent:true,opacity:.9,depthWrite:false}));S.add(stars);
const HEX={ok:0x3ddc97,notice:0x7db2ff,watch:0xffc531,att:0xff5a5f};
const nodes=[['hr','Heart rate',3.7,.55,.5],['spo2','Oxygen',4.1,-.45,.7],['sleep','Sleep',3.5,.8,-.6],['temp','Temperature',4.3,-.7,-.4]].map(([k,l,r,tilt,spd],i)=>{const g=new T.Group();g.rotation.set(tilt,i*.9,0);const m=new T.Mesh(new T.SphereGeometry(.12,16,16),new T.MeshBasicMaterial({color:0xffffff}));const o=new T.Sprite(new T.SpriteMaterial({map:glowTex,blending:T.AdditiveBlending,transparent:true,depthWrite:false}));o.scale.set(.9,.9,1);m.add(o);g.add(m);S.add(g);const el=document.createElement('div');el.className='vn';st.appendChild(el);return{k,l,r,spd,g,m,o,el,a:i*1.6}});
const wp=new T.Vector3(),cp=new T.Vector3(),dv=new T.Vector3();
const lab=()=>nodes.forEach(n=>{const v=D[29][n.k],s=stat(n.k,v)[0];n.el.innerHTML='<small>'+n.l+'</small><b>'+(n.k==='sleep'||n.k==='temp'?v.toFixed(1):Math.round(v))+' '+M[n.k].u+'</b>';n.el.style.borderLeft='3px solid '+col(s);n.m.material.color.setHex(HEX[s]||0xffffff);n.o.material.color.setHex(HEX[s]||0x6fa0ff)});
const place=(n,w,h)=>{n.m.getWorldPosition(wp);cp.copy(C.position);dv.copy(wp).sub(cp);const dist=dv.length();dv.normalize();const pr=-cp.dot(dv),cl=cp.clone().addScaledVector(dv,pr).length();const hid=cl<2.05&&pr<dist;wp.project(C);n.el.style.transform='translate('+((wp.x*.5+.5)*w+14)+'px,'+((-wp.y*.5+.5)*h-22)+'px)';n.el.style.opacity=hid?0:1};
let tx=0,ty=0,drag=false,lx=0,vel=0,a=0,t=0,vis=true,last=performance.now(),fr=0,fc=0;
cv.addEventListener('pointerdown',e=>{drag=true;lx=e.clientX;cv.setPointerCapture(e.pointerId)});
cv.addEventListener('pointermove',e=>{const b=cv.getBoundingClientRect();tx=(e.clientX-b.left)/b.width-.5;ty=(e.clientY-b.top)/b.height-.5;if(drag){vel=(e.clientX-lx)*.008;grp.rotation.y+=vel;lx=e.clientX}});
const up=()=>{drag=false};addEventListener('pointerup',up);
const rs=()=>{const w=st.clientWidth,h=st.clientHeight;if(w>10&&h>10){R.setSize(w,h,false);C.aspect=w/h;C.updateProjectionMatrix()}};
const ro=new ResizeObserver(rs);ro.observe(st);const io2=new IntersectionObserver(e=>vis=e[0].isIntersecting);io2.observe(st);
const tick=()=>{if(dead)return;requestAnimationFrame(tick);const now=performance.now(),dt=Math.min(.05,(now-last)/1000);last=now;if(!fx||!vis||document.hidden||document.documentElement.classList.contains('rm'))return;
t+=dt;if(!drag){vel*=.95;grp.rotation.y+=.0016+vel}clouds.rotation.y+=.0006;stars.rotation.y+=.00015;
const hr=D[29].hr,ph=(t*hr/60)%1;atm.scale.setScalar(1+.025*Math.exp(-ph*7));
rings.forEach((r,i)=>{const p=((t/2.6)+i/3)%1;r.scale.setScalar(1+p*.9);r.material.opacity=(1-p)*.35;r.quaternion.copy(C.quaternion)});
a+=.006;sta.position.set(3.1*Math.cos(a),3.1*Math.sin(a),0);sta.rotation.z=a+Math.PI/2;blink.visible=Math.sin(t*6)>0;
for(let i=0;i<TR;i++){tp[i*3]=3.1*Math.cos(a-i*.03);tp[i*3+1]=3.1*Math.sin(a-i*.03)}tg.attributes.position.needsUpdate=true;
hm.position.y=-1.7+Math.sin(t*1.2)*.12;hm.rotation.set(ty*.4,-.3+tx*.7+Math.sin(t*.5)*.15,Math.sin(t*.8)*.06);
const ez=1-Math.pow(1-Math.min(1,t/1.8),3);C.position.z=16-5*ez;C.position.x+=(tx*2.4-C.position.x)*.05;C.position.y+=(.5-ty*1.6-C.position.y)*.05;C.lookAt(0,0,0);
const w=st.clientWidth,h=st.clientHeight;nodes.forEach(n=>{n.a+=n.spd*dt*.35;n.m.position.set(n.r*Math.cos(n.a),0,n.r*Math.sin(n.a));n.g.updateMatrixWorld(true);place(n,w,h)});
if(fc%30===0)lab();R.render(S,C);fr+=dt;fc++;if(fc>=90){if(fr/fc>.03&&dpr>1){dpr=1;R.setPixelRatio(1);rs()}fr=0;fc=0}};
rs();lab();tick();return{set:(on:boolean)=>{fx=on;if(on)rs()},dispose:()=>{dead=true;ro.disconnect();io2.disconnect();removeEventListener('pointerup',up);nodes.forEach((n:any)=>n.el.remove());R.dispose()}}}
