(()=>{"use strict";
const KEY="bts_web_theme_v1",API="https://mqorslvouzmrvciubpoq.supabase.co/functions/v1/student-api";
const read=k=>{try{return localStorage.getItem(k)||sessionStorage.getItem(k)||""}catch{return""}};
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
 const key=mobile+"|"+token;if(flashKey===key&&document.getElementById("bts-demo-policy-flash"))return;
 try{
  const res=await fetch(API,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({action:"get_dashboard",mobile,session_token:token,device_token:(()=>{let x=read("deviceToken");if(x&&x.length>=24)return x;return ("web_"+btoa(mobile).replace(/=/g,"")).padEnd(25,"x")})(),client_version:"web-6078",app_version_code:6078,client_build:6078,api_contract_version:1,limit:500})});
  const data=await res.json();if(!data?.ok)return;const msg=data?.app_metadata?.demo_flash_message;if(!msg)return;
  const card=document.querySelector(".overview-card");if(!card)return;
  let el=document.getElementById("bts-demo-policy-flash");if(!el){el=document.createElement("div");el.id="bts-demo-policy-flash";el.className="bts-demo-policy-flash";card.insertAdjacentElement("afterend",el)}
  el.textContent=msg;flashKey=key
 }catch{}
}
const tick=()=>{ensureThemeButton();ensureDemoFlash()};
new MutationObserver(tick).observe(document.documentElement,{subtree:true,childList:true});
window.addEventListener("hashchange",()=>{flashKey="";setTimeout(tick,50)});
setTimeout(tick,50);
})();