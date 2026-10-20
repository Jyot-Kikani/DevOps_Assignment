import { createRequire } from 'node:module';
const require = createRequire(new URL('../apps/web/package.json', import.meta.url));
const { chromium } = require('@playwright/test');
const base = process.argv[2];
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  await page.goto(`${base}/health/live`);
  const result = await page.evaluate(async () => {
    const sid = 'gcns-edr3-20261013-20271720';
    const manifest = await (await fetch(`/v1/snapshots/${sid}/map?radius_ly=50`)).json();
    const chunk = manifest.chunks[0];
    const response = await fetch(chunk.url.replace('/api/catalog', ''));
    const bytes = await response.arrayBuffer();
    const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(x => x.toString(16).padStart(2, '0')).join('');
    const ordinal = new DataView(bytes).getUint32(0, true);
    const profile = await (await fetch(`/v1/snapshots/${sid}/ordinals/${ordinal}`)).json();
    return { snapshot_id: sid, total_count: manifest.total_count, content_encoding: response.headers.get('content-encoding'),
      decoded_bytes: bytes.byteLength, expected_bytes: chunk.uncompressed_bytes, decoded_sha256: hash,
      expected_sha256: chunk.uncompressed_sha256, ordinal, source_id: profile.source_id };
  });
  if (result.total_count !== 1151 || result.content_encoding !== 'gzip' || result.decoded_bytes !== result.expected_bytes ||
      result.decoded_sha256 !== result.expected_sha256 || result.ordinal !== 1 || typeof result.source_id !== 'string') {
    throw new Error(`Browser chunk verification failed: ${JSON.stringify(result)}`);
  }
  process.stdout.write(JSON.stringify({ status: 'passed', browser: browser.version(), ...result }, null, 2));
} finally {
  await browser.close();
}
