const fs=require('node:fs'),http=require('node:http'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require('playwright');
const ROOT=path.resolve(__dirname,'../docs'), results=[];
const paper=(code,week,day,date,title)=>({test_code:code,test_title:title||code+' paper',subject:'Physics',topic:'Test topic',status:'available',week_number:week,day_number:day,scheduled_date:date,q_count:4,duration_minutes:10,content_version:'fixture-v1',max_attempts:7,attempts_used:0,attempts_remaining:7});
const tests=[paper('A1',19,2,'2026-09-01','A1 paper'),paper('A2',19,3,'2026-09-02','A2 paper'),paper('B1',1,1,'2026-10-05','B1 paper'),paper('B2',1,2,'2026-10-06','B2 paper')];
const entitlements=[{course:'Course A',course_id:'a',test_codes:['A1','A2'],status:'active'},{course:'Course B',course_id:'b',test_codes:['B1','B2'],status:'active'}];
const questions=[2,17,42,80].map(qno=>({qno,question_text:'Fixture question '+qno+'\nThe relationship is unknown and all dimensions are known.',options:['Option A','Option B','Option C','Option D'],metadata:{},marks:1}));
let legacy=false,communityEnabled=true,communityUrl='https://t.me/bilaspur_test_series',dashboardTests=tests;
const server=http.createServer((req,res)=>{
 const relative=decodeURIComponent(req.url.split('?')[0]).replace(/^\/bts-daily-tests\/?/,'');
 const target=path.resolve(ROOT,relative||'index.html');
 if(!target.startsWith(ROOT+path.sep)){res.writeHead(403);return res.end();}
 if(!fs.existsSync(target)){res.writeHead(404);return res.end();}
 let data=fs.readFileSync(target);
 if(legacy&&target.endsWith('index.html')){
  let html=data.toString().replace(/<script type="module" crossorigin src="[^"]*index-[^"]*"><\/script>/g,'').replace(/<script type="module">[\s\S]*?<\/script>/g,'').replaceAll(' nomodule','');data=Buffer.from(html);
 }
 res.setHeader('Content-Type',target.endsWith('.js')?'application/javascript':target.endsWith('.css')?'text/css':target.endsWith('.png')?'image/png':'text/html');res.end(data);
});
function record(variant,name){results.push({variant,test:name,status:'PASS'});console.log('CASE_PASS '+variant+' '+name);}
(async()=>{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const base='http://127.0.0.1:'+server.address().port+'/bts-daily-tests/';
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||'/usr/bin/google-chrome',args:['--no-sandbox']});
 try{
 for(const mode of ['modern','legacy'])for(const viewport of [{width:390,height:844},{width:1280,height:900}]){
  legacy=mode==='legacy';communityEnabled=true;communityUrl='https://t.me/bilaspur_test_series';dashboardTests=tests;
  const variant=mode+'-'+viewport.width,context=await browser.newContext({viewport}),page=await context.newPage(),errors=[],calls=[];
  page.on('pageerror',error=>errors.push(error.message));
  await page.route('**/functions/v1/**',async route=>{
   const request=route.request(),body=request.postDataJSON()||{};calls.push(body);
   let data;
   switch(body.action){
    case 'verify_session':data={ok:true,student:{mobile:'9555555011',name:'Synthetic fixture'}};break;
    case 'get_dashboard':data={ok:true,student:{mobile:'9555555011',name:'Synthetic fixture'},entitlements,latest_tests:dashboardTests,attempted_tests:[],app_metadata:{community_links:{telegram_url:communityUrl,telegram_menu_enabled:communityEnabled,telegram_play_community_only:false}}};break;
    case 'get_demo_courses':data={ok:true,courses:[{course_id:'a',label:'Course A'}]};break;
    case 'get_test_public':data={ok:true,content_version:'fixture-v1',test:tests[0],attempt:{attempt_token:body.attempt_token,started_at:new Date().toISOString(),expires_at:new Date(Date.now()+600000).toISOString()},questions,passages:[]};break;
    case 'submit_native_result':data={ok:true,attempt_id:'synthetic-practice',score:2,total:4};break;
    case 'get_result_detail':data={ok:true,result:{test_code:'A1',test_title:'A1 paper',score:2,total:4,percentage:50,correct:2,wrong:1,unattempted:1},questions:questions.map(q=>({...q,attempted:true,is_correct:true,correct_option_index:0,selected_index:0,explanation:'Synthetic explanation'})),passages:[]};break;
    case 'get_leaderboard':data={ok:true,leaderboard:[]};break;
    case 'get_attempt_history':data={ok:true,max_attempts:7,attempts_used:2,attempts_remaining:5,attempts:[]};break;
    default:throw Error('Unexpected API action '+body.action);
   }
   await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(data)});
  });
  await page.addInitScript(()=>{if(!localStorage.getItem('sessionToken')){localStorage.setItem('mobile','9555555011');localStorage.setItem('sessionToken','SES_SYNTHETIC_ONLY');}localStorage.setItem('bts_privacy_consent_agreed_v1','true');});
  await page.goto(base);await page.getByRole('heading',{name:'My Tests',exact:true}).waitFor();
  assert(!(await page.locator('body').innerText()).includes('\\n'));record(variant,'literal newline removed and dashboard loads');
  await page.getByRole('button',{name:'Course A',exact:true}).click();
  const filter=page.locator('select');await filter.selectOption('19');assert.match(await filter.innerText(),/Week 19 \(1 Sep – 2 Sep\)/);record(variant,'selected course supplies week dates');
  await page.getByRole('button',{name:'Course B',exact:true}).click();assert.equal(await filter.inputValue(),'');assert.equal(await filter.locator('option').count(),2);assert.match(await filter.innerText(),/Week 1 \(5 Oct – 6 Oct\)/);assert.match(await page.locator('body').innerText(),/Week 1 • Day 2 • 6 Oct 2026/);assert(!(await page.locator('body').innerText()).includes('A1 paper'));record(variant,'course change resets week and retains exact access');
  await filter.selectOption('1');dashboardTests=tests.slice(0,2);await page.getByRole('button',{name:'Refresh',exact:true}).click();await page.waitForFunction(()=>document.querySelector('select')===null||document.querySelector('select').value==='');record(variant,'refresh removes stale week selection');dashboardTests=tests;await page.getByRole('button',{name:'Refresh',exact:true}).click();
  await page.getByRole('button',{name:'Menu',exact:true}).click();const link=page.getByRole('link',{name:'Telegram Community',exact:true});await link.waitFor();assert.equal(await link.getAttribute('href'),communityUrl);assert.equal(await link.getAttribute('rel'),'noopener noreferrer');record(variant,'backend-controlled Telegram link');
  await page.mouse.click(5,200);communityEnabled=false;await page.getByRole('button',{name:'Refresh',exact:true}).click();await page.getByRole('button',{name:'Menu',exact:true}).click();await page.waitForTimeout(150);assert.equal(await page.getByRole('link',{name:'Telegram Community',exact:true}).count(),0);record(variant,'disabled Telegram menu hidden');
  await page.getByRole('button',{name:/Dark Mode/}).click();await page.goto(base+'#/test/A1');await page.locator('.bts-question-status').waitFor();assert.match(await page.locator('.bts-question-status').innerText(),/Viewed/);assert.match(await page.locator('.q-content').first().innerText(),/unknown.*known/s);record(variant,'plain structured wording remains intact');
  await page.getByTitle('Question Navigator',{exact:true}).click();
  assert.equal(await page.locator('[data-qno="2"]').getAttribute('data-question-state'),'viewed');assert.equal(await page.locator('[data-qno="17"]').getAttribute('data-question-state'),'unanswered');
  await page.locator('[data-qno="80"]').click();await page.waitForFunction(()=>document.querySelector('.bts-question-status')&&document.body.innerText.includes('Fixture question 80'));record(variant,'non-sequential QNo jump uses list index');
  await page.locator('.bts-option').first().click();await page.getByRole('button',{name:'🔖 Mark',exact:true}).click();assert.match(await page.locator('.bts-question-status').innerText(),/Marked.*Answer selected/);
  await page.getByTitle('Question Navigator',{exact:true}).click();assert.equal(await page.locator('[data-qno="80"]').getAttribute('data-question-state'),'marked');assert.equal(await page.locator('[data-qno="80"]').getAttribute('data-answered'),'true');assert.equal(await page.locator('[data-qno="80"]').getAttribute('aria-current'),'step');const color=await page.locator('[data-qno="80"]').evaluate(el=>getComputedStyle(el).color);assert.equal(color,'rgb(243, 208, 126)');await page.getByRole('button',{name:'Close',exact:true}).click();record(variant,'review priority, answer marker and dark colours');
  await page.waitForTimeout(500);await page.reload();await page.locator('.bts-question-status').waitFor();assert.match(await page.locator('.q-content').first().innerText(),/Fixture question 80/);assert.match(await page.locator('.bts-question-status').innerText(),/Marked.*Answer selected/);record(variant,'draft restores current question, answer and mark');
  await page.getByTitle('Question Navigator',{exact:true}).click();assert.equal(await page.locator('[data-qno="2"]').getAttribute('data-question-state'),'viewed');assert.equal(await page.locator('[data-qno="17"]').getAttribute('data-question-state'),'unanswered');await page.getByRole('button',{name:'Close',exact:true}).click();record(variant,'draft preserves real visits without guessing unseen questions');
  await page.getByRole('button',{name:'✕ Clear answer',exact:true}).click();assert.match(await page.locator('.bts-question-status').innerText(),/Marked/);assert(!(await page.locator('.bts-question-status').innerText()).includes('Answer selected'));await page.getByRole('button',{name:'🔖 Marked',exact:true}).click();assert.match(await page.locator('.bts-question-status').innerText(),/Viewed/);record(variant,'clear and unmark update status without changing question');
  await page.locator('.bts-option').nth(1).click();await page.getByRole('button',{name:/Finish & Submit$/,exact:false}).click();await page.getByRole('button',{name:'Submit Now',exact:true}).click();await page.waitForURL(/#\/result\/A1\?attempt_id=synthetic-practice/);await page.getByText('Synthetic explanation',{exact:false}).first().waitFor();const submit=calls.find(x=>x.action==='submit_native_result');assert(submit);assert.equal(submit.answers.length,1);assert.equal(submit.answers[0].q,80);assert.equal(submit.answers[0].selected_index,1);assert.equal(submit.answers[0].given,'Option B');assert(!('visited'in submit));record(variant,'unchanged submission schema and specific practice result');
  assert.deepEqual(errors,[]);record(variant,'zero application page errors');
  await context.close();
 }
 }finally{await browser.close();server.close();}
 fs.mkdirSync(path.resolve(__dirname,'evidence'),{recursive:true});fs.writeFileSync(path.resolve(__dirname,'evidence/browser-6084.json'),JSON.stringify({status:'PASS',count:results.length,mode:'Synthetic API interception; no production requests, credentials or writes',results},null,2));console.log('BROWSER_PARITY_PASS '+JSON.stringify({count:results.length,results}));
})().catch(error=>{console.error(error);server.close();process.exitCode=1;});
