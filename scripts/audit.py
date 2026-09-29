#!/usr/bin/env python3
"""Reference audit: standard library only; external records are evidence, not verdicts."""
import argparse
import copy
import datetime as dt
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import uuid
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CSL_FIELDS = ('type', 'title', 'author', 'issued', 'container-title', 'volume', 'issue', 'page', 'DOI', 'URL', 'publisher', 'article-number')
DECISIONS = {'pending', 'approve', 'rewrite', 'replace', 'reject'}


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save(path, value):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    # Never silently overwrite a source, previous audit, or decision export.
    with p.open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)


def norm(value):
    return re.sub(r'[^\w]+', '', unicodedata.normalize('NFKC', str(value)).casefold())


def doi(value):
    value = urllib.parse.unquote(str(value or '').strip())
    value = re.sub(r'^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)', '', value, flags=re.I)
    return value.lower()


def arxiv(value):
    m = re.search(r'(?:arxiv:|arxiv\.org/(?:abs|pdf)/)?((?:\d{4}\.\d{4,5}|[a-z.-]+/\d{7})(?:v\d+)?)', str(value), re.I)
    return m.group(1) if m else ''


def year(value):
    try:
        return value['date-parts'][0][0]
    except (KeyError, IndexError, TypeError):
        return None


def plain(value):
    return html.unescape(re.sub('<[^>]+>', '', str(value)))


class Fetcher:
    def __init__(self, cache, offline=False):
        self.cache = Path(cache)
        self.cache.mkdir(parents=True, exist_ok=True)
        self.offline = offline
        self.last = {}

    def get(self, url):
        key = hashlib.sha256(url.encode()).hexdigest()
        meta_path = self.cache / (key + '.json')
        data_path = self.cache / (key + '.body')
        # Offline is explicit. Online audits retrieve fresh integrity data.
        if self.offline:
            if not meta_path.exists() or not data_path.exists():
                raise ValueError('offline_cache_miss')
            meta = read(meta_path)
            data = data_path.read_bytes()
            if hashlib.sha256(data).hexdigest() != meta['sha256']:
                raise ValueError('cache_hash_mismatch')
            return data, {**meta, 'cache_used': True}
        host = urllib.parse.urlsplit(url).hostname
        if host not in {'api.crossref.org', 'export.arxiv.org'}:
            raise ValueError('unsupported_api_host')
        delay = 3.1 if host == 'export.arxiv.org' else 0.25
        time.sleep(max(0, delay - (time.monotonic() - self.last.get(host, 0))))
        contact = os.environ.get('REFCHECK_CONTACT', '').strip()
        req = urllib.request.Request(url, headers={'User-Agent': 'ReferenceVerification/0.1' + (f' (mailto:{contact})' if contact else ''), 'Accept': 'application/json, application/atom+xml'})
        for attempt in range(2):
            self.last[host] = time.monotonic()
            try:
                with urllib.request.urlopen(req, timeout=25) as res:
                    data = res.read(12_000_001)
                    if len(data) > 12_000_000:
                        raise ValueError('api_response_too_large')
                break
            except urllib.error.HTTPError as exc:
                if exc.code in (429, 503) and attempt == 0:
                    wait = exc.headers.get('Retry-After', '4')
                    if wait.isdigit() and int(wait) <= 20:
                        time.sleep(max(delay, int(wait)))
                        continue
                raise ValueError(f'http_{exc.code}') from None
        meta = {'url': url, 'retrieved_at': now(), 'sha256': hashlib.sha256(data).hexdigest(), 'snapshot': data_path.name}
        # Cache is scratch evidence storage; the audit retains its retrieval time/hash.
        data_path.write_bytes(data)
        meta_path.write_text(json.dumps(meta, indent=2), encoding='utf-8')
        return data, meta

    def crossref(self, params=None, identifier=None):
        url = 'https://api.crossref.org/works'
        if identifier:
            url += '/' + urllib.parse.quote(doi(identifier), safe='')
        elif params:
            url += '?' + urllib.parse.urlencode(params)
        raw, source = self.get(url)
        return json.loads(raw)['message'], source

    def arxiv(self, params):
        raw, source = self.get('https://export.arxiv.org/api/query?' + urllib.parse.urlencode(params))
        return ET.fromstring(raw), source


def crossref_candidate(record, source):
    title = record.get('title', [''])
    container = record.get('container-title', [])
    kind = {'journal-article': 'article-journal', 'proceedings-article': 'paper-conference', 'posted-content': 'article', 'book-chapter': 'chapter'}.get(record.get('type'), 'article')
    authors = [{k: v for k, v in author.items() if k in ('given', 'family', 'literal', 'ORCID', 'suffix', 'non-dropping-particle', 'dropping-particle')} for author in record.get('author', [])]
    csl = {'type': kind, 'title': plain(title[0]) if title else '', 'author': authors,
           'issued': record.get('published') or record.get('issued') or {},
           'DOI': record.get('DOI', ''), 'URL': record.get('URL', '')}
    for key in ('volume', 'issue', 'page', 'publisher', 'article-number'):
        if record.get(key):
            csl[key] = record[key]
    if container:
        csl['container-title'] = plain(container[0])
    return {'csl': csl, 'source': {**source, 'provider': 'Crossref'},
            'version': 'publisher-deposited metadata; verify version on landing page',
            'dates': {k: record[k] for k in ('published', 'published-online', 'published-print', 'issued') if k in record},
            'relations': record.get('relation', {}), 'update_to': record.get('update-to', []),
            'abstract': plain(record.get('abstract', ''))}


def arxiv_candidates(root, source):
    ns = {'a': 'http://www.w3.org/2005/Atom', 'ar': 'http://arxiv.org/schemas/atom'}
    result = []
    for e in root.findall('a:entry', ns):
        identifier = e.findtext('a:id', '', ns)
        if '/api/errors' in identifier:
            raise ValueError('arxiv_api_error')
        if not identifier:
            continue
        date = e.findtext('a:published', '', ns)
        authors = [{'literal': a.findtext('a:name', '', ns)} for a in e.findall('a:author', ns)]
        csl = {'type': 'article', 'title': ' '.join(e.findtext('a:title', '', ns).split()), 'author': authors,
               'issued': {'date-parts': [[int(date[:4])]]} if date else {},
               'URL': identifier.replace('http:', 'https:'), 'publisher': 'arXiv'}
        result.append({'csl': csl, 'arxiv_id': arxiv(identifier), 'source': {**source, 'provider': 'arXiv'},
                       'version': arxiv(identifier), 'published': date, 'updated': e.findtext('a:updated', '', ns),
                       'related_published_doi': e.findtext('ar:doi', '', ns),
                       'journal_reference': e.findtext('ar:journal_ref', '', ns),
                       'abstract': ' '.join(e.findtext('a:summary', '', ns).split())})
    return result


def canonical(entry):
    index = entry.get('selected')
    if isinstance(index, int) and not isinstance(index, bool) and 0 <= index < len(entry.get('candidates', [])):
        return entry['candidates'][index]['csl']
    return None


def comparison(original, selected):
    changes = []
    if not selected:
        return changes
    for field in CSL_FIELDS:
        if field == 'URL':
            continue  # Links to preprints and publishers may intentionally differ.
        a, b = original.get(field), selected.get(field)
        if a in (None, '', []) and b in (None, '', []):
            continue
        if field == 'author':
            # Preserve full strings/order; initials and literal names need human interpretation.
            name_keys = ('given', 'family', 'literal', 'suffix', 'non-dropping-particle', 'dropping-particle')
            names = lambda names_list: [{k: norm(v) for k, v in person.items() if k in name_keys and v} for person in (names_list or [])]
            equivalent = names(a) == names(b)
        elif field == 'issued':
            equivalent = year(a) == year(b)
        elif field == 'DOI':
            equivalent = doi(a) == doi(b)
        else:
            equivalent = norm(a) == norm(b)
        state = 'matches' if equivalent else ('missing_in_input' if not a else 'not_in_source' if not b else 'differs')
        changes.append({'field': field, 'input': a, 'source': b, 'status': state})
    return changes


def fingerprint(entry):
    return digest({k: v for k, v in entry.items() if k not in ('human', 'evidence_hash')})


def stamp(entry):
    entry['metadata_diff'] = comparison(entry['original'], canonical(entry))
    csl = canonical(entry) or {}
    entry['formatting'] = {'status': 'not_rendered', 'missing_core_fields': [k for k in ('title', 'author', 'issued', 'type') if not csl.get(k)],
                           'note': 'Field presence only. CSL rendering and venue-specific requirements are separate.'}
    entry['evidence_hash'] = fingerprint(entry)
    return entry


def integrity(fetcher, candidate):
    result = {'status': 'not_checked', 'scope': 'Crossref DOI-linked updates only; not a comprehensive integrity assessment.', 'evidence': []}
    identifier = candidate['csl'].get('DOI')
    if not identifier:
        result['reason'] = 'No publisher DOI in selected metadata; inspect arXiv/publisher notices manually.'
        return result
    try:
        records, source = fetcher.crossref({'filter': f'updates:{identifier}', 'rows': 100})
        notices = [{'title': r.get('title'), 'DOI': r.get('DOI'), 'update_to': r.get('update-to', [])} for r in records.get('items', [])]
        result['evidence'] = [{'source': source, 'notices': notices, 'selected_record_updates_other_works': candidate.get('update_to', [])}]
        result['status'] = 'notice_found' if notices or candidate.get('update_to') else 'no_notice_found'
        result['checked_at'] = source['retrieved_at']
        if records.get('total-results', 0) > len(notices):
            result['truncated'] = True
    except Exception as exc:
        result['status'] = 'lookup_error'
        result['reason'] = type(exc).__name__ + ': ' + str(exc)[:160]
    return result


def base_entry(original):
    return {'id': str(original['id']), 'original': original, 'candidates': [], 'selected': None,
            'identity': {'status': 'unresolved', 'reason': 'No matching record retrieved yet.'},
            'integrity': {'status': 'not_checked', 'scope': 'No source checked'},
            'claims': [], 'extra_sources': [], 'duplicate_of': [], 'errors': [],
            'human': {'decision': 'pending'}}


def load_input(path):
    p = Path(path)
    if p.suffix.lower() == '.json':
        obj = read(p)
        entries = obj if isinstance(obj, list) else obj['entries']
        document = obj.get('original_document') if isinstance(obj, dict) else None
    elif p.suffix.lower() in ('.txt', '.doi'):
        entries = []
        document = p.read_text(encoding='utf-8')
        for line in document.splitlines():
            if not line.strip():
                continue
            text = line.strip()
            record = {'id': f'ref-{len(entries) + 1}', 'raw': text}
            if re.fullmatch(r'(?i)(?:https?://(?:dx\.)?doi\.org/|doi:\s*)?10\.\d{4,9}/\S+', text):
                record['DOI'] = doi(text)
            elif re.fullmatch(r'(?i)(?:https?://arxiv\.org/(?:abs|pdf)/|arxiv:\s*)?(?:\d{4}\.\d{4,5}|[a-z.-]+/\d{7})(?:v\d+)?', text):
                record['arxiv_id'] = arxiv(text)
            entries.append(record)
    else:
        raise ValueError('Parse BibTeX/RIS using citations.cjs first. PDF/manuscript extraction is agent-assisted; see SKILL.md.')
    ids = set()
    for i, entry in enumerate(entries):
        entry['id'] = str(entry.get('id', f'ref-{i + 1}'))
        if entry['id'] in ids:
            raise ValueError('Duplicate reference ID: ' + entry['id'])
        ids.add(entry['id'])
    if not entries:
        raise ValueError('No input references.')
    return entries, document


def resolve(original, fetcher, check_integrity):
    entry = base_entry(original)
    identifier = doi(original.get('DOI', ''))
    aid = original.get('arxiv_id') or (arxiv(original['URL']) if 'arxiv.org/' in original.get('URL', '') else '')
    arxiv_doi = identifier.startswith('10.48550/arxiv.')
    if arxiv_doi:
        aid = identifier.split('10.48550/arxiv.', 1)[1]
    try:
        if identifier and not arxiv_doi:
            record, source = fetcher.crossref(identifier=identifier)
            entry['candidates'] = [crossref_candidate(record, source)]
            entry['selected'] = 0
            entry['identity'] = {'status': 'identifier_resolved', 'reason': 'DOI resolves in Crossref. Check that the title/authors match the intended work.'}
        elif aid:
            root, source = fetcher.arxiv({'id_list': aid})
            entry['candidates'] = arxiv_candidates(root, source)
            matches = [i for i, c in enumerate(entry['candidates']) if (c['arxiv_id'] == aid if re.search(r'v\d+$', aid) else re.sub(r'v\d+$', '', c['arxiv_id']) == aid)]
            if len(matches) == 1:
                entry['selected'] = matches[0]
                entry['identity'] = {'status': 'identifier_resolved', 'reason': 'arXiv identifier resolved; this record describes a preprint version.'}
        else:
            query = original.get('title') or original.get('raw', '')
            if not query:
                raise ValueError('No title, identifier, or raw reference to search.')
            records, source = fetcher.crossref({'query.bibliographic': query, 'rows': 3})
            entry['candidates'] = [crossref_candidate(r, source) for r in records.get('items', [])]
            if entry['candidates']:
                entry['identity'] = {'status': 'candidates_only', 'reason': 'Search results are candidates, not a confirmed identity. Agent/human must compare evidence and select one.'}
        if not entry['candidates']:
            entry['identity']['reason'] = 'No result in the sources checked. This is NOT evidence that the paper is fabricated.'
        if entry['selected'] is not None and check_integrity:
            entry['integrity'] = integrity(fetcher, entry['candidates'][entry['selected']])
    except Exception as exc:
        entry['errors'].append({'operation': 'resolve', 'type': type(exc).__name__, 'message': str(exc)[:180]})
        entry['identity'] = {'status': 'lookup_error', 'reason': 'Source unavailable, no record, or unsupported registry. Do not infer fabrication.'}
    return stamp(entry)


def duplicates(entries):
    for e in entries:
        e['duplicate_of'] = []
    for i, a in enumerate(entries):
        ca = canonical(a) or a['original']
        for b in entries[:i]:
            cb = canonical(b) or b['original']
            same_doi = doi(ca.get('DOI')) and doi(ca.get('DOI')) == doi(cb.get('DOI'))
            same_title = ca.get('title') and norm(ca['title']) == norm(cb.get('title', ''))
            if same_doi or same_title:
                a['duplicate_of'].append({'id': b['id'], 'basis': 'same DOI' if same_doi else 'same normalized title; may be another version'})
    for entry in entries:
        stamp(entry)


def new_audit(mode):
    return {'schema_version': 1, 'run_id': str(uuid.uuid4()), 'created_at': now(), 'mode': mode, 'entries': [],
            'notice': 'Machine evidence is provisional. Only explicit human decisions can enter the reviewed export. Integrity coverage is limited.'}


def approval_errors(entry, decision):
    errors = []
    if decision.get('decision') not in DECISIONS:
        return ['unknown decision']
    if decision.get('evidence_hash') != fingerprint(entry):
        errors.append('stale or changed evidence')
    if decision.get('decision') == 'pending':
        return errors
    if not decision.get('reviewer', '').strip() or not decision.get('reviewed_at'):
        errors.append('reviewer and review time required')
    if decision.get('decision') != 'approve':
        if not decision.get('note', '').strip():
            errors.append('reason required for rewrite/replace/reject')
        return errors
    if canonical(entry) is None:
        errors.append('select an evidenced candidate before approval')
    else:
        source = entry['candidates'][entry['selected']].get('source', {})
        if not source.get('url') or not source.get('retrieved_at'):
            errors.append('selected record lacks source URL or retrieval time')
    if not decision.get('identity_checked') or not decision.get('metadata_checked'):
        errors.append('identity/version and metadata must be reviewed')
    if not decision.get('limitations_acknowledged'):
        errors.append('acknowledge integrity coverage, missing fields and remaining limitations')
    if entry.get('integrity', {}).get('status') == 'notice_found' and not decision.get('note', '').strip():
        errors.append('integrity notice requires explicit written disposition')
    if entry.get('formatting', {}).get('missing_core_fields') and not decision.get('note', '').strip():
        errors.append('missing bibliographic fields require explicit written disposition')
    if entry.get('duplicate_of') and not decision.get('note', '').strip():
        errors.append('duplicate/version candidate requires written disposition')
    if decision.get('scope') not in ('metadata', 'claims'):
        errors.append('approval scope must be metadata or claims')
    if entry.get('claims') and decision.get('scope') != 'claims':
        errors.append('attached manuscript claims must be reviewed; cannot downgrade to metadata-only')
    if decision.get('scope') == 'claims':
        if not entry.get('claims'):
            errors.append('no claims supplied')
        if not decision.get('claims_checked'):
            errors.append('claim review attestation missing')
        confirmed = set(decision.get('confirmed_claim_ids', []))
        for claim in entry.get('claims', []):
            if claim['id'] not in confirmed:
                errors.append('unconfirmed claim: ' + claim['id'])
            ev = claim.get('evidence', [])
            if claim.get('assessment') not in ('supported', 'human_supported') or not any(x.get('url') and x.get('locator') and x.get('excerpt') and x.get('retrieved_at') for x in ev):
                errors.append('claim needs supported assessment and located source evidence: ' + claim['id'])
    return errors


def validate(audit):
    if audit.get('schema_version') != 1:
        raise ValueError('Unsupported audit schema.')
    ids = set()
    for entry in audit['entries']:
        if entry['id'] in ids:
            raise ValueError('Duplicate entry ID.')
        ids.add(entry['id'])
        if entry.get('evidence_hash') != fingerprint(entry):
            raise ValueError('Changed evidence for ' + entry['id'] + '; use enrich to update and invalidate approvals.')
        if entry.get('selected') is not None and canonical(entry) is None:
            raise ValueError('Invalid candidate selection.')
        human = entry.get('human', {})
        if human.get('decision') != 'pending':
            problems = approval_errors(entry, human)
            if problems:
                raise ValueError(entry['id'] + ': ' + '; '.join(problems))


def render(audit, output):
    validate(audit)
    # JSON cannot terminate the script element; UI inserts all external strings with textContent.
    payload = json.dumps(audit, ensure_ascii=False).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    template = (ROOT / 'assets/review.html').read_text(encoding='utf-8')
    p = Path(output)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf-8') as f:
        f.write(template.replace('AUDIT_JSON_PLACEHOLDER', payload))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='cmd', required=True)
    for command in ('audit', 'discover'):
        p = sub.add_parser(command)
        p.add_argument('input', help='Input file, or research query for discover')
        p.add_argument('--out', required=True)
        p.add_argument('--cache', required=True)
        p.add_argument('--offline', action='store_true')
        if command == 'audit':
            p.add_argument('--skip-integrity', action='store_true')
        else:
            p.add_argument('--provider', choices=['crossref', 'arxiv'], default='crossref')
            p.add_argument('--limit', type=int, default=10)
    for command in ('render', 'enrich', 'merge', 'export', 'validate'):
        p = sub.add_parser(command)
        p.add_argument('audit')
        if command != 'validate':
            p.add_argument('--out', required=True)
        if command in ('enrich', 'merge'):
            p.add_argument('input')
    args = parser.parse_args()
    if args.cmd in ('audit', 'discover'):
        fetcher = Fetcher(args.cache, args.offline)
        audit = new_audit(args.cmd)
        if args.cmd == 'audit':
            entries, document = load_input(args.input)
            audit['input_file'] = str(Path(args.input).name)
            audit['original_document'] = document
            for index, entry in enumerate(entries):
                audit['entries'].append(resolve(entry, fetcher, not args.skip_integrity))
                print(f'{index + 1}/{len(entries)} {entry["id"]}: {audit["entries"][-1]["identity"]["status"]}', flush=True)
        else:
            if not 1 <= args.limit <= 50:
                raise ValueError('Use a discovery batch of 1–50 candidates.')
            audit['query'] = args.input
            if args.provider == 'crossref':
                records, source = fetcher.crossref({'query.bibliographic': args.input, 'rows': args.limit})
                candidates = [crossref_candidate(r, source) for r in records.get('items', [])]
            else:
                root, source = fetcher.arxiv({'search_query': args.input, 'start': 0, 'max_results': args.limit})
                candidates = arxiv_candidates(root, source)
            for index, candidate in enumerate(candidates):
                original = {'id': f'ref-{index + 1}', **copy.deepcopy(candidate['csl'])}
                if candidate.get('arxiv_id'):
                    original['arxiv_id'] = candidate['arxiv_id']
                entry = base_entry(original)
                entry.update(candidates=[candidate], selected=0, identity={'status': 'source_record', 'reason': 'Returned by discovery source. Relevance, identity corroboration, and full-text claims still require review.'})
                entry['discovery'] = {'query': args.input, 'summary_basis': 'abstract_only' if candidate.get('abstract') else 'metadata_only'}
                audit['entries'].append(stamp(entry))
        duplicates(audit['entries'])
        save(args.out, audit)
        print(f'Saved {len(audit["entries"])} records. Human decisions remain pending.')
        return
    audit = read(args.audit)
    validate(audit)
    if args.cmd == 'validate':
        print('Audit structure, evidence hashes, and approval gates valid. This does not independently verify scholarly claims.')
    elif args.cmd == 'render':
        render(audit, args.out)
    elif args.cmd == 'enrich':
        patch = read(args.input)
        if patch.get('run_id') != audit['run_id']:
            raise ValueError('Patch belongs to another audit run.')
        by_id = {e['id']: e for e in audit['entries']}
        for item in patch['entries']:
            entry = by_id[item['id']]
            if item.get('evidence_hash') != entry['evidence_hash']:
                raise ValueError('Stale patch for ' + entry['id'])
            old_record = copy.deepcopy(canonical(entry))
            for k, v in item.items():
                if k in ('id', 'evidence_hash'):
                    continue
                if k not in ('candidates', 'selected', 'identity', 'integrity', 'claims', 'extra_sources', 'discovery'):
                    raise ValueError('Unsupported patch field: ' + k)
                entry[k] = v
            if canonical(entry) != old_record:
                # Never transfer findings about one record to an alternate candidate.
                if 'integrity' not in item:
                    entry['integrity'] = {'status': 'not_checked', 'scope': 'Selected record changed; check notices again.'}
                if 'claims' not in item:
                    for c in entry['claims']:
                        c.update(assessment='not_checked', evidence=[], limitations='Selected record changed; inspect the new source.')
            claim_ids = [c['id'] for c in entry['claims']]
            if len(claim_ids) != len(set(claim_ids)):
                raise ValueError('Duplicate claim IDs.')
            for c in entry['claims']:
                if not c.get('text') or c.get('assessment') not in ('supported', 'human_supported', 'partial', 'not_found', 'contradicted', 'full_text_unavailable', 'not_checked'):
                    raise ValueError('Invalid claim assessment or empty claim text.')
            entry['human'] = {'decision': 'pending'}
            stamp(entry)
        duplicates(audit['entries'])
        # Duplicate links can change untouched records too; invalidate only mismatched approvals.
        for entry in audit['entries']:
            if entry.get('human', {}).get('decision') != 'pending' and entry['human'].get('evidence_hash') != entry['evidence_hash']:
                entry['human'] = {'decision': 'pending'}
        validate(audit)
        save(args.out, audit)
    elif args.cmd == 'merge':
        decisions = read(args.input)
        if decisions.get('run_id') != audit['run_id']:
            raise ValueError('Human decisions belong to another run.')
        by_id = {e['id']: e for e in audit['entries']}
        seen = set()
        for decision in decisions['decisions']:
            if decision['id'] in seen:
                raise ValueError('Duplicate human decision.')
            seen.add(decision['id'])
            entry = by_id[decision['id']]
            problems = approval_errors(entry, decision)
            if problems:
                raise ValueError(entry['id'] + ': ' + '; '.join(problems))
            entry['human'] = decision
        validate(audit)
        save(args.out, audit)
    elif args.cmd == 'export':
        accepted = []
        for entry in audit['entries']:
            if entry['human'].get('decision') == 'approve':
                csl = copy.deepcopy(canonical(entry))
                csl['id'] = entry['id']
                accepted.append(csl)
        save(args.out, accepted)
        print(f'Exported {len(accepted)} human-approved references; {len(audit["entries"]) - len(accepted)} withheld. See audit for metadata-only vs claim-reviewed scope.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'Error: {type(exc).__name__}: {exc}', file=sys.stderr)
        sys.exit(1)
