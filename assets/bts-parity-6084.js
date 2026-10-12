(function () {
  'use strict';
  // Presentation only. Access, attempts, deadlines and scoring stay server-owned.
  var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  function positive(value) { var n = Number(value); return Number.isInteger(n) && n > 0 ? n : 0; }
  function position(test) {
    var flags = test.flags || test.flags_json || {};
    var week = positive(test.week_number) || positive(flags.week_number);
    var day = positive(test.day_number) || positive(flags.day_number);
    if (week || day) return {week: week, day: day};
    var text = [test.test_title,test.paper_name,test.test_code,test.subject,test.topic].join(' ').replace(/[_-]+/g,' ');
    var w = text.match(/\bweek\s*0*(\d{1,3})\b/i), d = text.match(/\bday\s*0*(\d{1,3})\b/i);
    return {week: w ? Number(w[1]) : 0, day: /\bweekly\b/i.test(text) ? 7 : d ? Number(d[1]) : 0};
  }
  function date(value) {
    if (typeof value !== 'string') return null;
    var text = value.trim(), match = text.match(/^(\d{4})-(\d{2})-(\d{2})(?:$|T| )/);
    if (!match) return null;
    var y = Number(match[1]), m = Number(match[2]), d = Number(match[3]);
    var check = new Date(Date.UTC(y,m-1,d));
    if (check.getUTCFullYear() !== y || check.getUTCMonth() !== m-1 || check.getUTCDate() !== d) return null;
    if (/^\d{4}-\d{2}-\d{2}$/.test(text)) text += 'T00:00:00+05:30';
    else if (!/(Z|[+-]\d{2}:?\d{2})$/i.test(text)) text = text.replace(' ','T') + '+05:30';
    var time = Date.parse(text);
    return Number.isFinite(time) ? new Date(time + 19800000) : null;
  }
  function testDate(test) { return date(test.scheduled_date) || date(test.unlocks_at); }
  function dayLabel(d, year) { return d.getUTCDate()+' '+months[d.getUTCMonth()]+(year ? ' '+d.getUTCFullYear() : ''); }
  function kind(test) {
    var explicit = String(test.display_test_kind || '').trim().toLowerCase();
    if (explicit === 'mega' || explicit === 'full_syllabus') return explicit;
    var title = String(test.test_title || test.paper_name || '').replace(/[_-]+/g,' ');
    if (/\bfull\s+syllabus\b/i.test(title)) return 'full_syllabus';
    if (/\bmega\b/i.test(title) || (Array.isArray(test.eligible_course_ids) && test.eligible_course_ids.some(function(id){return /_mega15$/i.test(id);}))) return 'mega';
    return '';
  }
  function title(test, original) { var k=kind(test); return k==='mega' ? 'Mega Test' : k==='full_syllabus' ? 'Full Syllabus Test' : original; }
  function schedule(test, fallback) {
    var p=position(test), result=[];
    if (p.week) result.push('Week '+p.week);
    if (p.day) result.push('Day '+p.day);
    var label=result.join(' • ') || fallback || '', d=testDate(test);
    if (d) label+=(label ? ' • ' : '')+dayLabel(d,true);
    return label;
  }
  function entitlementName(e) {
    var parts=[e.course,e.post,e.subject].filter(function(v){return v && String(v).trim();});
    return parts.length ? parts.join(' - ') : e.plan_code || e.plan || 'Purchased Course';
  }
  function courseTests(tests, entitlements, selected, matches) {
    if (!selected) return tests;
    var entitlement=entitlements.find(function(e){return entitlementName(e)===selected;}) || {course:selected};
    return tests.filter(function(test){return matches(test,entitlement);});
  }
  function weeks(tests, entitlements, selected, matches) {
    var found=[];
    courseTests(tests,entitlements,selected,matches).forEach(function(test){var w=position(test).week;if(w && found.indexOf(w)<0)found.push(w);});
    return found.sort(function(a,b){return a-b;});
  }
  function weekLabel(week, tests, entitlements, selected, matches) {
    var papers=courseTests(tests,entitlements,selected,matches).filter(function(t){return position(t).week===week;});
    var dates=papers.map(testDate), label='Week '+week;
    if (!dates.length || dates.some(function(d){return !d;})) return label;
    dates.sort(function(a,b){return a-b;});
    var first=dates[0],last=dates[dates.length-1],year=first.getUTCFullYear()!==last.getUTCFullYear();
    var a=dayLabel(first,year), b=dayLabel(last,year);
    return label+' ('+a+(a===b ? '' : ' – '+b)+')';
  }
  function telegram(data) {
    var links=data && data.app_metadata && data.app_metadata.community_links;
    if (!links || links.telegram_menu_enabled !== true || typeof links.telegram_url !== 'string') return '';
    var url=links.telegram_url.trim();
    if (/^https:\/\/t\.me\/(?:\+[A-Za-z0-9_-]{6,128}|joinchat\/[A-Za-z0-9_-]{6,128})$/.test(url)) return url;
    var m=url.match(/^https:\/\/t\.me\/([A-Za-z][A-Za-z0-9_]{4,31})$/);
    var reserved=['share','proxy','socks','iv','login','joinchat','addstickers','addemoji','addtheme','setlanguage','confirmphone','boost','giftcode','contact','addlist'];
    return m && reserved.indexOf(m[1].toLowerCase())<0 ? url : '';
  }
  function communityItem(ui,data) {
    var href=telegram(data);if(!href)return null;
    return ui.jsx('a',{href:href,target:'_blank',rel:'noopener noreferrer',className:'bts-community-link',children:'Telegram Community'});
  }
  function restoreVisits(questions,draft,current,answers,marked) {
    var valid=questions.map(function(q){return Number(q.qno);}), visits={};
    if(draft){
      (Array.isArray(draft.visited) ? draft.visited : []).forEach(function(q){q=Number(q);if(valid.indexOf(q)>=0)visits[q]=true;});
    }
    Object.keys(answers||{}).concat(Object.keys(marked||{}).filter(function(q){return marked[q];})).forEach(function(q){if(valid.indexOf(Number(q))>=0)visits[q]=true;});
    if(questions[current])visits[questions[current].qno]=true;
    return visits;
  }
  function status(answered,marked,visited) {
    var dark=document.documentElement.dataset.btsTheme==='dark';
    if(marked)return {kind:'marked',label:answered ? 'Marked for review · Answer selected' : 'Marked for review',background:dark?'#40351B':'#FFF4DA',color:dark?'#F3D07E':'#7A4B00'};
    if(answered)return {kind:'answered',label:'Answer selected',background:dark?'#18382C':'#EAF6EF',color:dark?'#84D8AC':'#146C43'};
    if(visited)return {kind:'viewed',label:'Viewed · Unanswered',background:dark?'#40272C':'#FBEDEF',color:dark?'#F2A8B9':'#922C40'};
    return {kind:'unanswered',label:'Unanswered',background:'var(--color-surface)',color:'var(--color-text-main)'};
  }
  function statusBadge(ui,answered,marked,visited) {
    var s=status(answered,marked,visited);
    return ui.jsx('div',{className:'bts-question-status',role:'status','data-question-state':s.kind,style:{backgroundColor:s.background,color:s.color},children:s.label});
  }
  window.BTSWeb6084={position:position,date:date,testDate:testDate,kind:kind,title:title,schedule:schedule,weeks:weeks,weekLabel:weekLabel,telegram:telegram,communityItem:communityItem,restoreVisits:restoreVisits,status:status,statusBadge:statusBadge};
})();
