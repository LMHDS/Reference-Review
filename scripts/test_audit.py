"""Offline behavioral tests. All test records and approvals are synthetic fixtures."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

import audit as a


SOURCE = {'provider': 'test fixture', 'url': 'https://example.org/paper', 'retrieved_at': '2026-01-01T00:00:00Z'}


def entry():
    e = a.base_entry({'id': 'test-key', 'title': 'Fixture title', 'issued': {'date-parts': [[2023]]}})
    e['candidates'] = [{'source': SOURCE, 'csl': {'type': 'article-journal', 'title': 'Fixture title', 'author': [{'given': 'A', 'family': 'Example'}], 'issued': {'date-parts': [[2024]]}, 'DOI': '10.0000/test', 'URL': 'https://example.org/paper'}}]
    e['selected'] = 0
    return a.stamp(e)


def approval(e):
    return {'id': e['id'], 'decision': 'approve', 'evidence_hash': e['evidence_hash'], 'reviewer': 'SYNTHETIC TEST ONLY', 'reviewed_at': a.now(), 'scope': 'bibliography', 'identity_checked': True, 'metadata_checked': True, 'limitations_acknowledged': True, 'note': '', 'format_checked': True, 'keywords_checked': True}




class AuditTests(unittest.TestCase):
    def test_metadata_difference_preserves_input(self):
        e = entry()
        self.assertEqual(e['original']['issued']['date-parts'][0][0], 2023)
        self.assertEqual(next(d for d in e['metadata_diff'] if d['field'] == 'issued')['status'], 'differs')

    def test_pending_export_is_empty(self):
        with tempfile.TemporaryDirectory() as td:
            run = a.new_audit('test'); run['entries'] = [entry()]
            src, out = Path(td)/'audit.json', Path(td)/'out.json'
            a.save(src, run)
            subprocess.run([sys.executable, str(Path(a.__file__)), 'export', str(src), '--out', str(out)], check=True, capture_output=True)
            self.assertEqual(a.read(out), [])

    def test_explicit_bibliography_approval_allowed(self):
        e = entry()
        self.assertEqual(a.approval_errors(e, approval(e)), [])

    def test_unselected_candidate_blocked(self):
        e = entry(); e['selected'] = None; a.stamp(e)
        self.assertTrue(a.approval_errors(e, approval(e)))

    def test_missing_source_blocked(self):
        e = entry(); e['candidates'][0]['source'] = {}; a.stamp(e)
        self.assertTrue(a.approval_errors(e, approval(e)))

    def test_stale_approval_blocked(self):
        e = entry(); d = approval(e); e['candidates'][0]['csl']['title'] = 'Other work'; a.stamp(e)
        self.assertIn('stale or changed evidence', a.approval_errors(e, d))





    def test_integrity_notice_needs_disposition(self):
        e = entry(); e['integrity']['status'] = 'notice_found'; a.stamp(e)
        d = approval(e); self.assertTrue(a.approval_errors(e, d))
        d['note'] = 'Synthetic test: cited specifically to discuss the notice.'
        self.assertEqual(a.approval_errors(e, d), [])

    def test_error_is_not_fabrication(self):
        class Broken:
            def crossref(self, **kwargs):
                raise ValueError('http_429')
        e = a.resolve({'id': 'x', 'DOI': '10.0000/test'}, Broken(), True)
        self.assertEqual(e['identity']['status'], 'lookup_error')
        self.assertEqual(e['human']['decision'], 'pending')

    def test_title_search_never_selects_first_result(self):
        class Search:
            def crossref(self, *args, **kwargs):
                return {'items': [{'title': ['Fixture title'], 'DOI': '10.0000/test'}]}, SOURCE
        e = a.resolve({'id': 'x', 'title': 'Fixture title'}, Search(), True)
        self.assertIsNone(e['selected'])
        self.assertEqual(e['identity']['status'], 'candidates_only')

    def test_arxiv_keeps_version_and_separates_publication_doi(self):
        xml = '<feed xmlns="http://www.w3.org/2005/Atom" xmlns:ar="http://arxiv.org/schemas/atom"><entry><id>http://arxiv.org/abs/2401.00001v2</id><title>Fixture</title><published>2024-01-01</published><author><name>A Example</name></author><ar:doi>10.0000/journal</ar:doi></entry></feed>'
        c = a.arxiv_candidates(ET.fromstring(xml), SOURCE)[0]
        self.assertEqual(c['version'], '2401.00001v2')
        self.assertNotIn('DOI', c['csl'])
        self.assertEqual(c['related_published_doi'], '10.0000/journal')

    def test_arxiv_datacite_doi_routes_to_arxiv(self):
        class ArxivOnly:
            def arxiv(self, params):
                self.query = params
                return ET.fromstring('<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/abs/2401.00001v2</id><title>Fixture</title><published>2024-01-01</published></entry></feed>'), SOURCE
            def crossref(self, *args, **kwargs):
                raise AssertionError('Known arXiv DOI should not be routed to Crossref')
        fetcher=ArxivOnly()
        e=a.resolve({'id':'test','DOI':'https://doi.org/10.48550/arXiv.2401.00001'},fetcher,False)
        self.assertEqual(fetcher.query,{'id_list':'2401.00001'})
        self.assertEqual(e['identity']['status'],'identifier_resolved')

    def test_duplicates_flagged_not_deleted(self):
        x,y = entry(),entry(); y['id']='other'; y['original']['id']='other'
        records=[x,y]; a.duplicates(records)
        self.assertEqual(len(records),2)
        self.assertEqual(y['duplicate_of'][0]['id'], x['id'])

    def test_render_escapes_script_injection(self):
        with tempfile.TemporaryDirectory() as td:
            e = entry(); e['original']['raw'] = '</script><script>alert(1)</script>'; a.stamp(e)
            run=a.new_audit('test'); run['entries']=[e]
            dest=Path(td)/'review.html'; a.render(run,dest)
            self.assertNotIn('</script><script>alert(1)</script>', dest.read_text())
            self.assertIn('\\u003c/script\\u003e', dest.read_text())

    def test_input_keys_and_raw_text_retained(self):
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/'refs.txt'; src.write_text('10.0000/example\nDoe, J. (2024). Some title. Some journal.\n')
            values,document=a.load_input(src)
            self.assertEqual(values[0]['DOI'],'10.0000/example')
            self.assertEqual(values[1]['raw'],document.splitlines()[1])
            self.assertNotIn('title',values[1])

    def test_review_round_trip_and_changed_keywords_invalidates(self):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td); run=a.new_audit('test'); e=entry(); run['entries']=[e]
            src=folder/'audit.json'; dec=folder/'decisions.json'; reviewed=folder/'reviewed.json'; out=folder/'approved.json'
            a.save(src,run); a.save(dec,{'schema_version':2,'run_id':run['run_id'],'decisions':[approval(e)]})
            cmd=[sys.executable,str(Path(a.__file__))]
            subprocess.run(cmd+['merge',str(src),str(dec),'--out',str(reviewed)],check=True,capture_output=True)
            subprocess.run(cmd+['export',str(reviewed),'--out',str(out)],check=True,capture_output=True)
            self.assertEqual(a.read(out)[0]['id'],'test-key')
            patch=folder/'patch.json'; enriched=folder/'enriched.json'
            a.save(patch,{'run_id':run['run_id'],'entries':[{'id':e['id'],'evidence_hash':e['evidence_hash'],'keywords':{'terms':['new topic'],'basis':'agent_title_abstract','source_url':SOURCE['url'],'note':'Synthetic test'}}]})
            subprocess.run(cmd+['enrich',str(reviewed),str(patch),'--out',str(enriched)],check=True,capture_output=True)
            self.assertEqual(a.read(enriched)['entries'][0]['human']['decision'],'pending')
            bad=subprocess.run(cmd+['merge',str(enriched),str(dec),'--out',str(folder/'bad.json')],capture_output=True)
            self.assertNotEqual(bad.returncode,0)
            self.assertFalse((folder/'bad.json').exists())

    def test_crossref_notice_direction_preserved(self):
        class Notices:
            def crossref(self, *args, **kwargs):
                return {'items':[{'DOI':'10.0000/notice','title':['Fixture correction'],'update-to':[{'DOI':'10.0000/test','type':'correction'}]}]}, SOURCE
        result=a.integrity(Notices(),entry()['candidates'][0])
        self.assertEqual(result['status'],'notice_found')
        self.assertEqual(result['evidence'][0]['notices'][0]['DOI'],'10.0000/notice')

    def test_keyword_origin_is_explicit(self):
        e = entry()
        self.assertEqual(e['keywords']['basis'], 'title_terms')
        self.assertEqual(e['keywords']['terms'], ['Fixture', 'title'])
        self.assertEqual(e['keywords']['source_url'], SOURCE['url'])

    def test_format_and_keyword_checks_required(self):
        e = entry(); d = approval(e); d['format_checked'] = False
        self.assertTrue(a.approval_errors(e, d))
        d['format_checked'] = True; d['keywords_checked'] = False
        self.assertTrue(a.approval_errors(e, d))

    def test_previews_use_corrected_metadata_and_keep_keys(self):
        e = entry(); run = a.new_audit('audit'); run['entries'] = [e]
        preview = a.citation_previews(run)['test-key']
        self.assertIn('2024', preview['apa'])
        self.assertNotIn('2023', preview['apa'])
        self.assertIn('test-key', preview['bibtex'])
        self.assertEqual(e['human']['decision'], 'pending')

    def test_old_schema_and_unknown_keywords_rejected(self):
        run = a.new_audit('audit'); run['schema_version'] = 1
        with self.assertRaises(ValueError): a.validate(run)
        run = a.new_audit('audit'); e = entry(); e['keywords']['basis'] = 'verified_fact'; a.stamp(e); run['entries'] = [e]
        with self.assertRaises(ValueError): a.validate(run)

    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'original.json'; a.save(p,{'original':True})
            with self.assertRaises(FileExistsError): a.save(p,{'original':False})
            self.assertTrue(a.read(p)['original'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
