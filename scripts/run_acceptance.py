#!/usr/bin/env python3
"""Replay saved, externally sourced records; no new network verification is implied."""
import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys
import audit

ROOT=Path(__file__).resolve().parents[1]

def run(*args):
    subprocess.run(args,check=True,cwd=ROOT,stdout=subprocess.PIPE,text=True)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',required=True,help='New output directory')
    args=p.parse_args(); out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=False)
    sources=audit.read(ROOT/'examples/source-records.json'); results={}
    for topic,count in [('sparse-attention',10),('kv-cache-quantization',10),('small-reference-list',5)]:
        data=audit.read(ROOT/'examples'/f'{topic}.json'); initial=audit.new_audit('acceptance-replay')
        patch={'run_id':initial['run_id'],'entries':[]}
        for item in data['entries']:
            original=copy.deepcopy(item['original']);e=audit.stamp(audit.base_entry(original));initial['entries'].append(e)
            source=sources[item['source_key']]
            csl={'type':'article','title':source['title'],'author':[{'given':' '.join(n.split()[:-1]),'family':n.split()[-1]} for n in source['authors']], 'issued':{'date-parts':[[source['year']]]},'publisher':'arXiv','URL':'https://arxiv.org/abs/'+source['arxiv_id']}
            if source.get('doi'):csl['DOI']=source['doi']
            candidate={'csl':csl,'arxiv_id':source['arxiv_id'],'version':source['version']+'; preprint, original submission year; not merged with a proceedings edition', 'source':{'provider':'arXiv primary page via agent web retrieval (saved snapshot)', 'url':source['source_url'],'retrieved_at':source['retrieved_at'],'retrieval_method':source['retrieval_method']}}
            patch['entries'].append({'id':e['id'],'evidence_hash':e['evidence_hash'],'candidates':[candidate],'selected':0,'identity':{'status':'evidence_matched','reason':'Source title, full author order, arXiv ID, and original year were read from the primary page. This run replays that evidence; it is not a fresh API lookup.'},'integrity':{'status':'not_checked','scope':'No comprehensive retraction/correction search in this acceptance dataset. Inspect publisher and arXiv notices.'},'discovery':{'relevance':item['relevance'],'summary_basis':'agent selection note from title/abstract; not full-text claim verification','name_segmentation':'Given/family split inferred from source full names; human review required.'},'keywords':{'terms':item['keywords'],'basis':'agent_title_abstract','source_url':source['source_url'],'note':'Curated topic tags inferred from the sourced title/abstract; not publisher-supplied keywords.'}})
        initial_path=out/f'{topic}.initial.json';patch_path=out/f'{topic}.patch.json';final_path=out/f'{topic}.audit.json'
        audit.save(initial_path,initial);audit.save(patch_path,patch)
        run(sys.executable,'scripts/audit.py','enrich',str(initial_path),str(patch_path),'--out',str(final_path))
        result=audit.read(final_path);audit.validate(result)
        assert len(result['entries'])==count
        assert all(e['human']['decision']=='pending' for e in result['entries'])
        run(sys.executable,'scripts/audit.py','render',str(final_path),'--out',str(out/f'{topic}.review.html'))
        export_path=out/f'{topic}.approved.json'
        run(sys.executable,'scripts/audit.py','export',str(final_path),'--out',str(export_path))
        assert audit.read(export_path)==[], 'Pending records leaked into reviewed export'
        assert all(e['keywords']['terms'] and e['keywords']['source_url'] for e in result['entries'])
        previews=audit.citation_previews(result)
        assert len(previews)==count and all(v['apa'] and v['bibtex'] for v in previews.values())
        results[topic]={'records':count,'sourced_identity_records':count,'human_pending':count,'human_approved':0,'exported':0,'keyword_sets':count,'citation_preview_pairs':count}
        if topic=='small-reference-list':
            by={e['id']:e for e in result['entries']}
            for key,field,status in [('var-wrong-year','issued','differs'),('sparse-wrong-title','title','differs'),('kivi-missing-author','author','missing_in_input')]:
                assert any(d['field']==field and d['status']==status for d in by[key]['metadata_diff'])
            assert by['kivi-duplicate']['duplicate_of'][0]['id']=='kivi-missing-author'
            assert all(d['status']=='matches' for d in by['longformer-clean']['metadata_diff'])
            results[topic]['checks']=['wrong year detected','wrong title detected','missing author detected','duplicate detected','clean control unchanged']
    # Test parser/formatter behavior using a clearly synthetic record, never as human approval.
    fixture=out/'synthetic.bib';fixture.write_text('@misc{synthetic_key, title={{KV} Test: {Nested {Braces}}}, author={Example, Alice and Test, Bob}, year={2024}}\n')
    run('node','scripts/citations.cjs','parse',str(fixture),str(out/'synthetic.parsed.json'))
    parsed=audit.read(out/'synthetic.parsed.json')['entries'];assert parsed[0]['id']=='synthetic_key' and len(parsed[0]['author'])==2
    audit.save(out/'synthetic.csl.json',parsed)
    for fmt in ('bibtex','ris','apa'):
        suffix={'bibtex':'bib','ris':'ris','apa':'txt'}[fmt]
        target=out/f'synthetic.roundtrip.{suffix}'
        run('node','scripts/citations.cjs','format',str(out/'synthetic.csl.json'),str(target),'--format',fmt)
        assert target.stat().st_size>0
        if fmt!='apa':
            dest=out/f'synthetic.{fmt}.parsed.json';run('node','scripts/citations.cjs','parse',str(target),str(dest))
            entry=audit.read(dest)['entries'][0];assert len(entry['author'])==2 and audit.year(entry['issued'])==2024
    audit.save(out/'results.json',{'status':'passed','tested_at':audit.now(),'mode':'offline replay of separately retrieved primary-page metadata','datasets':results,'format_checks':['BibTeX nested braces and key','BibTeX/RIS author/year roundtrip','APA rendered'],'limits':['No human approval supplied','No live native API acceptance in this environment','No comprehensive integrity search','DOM tests do not establish visual layout quality']})
    print(json.dumps(results,indent=2));print('Acceptance passed. Real references remain pending human review.')

if __name__=='__main__':main()
