// node --test scripts/todo/__tests__/migration.test.mjs
// Covers the three changes image-ocean2's migrate-monolith.mjs makes to the coffee-explorer
// reference: an archivable preamble (heading null), absolute line numbers in archive comments,
// and a split section whose heading line travels with the first range.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { applyMigration, missingLines, splitSections } from '../migrate-monolith.mjs';

const meta = {
  slug: 'sample', title: 'Sample task', status: 'next', area: 'models', due: null,
  updated: '2026-10-03', owner: 'agent', brief: 'Continue the open work', refs: [], test: null,
  summary: ['**What:** Keep the task.', '**Why:** Preserve history.', '**Next:** Inspect it.'],
};

test('splitSections keeps the preamble as a heading-null section and every source line', () => {
  const source = '# Project TODO\n\n## Open\n- [ ] Keep me\n';
  const sections = splitSections(source);
  assert.equal(sections.length, 2);
  assert.equal(sections[0].heading, null);
  assert.equal(sections[1].startLine, 3);
  assert.equal(sections.map((s) => s.text).join(''), source);
});

test('archive comments carry absolute TODO.md line numbers for preamble and history cuts', () => {
  const source = '# Project TODO\n\nHandoff\n\n## Open\n\n- [x] Finished\n- [ ] Keep me\n';
  const result = applyMigration({
    sections: splitSections(source),
    metas: [{ heading: null, disposition: 'archive' }, { ...meta, heading: '## Open', disposition: 'file', archiveRanges: [[3, 3]] }],
    baseRev: 'abc123',
    archiveBase: '',
  });
  const task = result.files.get('docs/todo/models/sample.md');
  assert.ok(task.includes('- [ ] Keep me'));
  assert.ok(!task.includes('- [x] Finished'));
  assert.match(result.archive, /TODO\.md @ abc123, lines 1-4 -->\n# Project TODO/);
  assert.match(result.archive, /TODO\.md @ abc123, lines 7-7 -->\n- \[x\] Finished/);
  assert.ok(!result.archive.includes('lines 11-11'), 'the section offset must not be added twice');
  assert.match(result.mappingDoc, /preamble before the first heading/);
  assert.deepEqual(missingLines(source, [...result.files.values(), result.archive]), []);
});

test('a split section routes each range to its own task and keeps the heading with the first', () => {
  const source = '# T\n\n## Open\n- [ ] One\n- [ ] Two\n\n';
  const sections = splitSections(source);
  const sub = (slug, lines) => ({ ...meta, slug, title: slug, heading: '## Open', from: true, lines });
  const result = applyMigration({
    sections,
    metas: [{ heading: null, disposition: 'archive' }, { heading: '## Open', disposition: 'split' }, sub('one', [1, 2]), sub('two', [3, 3])],
    baseRev: 'abc123',
    archiveBase: '',
  });
  assert.deepEqual([...result.files.keys()].sort(), ['docs/todo/models/one.md', 'docs/todo/models/two.md']);
  assert.match(result.files.get('docs/todo/models/one.md'), /lines 3-4, on 2026-10-03\. -->\n## Open\n- \[ \] One\n/);
  assert.match(result.files.get('docs/todo/models/two.md'), /lines 5-5, on 2026-10-03\. -->\n- \[ \] Two\n/);
  assert.match(result.mappingDoc, /\| S001 \| 3-6 \| Open \| 2 files \|/);
  assert.deepEqual(missingLines(source, [...result.files.values(), result.archive]), []);
});

test('a split that leaves a non-empty line uncovered is refused', () => {
  const sections = splitSections('## Open\n- [ ] One\n- [ ] Two\n');
  assert.throws(
    () => applyMigration({ sections, metas: [{ heading: '## Open', disposition: 'split' }, { ...meta, heading: '## Open', from: true, lines: [1, 2] }], baseRev: 'r', archiveBase: '' }),
    /split leaves lines uncovered: 3/,
  );
});

test('missingLines counts duplicates and reports changed lines', () => {
  const old = '- [ ] Same task\n- [ ] Same task\n- [ ] Another\n';
  assert.deepEqual(missingLines(old, ['- [ ] Same task\n- [ ] Changed\n']), [
    { line: '- [ ] Same task', need: 2, have: 1 },
    { line: '- [ ] Another', need: 1, have: 0 },
  ]);
});
