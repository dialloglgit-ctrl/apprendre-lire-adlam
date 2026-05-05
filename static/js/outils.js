/**
 * PROMET – Page Outils IA
 * Gère les 3 onglets : Traduction, Translittération, Correction IA
 */

// ── Helpers CSRF ──────────────────────────────────────────────────────────────
function getCsrf() {
  return document.cookie.split('; ').find(r => r.startsWith('csrftoken='))?.split('=')[1] || '';
}

const API_BASE_URL = (window.PROMET_API_BASE_URL || '').replace(/\/+$/, '');

function apiUrl(path) {
  if (!path) return path;
  if (/^https?:\/\//i.test(path)) return path;
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return API_BASE_URL ? `${API_BASE_URL}${normalizedPath}` : normalizedPath;
}

async function apiPost(url, data) {
  const resp = await fetch(apiUrl(url), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
    body: JSON.stringify(data),
  });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

// ── Onglets ───────────────────────────────────────────────────────────────────
document.querySelectorAll('.filter-tab[data-tab]').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-tab[data-tab]').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tool-panel').forEach(p => (p.style.display = 'none'));
    btn.classList.add('active');
    document.getElementById('tab-' + btn.dataset.tab).style.display = '';
  });
});

// ── Onglet Traduction ─────────────────────────────────────────────────────────
const btnTraduire   = document.getElementById('btn-traduire');
const tradInput     = document.getElementById('trad-input');
const tradResult    = document.getElementById('trad-result');
const tradPulLatin  = document.getElementById('trad-pul-latin');
const tradPulAdlam  = document.getElementById('trad-pul-adlam');
const tradCoverage  = document.getElementById('trad-coverage');
const tradTokens    = document.getElementById('trad-tokens');

btnTraduire && btnTraduire.addEventListener('click', async () => {
  const texte = tradInput.value.trim();
  if (!texte) return;
  const depuis = document.querySelector('input[name="trad-lang"]:checked').value;
  btnTraduire.disabled = true;
  btnTraduire.textContent = '…';
  try {
    const data = await apiPost('/api/v1/traduire/', { texte, depuis });
    tradPulLatin.textContent  = data.pul_latin  || '—';
    tradPulAdlam.textContent  = data.pul_adlam  || '—';
    tradCoverage.textContent  = `${data.coverage}% des mots traduits (${data.found}/${data.total})`;
    // Détail token par token
    let html = '<div style="display:flex;flex-wrap:wrap;gap:.3rem">';
    (data.tokens || []).forEach(t => {
      if (t.found === null) {
        html += `<span style="color:var(--text-muted)">${t.token}</span>`;
      } else if (t.found) {
        html += `<span class="token-found" title="${t.pul_latin}">${t.token}</span>`;
      } else {
        html += `<span class="token-missing" title="Non traduit">${t.token}</span>`;
      }
    });
    html += '</div>';
    tradTokens.innerHTML = html;
    tradResult.style.display = '';
  } catch (e) {
    tradResult.style.display = '';
    tradPulLatin.textContent = 'Erreur réseau.';
  } finally {
    btnTraduire.disabled = false;
    btnTraduire.textContent = 'Traduire →';
  }
});

// Recherche dans le dictionnaire
const dictSearch = document.getElementById('dict-search');
const dictGrid   = document.getElementById('dict-grid');

async function loadDictionary(depuis = 'fr', filter = '') {
  try {
    const resp = await fetch(apiUrl(`/api/v1/vocabulaire/?depuis=${depuis}`));
    const data = await resp.json();
    const vocab = (data.vocabulaire || []).filter(v =>
      !filter || v.input.toLowerCase().includes(filter.toLowerCase())
    );
    dictGrid.innerHTML = '';
    vocab.slice(0, 80).forEach(v => {
      const el = document.createElement('div');
      el.className = 'letter-card dict-card';
      el.style.cursor = 'pointer';
      el.innerHTML = `<span class="letter-adlam-big" dir="rtl" style="font-size:1.1rem">${v.pul_adlam}</span>
                      <span class="letter-name" style="font-size:.75rem">${v.pul_latin}</span>
                      <span class="letter-latin" style="font-size:.7rem;color:var(--text-muted)">${v.input}</span>`;
      el.addEventListener('click', () => {
        tradInput.value = v.input;
        document.getElementById('outils-tabs').querySelector('[data-tab="traduction"]').click();
        btnTraduire.click();
      });
      dictGrid.appendChild(el);
    });
  } catch (_) {}
}

dictSearch && dictSearch.addEventListener('input', () => {
  const depuis = document.querySelector('input[name="trad-lang"]:checked')?.value || 'fr';
  loadDictionary(depuis, dictSearch.value);
});

document.querySelectorAll('input[name="trad-lang"]').forEach(r =>
  r.addEventListener('change', () => loadDictionary(r.value))
);

// Charger le dico au démarrage
loadDictionary('fr');

// ── Onglet Translittération ───────────────────────────────────────────────────
const btnTranslit      = document.getElementById('btn-transliterer');
const translitInput    = document.getElementById('translit-input');
const translitResult   = document.getElementById('translit-result');
const translitOutput   = document.getElementById('translit-output');
const translitDirLabel = document.getElementById('translit-direction-label');

btnTranslit && btnTranslit.addEventListener('click', async () => {
  const texte = translitInput.value.trim();
  if (!texte) return;
  const sens = document.querySelector('input[name="translit-sens"]:checked').value;
  btnTranslit.disabled = true;
  btnTranslit.textContent = '…';
  try {
    const data = await apiPost('/api/v1/transliterer/', { texte, sens });
    translitOutput.textContent = data.result || '—';
    // Direction du résultat
    if (data.output_script === 'adlam') {
      translitOutput.setAttribute('dir', 'rtl');
      translitDirLabel.textContent = 'Résultat en Adlam';
    } else {
      translitOutput.setAttribute('dir', 'ltr');
      translitDirLabel.textContent = 'Résultat en latin Pulaar';
    }
    translitResult.style.display = '';
  } catch (e) {
    translitOutput.textContent = 'Erreur réseau.';
    translitResult.style.display = '';
  } finally {
    btnTranslit.disabled = false;
    btnTranslit.textContent = 'Convertir →';
  }
});

// Clavier Adlam dans l'onglet translittération
window.CLAVIER_TARGET = 'translit-input';
// Le clavier_adlam.js sera rechargé ou on initialise manuellement
document.addEventListener('DOMContentLoaded', () => {
  if (window._buildAdlamKeyboard) {
    window._buildAdlamKeyboard('clavier-translit', 'translit-input');
  }
});

// Table de correspondance
const TRANSLIT_TABLE = [
  ['mb','𞤸'],['kp','𞤹'],['nj','𞤶'],['ng','𞤴'],['ny','𞤻'],
  ['ch','𞤽'],['bh/ɓ','𞤩'],['dh/ɗ','𞤯'],['nh/ɲ','𞤰'],['kh/ŋ','𞤲'],
  ['a','𞤢'],['b','𞤦'],['d','𞤣'],['e','𞤫'],['f','𞤬'],
  ['g','𞤳'],['h','𞤷'],['i','𞤭'],['j','𞤼'],['l','𞤤'],
  ['m','𞤥'],['n','𞤲'],['o','𞤮'],['p','𞤨'],['r','𞤪'],
  ['s','𞤧'],['t','𞤵'],['v/w','𞤱'],['y','𞤺'],
];

const tableEl = document.getElementById('translit-table');
if (tableEl) {
  TRANSLIT_TABLE.forEach(([latin, adlam]) => {
    const el = document.createElement('div');
    el.className = 'letter-card';
    el.style.cursor = 'default';
    el.innerHTML = `<span class="letter-adlam-big" dir="rtl">${adlam}</span>
                    <span class="letter-latin">${latin}</span>`;
    el.addEventListener('click', () => {
      translitInput.value += latin;
      translitInput.focus();
    });
    tableEl.appendChild(el);
  });
}

// ── Onglet Correction IA ──────────────────────────────────────────────────────
const btnCorriger  = document.getElementById('btn-corriger');
const corrReponse  = document.getElementById('corr-reponse');
const corrAttendu  = document.getElementById('corr-attendu');
const corrResult   = document.getElementById('corr-result');

btnCorriger && btnCorriger.addEventListener('click', async () => {
  const reponse = corrReponse.value.trim();
  const attendu = corrAttendu.value.trim();
  if (!reponse || !attendu) return;
  btnCorriger.disabled = true;
  btnCorriger.textContent = '…';
  try {
    const data = await apiPost('/api/v1/evaluer/', { reponse, attendu });
    const scorePct = Math.round((data.score || 0) * 100);
    corrResult.classList.remove('show', 'correct', 'wrong', 'near');
    corrResult.classList.add('show');
    if (data.accepted) {
      corrResult.classList.add(data.exact ? 'correct' : 'near');
    } else {
      corrResult.classList.add('wrong');
    }
    let html = `<div class="feedback-title">${data.feedback_message || (data.accepted ? '✓ Correct' : '✗ Incorrect')}</div>`;
    html += `<div style="margin-top:.4rem">Score : <strong>${scorePct}%</strong></div>`;
    if (data.diff_html) {
      html += `<div style="margin-top:.5rem">${data.diff_html}</div>`;
    }
    if (!data.accepted && data.best_match) {
      html += `<div style="margin-top:.4rem">Suggestion : <span class="adlam-text">${data.best_match}</span></div>`;
    }
    corrResult.innerHTML = html;
    if (data.accepted && data.exact && typeof window.launchConfetti === 'function') {
      window.launchConfetti(30);
    }
  } catch (e) {
    corrResult.classList.add('show', 'wrong');
    corrResult.textContent = 'Erreur réseau.';
  } finally {
    btnCorriger.disabled = false;
    btnCorriger.textContent = 'Corriger →';
  }
});
