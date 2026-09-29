#!/usr/bin/env node
// Local parsing/formatting only. No identifier resolver plugin is loaded.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { Cite, plugins } = require('@citation-js/core');
require('@citation-js/plugin-bibtex');
require('@citation-js/plugin-csl');
require('@citation-js/plugin-ris');

const [command, input, output, ...args] = process.argv.slice(2);
function write(file, value) {
  fs.mkdirSync(path.dirname(path.resolve(file)), { recursive: true });
  fs.writeFileSync(file, value, { flag: 'wx' });
}
try {
  if (!input || !output) throw new Error('Usage: node citations.cjs parse INPUT OUTPUT.json | format approved.csl.json OUTPUT --format bibtex|ris|apa|csl --style PATH.csl');
  const raw = fs.readFileSync(input, 'utf8');
  if (command === 'parse') {
    const ext = path.extname(input).toLowerCase();
    if (!['.bib', '.ris', '.json'].includes(ext)) throw new Error('Use .bib, .ris, or CSL .json. Plain text is handled by audit.py.');
    const parsed = new Cite(ext === '.json' ? JSON.parse(raw) : raw).data;
    const seen = new Set();
    const records = parsed.map((csl, index) => {
      const id = String(csl.id || `ref-${index + 1}`);
      if (seen.has(id)) throw new Error(`Duplicate citation key: ${id}; resolve keys before auditing.`);
      seen.add(id);
      return { ...csl, id, _input_file: path.basename(input), _input_sha256: crypto.createHash('sha256').update(raw).digest('hex') };
    });
    write(output, JSON.stringify({ entries: records, original_document: raw, parser: 'Citation.js', source_file: path.basename(input) }, null, 2));
    console.log(`Parsed ${records.length} references. This does not verify them.`);
  } else if (command === 'format') {
    const fmt = args.includes('--format') ? args[args.indexOf('--format') + 1] : 'bibtex';
    const entries = JSON.parse(raw);
    if (!Array.isArray(entries)) throw new Error('Expected CSL array exported by audit.py export.');
    const cite = new Cite(entries);
    let result;
    if (['bibtex', 'ris'].includes(fmt)) result = cite.format(fmt);
    else {
      let template = 'apa';
      if (fmt === 'csl') {
        const style = args[args.indexOf('--style') + 1];
        if (!args.includes('--style') || !style) throw new Error('Custom formatting requires --style FILE.csl.');
        const xml = fs.readFileSync(style, 'utf8');
        if (xml.includes('rel="independent-parent"')) throw new Error('Supply the independent parent CSL style, not a dependent style.');
        plugins.config.get('@csl').templates.add('requested', xml);
        template = 'requested';
      } else if (fmt !== 'apa') throw new Error('Supported formats: bibtex, ris, apa, csl.');
      result = cite.format('bibliography', { format: 'text', template, lang: 'en-US' });
    }
    write(output, result);
    console.log(`Formatted ${entries.length} records with Citation.js (${fmt}). Formatting does not verify claims.`);
  } else throw new Error('Unknown command.');
} catch (error) { console.error(error.message); process.exitCode = 1; }
