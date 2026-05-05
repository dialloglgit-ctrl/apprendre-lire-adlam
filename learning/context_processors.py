from .i18n import LANG_OPTIONS, normalize_lang
from django.conf import settings

_RTL_LANGS = {'ar', 'adlm'}


def ui_context(request):
    requested = request.session.get("ui_lang") or request.GET.get("lang") or request.LANGUAGE_CODE
    ui_lang = normalize_lang(requested)
    ui_dir = 'rtl' if ui_lang in _RTL_LANGS else 'ltr'
    return {
        "ui_lang": ui_lang,
        "ui_dir": ui_dir,
        "supported_langs": LANG_OPTIONS,
        "api_base_url": getattr(settings, "API_BASE_URL", ""),
    }