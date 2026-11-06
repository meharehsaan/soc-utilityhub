// Normalize complete 48-bit notation without accepting mixed separators.
export function normalizeMac(source) {
  if(!/^(?:[0-9a-f]{12}|(?:[0-9a-f]{2}:){5}[0-9a-f]{2}|(?:[0-9a-f]{2}-){5}[0-9a-f]{2}|(?:[0-9a-f]{4}\.){2}[0-9a-f]{4})$/i.test(source.trim())) throw new Error("Use a complete 48-bit MAC address.");
  return source.trim().replace(/[:.-]/g,"").toUpperCase();
}
// Match the longest assignment without asserting hardware identity.
export function inspectMac(source,data) {
  const hex=normalizeMac(source),first=parseInt(hex.slice(0,2),16),local=Boolean(first&2),multicast=Boolean(first&1);
  const assignment=data.entries.filter(item=>hex.startsWith(item.prefix.toUpperCase())).sort((a,b)=>b.prefix_length-a.prefix_length)[0]??null;
  return {source,normalized:hex.match(/../g).join(":"),locally_administered:local,multicast,assignment:local||multicast?null:assignment,context:local?"Local/random assignment; vendor not inferred":multicast?"Group address; vendor not inferred":assignment?"IEEE assignment holder; hardware identity unverified":"Unknown in partial snapshot"};
}
// Load the attributed offline snapshot only when requested.
export async function operate({text,dataset=null}) {
  const data=dataset??await(await fetch("/static/data/mac-assignments.json")).json();
  const lines=text.split(/\r?\n/).map(item=>item.trim()).filter(Boolean);
  if(lines.length>1000) throw new Error("Use at most 1,000 MAC addresses.");
  const rows=lines.map(source=>{try{return inspectMac(source,data);}catch(error){return {source,error:error.message};}});
  return {output:JSON.stringify({results:rows,dataset:{version:data.version,retrieved_on:data.retrieved_on,partial:data.partial,coverage:data.coverage,sources:data.sources}},null,2),meta:{values:rows.length},warnings:["Partial reference data; absence does not establish an unassigned address."]};
}
