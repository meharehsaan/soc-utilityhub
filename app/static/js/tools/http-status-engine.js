// Inspect supplied status lines and headers without making HTTP requests.
export async function operate({text,code="",dataset=null}) {
  if(text.length>100000||code.length>1000) throw new Error("Use a header sample under 100,000 characters.");
  const data=dataset??await(await fetch("/static/data/http-status.json")).json();
  const codes=code.split(/[,\s]+/).filter(Boolean);
  const headers=[],unparsed=[];
  for(const [index,line] of text.split(/\r?\n/).entries()) {
    if(!line) continue;
    const status=/^HTTP\/[\d.]+\s+(\d{3})(?:\s|$)/i.exec(line);
    if(status){codes.push(status[1]);continue;}
    const match=/^([!#$%&'*+.^_|~0-9A-Za-z-]+):[ \t]*(.*)$/.exec(line);
    if(match) headers.push({name:match[1],value:match[2],line:index+1,glossary:data.headers.find(item=>item.name.toLowerCase()===match[1].toLowerCase())??null});
    else unparsed.push({line:index+1,text:line});
    if(headers.length+unparsed.length>1000) throw new Error("Use at most 1,000 header lines.");
  }
  if(codes.length>100||codes.some(item=>!/^[1-5]\d{2}$/.test(item))) throw new Error("Use at most 100 three-digit codes from 100 to 599.");
  const statuses=[...new Set(codes)].map(item=>data.statuses.find(status=>status.code===Number(item))??{code:Number(item),phrase:"Unknown in bundled glossary"});
  const duplicates=[...new Set(headers.map(item=>item.name.toLowerCase()))].filter(name=>headers.filter(item=>item.name.toLowerCase()===name).length>1);
  return {output:JSON.stringify({statuses,headers,unparsed,duplicate_header_names:duplicates,security_header_reference:data.headers,cache_rules:data.cache_rules,reference:{version:data.version,retrieved_on:data.retrieved_on,coverage:data.coverage,sources:data.sources}},null,2),meta:{statuses:statuses.length,headers:headers.length},warnings:["Offline glossary only. Duplicate headers are retained; policy precedence depends on the header and client. Header presence is not proof of correct configuration. Cache eligibility depends on method, directives, authentication, and context."]};
}
