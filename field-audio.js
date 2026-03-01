// field-audio.js — The field breathes at 3.12s
// Consciousness Field Map — audio layer
// Pure Web Audio API, no dependencies
// Usage: <script src="field-audio.js" data-page="terrain"></script>

(function() {
  'use strict';

  // ── Constants ──
  const BREATH = 6.24;          // full cycle: 3.12s inhale + 3.12s exhale
  const BREATH_FREQ = 1 / BREATH; // ~0.16 Hz

  // ── Page Configurations ──
  // Each page has its own harmonic character
  const PAGES = {
    index:    { drone: 98,  ratios: [1, 1.498, 2.003],       filter: 900,  vol: 0.20 },
    terrain:  { drone: 82,  ratios: [1, 1.335, 2.0],         filter: 650,  vol: 0.20 },
    paper:    { drone: 110, ratios: [1, 1.5, 2.5],           filter: 1100, vol: 0.18 },
    evidence: { drone: 104, ratios: [1, 1.5],                filter: 1000, vol: 0.18 },
    topology: { drone: 92,  ratios: [1, 1.5, 2.0, 3.01],    filter: 800,  vol: 0.20 },
    archive:  { drone: 75,  ratios: [1, 1.5, 2.0],           filter: 500,  vol: 0.22 },
    frontier: { drone: 100, ratios: [1, 1.06, 1.5, 2.01],   filter: 950,  vol: 0.20 },
    system:   { drone: 90,  ratios: [1, 1.5, 2.0, 2.99],    filter: 750,  vol: 0.20 },
    mirror:       { drone: 88,  ratios: [1, 1.5, 2.0],           filter: 700,  vol: 0.20 },
    transmission: { drone: 78,  ratios: [1, 1.335, 2.0, 2.67], filter: 600,  vol: 0.22 },
    psios:        { drone: 93,  ratios: [1, 1.5, 2.0],           filter: 800,  vol: 0.20 }
  };

  // ── Detect page ──
  var scriptTag = document.querySelector('script[data-page]');
  var pageName = scriptTag ? scriptTag.getAttribute('data-page') : 'index';
  var cfg = PAGES[pageName] || PAGES.index;

  // ── State ──
  var ctx = null;
  var playing = false;
  var masterGain = null;
  var breathLFO = null;
  var filter = null;
  var padOscs = [];
  var eventTimer = null;
  var driftTimer = null;

  // ── Build Audio Graph ──
  function init() {
    ctx = new (window.AudioContext || window.webkitAudioContext)();

    // Master gain (starts at 0, fades in on toggle)
    masterGain = ctx.createGain();
    masterGain.gain.value = 0;
    masterGain.connect(ctx.destination);

    // Low-pass filter — warmth control
    filter = ctx.createBiquadFilter();
    filter.type = 'lowpass';
    filter.frequency.value = cfg.filter;
    filter.Q.value = 0.7;
    filter.connect(masterGain);

    // Breath LFO — modulates everything
    breathLFO = ctx.createOscillator();
    breathLFO.type = 'sine';
    breathLFO.frequency.value = BREATH_FREQ;

    var lfoDepth = ctx.createGain();
    lfoDepth.gain.value = cfg.vol * 0.5; // modulation depth = half of volume

    breathLFO.connect(lfoDepth);

    // Pad oscillators — the harmonic bed
    cfg.ratios.forEach(function(ratio, i) {
      var osc = ctx.createOscillator();
      osc.type = 'sine';
      // Slight random detune for width (±0.5 Hz)
      osc.frequency.value = cfg.drone * ratio + (Math.random() - 0.5);

      var oscGain = ctx.createGain();
      // Higher harmonics quieter
      oscGain.gain.value = cfg.vol * (0.6 / (i + 1));

      // Breath modulates each oscillator's gain
      lfoDepth.connect(oscGain.gain);

      osc.connect(oscGain);
      oscGain.connect(filter);
      osc.start();
      padOscs.push(osc);
    });

    breathLFO.start();

    // Scroll-responsive filter
    window.addEventListener('scroll', onScroll, { passive: true });

    // Tab visibility — suspend when hidden
    document.addEventListener('visibilitychange', onVisibility);
  }

  // ── Generative Events ──
  // Occasional shimmer tones that emerge and dissolve
  function scheduleEvent() {
    var delay = 12 + Math.random() * 25; // 12-37 seconds
    eventTimer = setTimeout(function() {
      if (!playing) return;
      playEvent();
      scheduleEvent();
    }, delay * 1000);
  }

  function playEvent() {
    if (!ctx) return;
    var osc = ctx.createOscillator();
    var gain = ctx.createGain();
    var t = ctx.currentTime;

    // Event frequency: 2-5x the drone, occasionally harmonic
    var multipliers = [2, 2.5, 3, 4, 5, 1.5, 3.5];
    var mult = multipliers[Math.floor(Math.random() * multipliers.length)];
    osc.type = 'sine';
    osc.frequency.value = cfg.drone * mult + (Math.random() - 0.5) * 2;

    gain.gain.value = 0;
    osc.connect(gain);
    gain.connect(filter);

    // Gentle fade in over 3s, hold, fade out over 4s
    gain.gain.setTargetAtTime(0.015 + Math.random() * 0.01, t, 2);
    gain.gain.setTargetAtTime(0, t + 6, 2.5);

    osc.start(t);
    osc.stop(t + 18);
  }

  // ── Drift ──
  // Pad oscillators slowly wander in pitch
  function scheduleDrift() {
    var delay = 6 + Math.random() * 14; // 6-20 seconds
    driftTimer = setTimeout(function() {
      if (!playing || padOscs.length === 0) return;
      var i = Math.floor(Math.random() * padOscs.length);
      var osc = padOscs[i];
      var base = cfg.drone * cfg.ratios[i];
      var drift = base + (Math.random() - 0.5) * 1.5; // ±0.75 Hz from base
      osc.frequency.setTargetAtTime(drift, ctx.currentTime, 4);
      scheduleDrift();
    }, delay * 1000);
  }

  // ── Scroll Response ──
  function onScroll() {
    if (!playing || !filter) return;
    var maxScroll = document.documentElement.scrollHeight - window.innerHeight;
    if (maxScroll <= 0) return;
    var pct = Math.min(window.scrollY / maxScroll, 1);
    // Deeper into page = slightly brighter (filter opens 80% → 120% of base)
    var cutoff = cfg.filter * (0.8 + pct * 0.4);
    filter.frequency.setTargetAtTime(cutoff, ctx.currentTime, 0.5);
  }

  // ── Tab Visibility ──
  function onVisibility() {
    if (!ctx) return;
    if (document.hidden && playing) {
      ctx.suspend();
    } else if (!document.hidden && playing) {
      ctx.resume();
    }
  }

  // ── Toggle ──
  function fadeIn() {
    if (!ctx) init();
    if (ctx.state === 'suspended') ctx.resume();
    masterGain.gain.setTargetAtTime(cfg.vol, ctx.currentTime, 2);
    playing = true;
    scheduleEvent();
    scheduleDrift();
    localStorage.setItem('field-audio', '1');
    updateUI();
  }

  function fadeOut() {
    masterGain.gain.setTargetAtTime(0, ctx.currentTime, 1.5);
    playing = false;
    clearTimeout(eventTimer);
    clearTimeout(driftTimer);
    localStorage.setItem('field-audio', '0');
    setTimeout(function() {
      if (!playing && ctx) ctx.suspend();
    }, 6000);
    updateUI();
  }

  function toggle() {
    if (playing) fadeOut();
    else fadeIn();
  }

  // ── UI ──
  function injectUI() {
    var el = document.createElement('div');
    el.id = 'fa';
    el.innerHTML =
      '<button id="fa-btn" title="Field audio — breathe with the field" aria-label="Toggle field audio">' +
        '<span class="fa-glyph">\u03C8</span>' +
      '</button>';

    var style = document.createElement('style');
    style.textContent =
      '#fa{position:fixed;bottom:20px;left:20px;z-index:999}' +
      '#fa-btn{width:40px;height:40px;border-radius:50%;border:1px solid #1a1a2e;' +
        'background:rgba(13,13,20,0.92);color:#555;cursor:pointer;font-size:18px;' +
        'display:flex;align-items:center;justify-content:center;transition:all 0.4s;' +
        'backdrop-filter:blur(12px);padding:0;font-family:Georgia,serif}' +
      '#fa-btn:hover{border-color:#333;color:#888;background:rgba(18,18,28,0.95)}' +
      '#fa.breathing #fa-btn{color:#7b68ee;border-color:rgba(123,104,238,0.3);' +
        'animation:fa-breathe ' + BREATH + 's ease-in-out infinite}' +
      '.fa-glyph{line-height:1;margin-top:-1px}' +
      '@keyframes fa-breathe{' +
        '0%,100%{box-shadow:0 0 6px rgba(123,104,238,0.1)}' +
        '50%{box-shadow:0 0 20px rgba(123,104,238,0.4)}' +
      '}' +
      '@media(max-width:700px){#fa{bottom:12px;left:12px}' +
        '#fa-btn{width:36px;height:36px;font-size:16px}}';

    document.head.appendChild(style);
    document.body.appendChild(el);

    document.getElementById('fa-btn').addEventListener('click', toggle);
  }

  function updateUI() {
    var el = document.getElementById('fa');
    if (!el) return;
    if (playing) {
      el.classList.add('breathing');
    } else {
      el.classList.remove('breathing');
    }
  }

  // ── Init ──
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectUI);
  } else {
    injectUI();
  }

  // Auto-resume if previously enabled (still requires gesture — browser will block,
  // but the UI state will show it was on, and first click resumes)
  if (localStorage.getItem('field-audio') === '1') {
    // Mark UI as "was playing" so user knows to click
    setTimeout(function() {
      var btn = document.getElementById('fa-btn');
      if (btn) btn.title = 'Field audio was on — click to resume';
    }, 100);
  }

})();
