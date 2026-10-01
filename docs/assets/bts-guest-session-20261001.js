(function(){"use strict";
var KEY="bts_guest_device_v1",cached="",API="https://mqorslvouzmrvciubpoq.supabase.co/functions/v1/student-api";
function device(){
 if(cached)return cached;
 try{cached=localStorage.getItem(KEY)||sessionStorage.getItem(KEY)||"";}catch(e){}
 if(!/^web_guest_[a-f0-9]{48}$/.test(cached)){
  if(!window.crypto||!window.crypto.getRandomValues)throw new Error("Please use an updated browser for Free Demo.");
  var b=new Uint8Array(24);window.crypto.getRandomValues(b);cached="web_guest_";
  for(var i=0;i<b.length;i++)cached+=("0"+b[i].toString(16)).slice(-2);
 }
 try{localStorage.setItem(KEY,cached);}catch(e){}
 try{sessionStorage.setItem(KEY,cached);}catch(e){}
 return cached;
}
function start(mobile,name,course){
 if(!/^\d{10}$/.test(String(mobile).trim())||!String(name).trim())return Promise.reject(new Error("Enter your name and 10-digit mobile number."));
 var d;try{d=device();}catch(e){return Promise.reject(e);}
 return fetch(API,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({action:"start_guest_demo",mobile:String(mobile).trim(),name:String(name).trim(),course:course,device_token:d,client_version:"web-6078-security-20261001",app_version_code:6078,client_build:6078,api_contract_version:1})})
 .then(function(r){return r.json().then(function(j){if(!r.ok||!j||j.ok!==true)throw new Error(j&&j.error||"Free Demo could not start.");if(!/^DG_[a-f0-9]{32}$/.test(j.mobile)||!/^DEMO_FREE_GUEST_[a-f0-9]{48}$/.test(j.session_token))throw new Error("Invalid demo session response.");return j;});});
}
window.BTSGuestSession={device:device,start:start};
})();
