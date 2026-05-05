/**
 * PROMET – Module microphone (Web Speech API SpeechRecognition)
 *
 * Usage :
 *   PrometMicro.start(options)     → démarre l'écoute
 *   PrometMicro.stop()             → arrête l'écoute
 *   PrometMicro.isSupported()      → boolean
 *
 * Options :
 *   lang        {string}   langue BCP-47 ('fr-FR' par défaut)
 *   onResult    {Function} appelée avec (transcript, isFinal)
 *   onError     {Function} appelée avec (errorCode, message)
 *   onStart     {Function} appelée quand l'écoute démarre
 *   onEnd       {Function} appelée quand l'écoute se termine
 *   continuous  {boolean}  true = écoute continue, false (défaut) = une seule phrase
 */

window.PrometMicro = (function () {
  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition || null;

  let recognition = null;
  let _active = false;

  function isSupported() {
    return !!SpeechRecognition;
  }

  function start(opts = {}) {
    if (!isSupported()) {
      if (opts.onError) opts.onError('not-supported',
        'La reconnaissance vocale n\'est pas disponible dans ce navigateur. Utilisez Chrome ou Edge.');
      return;
    }

    // Si déjà actif, arrêter d'abord
    if (_active && recognition) {
      recognition.stop();
    }

    recognition = new SpeechRecognition();
    recognition.lang        = opts.lang       || 'fr-FR';
    recognition.continuous  = opts.continuous || false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      _active = true;
      if (opts.onStart) opts.onStart();
    };

    recognition.onresult = (event) => {
      let transcript = '';
      let isFinal = false;
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
        if (event.results[i].isFinal) isFinal = true;
      }
      if (opts.onResult) opts.onResult(transcript.trim(), isFinal);
    };

    recognition.onerror = (event) => {
      _active = false;
      const messages = {
        'not-allowed':    'Microphone non autorisé. Vérifiez les permissions du navigateur.',
        'no-speech':      'Aucune parole détectée. Parlez plus fort ou rapprochez-vous du micro.',
        'audio-capture':  'Aucun microphone trouvé.',
        'network':        'Erreur réseau lors de la reconnaissance.',
        'aborted':        'Reconnaissance interrompue.',
        'service-not-allowed': 'Service de reconnaissance vocale non autorisé.',
      };
      if (opts.onError) opts.onError(
        event.error,
        messages[event.error] || `Erreur : ${event.error}`
      );
    };

    recognition.onend = () => {
      _active = false;
      if (opts.onEnd) opts.onEnd();
    };

    try {
      recognition.start();
    } catch (e) {
      if (opts.onError) opts.onError('start-failed', e.message);
    }
  }

  function stop() {
    if (recognition && _active) {
      recognition.stop();
    }
  }

  function isActive() { return _active; }

  return { start, stop, isSupported, isActive };
})();
