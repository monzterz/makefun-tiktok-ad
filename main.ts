// makefun-tiktok-ad entry program (Node 22, standard library only).
//
// The graded program is small on purpose: the entry's work is the video, which is made by
// ad/build_ad.py in the agent session that built this repository and posted on TikTok. Here
// the program publishes the one thing the gate reads: VIDEO.json, copied from the repository
// root to the output directory the grader hands it.
//
// The copy is checked before it goes out. A stale placeholder or a short link would make the
// entry invalid, and an invalid entry keeps its row but scores nothing, so the program says
// which fault it found on stderr and still writes the file: a run that ends non-zero would
// fail the entry outright, and a readable VIDEO.json is always better than a missing one.
//
// Outside the grader's container, point MAKEFUN_BOT_DIR and MAKEFUN_OUTPUT_DIR at local
// directories:
//   mkdir -p out && MAKEFUN_BOT_DIR=. MAKEFUN_OUTPUT_DIR=out node main.ts

import { copyFileSync, mkdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

const BOT_DIR = process.env.MAKEFUN_BOT_DIR ?? '/bot';
const OUTPUT_DIR = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';

const VIDEO_PATH = join(BOT_DIR, 'VIDEO.json');
const OUT_PATH = join(OUTPUT_DIR, 'VIDEO.json');

// A full TikTok video address, the form the gate accepts: /@handle/video/<digits>.
const FULL_VIDEO = /^https:\/\/(www\.)?tiktok\.com\/@[^/\s]+\/video\/\d+$/;

function inspect(): string[] {
  const notes: string[] = [];
  let url = '';
  try {
    const raw = readFileSync(VIDEO_PATH, 'utf8');
    const parsed: unknown = JSON.parse(raw);
    const value = (parsed as { url?: unknown })?.url;
    url = typeof value === 'string' ? value.trim() : '';
  } catch (err) {
    notes.push(`VIDEO.json is not readable JSON: ${(err as Error).message}`);
    return notes;
  }
  if (!url) notes.push('VIDEO.json has no url');
  else if (url.includes('<') || url.includes('>')) notes.push('VIDEO.json still holds a placeholder address');
  else if (/(^|\/\/)(vm|vt)\.tiktok\.com\//.test(url) || /tiktok\.com\/t\//.test(url)) {
    notes.push('VIDEO.json names a short link, not the /@handle/video/<id> address');
  } else if (!FULL_VIDEO.test(url)) notes.push('VIDEO.json does not name a full TikTok video address');
  return notes;
}

mkdirSync(OUTPUT_DIR, { recursive: true });
try {
  copyFileSync(VIDEO_PATH, OUT_PATH);
} catch (err) {
  console.error(`VIDEO.json could not be copied from ${BOT_DIR}: ${(err as Error).message}`);
  process.exit(1);
}
for (const note of inspect()) console.error(`warning: ${note}`);
