import { defineConfig } from 'vitest/config';

export default defineConfig({ server: { proxy: {
  '/api/catalog': { target: 'http://127.0.0.1:18000', rewrite: path => path.replace(/^\/api\/catalog/, '') },
  '/api/journey': { target: 'http://127.0.0.1:18001', rewrite: path => path.replace(/^\/api\/journey/, '') },
} }, test: { include: ['tests/*.test.ts'] } });
