import { createElement } from 'react';
import { createRoot } from 'react-dom/client';

const root = document.getElementById('root');
if (!root) throw new Error('Root element unavailable');
createRoot(root).render(createElement('main', null, createElement('h1', null, 'Stellar Atlas')));
