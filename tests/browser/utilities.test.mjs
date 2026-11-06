import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import test from "node:test";
import {Worker} from "node:worker_threads";
import {operate as entropy} from "../../app/static/js/tools/entropy-engine.js";
import {parseSid} from "../../app/static/js/tools/user-sid-engine.js";
import {inspectMac,normalizeMac} from "../../app/static/js/tools/mac-engine.js";
import {parseUserAgent} from "../../app/static/js/tools/user-agent-engine.js";
import {operate as regex,escapeRegex} from "../../app/static/js/tools/regex-engine.js";
import {operate as cron,parseCron} from "../../app/static/js/tools/cron-engine.js";
import {network,formatIp,ip,operate as cidr,contextMatches} from "../../app/static/js/tools/cidr-engine.js";
import {operate as http} from "../../app/static/js/tools/http-status-engine.js";
import {normalizedPoint,paintStrokes} from "../../app/static/js/tools/signature-engine.js";

// Load only synthetic or read-only fixtures from the checkout.
async function dataset(name) {return JSON.parse(await readFile(new URL("../../app/static/data/"+name+".json",import.meta.url),"utf8"));}

test("byte entropy covers empty, constant, binary and Unicode samples",()=>{
  assert.equal(JSON.parse(entropy({text:""}).output).bits_per_byte,null);
  assert.equal(JSON.parse(entropy({text:"aaaa"}).output).bits_per_byte,0);
  assert.equal(JSON.parse(entropy({text:"ABAB"}).output).bits_per_byte,1);
  assert.equal(JSON.parse(entropy({bytes:Uint8Array.from({length:256},(_,n)=>n)}).output).bits_per_byte,8);
  assert.equal(JSON.parse(entropy({text:"éé"}).output).characters.bits_per_codepoint,0);
});
test("SID labels require full account context",()=>{
  assert.equal(parseSid("S-1-5-21-1-2-3-500").meaning,"Administrator account");
  assert.equal(parseSid("S-1-5-21-1-2-3-513").meaning,"Domain Users group");
  assert.equal(parseSid("S-1-5-999-500").meaning,"Unknown SID");
  assert.equal(parseSid("s-01-005-018").meaning,"Local System");
  for(const source of ["S-1-5-4294967296","S-2-5-18","S-1-281474976710656","S-1-5-1.1"]) assert.throws(()=>parseSid(source));
});
test("MAC formats normalize and local/group flags prevent vendor inference",async()=>{
  for(const source of ["00:15:5d:00:00:01","00-15-5d-00-00-01","0015.5d00.0001","00155d000001"]) assert.equal(normalizeMac(source),"00155D000001");
  const data=await dataset("mac-assignments");
  assert.match(inspectMac("00:15:5D:00:00:01",data).assignment.organization,/Microsoft/i);
  assert.equal(inspectMac("02:11:22:33:44:55",data).assignment,null);
  assert.equal(inspectMac("01:00:5e:00:00:01",data).multicast,true);
  assert.throws(()=>normalizeMac("00:11-22:33:44:55"));
});
test("MAC most-specific assignment wins",()=>{
  const data={entries:[{prefix:"001122",prefix_length:24},{prefix:"0011223",prefix_length:28},{prefix:"001122334",prefix_length:36}]};
  assert.equal(inspectMac("001122334455",data).assignment.prefix_length,36);
});
test("UA precedence, legacy engines, unknowns and explicit baseline",()=>{
  assert.equal(parseUserAgent("Chrome/120.0 Safari/537.36 Edg/121.0").browser,"Edge");
  assert.equal(parseUserAgent("Edge/12.246").engine,"EdgeHTML");
  assert.equal(parseUserAgent("Opera/9.80 Presto/2.12 Version/12.16").version,"12.16");
  assert.equal(parseUserAgent("Opera/9.80 Presto/2.12 Version/12.16").engine,"Presto");
  assert.equal(parseUserAgent("made-up-client").browser,"Unknown");
  assert.equal(parseUserAgent("Chrome/90.0","100").hints.length,1);
  assert.match(parseUserAgent("Windows NT 10.0 Chrome/120.0").os,/indistinguishable/);
});
test("regex templates, literal escaping and UTF16 groups",()=>{
  const literal="a.b+[x]";assert.equal(new RegExp(escapeRegex(literal)).exec(literal)[0],literal);
  assert.equal(JSON.parse(regex({text:"CVE-2026-1234",template:"cve"}).output).matches.length,1);
  const data=JSON.parse(regex({text:"😀 aa",pattern:"(?<word>a+)",flags:"gu"}).output);
  assert.equal(data.matches[0].start_utf16,3);assert.equal(data.matches[0].named_groups.word,"aa");
  assert.equal(JSON.parse(regex({text:"😀",pattern:"(?:)",flags:"gu"}).output).matches.length,2);
  assert.throws(()=>regex({text:"x",pattern:"[",flags:"g"}));
  assert.throws(()=>regex({text:"x",pattern:".",flags:"gg"}));
});
test("regex capture amplification is rejected before output allocation",()=>{
  assert.throws(()=>regex({text:"a".repeat(10000),pattern:"(".repeat(100)+".*"+")".repeat(100),flags:""}),/budget/);
});
test("pathological regex can be terminated off the main thread",async()=>{
  const worker=new Worker(new URL("./regex-worker.mjs",import.meta.url),{execArgv:["--experimental-default-type=module"]});
  const completed=new Promise(resolve=>worker.once("message",resolve));
  worker.postMessage({text:"a".repeat(100000)+"!",pattern:"(a+)+$",flags:""});
  const outcome=await Promise.race([completed,new Promise(resolve=>setTimeout(()=>resolve("timeout"),250))]);
  assert.equal(outcome,"timeout");await worker.terminate();
});
test("IPv4/IPv6 strict parsing, mapped addresses, boundary networks",()=>{
  assert.equal(network("192.0.2.42/24").canonical,"192.0.2.0/24");
  assert.equal(network("0.0.0.0/0").count,4294967296n);
  assert.equal(network("::/0").count,1n<<128n);
  assert.equal(network("2001:0db8:0:0:0:0:0:1/128").canonical,"2001:db8::1/128");
  assert.equal(formatIp(ip("::ffff:192.0.2.1").value,128),"::ffff:c000:201");
  for(const source of ["01.2.3.4","256.1.1.1",":::", "1:2:3:4:5:6:7:8:9","1::2::3","fe80::1%eth0","1.2.3.4/33"]) assert.throws(()=>network(source));
});
test("IP canonical rendering agrees with Python ipaddress fixtures",async()=>{
  const fixtures=JSON.parse(await readFile(new URL("../fixtures/ip-cases.json",import.meta.url),"utf8"));
  for(const item of fixtures){const parsed=network(item.input);assert.equal(parsed.canonical,item.network);assert.equal(formatIp(parsed.end,parsed.bits),item.last);}
});
test("CIDR partial context and corporate membership remain separate",async()=>{
  const asn=await dataset("asn-prefixes"),cloud=await dataset("cloud-prefixes");
  assert.equal(contextMatches(network("1.1.0.0/16"),asn)[0].coverage,"partial input overlap");
  const result=JSON.parse((await cidr({text:"1.1.1.1\n10.10.1.2/24",context:true,datasets:[asn,cloud],comparison:"10.0.0.0/8",corporate:"10.10.0.0/16 Office"})).output);
  assert.deepEqual(result.results[0].offline_context.asn_origins[0].asns,[13335]);
  assert.equal(result.results[1].comparison.comparison_contains_input,true);
  assert.equal(result.results[1].corporate_matches[0].label,"Office");
  assert.equal(result.results[1].classification,"Private");
});
test("cron dialects and exact next instants are explicit",()=>{
  const five=JSON.parse(cron({text:"*/15 0-4 * * *",reference:"2026-01-01T00:00:00Z"}).output);
  assert.equal(five.schedules[0].next[0].utc,"2026-01-01T00:15:00.000Z");
  const six=JSON.parse(cron({text:"*/15 * * * * *",dialect:"seconds",reference:"2026-01-01T00:00:00Z"}).output);
  assert.equal(six.schedules[0].next[0].utc,"2026-01-01T00:00:15.000Z");
  assert.equal(six.schedules[0].next[4].utc,"2026-01-01T00:01:15.000Z");
  assert.throws(()=>parseCron("* * * * * *"));
  assert.throws(()=>parseCron("*/0 * * * *"));
  assert.throws(()=>parseCron("* * * * FUNDAY"));
});
test("cron follows DST gaps and both fold instants in UTC",()=>{
  const gap=JSON.parse(cron({text:"30 2 * * *",zone:"America/New_York",reference:"2025-03-09T00:00:00Z",horizon_days:7}).output);
  assert.equal(gap.schedules[0].next[0].utc,"2025-03-10T06:30:00.000Z");
  const fold=JSON.parse(cron({text:"30 1 * * *",zone:"America/New_York",reference:"2025-11-02T00:00:00Z",horizon_days:7}).output);
  assert.equal(fold.schedules[0].next[0].utc,"2025-11-02T05:30:00.000Z");
  assert.equal(fold.schedules[0].next[1].utc,"2025-11-02T06:30:00.000Z");
});
test("cron day OR semantics and bounded overlap preview",()=>{
  const result=JSON.parse(cron({text:"0 0 1 * MON\n0 0 * * 1",reference:"2026-01-04T23:59:00Z",horizon_days:60}).output);
  assert.equal(result.schedules[0].next[0].utc,"2026-01-05T00:00:00.000Z");
  assert.ok(result.overlaps_among_previewed_executions.length);
  const sparse=JSON.parse(cron({text:"0 0 31 FEB *",reference:"2026-02-01T00:00:00Z",horizon_days:2}).output);
  assert.equal(sparse.schedules[0].next.length,0);
});
test("HTTP glossary preserves duplicates and treats values as data",async()=>{
  const data=await dataset("http-status");
  const result=JSON.parse((await http({text:"HTTP/1.1 403 Forbidden\nX-Frame-Options: DENY\nX-Frame-Options: <script>inert</script>",code:"401 599",dataset:data})).output);
  assert.equal(result.headers.length,2);assert.equal(result.duplicate_header_names[0],"x-frame-options");
  assert.match(result.statuses.find(item=>item.code===599).phrase,/Unknown/);
  assert.match(result.headers[1].value,/<script>/);
});
test("signature coordinates and stroke budgets remain bounded",()=>{
  assert.deepEqual(normalizedPoint(200,-5,100,100),{x:1,y:0});
  assert.throws(()=>normalizedPoint(1,1,0,0));
  assert.throws(()=>paintStrokes({},Array.from({length:51},()=>[]),100,100,"black"));
});
