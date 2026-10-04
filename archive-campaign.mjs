import {readFile, mkdir, writeFile} from 'node:fs/promises';
import {join} from 'node:path';
import {createHash} from 'node:crypto';

const [id, name] = process.argv.slice(2);
if (!id || !/^[a-z0-9][a-z0-9-]{0,70}$/.test(name || '')) {
  throw Error('Usage: node archive-campaign.mjs <campaign-id> <archive-name>');
}
const jobs = JSON.parse(await readFile(join(process.env.DATA_DIR || 'data', 'jobs.json'), 'utf8'));
const job = jobs[id];
if (job?.busy || job?.stage !== 'done' || !job.final?.variants?.length) {
  throw Error('Campaign must have a completed, validated cloud result');
}
if (job.sample || job.rehearsal) throw Error('Sample and rehearsal campaigns use bundled media; there is nothing to archive');
const dir = join('docs', 'assets', name);
await mkdir(dir, {recursive: true});
const files = [];
const replacements = new Map();

async function keep(source, file, phase) {
  if (replacements.has(source)) return;
  const url = new URL(source);
  if (url.protocol !== 'https:' || !url.hostname.endsWith('.volces.com')) {
    throw Error('Expected an HTTPS BytePlus-generated asset URL');
  }
  const response = await fetch(url, {redirect: 'error', signal: AbortSignal.timeout(120000)});
  if (!response.ok) throw Error(`${file} ${phase}: HTTP ${response.status}`);
  const mime = (response.headers.get('content-type') || '').split(';')[0];
  const extensions = {'image/jpeg': 'jpg', 'image/png': 'png', 'image/webp': 'webp', 'video/mp4': 'mp4'};
  const ext = extensions[mime];
  if (!ext || (phase === 'video') !== (ext === 'mp4')) throw Error('Unexpected media type');
  const bytes = Buffer.from(await response.arrayBuffer());
  if (!bytes.length) throw Error('Empty media response');
  await writeFile(join(dir, `${file}.${ext}`), bytes);
  replacements.set(source, `${file}.${ext}`);
  files.push({file: `${file}.${ext}`, phase, mime, bytes: bytes.length, sha256: createHash('sha256').update(bytes).digest('hex')});
  console.log(`Archived ${file}.${ext}: ${bytes.length} bytes`);
}

// Every design the customer saw, then every round of every design that went into production.
for (const variant of job.explore.variants) {
  if (variant.design?.url) await keep(variant.design.url, `${variant.id}-design`, 'design');
}
for (const variant of job.final.variants) {
  for (const round of variant.rounds) {
    for (const phase of ['design', 'mockup', 'video']) {
      if (round[phase]?.url) await keep(round[phase].url, `${variant.id}-round-${round.number}-${phase}`, phase);
    }
  }
}

// Keep evidence and prompts, but exclude private IDs and remote signed URLs.
function sanitize(value) {
  if (typeof value === 'string') {
    return replacements.get(value) || value.replace(/(?:sesn|agent|env|skill|resp|cgt)-[A-Za-z0-9-]+/g, '[resource ID omitted]');
  }
  if (Array.isArray(value)) return value.map(sanitize);
  if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value)
    .filter(([key]) => !['response_id', 'task', 'contract_hash'].includes(key))
    .map(([key, item]) => [key, sanitize(item)]));
  return value;
}
const report = {archived_at: new Date().toISOString(), run_created: job.created,
  note: 'Sanitized documentation copy; local filenames replace signed URLs. Research source links are public pages and are kept. Not a raw manifest for replay or validation.',
  brief: sanitize(job.brief), limits: job.limits, selection: job.selection, explore: sanitize(job.explore), final: sanitize(job.final), files};
await writeFile(join(dir, 'result.json'), JSON.stringify(report, null, 2) + '\n');
console.log(`Saved ${dir}/result.json; ${files.length} media files. Review before sharing.`);
