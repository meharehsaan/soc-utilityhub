const RULES=[["Edge",/Edge\/([\d.]+)/,"EdgeHTML"],["Opera",/Opera\/.*Presto\/.*Version\/([\d.]+)/,"Presto"],["Edge",/Edg(?:A|iOS)?\/([\d.]+)/,"Blink"],["Opera",/OPR\/([\d.]+)/,"Blink"],["Firefox",/(?:Firefox|FxiOS)\/([\d.]+)/,"Gecko"],["Chrome",/(?:Chrome|CriOS)\/([\d.]+)/,"Blink"],["Safari",/Version\/([\d.]+).*Safari\//,"WebKit"]];
// Parse common claimed markers while preserving unknown and spoofable fields.
export function parseUserAgent(source,baseline="") {
  if(source.length>8192) throw new Error("Strings are limited to 8,192 characters.");
  const match=RULES.map(([name,pattern,engine])=>({name,match:pattern.exec(source),engine})).find(item=>item.match);
  let os="Unknown",device="Unknown",m;
  if(/Windows NT 10\.0/.test(source)) os="Windows NT 10.0 family (Windows 10/11 indistinguishable)";
  else if((m=/Windows NT ([\d.]+)/.exec(source))) os="Windows NT "+m[1];
  else if((m=/Android ([\d.]+)/.exec(source))) os="Android "+m[1];
  else if((m=/(?:CPU (?:iPhone )?OS|iPhone OS) ([\d_]+)/.exec(source))) os="iOS "+m[1].replaceAll("_",".");
  else if((m=/Mac OS X ([\d_]+)/.exec(source))) os="macOS "+m[1].replaceAll("_",".");
  else if(/Linux/.test(source)) os="Linux";
  if(/iPad|Tablet/.test(source)||/Android/.test(source)&&!/Mobile/.test(source)) device="Tablet-like";
  else if(/Mobile|iPhone/.test(source)) device="Mobile-like";
  else if(/Windows|Macintosh|X11/.test(source)) device="Desktop-like";
  if(baseline&&!/^\d{1,6}$/.test(baseline)) throw new Error("Baseline must be a numeric major version.");
  const hints=match&&baseline&&Number(match.match[1].split(".")[0])<Number(baseline)?["Below your supplied major-version baseline."]:[];
  const markers=source.match(/bot|crawler|spider|headless|curl|wget|python-requests|scrapy|selenium/ig)??[];
  return {source,browser:match?.name??"Unknown",version:match?.match[1]??null,engine:/iPhone|iPad/.test(source)&&match?"WebKit-like iOS UA (unverified)":match?.engine??"Unknown",os,device,bot_like_markers:[...new Set(markers.map(item=>item.toLowerCase()))],hints};
}
// Inspect bounded UA lines without remote version or identity lookups.
export function operate({text,baseline=""}) {
  const lines=text.split(/\r?\n/).filter(Boolean);
  if(lines.length>200) throw new Error("Use at most 200 strings.");
  return {output:JSON.stringify(lines.map(line=>parseUserAgent(line,baseline)),null,2),meta:{values:lines.length,rules:"2026-11-11"},warnings:["Spoofable heuristics, not verified browser/bot identity. Outdated hints use only your supplied baseline."]};
}
