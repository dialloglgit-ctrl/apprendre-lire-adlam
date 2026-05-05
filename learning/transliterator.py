"""
PROMET – Moteur de translittération Latin (Pulaar) ↔ Adlam

Correspondances officielles Unicode Adlam (bloc U+1E900–U+1E95F) :
  Majuscules : U+1E900–U+1E91B  |  Minuscules : U+1E922–U+1E93D
"""

import re
import unicodedata

# ── Correspondance Latin → Adlam ─────────────────────────────────────────────
# Ordre important : les séquences les plus longues AVANT les séquences courtes.
# Chaque paire : (latin_lower, adlam_lower)
# Les majuscules sont gérées automatiquement (offset U+1E922→U+1E900 = 34).

_PAIRS_LOWER = [
    # Prénasalisées / digrammes prioritaires
    ("mb",  "\U0001E938"),  # 𞤸 mbaa
    ("kp",  "\U0001E939"),  # 𞤹 kpaa / kfaa
    ("nj",  "\U0001E936"),  # 𞤶 ndja  (aussi écrit ndj)
    ("ndj", "\U0001E936"),  # 𞤶 ndja  (forme longue)
    ("ng",  "\U0001E934"),  # 𞤴 ngha  (prénasalisé)
    ("ny",  "\U0001E93B"),  # 𞤻 nyaa
    ("nh",  "\U0001E930"),  # 𞤰 nhaa  (nasale palatale)
    ("ch",  "\U0001E93D"),  # 𞤽 cham
    ("bh",  "\U0001E929"),  # 𞤩 bhe   (implosive b)
    ("dh",  "\U0001E92F"),  # 𞤯 dha   (implosive d)
    ("kh",  "\U0001E932"),  # 𞤲 kha   (nasale vélaire ŋ)
    # Caractères spéciaux Pulaar
    ("\u0253", "\U0001E929"),  # ɓ → 𞤩 implosive b
    ("\u0257", "\U0001E92F"),  # ɗ → 𞤯 implosive d
    ("\u0272", "\U0001E930"),  # ɲ → 𞤰 palatale n
    ("\u014b", "\U0001E932"),  # ŋ → 𞤲 nasale vélaire
    ("\u00f1", "\U0001E93B"),  # ñ → 𞤻 (souvent ny en pulaar)
    # Voyelles et consonnes simples
    ("a", "\U0001E922"),  # 𞤢 alif
    ("b", "\U0001E926"),  # 𞤦 baa
    ("c", "\U0001E93D"),  # 𞤽 cham  (k devant e/i dans certaines orthographes)
    ("d", "\U0001E923"),  # 𞤣 daali
    ("e", "\U0001E92B"),  # 𞤫 e
    ("f", "\U0001E92C"),  # 𞤬 fa
    ("g", "\U0001E933"),  # 𞤳 gaa/kaa
    ("h", "\U0001E937"),  # 𞤷 haa
    ("i", "\U0001E92D"),  # 𞤭 i
    ("j", "\U0001E93C"),  # 𞤼 jiim
    ("k", "\U0001E933"),  # 𞤳 (même glyphe que g en adlam)
    ("l", "\U0001E924"),  # 𞤤 laam
    ("m", "\U0001E925"),  # 𞤥 miim
    ("n", "\U0001E932"),  # 𞤲 kha (nasale par défaut)
    ("o", "\U0001E92E"),  # 𞤮 o
    ("p", "\U0001E928"),  # 𞤨 pe
    ("r", "\U0001E92A"),  # 𞤪 ra
    ("s", "\U0001E927"),  # 𞤧 sinnyiiyhe
    ("t", "\U0001E935"),  # 𞤵 too
    ("u", "\U0001E92E"),  # 𞤮 (u long → o en adlam)
    ("v", "\U0001E931"),  # 𞤱 vaa/waa
    ("w", "\U0001E931"),  # 𞤱 waa
    ("x", "\U0001E933"),  # 𞤳 (rare en pulaar)
    ("y", "\U0001E93A"),  # 𞤺 ya
    ("z", "\U0001E927"),  # 𞤧 (rare, même glyphe que s)
]

_ADLAM_CAP_START = 0x1E900
_ADLAM_LOW_START = 0x1E922
_ADLAM_CAP_END   = 0x1E91B
_ADLAM_LOW_END   = 0x1E93D


def _to_adlam_cap(adlam_low_char: str) -> str:
    """Convertit une lettre Adlam minuscule en majuscule."""
    cp = ord(adlam_low_char)
    if _ADLAM_LOW_START <= cp <= _ADLAM_LOW_END:
        return chr(cp - (_ADLAM_LOW_START - _ADLAM_CAP_START))
    return adlam_low_char


def _build_latin_adlam_map():
    """Construit la table (séquence_latine → adlam_min, adlam_maj)."""
    result = []
    for latin, adlam_low in _PAIRS_LOWER:
        adlam_up = _to_adlam_cap(adlam_low[0]) + adlam_low[1:] if len(adlam_low) == 1 else adlam_low
        result.append((latin, adlam_low, adlam_up))
    return result


_MAP = _build_latin_adlam_map()

# Table inverse : adlam_char → latin
_ADLAM_TO_LATIN = {}
for _latin, _adlam_low, _ in _MAP:
    if _adlam_low not in _ADLAM_TO_LATIN:
        _ADLAM_TO_LATIN[_adlam_low] = _latin
    cp = ord(_adlam_low)
    if _ADLAM_LOW_START <= cp <= _ADLAM_LOW_END:
        cap = chr(cp - (_ADLAM_LOW_START - _ADLAM_CAP_START))
        if cap not in _ADLAM_TO_LATIN:
            _ADLAM_TO_LATIN[cap] = _latin.upper() if len(_latin) == 1 else _latin.upper()


# ── API publique ───────────────────────────────────────────────────────────────

def latin_to_adlam(text: str) -> str:
    """
    Convertit du texte Pulaar en latin vers le script Adlam.
    Préserve la ponctuation, les espaces et les chiffres.
    """
    result = []
    i = 0
    lower_text = text.lower()
    while i < len(text):
        matched = False
        for latin, adlam_low, adlam_up in _MAP:
            end = i + len(latin)
            if lower_text[i:end] == latin:
                # Détecter la casse : si premier char en majuscule → version capitale
                if text[i].isupper():
                    result.append(_to_adlam_cap(adlam_low))
                else:
                    result.append(adlam_low)
                i = end
                matched = True
                break
        if not matched:
            result.append(text[i])
            i += 1
    return "".join(result)


def adlam_to_latin(text: str, pulaar_specials: bool = True) -> str:
    """
    Convertit du texte Adlam vers le latin Pulaar.
    Si pulaar_specials=True, utilise ɓ, ɗ, ɲ, ŋ ;
    sinon utilise bh, dh, nh, ng.
    """
    result = []
    for char in text:
        if char in _ADLAM_TO_LATIN:
            latin = _ADLAM_TO_LATIN[char]
            if not pulaar_specials:
                # Remplacer les caractères IPA par digraphes
                latin = (latin
                         .replace("ɓ", "bh").replace("Ɓ", "Bh")
                         .replace("ɗ", "dh").replace("Ɗ", "Dh")
                         .replace("ɲ", "nh").replace("Ɲ", "Nh")
                         .replace("ŋ", "ng").replace("Ŋ", "Ng"))
            result.append(latin)
        else:
            result.append(char)
    return "".join(result)


def detect_script(text: str) -> str:
    """Détecte si le texte est en Adlam, Latin ou Mixte."""
    adlam_count = sum(1 for c in text if _ADLAM_CAP_START <= ord(c) <= _ADLAM_LOW_END)
    latin_count = sum(1 for c in text if c.isalpha() and ord(c) < 0x500)
    if adlam_count > 0 and latin_count == 0:
        return "adlam"
    if latin_count > 0 and adlam_count == 0:
        return "latin"
    return "mixed"


def auto_convert(text: str, pulaar_specials: bool = True) -> dict:
    """
    Détecte automatiquement le script et convertit dans l'autre sens.
    Retourne {'input_script', 'output_script', 'result'}.
    """
    script = detect_script(text)
    if script == "adlam":
        return {
            "input_script": "adlam",
            "output_script": "latin",
            "result": adlam_to_latin(text, pulaar_specials),
        }
    # latin ou mixed → adlam
    return {
        "input_script": "latin",
        "output_script": "adlam",
        "result": latin_to_adlam(text),
    }
