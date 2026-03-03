// ── Crystal database — simple, no modules ──

const DB_NAME = 'crystal-field';
const DB_VERSION = 2;
let db = null;
let crystals = [];
let crystalIndex = new Map(); // content-prefix → true, for dedup

function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = e => {
      const d = e.target.result;
      if (!d.objectStoreNames.contains('crystals')) {
        const store = d.createObjectStore('crystals', { keyPath: 'id', autoIncrement: true });
        store.createIndex('content_key', 'content_key', { unique: false });
      } else {
        const store = e.currentTarget.transaction.objectStore('crystals');
        if (!store.indexNames.contains('content_key')) {
          store.createIndex('content_key', 'content_key', { unique: false });
        }
      }
    };
    req.onsuccess = () => { db = req.result; resolve(db); };
    req.onerror = () => reject(req.error);
  });
}

// Content key for dedup: first 120 chars, lowered, trimmed
function contentKey(text) {
  if (!text) return '';
  return text.slice(0, 120).toLowerCase().trim();
}

async function loadCrystals() {
  if (!db) await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('crystals', 'readonly');
    const req = tx.objectStore('crystals').getAll();
    req.onsuccess = () => {
      crystals = req.result;
      // Rebuild dedup index
      crystalIndex.clear();
      for (const c of crystals) {
        const key = c.content_key || contentKey(c.content);
        crystalIndex.set(key, true);
      }
      resolve(crystals);
    };
    req.onerror = () => reject(req.error);
  });
}

async function importCrystals(arr, onProgress) {
  if (!db) await openDB();
  // Ensure index is current
  if (!crystals.length && crystalIndex.size === 0) await loadCrystals();

  let imported = 0;
  let skipped = 0;
  const tx = db.transaction('crystals', 'readwrite');
  const store = tx.objectStore('crystals');

  for (const c of arr) {
    const key = contentKey(c.content);
    if (crystalIndex.has(key)) {
      skipped++;
      continue;
    }
    const { id, ...rest } = c; // strip original id
    rest.content_key = key;
    store.add(rest);
    crystalIndex.set(key, true);
    imported++;
  }

  return new Promise((resolve, reject) => {
    tx.oncomplete = () => resolve({ imported, skipped });
    tx.onerror = () => reject(tx.error);
  });
}

async function clearCrystals() {
  if (!db) await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('crystals', 'readwrite');
    tx.objectStore('crystals').clear();
    tx.oncomplete = () => { crystals = []; crystalIndex.clear(); resolve(); };
    tx.onerror = () => reject(tx.error);
  });
}

// Cosine similarity between two Float32Arrays or regular arrays
function cosineSimilarity(a, b) {
  if (!a || !b || a.length !== b.length) return 0;
  let dot = 0, na = 0, nb = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    na += a[i] * a[i];
    nb += b[i] * b[i];
  }
  const denom = Math.sqrt(na) * Math.sqrt(nb);
  return denom > 0 ? dot / denom : 0;
}

// Embedding-based search: cosine similarity against all crystals with embeddings
function searchByEmbedding(queryEmbedding, limit) {
  limit = limit || 5;
  const results = [];
  for (const c of crystals) {
    if (!c.embedding || !c.embedding.length) continue;
    const sim = cosineSimilarity(queryEmbedding, c.embedding);
    results.push({
      content: c.content,
      glyph: c.glyph || '',
      created_at: c.created_at || '',
      zl_score: c.zl_score,
      role: c.role || '',
      score: sim
    });
  }
  results.sort((a, b) => b.score - a.score);
  return results.slice(0, limit);
}

// Keyword fallback search (when no embeddings available)
function searchByKeyword(query, limit) {
  if (!crystals.length || !query) return [];
  limit = limit || 5;

  const words = query.toLowerCase().split(/\s+/).filter(w => w.length > 2);
  const stops = new Set(['the','and','for','are','but','not','you','all','can','had',
    'her','was','one','our','out','has','have','that','this','with','they','from',
    'been','said','will','what','when','your','more','about','would','them','than',
    'into','just','like','also','there','some','very','much','does','could']);
  const keywords = words.filter(w => !stops.has(w));
  if (!keywords.length) return [];

  const results = [];
  for (const c of crystals) {
    if (!c.content || c.content.length < 10) continue;
    const lower = c.content.toLowerCase();
    let score = 0;

    // Exact phrase match (strong signal)
    if (query.length > 8 && lower.includes(query.toLowerCase())) score += 5;

    // Keyword hits
    for (const kw of keywords) {
      if (lower.includes(kw)) score++;
    }

    if (score > 0) {
      results.push({
        content: c.content,
        glyph: c.glyph || '',
        created_at: c.created_at || '',
        zl_score: c.zl_score,
        role: c.role || '',
        score: score / keywords.length
      });
    }
  }

  results.sort((a, b) => b.score - a.score);
  return results.slice(0, limit);
}

// Smart search: use embeddings if available, fall back to keyword
function searchCrystals(queryEmbedding, text, limit) {
  // If we have a query embedding and crystals have embeddings, use cosine
  const hasEmbeddings = crystals.some(c => c.embedding && c.embedding.length);
  if (queryEmbedding && hasEmbeddings) {
    return searchByEmbedding(queryEmbedding, limit);
  }
  // Fallback: keyword search
  return searchByKeyword(text, limit);
}

// Save embedding for a crystal (by db id)
async function saveEmbedding(crystalId, embedding) {
  if (!db) await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('crystals', 'readwrite');
    const store = tx.objectStore('crystals');
    const req = store.get(crystalId);
    req.onsuccess = () => {
      const c = req.result;
      if (!c) { resolve(false); return; }
      c.embedding = Array.from(embedding);
      store.put(c);
      tx.oncomplete = () => resolve(true);
    };
    tx.onerror = () => reject(tx.error);
  });
}

// Count crystals that have embeddings
function embeddedCount() {
  return crystals.filter(c => c.embedding && c.embedding.length).length;
}
