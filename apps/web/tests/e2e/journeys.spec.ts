import { test, expect } from '@playwright/test';

test('explore, radius, search, selection and real 3D measurement', async ({ page, request }) => {
  const snapshot = await (await request.get('/api/catalog/v1/snapshots/active')).json();
  const stars = await (await request.get(`/api/catalog/v1/snapshots/${snapshot.snapshot_id}/stars?limit=1`)).json();
  const star = stars.items[0];
  const manifest = await (await request.get(`/api/catalog/v1/snapshots/${snapshot.snapshot_id}/map?radius_ly=50`)).json();
  const errors: string[] = []; page.on('pageerror', e => errors.push(e.message));
  await page.goto('/explore');
  await expect(page.locator('.count')).toContainText(`${manifest.total_count.toLocaleString('en-US')} catalog objects`);
  await expect(page.locator('canvas')).toBeVisible();
  await expect(page.getByText(/Loading map/)).toHaveCount(0);
  await page.getByRole('button', { name: 'Set measurement origin' }).click();
  await page.getByRole('searchbox', { name: 'Search stars' }).fill(star.source_id);
  const result = page.locator('.star-list button').first();
  await expect(result).toContainText(star.aliases[0] ?? star.source_id);
  await page.getByRole('searchbox').press('ArrowDown');
  await page.keyboard.press('Enter');
  await expect(page.locator('.inspector h2')).toHaveText(star.aliases[0] ?? star.source_id);
  await expect(page).toHaveURL(new RegExp(`star=${star.source_id}`));
  await expect(page.locator('.measurement')).toContainText(`${star.distance_ly.toLocaleString(undefined, { maximumFractionDigits: 5 })} ly`);
  await page.getByLabel('Distance from Sun').selectOption('326.16');
  await expect(page.locator('.count')).toContainText(`${snapshot.counts.within_100pc.toLocaleString('en-US')} catalog objects`);
  expect(errors).toEqual([]);
});

test('calculate, illustrate, save and reopen an immutable share', async ({ page, request }) => {
  const snapshot = await (await request.get('/api/catalog/v1/snapshots/active')).json();
  const { items } = await (await request.get(`/api/catalog/v1/snapshots/${snapshot.snapshot_id}/stars?limit=1`)).json();
  const star = items[0];
  await page.goto(`/journeys?destination=${star.source_id}`);
  await page.getByRole('button', { name: 'Calculate journey' }).click();
  await expect(page.getByTestId('journey-result')).toContainText((star.distance_ly / .1).toLocaleString(undefined, { maximumFractionDigits: 4 }));
  await page.getByRole('button', { name: 'Play', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Pause', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Pause', exact: true }).click();
  await page.getByRole('button', { name: 'Save journey', exact: true }).click();
  await page.getByRole('button', { name: 'Create 30-day share' }).click();
  const sharedLink = page.getByRole('link', { name: 'Open shared journey' });
  await expect(sharedLink).toBeVisible();
  await sharedLink.click();
  await expect(page.getByText('Frozen journey', { exact: false })).toBeVisible();
  await expect(page.getByTestId('journey-result')).toContainText((star.distance_ly / .1).toLocaleString(undefined, { maximumFractionDigits: 4 }));
  await page.getByRole('link', { name: 'Saved', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Journeys (1)' })).toBeVisible();
  await page.locator('.saved-row a').click();
  await expect(page.getByTestId('journey-result')).toBeVisible();
});
