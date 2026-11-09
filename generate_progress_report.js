const fs = require('fs');
const path = require('path');
const { AlignmentType, BorderStyle, Document, HeadingLevel, LevelFormat, Packer,
  Paragraph, ShadingType, Table, TableCell, TableRow, TextRun, WidthType } = require('docx');

const outputDir = path.join(__dirname, 'reports');
const outputPath = path.join(outputDir, 'Research_Progress_Report_Aarav_Khanal.docx');
fs.mkdirSync(outputDir, { recursive: true });
const FONT = 'Times New Roman', TEXT = '111111', ACCENT = '1F4E79', WHITE = 'FFFFFF', WIDTH = 9360;

function run(text, o = {}) { return new TextRun({ text, font: FONT, size: o.size ?? 22,
  bold: o.bold, italics: o.italics, color: o.color ?? TEXT }); }
function para(parts, o = {}) {
  const values = Array.isArray(parts) ? parts : [{ text: parts }];
  return new Paragraph({ alignment: o.alignment ?? AlignmentType.JUSTIFIED,
    spacing: { after: o.after ?? 110, line: o.line ?? 276 },
    indent: o.firstLine === false ? undefined : { firstLine: 360 },
    children: values.map(v => typeof v === 'string' ? run(v) : run(v.text, v)) });
}
function heading(text, level = 1, pageBreakBefore = false) {
  return new Paragraph({ text, heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2,
    spacing: { before: level === 1 ? 240 : 150, after: 80 }, keepNext: true, pageBreakBefore });
}
function bullet(text) { return new Paragraph({ numbering: { reference: 'bullets', level: 0 },
  spacing: { after: 65, line: 260 }, children: [run(text)] }); }
function cell(text, width, header = false) { return new TableCell({ width: { size: width, type: WidthType.DXA },
  shading: header ? { fill: ACCENT, type: ShadingType.CLEAR, color: 'auto' } : undefined,
  margins: { top: 70, bottom: 70, left: 80, right: 80 },
  children: [new Paragraph({ spacing: { after: 0, line: 225 },
    children: [run(String(text), { bold: header, color: header ? WHITE : TEXT, size: 19 })] })] }); }
function table(headers, rows, widths) {
  const edge = { style: BorderStyle.SINGLE, size: 4, color: '7F8C8D' };
  const inner = { style: BorderStyle.SINGLE, size: 2, color: 'B7C9D6' };
  return new Table({ width: { size: WIDTH, type: WidthType.DXA }, columnWidths: widths,
    borders: { top: edge, bottom: edge, left: edge, right: edge,
      insideHorizontal: inner, insideVertical: inner },
    rows: [new TableRow({ tableHeader: true,
      children: headers.map((v, i) => cell(v, widths[i], true)) }),
      ...rows.map(row => new TableRow({ children: row.map((v, i) => cell(v, widths[i])) }))] });
}

const content = [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 100, after: 130 },
    children: [run('Research Progress Report', { bold: true, size: 36, color: ACCENT })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 45 },
    children: [run('Controlled Canary Memorization Study', { bold: true, size: 28 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 25 },
    children: [run('Aarav Khanal', { bold: true, size: 24 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 180 },
    children: [run('Status verified 9 November 2026', { italics: true, size: 20 })] }),
  para([{ text: 'Executive summary—', bold: true }, { text: 'The exploratory 14M grid, matched 48M scale-transfer grid, and separate contamination-free 24-cell confirmatory computational grid are complete. The frozen confirmatory exposure model estimated 1.223 additional exposure bits per log10 insertion-frequency decade (95% CI 0.691–1.755; 960 observations across 40 canary clusters). None of the three registered architecture-by-frequency interactions survived Holm correction. These are exposure findings only. The primary human V/T/N novelty endpoint remains blank, so the study does not yet establish a memorization–creativity trade-off. Independent clean-room reproduction has verified 8 of 24 cells; the ninth cell is partial and inactive. MIT is selected for original project software and documentation, while redistribution rights for datasets, generated text, tokenizer/model artifacts, and weights remain unresolved.' }], { firstLine: false, line: 255 }),

  heading('1. Research question and scope'),
  para('The project asks whether controlled repetition of narrative canaries changes model memorization and human-rated recombination, and whether that relationship differs across transformer architectures. Exposure, extraction, exact training-corpus overlap, automated lexical diversity, and blinded human novelty are intentionally separate measures. Lexical diversity is not treated as creativity, and exposure alone is not interpreted as a human-novelty result.'),
  para('Four near-parameter-matched decoder-only architectures are studied: the RoPE/GQA/RMSNorm baseline, learned absolute positions, full multi-head attention, and LayerNorm. Exploratory treatment frequencies are 1, 10, 50, 100, and 500 insertions, with matched frequency-zero controls.'),

  heading('2. Completed computational work'),
  table(['Workstream', 'Verified state', 'Principal artifact'], [
    ['Exploratory 14M grid', '24/24 architecture-frequency cells complete', 'results/mem_*.json; results/novelty_*.json'],
    ['48M scale-transfer grid', '24/24 cells complete; single seed', 'results/mem_scale_48m_*.json'],
    ['Confirmatory grid', '24/24 cells trained and evaluated', 'results/confirmatory/*/*/seed_*/evaluated.json'],
    ['Exposure model', 'Frozen analysis complete', 'results/confirmatory/exposure_analysis.json'],
    ['Annotation package', '3 × 7,680 rows; all labels blank', 'results/confirmatory/annotation/'],
    ['Independent reproduction', '8/24 cells complete; ninth partial', '.runtime/clean-room-reproduction/'],
  ], [2300, 2800, 4260]),
  para('All 24 confirmatory cells include locked exposure evaluation, deterministic generation, checkpoint and corpus provenance, and exact word-four-gram overlap against the selected training split. The condition-hidden annotation builder produced two independently shuffled external-rater sheets and one separate investigator-sensitivity sheet. It does not create automated human labels.'),

  heading('3. Main supported findings', 1, true),
  heading('3.1 Confirmatory exposure result', 2),
  para('The registered OLS model with canary-clustered sandwich covariance estimated a grand-mean frequency slope of 1.223 exposure bits per log10 frequency decade. The 95% confidence interval was 0.691 to 1.755, with p = 6.55 × 10⁻⁶. None of the three architecture-by-frequency interaction terms survived the registered Holm correction. The defensible conclusion is therefore a positive exposure-frequency association in this locked grid, not evidence of a creativity effect or a confirmed architecture difference.'),
  heading('3.2 Exploratory lessons', 2),
  bullet('Three original canary identities already occurred in the base corpus, producing misleading ceiling exposure in zero-insertion controls. The confirmatory bank was screened for absence before locking.'),
  bullet('Two matched baseline training seeds demonstrated substantial per-canary sensitivity. Two seeds diagnose instability but do not estimate a population noise distribution.'),
  bullet('Teacher-forced global-argmax extraction was 0/120 in the audited baseline and learned-position scope. This bounded negative result does not generalize to every model or decoder.'),
  bullet('Automated distinct-2 and exact n-gram overlap are useful diagnostics, but neither measures semantic creativity or substitutes for blinded human judgment.'),

  heading('4. Work that remains'),
  table(['Priority', 'Required work', 'Why it matters'], [
    ['1', 'Resolve ethics/institutional determination and finalize consent, compensation, retention, withdrawal, and secure-return procedures.', 'External recruitment and annotation are currently prohibited.'],
    ['2', 'Reconcile the intended 7,680-item confirmatory workload with documents that currently describe a 1,280-item batch; run a timing pilot before recruitment.', 'Workload, payment, feasibility, and consent must describe the same endpoint.'],
    ['3', 'Collect two independent external ratings, preserve the separate self-sensitivity sheet, and adjudicate disagreements while conditions remain hidden.', 'The primary human-novelty endpoint has zero labels.'],
    ['4', 'Run the frozen binomial GEE human-novelty model and then produce the joint exposure–novelty interpretation.', 'Required before making any trade-off claim.'],
    ['5', 'Complete the remaining 16 clean-room cells on validated storage or adopt a documented, justified reproduction amendment.', 'The declared full-cell reproduction gate remains open.'],
    ['6', 'Confirm redistribution terms, authorize release, create a permanent archive, and record a real DOI.', 'MIT does not cover all third-party or generated artifacts.'],
  ], [900, 4900, 3560]),

  heading('5. Current gates and risks', 1, true),
  para([{ text: 'Human endpoint. ', bold: true }, { text: 'The two confirmatory external-rater files and the separate self-sensitivity file each contain 7,680 rows with blank label, confidence, and notes fields. No V/T/N rate, inter-rater agreement, or adjudication result exists.' }], { firstLine: false }),
  para([{ text: 'Annotation feasibility. ', bold: true }, { text: 'The confirmatory sheets contain 7,680 items per rater, but the current draft information and compensation materials describe 1,280 items. This inconsistency must be resolved through a prospective, dated decision before recruitment.' }], { firstLine: false }),
  para([{ text: 'Clean-room reproduction. ', bold: true }, { text: 'Eight independent cells are complete: all four 14M architectures for seeds 20261016 and 20261017. The next baseline seed-20261018 run stopped at step 2,525 of 6,000 and is inactive. Approximately 31.76 GiB was free at the latest audit, insufficient to retain the remaining cells while preserving the frozen 25-GiB reserve.' }], { firstLine: false }),
  para([{ text: 'Release rights. ', bold: true }, { text: 'The MIT License covers original project software and documentation. It does not by itself authorize redistribution of TinyStories-derived corpora, generated text, tokenizer/model artifacts, or weights. The permanent archive, DOI, release authorization, and non-software rights review remain open.' }], { firstLine: false }),

  heading('6. Immediate action plan'),
  bullet('Commit the reconciled license, progress, ethics-draft, and report state without adding unrelated generated labeling files.'),
  bullet('Decide the confirmatory annotation workload prospectively and update every protocol, consent, compensation, and power artifact consistently.'),
  bullet('Obtain the responsible institutional determination before contacting raters or distributing sheets.'),
  bullet('Complete independent ratings and adjudication, run the frozen novelty analysis, and refresh the manuscript claim audit.'),
  bullet('Move clean-room artifacts to adequate validated storage before resuming the remaining reproduction grid.'),
  bullet('Package the final reproducibility bundle, confirm redistribution boundaries, and create the permanent DOI archive.'),

  heading('7. Claim boundary'),
  para('The project may currently report that controlled insertion frequency was positively associated with exposure in the three-seed, two-scale confirmatory grid and that the registered architecture-interaction family was not significant after correction. It must not currently claim that memorization reduces or improves creativity, that any architecture changes human novelty, or that the artifact is fully independently reproduced and publication-ready.'),
  para('This report is an operational research-status document. Numerical claims should be checked against the versioned JSON/CSV sources and the repository claim audit before external use.'),
];

const doc = new Document({ creator: 'Aarav Khanal', lastModifiedBy: 'Aarav Khanal',
  title: 'Research Progress Report — Controlled Canary Memorization Study',
  subject: 'Verified project status as of 9 November 2026',
  styles: { default: { document: { run: { font: FONT, size: 22, color: TEXT },
    paragraph: { spacing: { line: 276 } } } }, paragraphStyles: [
    { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
      run: { font: FONT, size: 26, bold: true, color: ACCENT },
      paragraph: { spacing: { before: 240, after: 80 }, outlineLevel: 0, keepNext: true } },
    { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
      run: { font: FONT, size: 23, bold: true, color: ACCENT },
      paragraph: { spacing: { before: 150, after: 70 }, outlineLevel: 1, keepNext: true } }] },
  numbering: { config: [{ reference: 'bullets', levels: [{ level: 0, format: LevelFormat.BULLET,
    text: '•', alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{ properties: { page: { size: { width: 12240, height: 15840 },
    margin: { top: 900, right: 1440, bottom: 900, left: 1440 } } }, children: content }] });

Packer.toBuffer(doc).then(buffer => { fs.writeFileSync(outputPath, buffer); console.log(`wrote ${outputPath}`); });
