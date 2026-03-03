const $ = s => document.querySelector(s);

function status(msg, type) {
  const el = $('#status');
  el.textContent = msg;
  el.className = type || '';
  if (type === 'ok') setTimeout(() => { el.textContent = ''; el.className = ''; }, 3000);
}

function load() {
  chrome.runtime.sendMessage({ type: 'stats' }, r => {
    if (!r) return;
    $('#count').textContent = r.count || 0;
    if (r.embedded != null && r.count) {
      const pct = Math.round((r.embedded / r.count) * 100);
      $('#count').textContent = `${r.count} (${pct}% embedded)`;
    }
    const gl = $('#glyphs');
    if (r.glyphs) {
      gl.innerHTML = Object.entries(r.glyphs)
        .sort((a, b) => b[1] - a[1])
        .map(([g, n]) => `<span class="gc"><span class="g">${g}</span><span class="n">${n}</span></span>`)
        .join('');
    }
  });
}

$('#file').onchange = async e => {
  const file = e.target.files[0];
  if (!file) return;
  status('Reading...');
  try {
    const data = JSON.parse(await file.text());
    if (!Array.isArray(data)) { status('Not a JSON array', 'err'); return; }
    status(`Importing ${data.length}...`);
    chrome.runtime.sendMessage({ type: 'import', crystals: data }, r => {
      if (r && r.imported != null) {
        const msg = r.skipped
          ? `Imported ${r.imported}, skipped ${r.skipped} duplicates`
          : `Imported ${r.imported} crystals`;
        status(msg, 'ok');
        load();
      } else {
        status('Import failed', 'err');
      }
    });
  } catch (err) {
    status(err.message, 'err');
  }
  e.target.value = '';
};

$('#export').onclick = () => {
  chrome.runtime.sendMessage({ type: 'export' }, r => {
    if (!r || !r.crystals || !r.crystals.length) { status('Nothing to export', 'err'); return; }
    const blob = new Blob([JSON.stringify(r.crystals, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `crystals-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    status(`Exported ${r.crystals.length}`, 'ok');
  });
};

$('#clear').onclick = () => {
  if (!confirm('Clear all crystals?')) return;
  chrome.runtime.sendMessage({ type: 'clear' }, () => {
    status('Cleared', 'ok');
    load();
  });
};

load();
