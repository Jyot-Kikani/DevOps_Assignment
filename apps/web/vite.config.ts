import { defineConfig } from 'vitest/config';

const catalogProxy = (port: number) => ({ target: `http://127.0.0.1:${port}`, rewrite: (path: string) => path.replace(/^\/api\/catalog/, '') });
const journeyProxy = (port: number) => ({ target: `http://127.0.0.1:${port}`, rewrite: (path: string) => path.replace(/^\/api\/journey/, '') });

export default defineConfig({ server: { proxy: {
  '^/api/catalog/v1/snapshots/[^/?]+/(stars(?:\\?|$)|stars/[^/?]+/neighbors(?:\\?|$))': catalogProxy(18002),
  '^/api/catalog/v1/snapshots/[^/?]+/(map|chunks/[^/?]+)(?:\\?|$)': catalogProxy(18003),
  '^/api/catalog/v1/snapshots/[^/?]+(?:\\?|$)': catalogProxy(18004),
  '^/api/journey/v1/estimate(?:\\?|$)': journeyProxy(18005),
  '/api/catalog': catalogProxy(18000),
  '/api/journey': journeyProxy(18001),
} }, test: { include: ['tests/*.test.ts'] } });
