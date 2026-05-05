/**
 * PROMET – Lecteur audio pour les lettres Adlam
 *
 * Tous les boutons [data-audio-url] déclenchent la lecture d'un fichier MP3
 * généré côté serveur via gTTS (endpoint /api/v1/audio/lettre/<pk>/).
 *
 * L'objet Audio est réutilisé (singleton) pour éviter les lectures multiples.
 */

(function () {
  let currentAudio = null;

  /**
   * Joue un fichier audio depuis une URL.
   * @param {string} url - URL du fichier MP3
   * @param {HTMLElement} btn - Bouton déclencheur (pour le feedback visuel)
   */
  function playAudio(url, btn) {
    // Arrêter l'audio en cours si nécessaire
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
      document.querySelectorAll('.speak-btn.speaking').forEach(b => b.classList.remove('speaking', 'loading'));
    }

    btn.classList.add('loading');

    const audio = new Audio(url);
    currentAudio = audio;

    audio.addEventListener('canplaythrough', () => {
      btn.classList.remove('loading');
      btn.classList.add('speaking');
    }, { once: true });

    audio.addEventListener('ended', () => {
      btn.classList.remove('speaking', 'loading');
    }, { once: true });

    audio.addEventListener('error', () => {
      btn.classList.remove('speaking', 'loading');
      btn.title = 'Audio indisponible';
    }, { once: true });

    audio.play().catch(() => {
      btn.classList.remove('speaking', 'loading');
    });
  }

  // Délégation d'événements sur tous les boutons [data-audio-url]
  document.addEventListener('click', e => {
    const btn = e.target.closest('[data-audio-url]');
    if (!btn) return;
    e.preventDefault();
    e.stopPropagation();
    playAudio(btn.dataset.audioUrl, btn);
  });
})();
