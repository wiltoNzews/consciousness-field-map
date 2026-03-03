// ── Service worker — crystal search, storage, embedding routing ──

importScripts('crystal-db.js');

let loaded = false;
let offscreenReady = false;

chrome.runtime.onInstalled.addListener(async () => {
  await openDB();
  await loadCrystals();
  loaded = true;
  console.log('[Crystal Field] Installed.', crystals.length, 'crystals,', embeddedCount(), 'with embeddings.');
});

chrome.runtime.onMessage.addListener((msg, sender, reply) => {
  handle(msg).then(reply).catch(err => reply({ error: err.message }));
  return true;
});

async function ensureLoaded() {
  if (!loaded) {
    await openDB();
    await loadCrystals();
    loaded = true;
  }
}

// ── Offscreen document for transformers.js embedding ──

async function ensureOffscreen() {
  // Always check — Chrome can terminate offscreen docs
  const contexts = await chrome.runtime.getContexts({
    contextTypes: ['OFFSCREEN_DOCUMENT']
  });
  if (contexts.length === 0) {
    await chrome.offscreen.createDocument({
      url: 'offscreen.html',
      reasons: ['WORKERS'],
      justification: 'Run transformers.js embedding model'
    });
  }
  offscreenReady = true;
}

async function embed(text) {
  await ensureOffscreen();
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage({ type: '_embed', text }, r => {
      if (chrome.runtime.lastError) reject(new Error(chrome.runtime.lastError.message));
      else if (r && r.error) reject(new Error(r.error));
      else resolve(r.embedding);
    });
  });
}

// ── Message handler ──

async function handle(msg) {
  // Internal messages from offscreen doc — ignore here
  if (msg.type === '_embed_result' || msg.type === '_embed') return;

  await ensureLoaded();

  switch (msg.type) {
    case 'search': {
      let queryEmb = null;
      if (msg.text) {
        try { queryEmb = await embed(msg.text); } catch (e) {
          console.warn('[Crystal Field] Embedding failed, falling back to keyword:', e.message);
        }
      }
      return { crystals: searchCrystals(queryEmb, msg.text, msg.limit) };
    }

    case 'import': {
      const result = await importCrystals(msg.crystals);
      await loadCrystals(); // refresh cache
      loaded = true;
      // Queue background embedding for new crystals
      embedUnembedded();
      return { imported: result.imported, skipped: result.skipped, total: crystals.length };
    }

    case 'clear':
      await clearCrystals();
      loaded = true;
      return { ok: true };

    case 'stats': {
      const glyphs = {};
      for (const c of crystals) {
        const g = c.glyph || '?';
        glyphs[g] = (glyphs[g] || 0) + 1;
      }
      return {
        count: crystals.length,
        embedded: embeddedCount(),
        glyphs
      };
    }

    case 'export':
      return { crystals: crystals.map(c => {
        const { embedding, content_key, ...rest } = c;
        return rest;
      })};

    case 'embed_status':
      return { total: crystals.length, embedded: embeddedCount() };

    default:
      return { error: 'unknown type' };
  }
}

// ── Background embedding of unembedded crystals ──

let embedding_in_progress = false;

async function embedUnembedded() {
  if (embedding_in_progress) return;
  embedding_in_progress = true;

  const unembedded = crystals.filter(c => !c.embedding || !c.embedding.length);
  if (unembedded.length === 0) {
    embedding_in_progress = false;
    return;
  }

  console.log(`[Crystal Field] Embedding ${unembedded.length} crystals...`);
  let done = 0;

  for (const c of unembedded) {
    try {
      const emb = await embed(c.content || '');
      if (emb) {
        await saveEmbedding(c.id, emb);
        c.embedding = emb; // update in-memory cache
        done++;
        if (done % 50 === 0) console.log(`[Crystal Field] Embedded ${done}/${unembedded.length}`);
      }
    } catch (e) {
      console.warn('[Crystal Field] Embed failed for crystal', c.id, e.message);
      // Model might not be loaded yet — stop and retry later
      break;
    }
  }

  console.log(`[Crystal Field] Finished embedding batch: ${done} done.`);
  if (done > 0) await loadCrystals(); // refresh cache with new embeddings
  embedding_in_progress = false;
}
