// ── Content script: sidebar on AI platforms ──
(function() {
  'use strict';

  const INPUTS = {
    chatgpt: 'div#prompt-textarea, div[contenteditable="true"][data-placeholder]',
    claude: 'div.ProseMirror[contenteditable="true"]'
  };

  const host = location.hostname;
  const platform = host.includes('chatgpt.com') || host.includes('chat.openai.com')
    ? 'chatgpt' : host.includes('claude.ai') ? 'claude' : null;
  if (!platform) return;

  let open = false;
  let root = null;
  let timer = null;
  let total = 0;

  // ── Build sidebar ──
  function init() {
    const el = document.createElement('div');
    el.id = 'crystal-field-host';
    root = el.attachShadow({ mode: 'closed' });
    root.innerHTML = `<style>${CSS}</style>
      <div class="sidebar" id="sb">
        <div class="hdr">
          <span class="psi" id="close">\u03C8</span>
          <span class="title">Your field</span>
          <span class="count" id="count">0</span>
        </div>
        <div class="body" id="body">
          <div class="hint" id="hint">Type something, then press <kbd>Ctrl+Shift+K</kbd></div>
        </div>
        <div class="foot">crystals from PsiOS</div>
      </div>
      <div class="fab" id="fab">\u03C8</div>`;
    document.body.appendChild(el);

    root.getElementById('close').onclick = () => toggle(false);
    root.getElementById('fab').onclick = () => {
      const text = getInput();
      if (text.length > 3) search(text);
      else toggle(!open);
    };

    chrome.runtime.sendMessage({ type: 'stats' }, r => {
      if (r && r.count) { total = r.count; root.getElementById('count').textContent = total; }
    });

    // Watch input
    setInterval(() => {
      const inp = document.querySelector(INPUTS[platform]);
      if (inp && !inp._cf) {
        inp._cf = true;
        inp.addEventListener('input', () => {
          clearTimeout(timer);
          timer = setTimeout(() => {
            const t = getInput();
            if (t.length > 20) search(t);
          }, 1500);
        });
      }
    }, 2000);
  }

  function getInput() {
    const el = document.querySelector(INPUTS[platform]);
    return el ? (el.innerText || el.textContent || '').trim() : '';
  }

  function toggle(show) {
    open = show;
    root.getElementById('sb').classList.toggle('open', show);
    root.getElementById('fab').classList.toggle('hide', show);
  }

  function search(text) {
    toggle(true);
    root.getElementById('body').innerHTML = '<div class="searching">searching...</div>';
    chrome.runtime.sendMessage({ type: 'search', text }, r => {
      if (r && r.crystals && r.crystals.length > 0) {
        show(r.crystals);
      } else {
        root.getElementById('body').innerHTML = '<div class="hint">No matches found</div>';
      }
    });
  }

  function show(list) {
    root.getElementById('count').textContent = list.length + ' / ' + total;
    root.getElementById('body').innerHTML = list.map(c => {
      const preview = (c.content || '').slice(0, 200);
      const pct = Math.round((c.score || 0) * 100);
      const date = c.created_at ? new Date(c.created_at).toLocaleDateString() : '';
      return `<div class="card" data-text="${esc(c.content || '')}">
        <div class="meta"><span class="gl">${c.glyph || '\u2205'}</span><span>${date}</span><span class="pct">${pct}%</span></div>
        <div class="txt">${escH(preview)}</div>
      </div>`;
    }).join('');

    root.querySelectorAll('.card').forEach(card => {
      card.onclick = () => {
        navigator.clipboard.writeText(card.dataset.text);
        card.classList.add('copied');
        setTimeout(() => card.classList.remove('copied'), 1200);
      };
    });
  }

  function esc(s) { return s.replace(/"/g, '&quot;').replace(/</g, '&lt;'); }
  function escH(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

  // ── Keyboard shortcut ──
  document.addEventListener('keydown', e => {
    if (e.ctrlKey && e.shiftKey && e.key === 'K') {
      e.preventDefault();
      if (open) { toggle(false); return; }
      const t = getInput();
      if (t.length > 3) search(t);
      else toggle(true);
    }
  });

  const CSS = `
    * { box-sizing: border-box; margin: 0; padding: 0; }
    .sidebar {
      position: fixed; top: 0; right: -340px; width: 340px; height: 100vh;
      background: #0a0a0f; border-left: 1px solid rgba(123,104,238,.3);
      z-index: 999999; display: flex; flex-direction: column;
      font-family: -apple-system, sans-serif; color: #e0e0e0;
      transition: right .25s ease; box-shadow: -4px 0 20px rgba(0,0,0,.5);
    }
    .sidebar.open { right: 0; }
    .hdr {
      display: flex; align-items: center; gap: 10px; padding: 14px 16px;
      border-bottom: 1px solid rgba(123,104,238,.2); background: rgba(123,104,238,.05);
    }
    .psi { font-size: 22px; color: #7b68ee; cursor: pointer; }
    .title { font-size: 14px; font-weight: 600; color: #b8b0ff; flex: 1; }
    .count { font-size: 12px; color: #7b68ee; background: rgba(123,104,238,.15); padding: 2px 8px; border-radius: 10px; }
    .body { flex: 1; overflow-y: auto; padding: 10px; }
    .body::-webkit-scrollbar { width: 4px; }
    .body::-webkit-scrollbar-thumb { background: rgba(123,104,238,.3); border-radius: 2px; }
    .hint { text-align: center; padding: 40px 16px; color: #555; font-size: 13px; line-height: 1.6; }
    .hint kbd { background: rgba(123,104,238,.15); border: 1px solid rgba(123,104,238,.3); border-radius: 4px; padding: 1px 5px; font-family: monospace; font-size: 11px; color: #b8b0ff; }
    .foot { padding: 10px 16px; font-size: 11px; color: #444; text-align: center; border-top: 1px solid rgba(123,104,238,.1); }
    .card {
      background: rgba(123,104,238,.05); border: 1px solid rgba(123,104,238,.15);
      border-radius: 8px; padding: 10px; margin-bottom: 8px; cursor: pointer;
      transition: all .15s;
    }
    .card:hover { background: rgba(123,104,238,.1); border-color: rgba(123,104,238,.4); }
    .card.copied { border-color: rgba(100,255,150,.5); background: rgba(100,255,150,.05); }
    .meta { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; font-size: 11px; color: #888; }
    .gl { font-size: 15px; color: #7b68ee; }
    .pct { margin-left: auto; color: #7b68ee; font-weight: 600; }
    .txt { font-size: 13px; line-height: 1.4; color: #ccc; word-break: break-word; }
    .searching { text-align: center; padding: 20px; color: #7b68ee; font-size: 13px; }
    .fab {
      position: fixed; bottom: 80px; right: 16px; width: 40px; height: 40px;
      background: #0a0a0f; border: 1px solid rgba(123,104,238,.4); border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-size: 20px; color: #7b68ee; cursor: pointer; z-index: 999998;
      transition: all .2s; box-shadow: 0 2px 12px rgba(0,0,0,.4);
    }
    .fab:hover { border-color: #7b68ee; transform: scale(1.1); }
    .fab.hide { display: none; }
  `;

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
