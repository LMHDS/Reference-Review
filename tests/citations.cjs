// Temporary synthetic fixtures; no network requests or bundled paper lists.
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict');
const {execFileSync}=require('node:child_process');
const script=path.resolve(__dirname,'../scripts/citations.cjs');
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'reference-review-citations-'));
const file=name=>path.join(dir,name);
const run=(...args)=>execFileSync(process.execPath,[script,...args],{stdio:'pipe'});
try {
 fs.writeFileSync(file('input.bib'),'@misc{synthetic-key, title={{ABC} Test: {Nested {Braces}}}, author={Example, Alice and Test, Bob}, year={2024}}\n');
 run('parse',file('input.bib'),file('parsed.json'));
 const entries=JSON.parse(fs.readFileSync(file('parsed.json'),'utf8')).entries;
 assert.equal(entries.length,1);assert.equal(entries[0].id,'synthetic-key');assert.equal(entries[0].author.length,2);
 fs.writeFileSync(file('records.json'),JSON.stringify(entries));
 for(const format of ['bibtex','ris','apa']){
  const target=file('output.'+({bibtex:'bib',ris:'ris',apa:'txt'}[format]));
  run('format',file('records.json'),target,'--format',format);
  const text=fs.readFileSync(target,'utf8');assert.ok(text.includes('2024'));
  if(format==='bibtex')assert.match(text,/@misc\{synthetic-key,/);
  if(format!=='apa'){
   const parsed=file(format+'.json');run('parse',target,parsed);
   const record=JSON.parse(fs.readFileSync(parsed,'utf8')).entries[0];
   assert.equal(record.author.length,2);assert.equal(record.issued['date-parts'][0][0],2024);
   assert.match(record.title,/ABC/);assert.match(record.title,/Nested/);
  }
 }
 run('preview',file('records.json'),file('preview.json'));
 const preview=JSON.parse(fs.readFileSync(file('preview.json'),'utf8'))['synthetic-key'];
 assert.equal(preview.bibtex,fs.readFileSync(file('output.bib'),'utf8'));
 assert.equal(preview.apa,fs.readFileSync(file('output.txt'),'utf8'));
 console.log('Citation parsing, key preservation, BibTeX/RIS roundtrips and preview/export consistency passed.');
} finally {fs.rmSync(dir,{recursive:true,force:true});}
