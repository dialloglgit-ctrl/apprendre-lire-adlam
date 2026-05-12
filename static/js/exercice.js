/**
 * PROMET – Logique des exercices interactifs (Design PRO)
 * Variables injectées depuis le template :
 *   EXERCICE_ID, TYPE, CHOIX
 */

document.addEventListener('DOMContentLoaded', () => {

  const resultatEl = document.getElementById('resultat');
  const pointsEl = document.getElementById('points-earned');
  const xpBarEl = document.getElementById('xp-bar');
  const heartsEl = document.getElementById('hearts-container');
  const btnValider = document.getElementById('btn-valider');
  const TXT = window.I18N || {};
  const defaultValidateLabel = btnValider ? btnValider.textContent : 'Valider';

  function getBestSuggestion(data) {
    return data.suggestion || data.best_match || '';
  }

  function afficherResultat(data) {
    if (!resultatEl) {
      return;
    }

    const succes = Boolean(data.succes);
    const scorePct = Math.round((data.score || 0) * 100);
    const suggestion = getBestSuggestion(data);
    const feedbackLevel = data.feedback_level || (succes ? 'perfect' : 'wrong');

    resultatEl.classList.remove('show', 'correct', 'wrong', 'near');
    resultatEl.classList.add('show');

    if (succes) {
      if (feedbackLevel === 'near' || feedbackLevel === 'phonetic' || data.near_phonetic) {
        resultatEl.classList.add('near');
      } else {
        resultatEl.classList.add('correct');
      }
    } else {
      resultatEl.classList.add('wrong');
    }

    let html = `<div class="feedback-title">${data.feedback_message || data.feedback || (succes ? (TXT.goodAnswer || 'Bonne reponse !') : (TXT.badAnswer || 'Mauvaise reponse.'))}</div>`;

    if (!succes) {
      html += `<div style="margin-top:.4rem"><strong>${TXT.correctAnswer || 'Reponse correcte'}:</strong> <span class="adlam-text">${data.reponse_correcte || ''}</span></div>`;
      if (suggestion) {
        html += `<div style="margin-top:.35rem">${TXT.closeSuggestion || 'Suggestion proche'}: <span class="adlam-text">${suggestion}</span></div>`;
      }
    }

    if (data.diff_html) {
      html += `<div style="margin-top:.5rem">${data.diff_html}</div>`;
    }

    html += `<div style="margin-top:.45rem;font-size:.85rem;opacity:.85">Score: ${scorePct}%</div>`;
    resultatEl.innerHTML = html;

    // Afficher le bouton "Question suivante" après toute réponse
    const btnSuivant = document.getElementById('btn-suivant');
    if (btnSuivant) btnSuivant.style.display = 'block';

    if (pointsEl) {
      const earned = Number(data.points_earned || 0);
      if (earned > 0) {
        pointsEl.textContent = `+${earned} XP`;
        pointsEl.style.display = 'block';
      } else {
        pointsEl.style.display = 'none';
      }
    }

    if (typeof data.total_points !== 'undefined' && xpBarEl && typeof window.animateXpBar === 'function') {
      window.animateXpBar(xpBarEl, Math.max(0, Math.min(100, Number(data.total_points || 0) % 100)));
    }

    if (succes && data.exact) {
      const lottieWrap = document.getElementById('lottie-success-wrap');
      const lottiePlayer = document.getElementById('lottie-success');
      if (lottieWrap && lottiePlayer) {
        lottieWrap.style.display = 'block';
        lottiePlayer.play();
        setTimeout(() => {
          lottieWrap.style.display = 'none';
        }, 2500);
      }

      if (typeof window.launchConfetti === 'function') {
        window.launchConfetti(40);
      }
    }

    if (!succes && heartsEl && typeof window.loseHeart === 'function') {
      window.loseHeart(heartsEl);
    }
  }

  async function soumettre(reponse) {
    const csrfToken = document.cookie
      .split('; ')
      .find(r => r.startsWith('csrftoken='))
      ?.split('=')[1];

    let resp;
    try {
      resp = await fetch(`/exercices/${EXERCICE_ID}/repondre/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken || '',
        },
        body: JSON.stringify({ reponse }),
      });
    } catch (error) {
      resultatEl.classList.remove('correct', 'near');
      resultatEl.classList.add('show', 'wrong');
      resultatEl.textContent = 'Erreur reseau.';
      return null;
    }

    if (resp.status === 401 || resp.status === 403) {
      resultatEl.classList.remove('correct', 'near');
      resultatEl.classList.add('show', 'wrong');
      resultatEl.textContent = TXT.loginRequired || 'Connectez-vous pour soumettre une reponse.';
      return null;
    }

    if (!resp.ok) {
      resultatEl.classList.remove('correct', 'near');
      resultatEl.classList.add('show', 'wrong');
      resultatEl.textContent = 'Erreur serveur.';
      return null;
    }

    const data = await resp.json();
    afficherResultat(data);
    return data;
  }

  // ── QCM ──
  const choixBtns = document.querySelectorAll('.qcm-btn');
  choixBtns.forEach(btn => {
    btn.addEventListener('click', async () => {
      choixBtns.forEach(b => {
        b.disabled = true;
      });
      const reponse = btn.dataset.valeur;
      btn.classList.add('selected');
      const payload = await soumettre(reponse);
      if (!payload) return;

      document.querySelectorAll('.qcm-btn').forEach(b => {
        if (b.dataset.valeur === reponse) {
          b.classList.remove('selected');
          b.classList.add(payload.succes ? 'correct' : 'wrong');
        }
        if (!payload.succes && payload.reponse_correcte && b.dataset.valeur === payload.reponse_correcte) {
          b.classList.add('correct');
        }
      });
    });
  });

  // ── Saisie libre ──
  if (btnValider) {
    btnValider.addEventListener('click', async () => {
      const input = document.getElementById('reponse-input');
      if (!input || !input.value.trim()) return;
      btnValider.disabled = true;
      btnValider.textContent = '...';
      await soumettre(input.value.trim());
      btnValider.disabled = false;
      btnValider.textContent = defaultValidateLabel;
    });

    // Valider avec Entrée
    const input = document.getElementById('reponse-input');
    if (input) {
      input.addEventListener('keydown', e => {
        if (e.key === 'Enter') btnValider.click();
      });
    }
  }
});
