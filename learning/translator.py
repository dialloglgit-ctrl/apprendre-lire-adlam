"""
PROMET – Dictionnaire de traduction FR/EN → Pulaar (latin)

Vocabulaire éducatif : salutations, nombres, alphabet, corps, couleurs,
famille, animaux, verbes courants, contexte scolaire.
Les entrées incluent aussi la translittération Adlam générée dynamiquement.
"""

from .transliterator import latin_to_adlam

# ── Dictionnaire principal ─────────────────────────────────────────────────────
# Format : mot_fr → { "pul": "pulaar latin", "note": "(optionnel)" }
# Les clés sont normalisées en minuscules sans accents pour la recherche floue.

_FR_DICT: dict[str, dict] = {
    # Salutations / politesse
    "bonjour": {"pul": "jam waali"},
    "bonsoir": {"pul": "jam hiiri"},
    "bonne nuit": {"pul": "jam lekki"},
    "au revoir": {"pul": "seeɗa"},
    "merci": {"pul": "a jaaraama"},
    "s'il vous plaît": {"pul": "tiiɗno"},
    "oui": {"pul": "eey"},
    "non": {"pul": "alaa"},
    "comment allez-vous": {"pul": "no mbadaa"},
    "je vais bien": {"pul": "mi waawi"},
    "pardon": {"pul": "mi yofo"},
    "bienvenue": {"pul": "jam joodii"},

    # Apprentissage / école
    "apprendre": {"pul": "janngo"},
    "lire": {"pul": "janngo"},
    "écrire": {"pul": "winndo"},
    "écriture": {"pul": "binndol"},
    "lettre": {"pul": "alkule"},
    "alphabet": {"pul": "alifba"},
    "mot": {"pul": "konngol"},
    "phrase": {"pul": "miijo"},
    "leçon": {"pul": "darsu"},
    "exercice": {"pul": "jarol"},
    "question": {"pul": "ɗanndo"},
    "réponse": {"pul": "jaabawol"},
    "correct": {"pul": "moƴƴi"},
    "incorrect": {"pul": "moƴƴaani"},
    "bravo": {"pul": "ɗum moƴƴi"},
    "répéter": {"pul": "etti"},
    "comprendre": {"pul": "faamo"},
    "savoir": {"pul": "anndo"},
    "pratiquer": {"pul": "jaaro"},
    "commencer": {"pul": "fuɗɗo"},
    "terminer": {"pul": "gaso"},
    "continuer": {"pul": "jokkito"},

    # Chiffres
    "zéro": {"pul": "sifir"},
    "un": {"pul": "go'o"},
    "deux": {"pul": "ɗiɗi"},
    "trois": {"pul": "tati"},
    "quatre": {"pul": "nayi"},
    "cinq": {"pul": "jowi"},
    "six": {"pul": "jeegom"},
    "sept": {"pul": "jeedidi"},
    "huit": {"pul": "jeetati"},
    "neuf": {"pul": "jeenayi"},
    "dix": {"pul": "sappo"},
    "vingt": {"pul": "noogaas"},
    "cent": {"pul": "teemeer"},
    "mille": {"pul": "ujunere"},

    # Couleurs
    "rouge": {"pul": "woɗeere"},
    "bleu": {"pul": "bulondu"},
    "vert": {"pul": "beleeje"},
    "jaune": {"pul": "jawnde"},
    "blanc": {"pul": "daneeji"},
    "noir": {"pul": "baleeri"},
    "orange": {"pul": "lemooru"},

    # Famille
    "père": {"pul": "baaba"},
    "mère": {"pul": "yaayo"},
    "enfant": {"pul": "ɓiɗɗo"},
    "fils": {"pul": "ɓiɗɗo gorko"},
    "fille": {"pul": "ɓiɗɗo debbo"},
    "frère": {"pul": "mawniiɗo"},
    "sœur": {"pul": "mawniiɗo debbo"},
    "grand-père": {"pul": "kaawu"},
    "grand-mère": {"pul": "maamiraaɗo"},
    "famille": {"pul": "galle"},
    "homme": {"pul": "gorko"},
    "femme": {"pul": "debbo"},
    "enfants": {"pul": "sukaaɓe"},

    # Corps
    "tête": {"pul": "hoore"},
    "main": {"pul": "junngo"},
    "pied": {"pul": "koyngal"},
    "œil": {"pul": "gite"},
    "bouche": {"pul": "hunuko"},
    "oreille": {"pul": "nofru"},
    "nez": {"pul": "hinere"},
    "cœur": {"pul": "daande"},
    "dent": {"pul": "nyiire"},

    # Animaux
    "vache": {"pul": "nagge"},
    "mouton": {"pul": "mbabba"},
    "chèvre": {"pul": "mbabba"},
    "cheval": {"pul": "puccu"},
    "âne": {"pul": "mbabba"},
    "oiseau": {"pul": "fowru"},
    "poisson": {"pul": "liingu"},
    "chien": {"pul": "rawaandu"},
    "chat": {"pul": "muusooru"},

    # Nature / lieu
    "eau": {"pul": "ndiyam"},
    "feu": {"pul": "jaɓɓo"},
    "terre": {"pul": "leydi"},
    "ciel": {"pul": "kammu"},
    "soleil": {"pul": "naange"},
    "lune": {"pul": "lewru"},
    "arbre": {"pul": "leggal"},
    "village": {"pul": "wuro"},
    "maison": {"pul": "suudu"},
    "chemin": {"pul": "laawol"},
    "marché": {"pul": "luumo"},
    "école": {"pul": "janngirde"},

    # Verbes courants
    "manger": {"pul": "nyaamo"},
    "boire": {"pul": "yaro"},
    "dormir": {"pul": "hirno"},
    "marcher": {"pul": "yahdo"},
    "courir": {"pul": "mbeltoto"},
    "parler": {"pul": "haalo"},
    "voir": {"pul": "yiido"},
    "venir": {"pul": "arde"},
    "aller": {"pul": "yahde"},
    "aimer": {"pul": "yidde"},
    "travailler": {"pul": "gollude"},
    "chercher": {"pul": "yiylo"},
    "donner": {"pul": "hokko"},
    "prendre": {"pul": "hono"},

    # Adjectifs
    "grand": {"pul": "mawɗo"},
    "petit": {"pul": "pitiliiɗo"},
    "beau": {"pul": "moƴƴo"},
    "bon": {"pul": "moƴƴo"},
    "mauvais": {"pul": "moƴƴaani"},
    "nouveau": {"pul": "keso"},
    "vieux": {"pul": "woɗɓe"},
    "fort": {"pul": "doole"},
    "chaud": {"pul": "keeɗo"},
    "froid": {"pul": "keewɗo"},
}

# ── Dictionnaire Anglais → Pulaar ──────────────────────────────────────────────
_EN_DICT: dict[str, dict] = {
    "hello": {"pul": "jam waali"},
    "good morning": {"pul": "jam waali"},
    "good evening": {"pul": "jam hiiri"},
    "good night": {"pul": "jam lekki"},
    "goodbye": {"pul": "seeɗa"},
    "thank you": {"pul": "a jaaraama"},
    "please": {"pul": "tiiɗno"},
    "yes": {"pul": "eey"},
    "no": {"pul": "alaa"},
    "how are you": {"pul": "no mbadaa"},
    "i am fine": {"pul": "mi waawi"},
    "sorry": {"pul": "mi yofo"},
    "welcome": {"pul": "jam joodii"},
    # Learning
    "learn": {"pul": "janngo"},
    "read": {"pul": "janngo"},
    "write": {"pul": "winndo"},
    "writing": {"pul": "binndol"},
    "letter": {"pul": "alkule"},
    "alphabet": {"pul": "alifba"},
    "word": {"pul": "konngol"},
    "sentence": {"pul": "miijo"},
    "lesson": {"pul": "darsu"},
    "exercise": {"pul": "jarol"},
    "question": {"pul": "ɗanndo"},
    "answer": {"pul": "jaabawol"},
    "correct": {"pul": "moƴƴi"},
    "wrong": {"pul": "moƴƴaani"},
    "repeat": {"pul": "etti"},
    "understand": {"pul": "faamo"},
    "know": {"pul": "anndo"},
    "practice": {"pul": "jaaro"},
    "start": {"pul": "fuɗɗo"},
    "finish": {"pul": "gaso"},
    # Numbers
    "zero": {"pul": "sifir"},
    "one": {"pul": "go'o"},
    "two": {"pul": "ɗiɗi"},
    "three": {"pul": "tati"},
    "four": {"pul": "nayi"},
    "five": {"pul": "jowi"},
    "six": {"pul": "jeegom"},
    "seven": {"pul": "jeedidi"},
    "eight": {"pul": "jeetati"},
    "nine": {"pul": "jeenayi"},
    "ten": {"pul": "sappo"},
    "twenty": {"pul": "noogaas"},
    "hundred": {"pul": "teemeer"},
    "thousand": {"pul": "ujunere"},
    # Colors
    "red": {"pul": "woɗeere"},
    "blue": {"pul": "bulondu"},
    "green": {"pul": "beleeje"},
    "yellow": {"pul": "jawnde"},
    "white": {"pul": "daneeji"},
    "black": {"pul": "baleeri"},
    "orange": {"pul": "lemooru"},
    # Family
    "father": {"pul": "baaba"},
    "mother": {"pul": "yaayo"},
    "child": {"pul": "ɓiɗɗo"},
    "son": {"pul": "ɓiɗɗo gorko"},
    "daughter": {"pul": "ɓiɗɗo debbo"},
    "brother": {"pul": "mawniiɗo"},
    "sister": {"pul": "mawniiɗo debbo"},
    "grandfather": {"pul": "kaawu"},
    "grandmother": {"pul": "maamiraaɗo"},
    "family": {"pul": "galle"},
    "man": {"pul": "gorko"},
    "woman": {"pul": "debbo"},
    # Body
    "head": {"pul": "hoore"},
    "hand": {"pul": "junngo"},
    "foot": {"pul": "koyngal"},
    "eye": {"pul": "gite"},
    "mouth": {"pul": "hunuko"},
    "ear": {"pul": "nofru"},
    "nose": {"pul": "hinere"},
    "heart": {"pul": "daande"},
    "tooth": {"pul": "nyiire"},
    # Animals
    "cow": {"pul": "nagge"},
    "horse": {"pul": "puccu"},
    "bird": {"pul": "fowru"},
    "fish": {"pul": "liingu"},
    "dog": {"pul": "rawaandu"},
    "cat": {"pul": "muusooru"},
    # Nature
    "water": {"pul": "ndiyam"},
    "fire": {"pul": "jaɓɓo"},
    "earth": {"pul": "leydi"},
    "sky": {"pul": "kammu"},
    "sun": {"pul": "naange"},
    "moon": {"pul": "lewru"},
    "tree": {"pul": "leggal"},
    "village": {"pul": "wuro"},
    "house": {"pul": "suudu"},
    "road": {"pul": "laawol"},
    "market": {"pul": "luumo"},
    "school": {"pul": "janngirde"},
    # Verbs
    "eat": {"pul": "nyaamo"},
    "drink": {"pul": "yaro"},
    "sleep": {"pul": "hirno"},
    "walk": {"pul": "yahdo"},
    "run": {"pul": "mbeltoto"},
    "speak": {"pul": "haalo"},
    "see": {"pul": "yiido"},
    "come": {"pul": "arde"},
    "go": {"pul": "yahde"},
    "love": {"pul": "yidde"},
    "work": {"pul": "gollude"},
    "look": {"pul": "yiylo"},
    "give": {"pul": "hokko"},
    "take": {"pul": "hono"},
    # Adjectives
    "big": {"pul": "mawɗo"},
    "small": {"pul": "pitiliiɗo"},
    "beautiful": {"pul": "moƴƴo"},
    "good": {"pul": "moƴƴo"},
    "bad": {"pul": "moƴƴaani"},
    "new": {"pul": "keso"},
    "old": {"pul": "woɗɓe"},
    "strong": {"pul": "doole"},
    "hot": {"pul": "keeɗo"},
    "cold": {"pul": "keewɗo"},
}

_DICTS = {"fr": _FR_DICT, "en": _EN_DICT}


def _normalize_key(text: str) -> str:
    """Normalise une clé pour la recherche : minuscule + sans accents."""
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", text.lower().strip())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def translate_word(word: str, from_lang: str = "fr") -> dict | None:
    """
    Traduit un mot vers le Pulaar (latin + Adlam).
    Retourne None si introuvable.
    """
    dictionary = _DICTS.get(from_lang, _FR_DICT)
    key = _normalize_key(word)
    entry = dictionary.get(key)
    if entry:
        pul = entry["pul"]
        return {
            "input": word,
            "pul_latin": pul,
            "pul_adlam": latin_to_adlam(pul),
            "note": entry.get("note", ""),
            "found": True,
        }
    return None


def translate_text(text: str, from_lang: str = "fr") -> dict:
    """
    Traduction mot à mot.
    Retourne chaque token avec sa traduction (ou None si inconnu).
    """
    # Tokeniser en conservant la ponctuation
    import re
    tokens = re.findall(r"[\w''\u00C0-\u024F]+|[^\w''\u00C0-\u024F]+", text)
    results = []
    pulaar_parts = []
    adlam_parts = []
    found_count = 0

    for token in tokens:
        if re.match(r"[\w''\u00C0-\u024F]+", token):
            translation = translate_word(token, from_lang)
            if translation:
                results.append({"token": token, **translation})
                pulaar_parts.append(translation["pul_latin"])
                adlam_parts.append(translation["pul_adlam"])
                found_count += 1
            else:
                results.append({"token": token, "found": False, "pul_latin": None, "pul_adlam": None})
                pulaar_parts.append(f"[{token}]")
                adlam_parts.append(f"[{token}]")
        else:
            results.append({"token": token, "found": None})
            pulaar_parts.append(token)
            adlam_parts.append(token)

    total_words = sum(1 for r in results if r.get("found") is not None)
    coverage = round(found_count / total_words * 100) if total_words > 0 else 0

    return {
        "tokens": results,
        "pul_latin": " ".join(p for p in pulaar_parts if p.strip()),
        "pul_adlam": " ".join(p for p in adlam_parts if p.strip()),
        "coverage": coverage,
        "found": found_count,
        "total": total_words,
    }


def get_vocabulary(from_lang: str = "fr") -> list[dict]:
    """Retourne tout le vocabulaire disponible pour une langue source."""
    dictionary = _DICTS.get(from_lang, _FR_DICT)
    return [
        {
            "input": word,
            "pul_latin": entry["pul"],
            "pul_adlam": latin_to_adlam(entry["pul"]),
        }
        for word, entry in dictionary.items()
    ]
