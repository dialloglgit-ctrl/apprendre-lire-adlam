"""
PROMET – Moteur d'évaluation IA avancé pour l'Adlam.

Fonctionnalités :
  - Normalisation Unicode Adlam (U+1E900–U+1E95F)
  - Correspondance majuscule/minuscule Adlam
  - Distance de Levenshtein avec coûts de substitution adaptés
  - Confusion de caractères visuellement similaires
  - Normalisation phonétique Pulaar
  - Score multi-niveaux avec feedback enrichi
  - Diff HTML caractère par caractère
"""

import unicodedata
from difflib import SequenceMatcher

# ──────────────────────────────────────────────────────────────────────────────
# Correspondance uppercase ↔ lowercase Adlam
# U+1E900-U+1E921 = majuscules, U+1E922-U+1E943 = minuscules
# ──────────────────────────────────────────────────────────────────────────────
_ADLAM_UPPER_START = 0x1E900
_ADLAM_LOWER_START = 0x1E922
_ADLAM_LETTER_COUNT = 34  # lettres + chiffres Adlam


def _adlam_to_lower(char: str) -> str:
    """Convertit une lettre Adlam majuscule en minuscule."""
    cp = ord(char)
    if _ADLAM_UPPER_START <= cp < _ADLAM_UPPER_START + _ADLAM_LETTER_COUNT:
        offset = cp - _ADLAM_UPPER_START
        return chr(_ADLAM_LOWER_START + offset)
    return char


def _normalize_adlam_case(text: str) -> str:
    return ''.join(_adlam_to_lower(c) for c in text)


# ──────────────────────────────────────────────────────────────────────────────
# Paires de caractères Adlam visuellement / phonétiquement proches
# coût réduit lors du calcul Levenshtein
# ──────────────────────────────────────────────────────────────────────────────
_CONFUSABLE_ADLAM = {
    # (char_a, char_b) -> coût de substitution (0.0=identique … 1.0=totalement différent)
    ('\U0001E900', '\U0001E922'): 0.0,   # Alif upper/lower
    ('\U0001E901', '\U0001E923'): 0.0,
    ('\U0001E902', '\U0001E924'): 0.0,
    ('\U0001E903', '\U0001E925'): 0.0,
    ('\U0001E904', '\U0001E926'): 0.0,
    ('\U0001E905', '\U0001E927'): 0.0,
    ('\U0001E906', '\U0001E928'): 0.0,
    ('\U0001E907', '\U0001E929'): 0.0,
    ('\U0001E908', '\U0001E92A'): 0.0,
    ('\U0001E909', '\U0001E92B'): 0.0,
    ('\U0001E90A', '\U0001E92C'): 0.0,
    ('\U0001E90B', '\U0001E92D'): 0.0,
    ('\U0001E90C', '\U0001E92E'): 0.0,
    # Similitudes phonétiques Pulaar
    ('\U0001E905', '\U0001E927'): 0.1,   # S/s
    ('\U0001E908', '\U0001E92A'): 0.1,   # R/r
}

# Normaliser le dictionnaire pour lookup rapide
_CONFUSABLE_MAP: dict[frozenset, float] = {
    frozenset(pair): cost for pair, cost in _CONFUSABLE_ADLAM.items()
}


def _substitution_cost(a: str, b: str) -> float:
    if a == b:
        return 0.0
    key = frozenset((a, b))
    return _CONFUSABLE_MAP.get(key, 1.0)


# ──────────────────────────────────────────────────────────────────────────────
# Normalisation phonétique Pulaar (transcription latine)
# ──────────────────────────────────────────────────────────────────────────────
_PULAAR_PHONETIC = [
    ('ñ', 'ny'), ('ŋ', 'ng'), ('ɓ', 'b'), ('ɗ', 'd'), ('ƴ', 'y'),
    ('é', 'e'), ('ó', 'o'), ('ú', 'u'), ('á', 'a'), ('í', 'i'),
    ('bb', 'b'), ('dd', 'd'), ('gg', 'g'), ('kk', 'k'),
    ('ndd', 'nd'), ('mb', 'mb'), ('ng', 'ng'), ('nd', 'nd'),
]


def _normalize_pulaar_phonetics(text: str) -> str:
    t = text.lower()
    for src, dst in _PULAAR_PHONETIC:
        t = t.replace(src, dst)
    return t


# ──────────────────────────────────────────────────────────────────────────────
# Normalisation générale
# ──────────────────────────────────────────────────────────────────────────────
def normalize_answer(value: str) -> str:
    """Normalise une réponse : casse, accents, espaces, Adlam case."""
    if not value:
        return ''
    # Adlam case normalization
    value = _normalize_adlam_case(value)
    # Strip & lowercase
    value = value.strip().lower()
    # Enlever accents latin (NFD + supprimer Mn)
    decomposed = unicodedata.normalize('NFD', value)
    without_marks = ''.join(
        c for c in decomposed if unicodedata.category(c) != 'Mn'
    )
    # Normaliser les espaces
    return ' '.join(without_marks.split())


# ──────────────────────────────────────────────────────────────────────────────
# Distance de Levenshtein pondérée
# ──────────────────────────────────────────────────────────────────────────────
def _weighted_levenshtein(s: str, t: str) -> float:
    """
    Distance de Levenshtein avec coûts de substitution pondérés pour Adlam.
    Retourne un score de similarité [0.0, 1.0].
    """
    if s == t:
        return 1.0
    if not s or not t:
        return 0.0

    ls, lt = len(s), len(t)
    # Matrice dp
    prev = list(range(lt + 1))
    curr = [0] * (lt + 1)

    for i in range(1, ls + 1):
        curr[0] = i
        for j in range(1, lt + 1):
            cost = _substitution_cost(s[i - 1], t[j - 1])
            curr[j] = min(
                prev[j] + 1,           # suppression
                curr[j - 1] + 1,       # insertion
                prev[j - 1] + cost,    # substitution
            )
        prev, curr = curr, [0] * (lt + 1)

    dist = prev[lt]
    max_len = max(ls, lt)
    return max(0.0, 1.0 - dist / max_len)


# ──────────────────────────────────────────────────────────────────────────────
# Diff HTML pour afficher les erreurs caractère par caractère
# ──────────────────────────────────────────────────────────────────────────────
def _build_diff_html(user: str, expected: str) -> str:
    """
    Retourne un HTML avec caractères corrects en vert, incorrects en rouge,
    manquants en orange.
    """
    matcher = SequenceMatcher(None, user, expected, autojunk=False)
    result = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            result.append(f'<span class="diff-ok">{user[i1:i2]}</span>')
        elif tag == 'replace':
            result.append(f'<span class="diff-wrong">{user[i1:i2]}</span>')
            result.append(f'<span class="diff-missing">{expected[j1:j2]}</span>')
        elif tag == 'delete':
            result.append(f'<span class="diff-wrong">{user[i1:i2]}</span>')
        elif tag == 'insert':
            result.append(f'<span class="diff-missing">{expected[j1:j2]}</span>')
    return ''.join(result)


# ──────────────────────────────────────────────────────────────────────────────
# Évaluation principale
# ──────────────────────────────────────────────────────────────────────────────
def evaluate_answer(user_answer: str, expected_answer: str) -> dict:
    """
    Évalue la réponse utilisateur avec plusieurs niveaux de tolérance.

    Retourne:
      accepted        bool     - réponse acceptée ?
      score           float    - score de similarité [0,1]
      exact           bool     - correspondance parfaite
      near_phonetic   bool     - correspondance phonétique/tolérance
      feedback_level  str      - 'perfect'|'near'|'phonetic'|'almost'|'wrong'
      feedback_message str     - message à afficher
      diff_html       str      - diff HTML caractère par caractère
      best_match      str      - meilleure option attendue
    """
    # Réponses alternatives séparées par |
    options = [p.strip() for p in expected_answer.split('|') if p.strip()]
    if not options:
        options = [expected_answer]

    norm_user = normalize_answer(user_answer)

    best_score = 0.0
    best_option = options[0]
    best_norm_option = normalize_answer(options[0])

    for opt in options:
        norm_opt = normalize_answer(opt)
        # Score SequenceMatcher (rapidité)
        sm_score = SequenceMatcher(None, norm_user, norm_opt).ratio()
        # Score Levenshtein pondéré
        lev_score = _weighted_levenshtein(norm_user, norm_opt)
        # Score phonétique Pulaar
        ph_user = _normalize_pulaar_phonetics(norm_user)
        ph_opt = _normalize_pulaar_phonetics(norm_opt)
        ph_score = SequenceMatcher(None, ph_user, ph_opt).ratio()

        # Score combiné : max des trois approches
        combined = max(sm_score, lev_score, ph_score * 0.95)

        if combined > best_score:
            best_score = combined
            best_option = opt
            best_norm_option = norm_opt

    exact = norm_user in [normalize_answer(o) for o in options]
    near = best_score >= 0.85 and not exact
    phonetic_match = _normalize_pulaar_phonetics(norm_user) in [
        _normalize_pulaar_phonetics(normalize_answer(o)) for o in options
    ]
    near_phonetic = phonetic_match and not exact

    accepted = exact or near or near_phonetic

    # Niveau de feedback
    if exact:
        level = 'perfect'
        message = '🎉 Parfait !'
    elif near_phonetic:
        level = 'phonetic'
        message = '✅ Bonne réponse (variante phonétique acceptée)'
    elif near:
        level = 'near'
        message = '✅ Presque parfait – petite faute de frappe tolérée'
    elif best_score >= 0.60:
        level = 'almost'
        message = f'⚠️ Presque ! Vérifiez l\'orthographe Adlam.'
    else:
        level = 'wrong'
        message = '❌ Mauvaise réponse'

    diff = _build_diff_html(norm_user, best_norm_option) if not exact else ''

    return {
        'accepted': accepted,
        'score': round(best_score, 4),
        'exact': exact,
        'near_phonetic': near_phonetic,
        'feedback_level': level,
        'feedback_message': message,
        'best_match': best_option,
        'diff_html': diff,
    }
