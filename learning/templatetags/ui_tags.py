from django import template

from learning.i18n import get_exercise_type_label, get_level_label, get_text


register = template.Library()


@register.filter
def add_class(field, css_class):
    """Ajoute une classe CSS à un champ de formulaire Django."""
    return field.as_widget(attrs={'class': css_class})


@register.simple_tag(takes_context=True)
def tr(context, key):
    lang = context.get("ui_lang", "fr")
    return get_text(lang, key)


@register.filter
def level_label(level_code, lang="fr"):
    return get_level_label(lang, level_code)


@register.filter
def exercise_type_label(type_code, lang="fr"):
    return get_exercise_type_label(lang, type_code)