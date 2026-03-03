// ── Offscreen document: transformers.js embedding engine ──
// Runs in offscreen document because transformers.js needs DOM/Worker APIs
// not available in service workers.

import { pipeline, env } from './lib/transformers.min.js';

let embedder = null;
let loading = false;
let loadPromise = null;

// Point WASM to our local copy
if (env && env.backends && env.backends.onnx && env.backends.onnx.wasm) {
  env.backends.onnx.wasm.wasmPaths = chrome.runtime.getURL('lib/');
}

// Allow fetching model from HuggingFace Hub
env.allowLocalModels = false;
env.allowRemoteModels = true;

async function getEmbedder() {
  if (embedder) return embedder;
  if (loading) return loadPromise;
  loading = true;

  console.log('[Crystal Field] Loading embedding model...');
  loadPromise = pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2', {
    dtype: 'fp32',
    device: 'wasm'
  });

  embedder = await loadPromise;
  loading = false;
  console.log('[Crystal Field] Embedding model ready.');
  return embedder;
}

// Listen for embed requests from service worker
chrome.runtime.onMessage.addListener((msg, sender, reply) => {
  if (msg.type !== '_embed') return;

  (async () => {
    try {
      const model = await getEmbedder();
      const text = (msg.text || '').slice(0, 512); // cap input length
      const result = await model(text, { pooling: 'mean', normalize: true });
      // result.data is a Float32Array (384-dim for MiniLM-L6-v2)
      reply({ embedding: Array.from(result.data) });
    } catch (err) {
      console.error('[Crystal Field] Embedding error:', err);
      reply({ error: err.message });
    }
  })();

  return true; // async reply
});
