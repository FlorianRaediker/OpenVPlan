!function(){"use strict";function s(e,t=null){try{var n=e.name,s=(null==t?void 0:t.message)||e.message,o=e.description,i=e.number,a=(null==t?void 0:t.filename)||e.fileName,r=(null==t?void 0:t.lineno)||e.lineNumber,l=(null==t?void 0:t.colno)||e.columnNumber,d=(null==t?void 0:t.stack)||e.stack,c=(n||"Generic Error")+": "+s,u=d+" - "+a+":"+r+":"+l+" "+o+" "+i;console.log("report error",c,u),plausible("JavaScript Error",{props:{[c]:u}})}catch(e){console.error("reporting error failed",e)}}window.addEventListener("error",e=>s(e.error,e)),window.addEventListener("unhandledrejection",e=>s(e.reason));const i=window.location.pathname.split("/",2)[1],a=document.getElementById("selectionInput").value,e=document.getElementById("timetables-block");if(e&&(e.hidden=!1),window.location.hash.startsWith("#timetable:"))try{let[,n,s]=window.location.hash.split(":");s=atob(s);let e=!0,o;if(150!==s.length)console.warn("Timetable in URL has wrong length:",s.length,"instead of",150,s),e=!1;else{o=[];for(let n=0;n<5;n++){let t=[];o.push(t);for(let e=0;e<10;e++){var r=s.substr(10*n*3+3*e,3).trim();t.push(r)}}}if(e){let e;try{e=JSON.parse(window.localStorage.getItem(i+"-timetables")),e=e||{}}catch{e={}}n=n.toUpperCase();let t=n in e?"Die aufgerufene URL enthält einen Stundenplan für "+n+". Soll der aktuell gespeicherte Stundenplan für "+n+" durch diesen ersetzt werden?":"Die aufgerufene URL enthält einen Stundenplan für "+n+". Diesen Stundenplan setzen?";if(a){let e=!1;for(var l of a.split(", "))if(l.toUpperCase()===n){e=!0;break}e||(t+=" Achtung: Der Stundenplan wird erst angewendet, wenn "+n+" auch ausgewählt ist.")}else t+=" Achtung: Der Stundenplan wird erst angewendet, wenn Vertretungen ausgewählt sind.";confirm(t)&&(e[n]=o,window.localStorage.setItem(i+"-timetables",JSON.stringify(e))),window.location.hash="",plausible("Timetable: Set From Link")}}catch(e){console.error("Error while retrieving timetable from URL",e),s(e)}let t;try{t=JSON.parse(localStorage.getItem("seen-news"))||[]}catch{t=[]}const n={};let o=!1;for(const R of document.getElementsByClassName("news")){o=!0;const Y=R.dataset.newsId;t.includes(Y)?(R.hidden=!0,n[Y]="hidden"):(R.querySelector(".btn-close").addEventListener("click",()=>{R.hidden=!0,t.push(Y),localStorage.setItem("seen-news",JSON.stringify(t)),plausible("News: Dismiss",{props:{[Y]:"Close"}})}),n[Y]="visible")}o&&plausible("News",{props:n});const d=document.getElementsByClassName("date");function c(){const e=new Date;if(0<d.length&&d[0].innerHTML===e.getDate()+"."+(e.getMonth()+1)+"."+e.getFullYear()){var t,n=e.getHours(),s=e.getMinutes();for(t of[["1",8,35],["2",9,25],["3",10,30],["4",11,15],["5",12,20],["6",13,10],["7",14,35],["8",15,25],["9",16,20],["10",17,5]]){if(!(t[1]<n||t[1]===n&&t[2]<=s)){setTimeout(c,new Date(e.getFullYear(),e.getMonth(),e.getDate(),t[1],t[2]).getTime()-e.getTime());break}for(var o of document.getElementsByClassName("lesson"+t[0]))o.classList.add("grey")}}}c(),window.addEventListener("focus",()=>c());let u;var g,f=document.getElementById("status").textContent;try{if(u=JSON.parse(window.localStorage.getItem(i+"-seen-substitutions")),u.status!==f){var m,h,p,b=Date.now();for(m of Object.keys(u.seenSubstitutions))m<=b&&delete u.seenSubstitutions[m];for([h,p]of Object.entries(u.newSubstitutions))h>b&&(h in u.seenSubstitutions?u.seenSubstitutions[h].push(...p):u.seenSubstitutions[h]=p);u.newSubstitutions={},u.status=f}}catch{}u=u||{seenSubstitutions:{},newSubstitutions:{},status:f};for(g of document.getElementsByClassName("substitutions-box")){var w=g.querySelector(".substitutions-table tbody");if(w){const z=g.querySelector(".date").textContent.trim();var S,[,v,y,k]=z.match(/(\d\d?).(\d\d?).(\d\d\d\d)/),E=Date.UTC(k,y-1,v+1);E in u.seenSubstitutions||(u.seenSubstitutions[E]=[]),E in u.newSubstitutions||(u.newSubstitutions[E]=[]);let n;for(S of w.children){let e=S.querySelector(".group-name");null!=e&&(n=e.textContent.trim());let t=n;for(var L of S.children)L.classList.contains(".group-name")||(t+="#"+L.textContent.trim());u.seenSubstitutions[E].includes(t)||(S.classList.add("new-subs"),u.newSubstitutions[E].includes(t)||u.newSubstitutions[E].push(t))}}}window.localStorage.setItem(i+"-seen-substitutions",JSON.stringify(u));const N=document.getElementById("notifications-toggle");function I(e){for(var t of document.getElementsByClassName("notification-state"))t.hidden=!0;document.querySelector(`.notification-state[data-n="${e}"]`).hidden=!1}function C(e){localStorage.setItem(i+"-notification-state-pa",e)}function O(e,t){return e.pushManager.subscribe({userVisibleOnly:!0,applicationServerKey:function(e){e=(e+"=".repeat((4-e.length%4)%4)).replace(/-/g,"+").replace(/_/g,"/");const t=atob(e),n=new Uint8Array(t.length);for(let e=0;e<t.length;++e)n[e]=t.charCodeAt(e);return n}("BDu6tTwQHFlGb36-pLCzwMdgumSlyj_vqMR3I1KahllZd3v2se-LM25vhP3Yv_y0qXYx_KPOVOD2EYTaJaibzo8")}).then(e=>fetch("api/subscribe-push",{method:"post",headers:{"Content-Type":"application/json"},body:JSON.stringify({subscription:e.toJSON(),selection:a,is_active:t})})).then(e=>{if(!e.ok)throw Error(`Got ${e.status} from server`);return e.json()}).then(e=>{if(!e.ok)throw Error("Got ok: False from server")})}let B;function D(t,e){switch("failed"!==(B=e)&&localStorage.setItem(i+"-notification-state",B),C(e),N.checked="granted-and-enabled"===B,N.disabled="denied"===B,B){case"granted-and-enabled":I("subscribing"),O(t,!0).then(()=>I("enabled")).catch(e=>{D(t,"failed"),s(e)});break;case"denied":I("blocked");break;case"failed":I("failed");break;default:case"default":case"granted-and-disabled":I("disabled")}}window.addEventListener("load",()=>{"serviceWorker"in navigator&&navigator.serviceWorker?(navigator.serviceWorker.ready.then(e=>{var t;function n(){return!B.startsWith(Notification.permission)&&"failed"!==B&&(console.log(B+" changed to "+Notification.permission),D(t,"granted"===Notification.permission?"granted-and-disabled":Notification.permission),!0)}"Notification"in window?"PushManager"in window?(t=e,document.getElementById("notifications-not-available-alert").hidden=!0,document.getElementById("toggle-notifications-wrapper").hidden=!1,B=window.localStorage.getItem(i+"-notification-state"),N.addEventListener("change",()=>{N.checked?(Notification.requestPermission().then(e=>{D(t,"granted"===e?"granted-and-enabled":e)}),plausible("Push Subscription",{props:{[i]:"Subscribe"}})):("granted-and-enabled"===B&&(I("unsubscribing"),O(t,!1).then(()=>{D(t,"granted-and-disabled")}).catch(e=>{D(t,"failed"),s(e)})),plausible("Push Subscription",{props:{[i]:"Unsubscribe"}}))}),B&&"failed"!==B||(B="default"),n()||D(t,B),window.addEventListener("focus",n)):C("unsupported (PushManager)"):C("unsupported (Notification)")}).catch(e=>s(e)),navigator.serviceWorker.register("/sw.js").catch(e=>s(e))):C("unsupported (Service Worker)")});const J=document.getElementById("online-status");let T=null;function x(){J.textContent="Aktuell",J.classList.add("online"),J.classList.remove("offline","updating")}function W(){J.textContent="Offline",J.classList.add("offline"),J.classList.remove("online","updating")}function M(t=null){T=new WebSocket(("http:"===window.location.protocol?"ws:":"wss:")+"//"+window.location.host+window.location.pathname+"api/wait-for-updates"),T.addEventListener("open",e=>{console.log("WebSocket opened",e),x(),t&&t(e.target)}),T.addEventListener("close",e=>{console.log("WebSocket closed",e),W()}),T.addEventListener("message",e=>{var t=JSON.parse(e.data);console.log("WebSocket message",t),"status"===t.type?(e=t.status)&&(e===document.getElementById("status").textContent?x():window.location.reload()):console.warn("Unknown WebSocket message type",t.type)})}function q(){J.textContent="Aktualisiere...",J.classList.add("updating"),J.classList.remove("online","offline"),T.readyState===T.OPEN?T.send(JSON.stringify({type:"get_status"})):M(e=>e.send(JSON.stringify({type:"get_status"})))}M(),window.addEventListener("focus",()=>{console.log("focus, checking for new substitutions"),q()}),window.addEventListener("online",()=>{console.log("online, checking for new substitutions"),q()}),window.addEventListener("offline",()=>{console.log("offline"),W()}),document.getElementById("themes-block").hidden=!1;const A=document.documentElement,U=document.getElementById("themes-system-default"),P=document.getElementById("themes-light"),j=document.getElementById("themes-dark");function _(e){switch(localStorage.setItem("theme",e),e){case"system-default":A.classList.remove("light","dark");break;case"light":A.classList.add("light"),A.classList.remove("dark");break;case"dark":A.classList.add("dark"),A.classList.remove("light")}}switch(localStorage.getItem("theme")){case"light":P.checked=!0;break;case"dark":j.checked=!0}U.addEventListener("change",()=>_("system-default")),P.addEventListener("change",()=>_("light")),j.addEventListener("change",()=>_("dark"));try{let e=localStorage.getItem("theme");"system-default"!==e&&e||(e="system-"+(window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light")),plausible("Features - "+i,{props:{Selection:a?(a.match(/,/g)||[]).length+1:0,Notifications:localStorage.getItem(i+"-notification-state-pa")||"unknown",Theme:e,Timetables:null}})}catch(e){console.error(e),s(e)}function F(e,t){for(var n of e)n.addEventListener("click",t),n.addEventListener("auxclick",t)}function K(e){e=e.split(",");plausible(JSON.parse(e[0]),e[1]?{props:JSON.parse(e[1])}:null)}F(document.querySelectorAll("a[data-pa]"),function(e){let t=e.target;var n="auxclick"===e.type&&2===e.which,s="click"===e.type;for(;t&&(void 0===t.tagName||"a"!==t.tagName.toLowerCase()||!t.href);)t=t.parentNode;(n||s)&&K(t.getAttribute("data-pa"));t.target||e.ctrlKey||e.metaKey||e.shiftKey||!s||(setTimeout(function(){location.href=t.href},150),e.preventDefault())}),F(document.querySelectorAll("button[data-pa]"),function(e){e.preventDefault(),K(e.target.getAttribute("data-pa")),setTimeout(function(){e.target.form.submit()},150)})}();
//# sourceMappingURL=substitutions.js.map
