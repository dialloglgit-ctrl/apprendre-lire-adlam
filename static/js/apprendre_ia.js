/**
 * PROMET – Page "IA Apprendre Pulaar en Adlam"
 * Gère les 4 onglets : Lire / Prononcer / Écrire / Converser
 */

(function () {
  // ── Utilitaires ────────────────────────────────────────────────────────────

  const $ = id => document.getElementById(id);
  const CSRF = () => {
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? m[1] : '';
  };

  const API_BASE_URL = (window.PROMET_API_BASE_URL || '').replace(/\/+$/, '');

  function apiUrl(path) {
    if (!path) return path;
    if (/^https?:\/\//i.test(path)) return path;
    const normalizedPath = path.startsWith('/') ? path : `/${path}`;
    return API_BASE_URL ? `${API_BASE_URL}${normalizedPath}` : normalizedPath;
  }

  function post(url, data) {
    return fetch(apiUrl(url), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF() },
      body: JSON.stringify(data),
    }).then(r => r.json());
  }

  function get(url) {
    return fetch(apiUrl(url)).then(r => r.json());
  }

  const STORAGE_TAB_KEY = 'promet_ia_last_tab';
  const STORAGE_CONV_KEY = 'promet_ia_conv_history';

  // ── Données injectées par Django ───────────────────────────────────────────
  let PHRASES = [];
  let LETTRES = [];

  try {
    const phrasesEl = document.getElementById('phrases-data');
    const lettresEl = document.getElementById('lettres-data');
    if (phrasesEl) PHRASES = JSON.parse(phrasesEl.textContent);
    if (lettresEl) LETTRES = JSON.parse(lettresEl.textContent);
  } catch (e) { console.error('Données JSON invalides', e); }

  // ── Onglets ────────────────────────────────────────────────────────────────
  function activateTab(name) {
    if (!name) return;
    document.querySelectorAll('.ia-tabs .tab-btn').forEach(b => {
      b.classList.remove('active');
      b.setAttribute('aria-selected', 'false');
    });
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    const btn = document.querySelector(`.ia-tabs .tab-btn[data-tab="${name}"]`);
    if (!btn) return;

    btn.classList.add('active');
    btn.setAttribute('aria-selected', 'true');

    const tab = document.getElementById('tab-' + name);
    if (tab) tab.classList.add('active');

    localStorage.setItem(STORAGE_TAB_KEY, name);
  }

  document.querySelectorAll('.ia-tabs .tab-btn').forEach(btn => {
    btn.addEventListener('click', () => activateTab(btn.dataset.tab));
  });

  const storedTab = localStorage.getItem(STORAGE_TAB_KEY);
  if (storedTab) activateTab(storedTab);

  // ── Mode cards → clic active l'onglet correspondant ────────────────────────
  document.querySelectorAll('.ia-mode-card[data-goto-tab]').forEach(card => {
    card.addEventListener('click', () => {
      activateTab(card.dataset.gotoTab);
      const tabs = document.querySelector('.ia-tabs');
      if (tabs) tabs.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });

  // ── Bouton "S'entraîner" dans l'onglet Lire → bascule vers Écrire ──────────
  document.addEventListener('click', e => {
    const btn = e.target.closest('.ia-learn-btn');
    if (!btn) return;
    const lat = btn.dataset.latin;
    const adl = btn.dataset.adlam;
    const fr  = btn.dataset.fr;
    // Basculer vers onglet Écrire et charger la phrase
    activateTab('ecrire');
    loadPhraseEcrire({ latin: lat, adlam: adl, fr: fr });
    const tabs = document.querySelector('.ia-tabs');
    if (tabs) tabs.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  // ══════════════════════════════════════════════════════════════════════════
  // ONGLET LIRE
  // ══════════════════════════════════════════════════════════════════════════

  function applyLireFilter(filter) {
    let visibleCount = 0;
    document.querySelectorAll('.phrase-card').forEach(card => {
      const visible = (filter === 'all' || card.dataset.cat === filter);
      card.style.display = visible ? '' : 'none';
      if (visible) visibleCount += 1;
    });

    const empty = $('phrase-empty');
    if (empty) empty.style.display = visibleCount ? 'none' : 'block';
  }

  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      applyLireFilter(btn.dataset.filter);
    });
  });

  applyLireFilter('all');

  // ══════════════════════════════════════════════════════════════════════════
  // ONGLET ÉCRIRE
  // ══════════════════════════════════════════════════════════════════════════

  let ecrireIndex = 0;
  let ecrireScore = 0;
  let ecrireTotal = 0;
  let ecrireCurrent = null;
  const shuffled = [...PHRASES].sort(() => Math.random() - 0.5);

  function loadPhraseEcrire(phrase) {
    ecrireCurrent = phrase;
    $('ecrire-fr').textContent = phrase.fr;
    $('ecrire-hint').style.display = 'none';
    $('ecrire-hint').textContent = '';
    $('ecrire-input').value = '';
    $('ecrire-input').className = 'adlam-input';
    $('ecrire-feedback').style.display = 'none';
    $('ecrire-correct').style.display = 'none';
  }

  function nextPhraseEcrire() {
    if (shuffled.length === 0) return;
    loadPhraseEcrire(shuffled[ecrireIndex % shuffled.length]);
    ecrireIndex++;
    updateEcrireProgress();
  }

  function updateEcrireProgress() {
    const total = shuffled.length;
    const done  = Math.min(ecrireIndex, total);
    $('ecrire-count').textContent = `${done} / ${total}`;
    $('ecrire-score-label').textContent = `Score : ${ecrireScore} pt`;
    const pct = total ? (done / total * 100) : 0;
    $('ecrire-progress-bar').style.width = pct + '%';
  }

  // Initialisation
  if (shuffled.length > 0) {
    loadPhraseEcrire(shuffled[0]);
    ecrireIndex = 1;
    updateEcrireProgress();
  }

  // Bouton Indice
  $('ecrire-hint-btn') && $('ecrire-hint-btn').addEventListener('click', () => {
    if (!ecrireCurrent) return;
    const hint = $('ecrire-hint');
    if (hint.style.display === 'none') {
      hint.textContent = '→ ' + ecrireCurrent.latin;
      hint.style.display = 'block';
    } else {
      hint.style.display = 'none';
    }
  });

  // Bouton Écouter (phrase cible)
  $('ecrire-audio-btn') && $('ecrire-audio-btn').addEventListener('click', () => {
    if (!ecrireCurrent) return;
    const url = apiUrl(`/api/v1/audio/texte/?texte=${encodeURIComponent(ecrireCurrent.latin)}&lang=fr`);
    playAudioUrl(url, $('ecrire-audio-btn'));
  });

  // Bouton Suivante
  $('ecrire-suivant') && $('ecrire-suivant').addEventListener('click', nextPhraseEcrire);

  // Bouton Valider (correction IA)
  $('ecrire-valider') && $('ecrire-valider').addEventListener('click', async () => {
    if (!ecrireCurrent) return;
    const reponse = $('ecrire-input').value.trim();
    if (!reponse) { $('ecrire-input').focus(); return; }

    const btn = $('ecrire-valider');
    btn.disabled = true;
    btn.textContent = '⏳ Correction…';

    try {
      const data = await post('/api/v1/evaluer/', {
        reponse: reponse,
        reponse_attendue: ecrireCurrent.adlam,
      });

      const fb = $('ecrire-feedback');
      const msg = $('ecrire-feedback-msg');
      const diff = $('ecrire-diff');

      fb.style.display = 'block';
      fb.className = 'feedback-panel show ' + (data.succes ? 'correct' : 'wrong');

      if (data.succes) {
        msg.innerHTML = `<strong>✅ Parfait !</strong> +${data.points_earned || 10} pts`;
        ecrireScore += (data.points_earned || 10);
        $('ecrire-input').className = 'adlam-input correct';
      } else {
        msg.innerHTML = `<strong>❌</strong> ${data.feedback || 'Essaie encore.'}`;
        $('ecrire-input').className = 'adlam-input wrong';
      }

      diff.innerHTML = data.diff_html || '';

      // Toujours montrer la bonne réponse
      const correctRow = $('ecrire-correct');
      correctRow.style.display = 'flex';
      $('ecrire-correct-adlam').textContent = ecrireCurrent.adlam;
      $('ecrire-correct-audio').dataset.audioUrl =
        apiUrl(`/api/v1/audio/texte/?texte=${encodeURIComponent(ecrireCurrent.latin)}&lang=fr`);

      updateEcrireProgress();

    } catch (err) {
      $('ecrire-feedback-msg').textContent = 'Erreur réseau. Réessaie.';
      $('ecrire-feedback').style.display = 'block';
    } finally {
      btn.disabled = false;
      btn.textContent = '✅ Corriger avec l\'IA';
    }
  });

  // Audio bouton correct answer
  document.addEventListener('click', e => {
    const btn = e.target.closest('#ecrire-correct-audio');
    if (!btn || !btn.dataset.audioUrl) return;
    playAudioUrl(btn.dataset.audioUrl, btn);
  });

  // ══════════════════════════════════════════════════════════════════════════
  // ONGLET CONVERSER
  // ══════════════════════════════════════════════════════════════════════════

  const convInput  = $('conv-input');
  const convEnvoyer = $('conv-envoyer');
  const convResult  = $('conv-result');
  const convHistory = $('conv-history');
  const convHistoryHeader = $('conv-history-header');
  const convClearBtn = $('conv-clear-btn');

  function toggleHistoryHeader() {
    if (!convHistoryHeader || !convHistory) return;
    convHistoryHeader.style.display = convHistory.children.length ? 'flex' : 'none';
  }

  function saveHistoryToStorage() {
    if (!convHistory) return;
    const items = [...convHistory.querySelectorAll('.conv-history-item')].map(item => ({
      original: item.querySelector('.conv-hist-original')?.textContent || '',
      adlam: item.querySelector('.conv-hist-adlam')?.textContent || '',
      latin: item.querySelector('.conv-hist-latin')?.textContent || '',
    }));
    localStorage.setItem(STORAGE_CONV_KEY, JSON.stringify(items));
  }

  function restoreHistoryFromStorage() {
    if (!convHistory) return;
    const raw = localStorage.getItem(STORAGE_CONV_KEY);
    if (!raw) return;
    try {
      const items = JSON.parse(raw);
      if (!Array.isArray(items)) return;
      items.slice().reverse().forEach(entry => {
        const latin = entry.latin || entry.original || '';
        const audioUrl = apiUrl(`/api/v1/audio/texte/?texte=${encodeURIComponent(latin)}&lang=fr`);
        addToHistory(entry.original || '', entry.adlam || '', latin, audioUrl, false);
      });
      toggleHistoryHeader();
    } catch (_) {}
  }

  restoreHistoryFromStorage();

  convEnvoyer && convEnvoyer.addEventListener('click', async () => {
    const texte = convInput.value.trim();
    if (!texte) { convInput.focus(); return; }

    convEnvoyer.disabled = true;
    convEnvoyer.textContent = '⏳';

    try {
      // 1. Appel au tuteur IA (Gemini)
      const chat = await post('/api/chat-ia/', { message: texte });
      if (chat.error) throw new Error(chat.error);

      const reply = chat.reply;
      const adlam = chat.adlam;

      // 2. Afficher le résultat
      $('conv-bubble-user').textContent = texte;
      $('conv-adlam').textContent = adlam;
      $('conv-latin').textContent = reply;
      convResult.style.display = 'block';

      // 3. Audio
      const audioLatin = $('conv-audio-latin');
      const audioAdlam = $('conv-audio-adlam');
      const audioUrl = apiUrl(`/api/v1/audio/texte/?texte=${encodeURIComponent(reply)}&lang=fr`);
      audioLatin.dataset.audioUrl = audioUrl;
      audioAdlam.dataset.audioUrl = audioUrl;

      // 4. Masquer correction si non applicable
      $('conv-correction-row').style.display = 'none';

      // 5. Ajouter à l'historique
      addToHistory(texte, adlam, reply, audioUrl);

      // 6. Vider input
      convInput.value = '';

    } catch (err) {
      console.error(err);
    } finally {
      convEnvoyer.disabled = false;
      convEnvoyer.textContent = 'Envoyer';
    }
  });

  // Enter dans le textarea
  convInput && convInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      convEnvoyer && convEnvoyer.click();
    }
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      convEnvoyer && convEnvoyer.click();
    }
  });

  convClearBtn && convClearBtn.addEventListener('click', () => {
    if (!convHistory) return;
    convHistory.innerHTML = '';
    localStorage.removeItem(STORAGE_CONV_KEY);
    toggleHistoryHeader();
  });

  // Audio boutons conversation
  document.addEventListener('click', e => {
    const btn = e.target.closest('#conv-audio-latin, #conv-audio-adlam');
    if (!btn || !btn.dataset.audioUrl) return;
    playAudioUrl(btn.dataset.audioUrl, btn);
  });

  function addToHistory(original, adlam, latin, audioUrl, persist = true) {
    const item = document.createElement('div');
    item.className = 'conv-history-item';
    item.innerHTML = `
      <div class="conv-hist-original">${escHtml(original)}</div>
      <div class="conv-hist-adlam adlam-text" dir="rtl">${escHtml(adlam)}</div>
      <div class="conv-hist-latin">${escHtml(latin)}</div>
      <button class="speak-btn speak-btn-sm" data-audio-url="${escHtml(audioUrl)}" title="Écouter">🔊</button>
    `;
    convHistory.prepend(item);
    // Limiter à 10 entrées
    while (convHistory.children.length > 10) {
      convHistory.removeChild(convHistory.lastChild);
    }
    toggleHistoryHeader();
    if (persist) saveHistoryToStorage();
  }

  function escHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // ── Lecture audio centralisée (délégation) ──────────────────────────────────
  function playAudioUrl(url, btn) {
    // Utilise l'objet Audio natif ; audio.js gère le singleton
    const event = new CustomEvent('promet:play-audio', { detail: { url, btn } });
    document.dispatchEvent(event);
  }

  // Écouter l'événement custom depuis audio.js ou gérer directement
  document.addEventListener('promet:play-audio', e => {
    const { url, btn } = e.detail;
    let currentAudio = window._prometCurrentAudio;
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
    }
    if (btn) {
      document.querySelectorAll('.speak-btn.speaking').forEach(b => b.classList.remove('speaking', 'loading'));
      btn.classList.add('loading');
    }
    const audio = new Audio(url);
    window._prometCurrentAudio = audio;
    audio.addEventListener('canplaythrough', () => {
      if (btn) { btn.classList.remove('loading'); btn.classList.add('speaking'); }
    }, { once: true });
    audio.addEventListener('ended', () => {
      if (btn) btn.classList.remove('speaking', 'loading');
    }, { once: true });
    audio.addEventListener('error', () => {
      if (btn) btn.classList.remove('speaking', 'loading');
    }, { once: true });
    audio.play().catch(() => { if (btn) btn.classList.remove('speaking', 'loading'); });
  });

  // ── Clavier Adlam dans l'onglet Écrire ────────────────────────────────────
  // On clone le clavier existant ou on charge clavier_adlam.js
  // window.CLAVIER_TARGET est utilisé par clavier_adlam.js
  const clavierContainer = $('clavier-ecrire');
  if (clavierContainer && typeof window.buildClavierAdlam === 'function') {
    window.buildClavierAdlam(clavierContainer, $('ecrire-input'));
  } else {
    // Fallback : set la cible globale pour clavier_adlam.js
    window.CLAVIER_TARGET = 'ecrire-input';
    const clavierScript = document.createElement('script');
    clavierScript.src = '/static/js/clavier_adlam.js';
    document.body.appendChild(clavierScript);
  }

  // ══════════════════════════════════════════════════════════════════════════
  // ONGLET PRONONCER (micro)
  // ══════════════════════════════════════════════════════════════════════════

  // Vérification support micro
  if (!PrometMicro.isSupported()) {
    const el = $('micro-not-supported');
    if (el) el.style.display = 'block';
    const guided = $('micro-guided');
    if (guided) guided.style.display = 'none';
  }

  // Phrase courante pour l'onglet Prononcer
  let prononcerIndex = 0;
  let prononcerScore = 0;
  const pronShuffled = [...PHRASES].sort(() => Math.random() - 0.5);

  function loadPhrasePrononcer(phrase) {
    if (!phrase) return;
    $('prononcer-fr').textContent    = phrase.fr;
    $('prononcer-adlam').textContent = phrase.adlam;
    $('prononcer-latin').textContent = phrase.latin;
    if ($('prononcer-num')) $('prononcer-num').textContent = String(Math.max(1, prononcerIndex));
    $('micro-result').style.display  = 'none';
    $('micro-listening').style.display = 'none';
    $('micro-start-btn').style.display = '';
    $('micro-live-text').textContent = 'En écoute…';
    updatePrononcerProgress();

    // Mettre à jour le bouton audio
    const audioBtn = $('prononcer-audio-btn');
    if (audioBtn) {
      audioBtn.dataset.audioUrl = apiUrl(`/api/v1/audio/texte/?texte=${encodeURIComponent(phrase.latin)}&lang=fr`);
    }
  }

  function updatePrononcerProgress() {
    const total = pronShuffled.length;
    const done  = Math.min(prononcerIndex, total);
    if ($('prononcer-count'))       $('prononcer-count').textContent = `${done} / ${total}`;
    if ($('prononcer-score-label')) $('prononcer-score-label').textContent = `Score : ${prononcerScore} pt`;
    const pct = total ? (done / total * 100) : 0;
    const bar = $('prononcer-progress-bar');
    if (bar) bar.style.width = pct + '%';
  }

  if (pronShuffled.length > 0) {
    loadPhrasePrononcer(pronShuffled[0]);
    prononcerIndex = 1;
  }

  // ── Bouton démarrer micro ──────────────────────────────────────────────────
  $('micro-start-btn') && $('micro-start-btn').addEventListener('click', () => {
    if (!PrometMicro.isSupported()) return;

    const current = pronShuffled[(prononcerIndex - 1) % pronShuffled.length];
    if (!current) return;

    $('micro-start-btn').style.display  = 'none';
    $('micro-listening').style.display  = '';
    $('micro-result').style.display     = 'none';

    let finalTranscript = '';

    PrometMicro.start({
      lang: 'fr-FR',
      continuous: false,
      onResult: (transcript, isFinal) => {
        $('micro-live-text').textContent = transcript || 'En écoute…';
        if (isFinal) finalTranscript = transcript;
      },
      onEnd: async () => {
        $('micro-listening').style.display = 'none';
        $('micro-start-btn').style.display = '';

        if (!finalTranscript) {
          $('micro-result').style.display = 'block';
          $('micro-said').textContent     = '(rien détecté)';
          $('micro-expected').textContent = current.latin;
          $('micro-score-circle').className = 'micro-score-circle score-bad';
          $('micro-score-pct').textContent  = '0%';
          $('micro-score-label').textContent = 'Aucune parole détectée';
          $('micro-score-detail').textContent = 'Réessaie en parlant clairement dans le micro.';
          $('micro-diff').innerHTML = '';
          return;
        }

        // Envoyer à l'API IA pour évaluation phonétique
        try {
          const data = await post('/api/v1/evaluer/', {
            reponse: finalTranscript,
            reponse_attendue: current.latin,
          });

          const score = data.score || 0;  // 0–100
          const pct   = Math.round(score);

          $('micro-result').style.display = 'block';
          $('micro-said').textContent     = finalTranscript;
          $('micro-expected').textContent = current.latin;
          $('micro-diff').innerHTML       = data.diff_html || '';

          // Couleur selon le score
          const circle = $('micro-score-circle');
          circle.className = 'micro-score-circle ' +
            (pct >= 80 ? 'score-perfect' : pct >= 50 ? 'score-ok' : 'score-bad');
          $('micro-score-pct').textContent = pct + '%';

          let label, detail;
          if (data.exact) {
            label  = '🎉 Parfait !';
            detail = 'Excellente prononciation !';
            prononcerScore += 10;
          } else if (data.near_phonetic) {
            label  = '👍 Très bien !';
            detail = 'Légère différence phonétique, continue comme ça.';
            prononcerScore += 7;
          } else if (pct >= 50) {
            label  = '🟡 Pas mal';
            detail = data.feedback || 'Continue à t\'entraîner.';
            prononcerScore += 3;
          } else {
            label  = '❌ À améliorer';
            detail = data.feedback || 'Écoute d\'abord la bonne prononciation, puis réessaie.';
          }

          $('micro-score-label').textContent  = label;
          $('micro-score-detail').textContent = detail;
          updatePrononcerProgress();

        } catch (err) {
          console.error('Erreur évaluation prononciation', err);
          $('micro-result').style.display = 'block';
          $('micro-score-label').textContent = 'Erreur réseau.';
        }
      },
      onError: (code, msg) => {
        $('micro-listening').style.display = 'none';
        $('micro-start-btn').style.display = '';
        $('micro-result').style.display    = 'block';
        $('micro-said').textContent        = '';
        $('micro-score-label').textContent = msg;
        $('micro-score-circle').className  = 'micro-score-circle score-bad';
        $('micro-score-pct').textContent   = '!';
      },
    });
  });

  // Bouton Arrêter
  $('micro-stop-btn') && $('micro-stop-btn').addEventListener('click', () => {
    PrometMicro.stop();
  });

  // Bouton Réessayer
  $('prononcer-retry-btn') && $('prononcer-retry-btn').addEventListener('click', () => {
    const current = pronShuffled[(prononcerIndex - 1) % pronShuffled.length];
    if (current) loadPhrasePrononcer(current);
  });

  // Bouton Suivante
  $('prononcer-suivant-btn') && $('prononcer-suivant-btn').addEventListener('click', () => {
    prononcerIndex = (prononcerIndex % pronShuffled.length) + 1;
    loadPhrasePrononcer(pronShuffled[prononcerIndex - 1]);
  });

  // Bouton audio phrase correcte
  $('prononcer-audio-btn') && $('prononcer-audio-btn').addEventListener('click', function () {
    const url = this.dataset.audioUrl;
    if (url) playAudioUrl(url, this);
  });

  // ── Bouton micro rapide sur les cartes Lire ────────────────────────────────
  document.addEventListener('click', e => {
    const btn = e.target.closest('.micro-btn');
    if (!btn) return;
    if (!PrometMicro.isSupported()) {
      alert('Reconnaissance vocale non disponible. Utilisez Chrome ou Edge.');
      return;
    }
    // Basculer vers l'onglet Prononcer et charger la phrase
    const lat = btn.dataset.latin;
    const fr  = btn.dataset.fr;
    const phrase = PHRASES.find(p => p.latin === lat);
    if (!phrase) return;

    activateTab('prononcer');
    // Charger cette phrase spécifique en début de liste
    pronShuffled.unshift({ ...phrase });
    prononcerIndex = 1;
    loadPhrasePrononcer(pronShuffled[0]);
    // Scroll vers le micro
    $('micro-start-btn') && $('micro-start-btn').scrollIntoView({ behavior: 'smooth', block: 'center' });
  });

})();
