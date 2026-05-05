// PROMET – main.js  (Design PRO + animations + PWA)
'use strict';

// ── Menu mobile ─────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('.menu-toggle');
  const links  = document.querySelector('.navbar-links');
  if (toggle && links) {
    toggle.addEventListener('click', () => links.classList.toggle('open'));
    document.addEventListener('click', (e) => {
      if (!toggle.contains(e.target) && !links.contains(e.target)) {
        links.classList.remove('open');
      }
    });
  }

  // Tabbar – active link
  const tabLinks = document.querySelectorAll('.mobile-tabbar a');
  tabLinks.forEach(a => {
    if (a.href === location.href || location.pathname.startsWith(new URL(a.href).pathname)) {
      a.classList.add('active');
    }
  });

  // PWA Service Worker
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch(() => {});
  }
});

// ── Confetti ─────────────────────────────────────────────────────────────────
function launchConfetti(count = 40) {
  const colors = ['#58cc02','#ffc800','#1cb0f6','#ff4b4b','#ce82ff','#ff9600'];
  for (let i = 0; i < count; i++) {
    const el = document.createElement('div');
    el.className = 'confetti-piece';
    el.style.cssText = `
      left: ${Math.random() * 100}vw;
      width: ${6 + Math.random() * 8}px;
      height: ${6 + Math.random() * 8}px;
      background: ${colors[Math.floor(Math.random() * colors.length)]};
      animation-delay: ${Math.random() * .8}s;
      animation-duration: ${1.5 + Math.random() * 1}s;
      border-radius: ${Math.random() > .5 ? '50%' : '2px'};
    `;
    document.body.appendChild(el);
    el.addEventListener('animationend', () => el.remove());
  }
}
window.launchConfetti = launchConfetti;

// ── XP bar animation helper ───────────────────────────────────────────────────
function animateXpBar(bar, targetPct) {
  bar.style.width = '0%';
  requestAnimationFrame(() => {
    bar.style.transition = 'width .8s cubic-bezier(.22,1,.36,1)';
    bar.style.width = targetPct + '%';
  });
}
window.animateXpBar = animateXpBar;

// ── Heart animation ───────────────────────────────────────────────────────────
function loseHeart(hearts) {
  const active = hearts.querySelectorAll('.heart:not(.lost)');
  if (active.length > 0) {
    const last = active[active.length - 1];
    last.classList.add('lost');
    last.style.transform = 'scale(1.4)';
    setTimeout(() => { last.style.transform = ''; }, 200);
  }
}
window.loseHeart = loseHeart;

// ── Dark mode ────────────────────────────────────────────────────────────────
(function () {
  const STORAGE_KEY = 'promet-theme';
  const root = document.documentElement;

  function applyTheme(theme) {
    root.setAttribute('data-theme', theme);
    const btn = document.getElementById('dark-toggle-btn');
    if (btn) btn.textContent = theme === 'dark' ? '☀️' : '🌙';
  }

  const saved = localStorage.getItem(STORAGE_KEY);
  const preferred = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  applyTheme(saved || preferred);

  document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('dark-toggle-btn');
    if (!btn) return;
    const current = root.getAttribute('data-theme') || 'light';
    btn.textContent = current === 'dark' ? '☀️' : '🌙';
    btn.addEventListener('click', () => {
      const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      localStorage.setItem(STORAGE_KEY, next);
    });
  });
})();

// ── Page loader ───────────────────────────────────────────────────────────────
(function () {
  const loader = document.createElement('div');
  loader.className = 'page-loader';
  document.documentElement.prepend(loader);
  window.addEventListener('load', () => {
    loader.classList.add('done');
    setTimeout(() => loader.remove(), 400);
  });
})();

// ── Back to top ───────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const btn = document.createElement('button');
  btn.className = 'back-to-top';
  btn.title = 'Revenir en haut';
  btn.textContent = '↑';
  document.body.appendChild(btn);
  window.addEventListener('scroll', () => {
    btn.classList.toggle('visible', window.scrollY > 300);
  }, { passive: true });
  btn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
});

// ── Recherche globale (live) ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('global-search-input');
  const dropdown = document.getElementById('search-dropdown');
  if (!input || !dropdown) return;

  let debounce = null;

  input.addEventListener('input', () => {
    clearTimeout(debounce);
    const q = input.value.trim();
    if (q.length < 2) { dropdown.style.display = 'none'; return; }
    debounce = setTimeout(() => {
      fetch(`/recherche/?q=${encodeURIComponent(q)}&format=json`)
        .then(r => r.json())
        .then(data => renderSearchResults(data, dropdown))
        .catch(() => { dropdown.style.display = 'none'; });
    }, 220);
  });

  document.addEventListener('click', (e) => {
    if (!input.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.style.display = 'none';
    }
  });

  function renderSearchResults(data, el) {
    if (!data.total) { el.style.display = 'none'; return; }
    let html = '';
    const groups = [
      { key: 'lecons',  ico: '📘', label: 'Leçons'  },
      { key: 'livres',  ico: '📚', label: 'Livres'  },
      { key: 'videos',  ico: '🎬', label: 'Vidéos'  },
    ];
    groups.forEach(({ key, ico, label }) => {
      const items = data[key] || [];
      if (!items.length) return;
      html += `<div class="srg"><div class="srg-title">${label}</div>`;
      items.forEach(item => {
        html += `<a href="${item.url}"><span class="sr-ico">${ico}</span>${item.titre}<span class="sr-sub">${item.sub || ''}</span></a>`;
      });
      html += '</div>';
    });
    el.innerHTML = html;
    el.style.display = 'block';
  }
});

