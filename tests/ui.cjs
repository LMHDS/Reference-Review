// DOM tests only; no browser navigation, network, or real reviewer decisions.
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict');
const {execFileSync}=require('node:child_process');
const root=path.resolve(__dirname,'..');
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'reference-review-ui-'));
try {
const {JSDOM,VirtualConsole}=require('jsdom');
// Build temporary synthetic records with the actual audit renderer, independent of sample datasets.
execFileSync('python3',['-c',`
from pathlib import Path
import sys
sys.path.insert(0, str(Path(sys.argv[1])/'scripts'))
import audit as a
run=a.new_audit('audit')
for index in range(2):
    record={'id':'fixture-'+str(index),'type':'article','title':'Synthetic bibliography fixture '+str(index),'author':[{'given':'Alice','family':'Example'}],'issued':{'date-parts':[[2024]]},'URL':'https://example.org/fixture'}
    entry=a.base_entry(dict(record))
    entry['candidates']=[{'csl':record,'source':{'provider':'Synthetic fixture','url':record['URL'],'retrieved_at':'2026-01-01T00:00:00Z'},'version':'Synthetic test only'}]
    entry['selected']=0
    entry['keywords']={'terms':['fixture topic'],'basis':'agent_title_abstract','source_url':record['URL'],'note':'Synthetic keyword fixture'}
    run['entries'].append(a.stamp(entry))
a.render(run, Path(sys.argv[2])/'review.html')
`,root,dir],{stdio:'pipe'});
const raw=fs.readFileSync(path.join(dir,'review.html'),'utf8');
const errors=[],vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(e.message));
const dom=new JSDOM(raw,{runScripts:'dangerously',url:'https://test.invalid/',virtualConsole:vc});const doc=dom.window.document;
assert.equal(doc.querySelectorAll('#list button').length,2);
const audit=JSON.parse(doc.getElementById('auditData').textContent);
assert.equal(audit.schema_version,2);
assert.match(doc.getElementById('detail').textContent,/BibTeX preview/);
assert.match(doc.getElementById('detail').textContent,/fixture-0/);
assert.match(doc.getElementById('detail').textContent,/2024/);
assert.match(doc.getElementById('detail').textContent,/AI-suggested from title/);
assert.equal(doc.querySelector('#claimsChecked'),null);
assert.equal(doc.querySelector('option[value="rewrite"]'),null);
doc.getElementById('reviewer').value='SYNTHETIC UI TEST';
for(const id of ['identity','metadata','limitations'])doc.getElementById(id).checked=true;
doc.getElementById('action').value='approve';doc.getElementById('record').click();
assert.match(doc.getElementById('feedback').textContent,/Complete the bibliography review checks/);
assert.match(doc.getElementById('summary').textContent,/Approved 0/);
for(const id of ['format','keywords'])doc.getElementById(id).checked=true;
doc.getElementById('record').click();assert.match(doc.getElementById('summary').textContent,/Approved 1/);
doc.getElementById('saveDraft').click();
const saved=JSON.parse(dom.window.localStorage.getItem('reference-review-v2:'+audit.run_id));
assert.equal(saved.decisions[0].scope,'bibliography');assert.equal(saved.decisions[0].format_checked,true);assert.equal(saved.decisions[0].keywords_checked,true);
doc.querySelectorAll('#list button')[1].click();doc.getElementById('action').value='revise';doc.getElementById('note').value='Synthetic test: revise topic tags.';doc.getElementById('record').click();assert.match(doc.getElementById('summary').textContent,/Decisions 2/);
doc.getElementById('search').value='unmatched-synthetic-query';doc.getElementById('search').dispatchEvent(new dom.window.Event('input'));assert.equal(doc.querySelectorAll('#list button').length,0);
assert.deepEqual(errors,[]);dom.window.close();
console.log('DOM tests passed: citation/keyword preview, bibliography gate, decisions, draft persistence, correction request, search. No visual layout test.');

} finally { fs.rmSync(dir,{recursive:true,force:true}); }
