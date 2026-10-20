import { defineConfig } from '@playwright/test';

export default defineConfig({ testDir: './tests/e2e', outputDir: '../../.local/reports/browser-results',
  workers: 1, retries: 0, timeout: 45000, reporter: 'list',
  use: { baseURL: process.env.STELLAR_BASE_URL ?? 'http://127.0.0.1:5173', locale: 'en-US', viewport: { width: 1440, height: 900 },
    launchOptions: { args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] } },
});
