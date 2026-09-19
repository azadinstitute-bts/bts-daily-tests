(()=>{"use strict";
const KEY="bts_web_theme_v1",API="https://mqorslvouzmrvciubpoq.supabase.co/functions/v1/student-api";
const read=k=>{try{return localStorage.getItem(k)||sessionStorage.getItem(k)||""}catch{return""}};
const device=mobile=>{let x=read("deviceToken");if(x&&x.length>=24)return x;return("web_"+btoa(mobile||"").replace(/=/g,"")).padEnd(25,"x")};
const post=async(action,body={})=>{const mobile=body.mobile||read("mobile");const r=await fetch(API,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({action,device_token:device(mobile),client_version:"web-6078",app_version_code:6078,client_build:6078,api_contract_version:1,...body})});let j={};try{j=await r.json()}catch{}if(!r.ok||j?.ok!==true)throw new Error(j?.error||"Request failed");return j};
const apply=mode=>{const m=mode==="dark"?"dark":"light";document.documentElement.dataset.btsTheme=m;document.documentElement.style.colorScheme=m;try{localStorage.setItem(KEY,m)}catch{};document.querySelectorAll("[data-bts-theme-toggle]").forEach(b=>b.textContent=m==="dark"?"☀️ Light Mode":"🌙 Dark Mode")};
apply(read(KEY)||"light");
function ensureThemeButton(){
 const guide=[...document.querySelectorAll("button")].find(b=>(b.textContent||"").trim()==="User Guide");
 if(!guide||document.querySelector("[data-bts-theme-toggle]"))return;
 const b=guide.cloneNode(true);b.dataset.btsThemeToggle="1";b.removeAttribute("disabled");
 b.onclick=e=>{e.preventDefault();e.stopPropagation();apply(document.documentElement.dataset.btsTheme==="dark"?"light":"dark")};
 guide.parentNode.insertBefore(b,guide.nextSibling);apply(document.documentElement.dataset.btsTheme||"light")
}
let flashKey="";
async function ensureDemoFlash(){
 if(!location.hash.startsWith("#/")||location.hash.startsWith("#/login"))return;
 const mobile=read("mobile"),token=read("sessionToken");if(!mobile||!token.startsWith("DEMO_FREE_"))return;
 const key=mobile+"|"+token;if(flashKey===key)return;
 try{
  const data=await post("get_dashboard",{mobile,session_token:token,limit:500}),msg=data?.app_metadata?.demo_flash_message,id=data?.app_metadata?.demo_flash_id;
  if(!msg||!id){flashKey=key;return}
  const seenKey="seen_flash_"+id;if(read(seenKey)==="true"){flashKey=key;return}
  const card=document.querySelector(".overview-card");if(!card)return;
  try{localStorage.setItem(seenKey,"true")}catch{}
  let el=document.getElementById("bts-demo-policy-flash");if(!el){el=document.createElement("div");el.id="bts-demo-policy-flash";el.className="bts-demo-policy-flash";card.insertAdjacentElement("afterend",el)}
  el.textContent="";const span=document.createElement("span");span.textContent=msg;const close=document.createElement("button");close.type="button";close.className="bts-demo-flash-close";close.textContent="DISMISS";close.onclick=()=>el.remove();el.append(span,close);flashKey=key
 }catch{}
}
function ensureLoginSupport(){
 if(!location.hash.startsWith("#/login")){document.querySelector("[data-bts-login-support]")?.remove();return}
 if(document.querySelector("[data-bts-login-support]"))return;
 const login=[...document.querySelectorAll("button")].find(b=>(b.textContent||"").trim()==="Login Securely");if(!login)return;
 const b=document.createElement("button");b.type="button";b.dataset.btsLoginSupport="1";b.className="btn btn-outline";b.style.width="100%";b.style.marginTop=".65rem";b.textContent="Call Support • 9669946966";b.onclick=()=>{location.href="tel:+919669946966"};
 login.insertAdjacentElement("afterend",b)
}
function closeAttemptModal(){document.getElementById("bts-attempt-modal")?.remove()}
async function openAttemptHistory(testCode){
 closeAttemptModal();
 const overlay=document.createElement("div");overlay.id="bts-attempt-modal";overlay.className="bts-attempt-overlay";
 const box=document.createElement("div");box.className="bts-attempt-box";
 const title=document.createElement("div");title.className="bts-attempt-title";title.textContent="Attempt History";box.appendChild(title);
 const loading=document.createElement("div");loading.className="bts-attempt-loading";loading.textContent="Loading attempts…";box.appendChild(loading);
 const close=document.createElement("button");close.className="bts-attempt-close";close.textContent="Close";close.onclick=closeAttemptModal;box.appendChild(close);
 overlay.onclick=e=>{if(e.target===overlay)closeAttemptModal()};overlay.appendChild(box);document.body.appendChild(overlay);
 try{
  const mobile=read("mobile"),token=read("sessionToken"),h=await post("get_attempt_history",{mobile,session_token:token,test_code:testCode});
  loading.remove();
  const meta=document.createElement("div");meta.className="bts-attempt-meta";meta.textContent=`${h.attempts_used||0}/${h.max_attempts||0} attempts used • ${h.attempts_remaining||0} remaining`;box.insertBefore(meta,close);
  const list=document.createElement("div");list.className="bts-attempt-list";
  (h.attempts||[]).forEach(a=>{const b=document.createElement("button");b.className="bts-attempt-row";const d=a.submitted_at?new Date(a.submitted_at).toLocaleString("en-IN"):"";b.textContent=`Attempt ${a.attempt_number} • ${a.is_official_attempt?"Official":"Practice"} • Score ${a.score}/${a.total}${d?" • "+d:""}`;b.onclick=()=>{const base=`#/result/${encodeURIComponent(testCode)}`,q=a.attempt_id?`?attempt_id=${encodeURIComponent(a.attempt_id)}`:"";location.hash=base+q;location.reload()};list.appendChild(b)});
  if(!(h.attempts||[]).length){const none=document.createElement("div");none.className="bts-attempt-loading";none.textContent="No completed attempts found.";list.appendChild(none)}
  box.insertBefore(list,close)
 }catch(e){loading.textContent=e.message||"Attempt history could not be loaded."}
}
function ensureAttemptButton(){
 const m=location.hash.match(/^#\/result\/([^?]+)/);if(!m){document.querySelector("[data-bts-attempt-history]")?.remove();return}
 if(document.querySelector("[data-bts-attempt-history]"))return;
 const header=document.querySelector("header");if(!header)return;
 const b=document.createElement("button");b.dataset.btsAttemptHistory="1";b.className="bts-attempt-header";b.textContent="↻ Attempts";b.title="Attempt History";
 b.onclick=e=>{e.preventDefault();e.stopPropagation();openAttemptHistory(decodeURIComponent(m[1]))};
 header.appendChild(b)
}
const tick=()=>{ensureThemeButton();ensureLoginSupport();ensureDemoFlash();ensureAttemptButton()};
new MutationObserver(tick).observe(document.documentElement,{subtree:true,childList:true});
window.addEventListener("hashchange",()=>{flashKey="";closeAttemptModal();setTimeout(tick,50)});
setTimeout(tick,50);
})();