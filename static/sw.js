!function(){"use strict";function u(e,t){const n={n:e,u:self.location.toString(),d:"gawvertretung.florian-raediker.de",r:null};return t&&t.meta&&(n.m=JSON.stringify(t.meta)),t&&t.props&&(n.p=JSON.stringify(t.props)),fetch("https://plausible.florian-raediker.de/api/event",{method:"POST",headers:{"Content-Type":"text/plain"},body:JSON.stringify(n)}).catch(e=>console.error("reporting error failed",e))}function t(e,t=null){try{var n=e.name,o=(null==t?void 0:t.message)||e.message,a=e.description,i=e.number,r=(null==t?void 0:t.filename)||e.fileName,s=(null==t?void 0:t.lineno)||e.lineNumber,l=(null==t?void 0:t.colno)||e.columnNumber,c=(null==t?void 0:t.stack)||e.stack,d=(n||"Generic Error")+": "+o,f=c+" - "+r+":"+s+":"+l+" "+a+" "+i;console.log("report error",d,f),u("JavaScript Error (Service Worker)",{props:{[d]:f}})}catch(e){console.error("reporting error failed",e)}}self.addEventListener("error",e=>t(e.error,e)),self.addEventListener("unhandledrejection",e=>t(e.reason));const a="gawvertretung-v1",e="##empty##"
/*!
default-plan-path
*/,i=[]
/*!
plan-paths
*/,r=["/assets/style/main.css","/assets/js/substitutions.js","/assets/js/timetables.js","/assets/ferien/style.css","/assets/ferien/script.js"];self.addEventListener("install",e=>{e.waitUntil(caches.open(a).then(n=>Promise.all([Promise.all(i.map(t=>fetch(t+"?all&sw").then(e=>n.put(t,e))))])))}),self.addEventListener("activate",e=>{e.waitUntil(caches.open(a).then(n=>{n.keys().then(e=>Promise.all(e.map(e=>{var t=new URL(e.url);if(!r.includes(t.pathname)&&!i.includes(t.pathname))return console.log("cache: delete old",e),n.delete(e)})))}))}),self.addEventListener("fetch",o=>{const n=new URL(o.request.url);"/"===n.pathname?e:i.includes(n.pathname)?o.respondWith(new Promise((e,t)=>{fetch(o.request).then(t=>{e(t.clone()),caches.open(a).then(e=>e.put(n.pathname,t))},t)}).catch(()=>caches.open(a).then(e=>e.match(n.pathname,{ignoreSearch:!0}).then(e=>e||Promise.reject("no-match"))))):r.includes(n.pathname)&&o.respondWith(new Promise(n=>caches.open(a).then(t=>t.match(o.request).then(e=>{e?n(e):fetch(o.request).then(async e=>{n(e.clone()),await t.delete(o.request,{ignoreSearch:!0,ignoreVary:!0}).then(e=>console.log("deleted",e,o.request.url)),await t.put(o.request,e)}).catch(()=>{n(t.match(o.request,{ignoreSearch:!0,ignoreVary:!0}))})}))))}),self.addEventListener("push",async e=>{if(e.data){var t=e.data.json();if("generic_message"===t.type)e.waitUntil(self.registration.showNotification(t.title,{body:t.body||"",icon:"android-chrome-512x512.png",badge:"monochrome-96x96.png",lang:"de",data:{type:"generic_message"}}));else{let r=t.plan_id,s=t.affected_groups_by_day;console.log("affectedGroups",s);for(var n of Object.values(s))n.groups=new Set(n.groups);let l=Date.now()/1e3;e.waitUntil(self.registration.getNotifications().then(e=>{for(var n of e)if(n.data&&n.data.plan_id===r){for(let[t,e]of Object.entries(n.data.affected_groups_by_day))console.log("expiryTime, currentTimestamp:",t,l),t>l&&(console.log("add",e.groups),t in s?e.groups.forEach(e=>s[t].groups.add(e)):(e.groups=new Set(e.groups),s[t]=e));n.close()}for(var t of Object.values(s))t.groups=Array.from(t.groups);let o,a;if(1===Object.keys(s).length){let e=Object.values(s)[0];o=e.name+": Neue Vertretungen",a=e.groups.join(", ")}else{o="Neue Vertretungen",a="";for(var i of Object.values(s))a+=i.name+": "+i.groups.join(", ")+"\n"}e={body:a,icon:"android-chrome-512x512.png",badge:"monochrome-96x96.png",lang:"de",vibrate:[300,100,400],data:{type:"subs_update",plan_id:r,url:new URL("/"+r+"/?source=Notification",self.location.origin).href,affected_groups_by_day:s}};self.registration.showNotification(o,e),u("Notification",{props:{[r]:"Received"}})}))}}else e.waitUntil(Promise.all([self.registration.showNotification("Neue Benachrichtigung",{icon:"android-chrome-512x512.png",badge:"monochrome-96x96.png",lang:"de"}),u("Notification",{props:{other:"Received, but without Payload"}})]))}),self.addEventListener("notificationclick",a=>{a.notification.close(),a.notification.data&&"subs_update"===a.notification.data.type&&a.waitUntil(Promise.all([self.clients.matchAll().then(function(e){var t,n=new URL(a.notification.data.url);for(t of e){var o=new URL(t.url);if(o.origin+o.pathname===n.origin+n.pathname&&"focus"in t)return t.focus()}if(self.clients.openWindow)return self.clients.openWindow(a.notification.data.url)}),self.registration.getNotifications().then(e=>{e.forEach(e=>{null!=e.data&&e.data.plan_id===a.notification.data.plan_id&&e.close()})}),u("Notification",{props:{[a.notification.data.plan_id]:"Clicked"}})]))})}();
//# sourceMappingURL=sw.js.map
