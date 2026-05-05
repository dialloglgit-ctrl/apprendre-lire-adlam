from django.contrib import admin
from django.utils.translation import get_language

from .i18n import get_exercise_type_label, get_level_label, normalize_lang
from .models import LettrAdlam, Lecon, Exercice, Progression, Video, Livre, LivreVendre, \
    Annonce, FAQ, Temoignage, ContactMessage, NoteLivre, VueLivre, VueVideo


def _ui_lang_from_request(request):
    session = getattr(request, 'session', None)
    ui_lang = session.get('ui_lang') if session else None
    return normalize_lang(ui_lang or get_language())


def _iter_choices(db_field):
    choices = getattr(db_field, 'flatchoices', None)
    if choices is None:
        choices = db_field.choices
    return list(choices)


class NiveauListFilter(admin.SimpleListFilter):
    title = 'Niveau'
    parameter_name = 'niveau'

    def lookups(self, request, model_admin):
        lang = _ui_lang_from_request(request)
        return [
            ('debutant', get_level_label(lang, 'debutant')),
            ('intermediaire', get_level_label(lang, 'intermediaire')),
            ('avance', get_level_label(lang, 'avance')),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(niveau=value)
        return queryset


class TypeExerciceListFilter(admin.SimpleListFilter):
    title = 'Type'
    parameter_name = 'type_exercice'

    def lookups(self, request, model_admin):
        lang = _ui_lang_from_request(request)
        return [
            ('qcm', get_exercise_type_label(lang, 'qcm')),
            ('dictee', get_exercise_type_label(lang, 'dictee')),
            ('association', get_exercise_type_label(lang, 'association')),
            ('ecriture', get_exercise_type_label(lang, 'ecriture')),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(type_exercice=value)
        return queryset


@admin.register(LettrAdlam)
class LettrAdlamAdmin(admin.ModelAdmin):
    list_display  = ('caractere', 'nom', 'transliteration', 'ordre')
    list_editable = ('ordre',)
    ordering      = ('ordre',)
    search_fields = ('nom', 'transliteration')


class ExerciceInline(admin.TabularInline):
    model  = Exercice
    extra  = 1
    fields = ('type_exercice', 'question', 'reponse_correcte', 'niveau', 'ordre')

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        lang = _ui_lang_from_request(request)
        if db_field.name == 'niveau':
            kwargs['choices'] = [
                (code, label if code in (None, '') else get_level_label(lang, code))
                for code, label in _iter_choices(db_field)
            ]
        if db_field.name == 'type_exercice':
            kwargs['choices'] = [
                (code, label if code in (None, '') else get_exercise_type_label(lang, code))
                for code, label in _iter_choices(db_field)
            ]
        return super().formfield_for_choice_field(db_field, request, **kwargs)


@admin.register(Lecon)
class LeconAdmin(admin.ModelAdmin):
    list_display  = ('titre', 'niveau_label', 'ordre', 'creee_le')
    list_filter   = (NiveauListFilter,)
    list_editable = ('ordre',)
    search_fields = ('titre',)
    filter_horizontal = ('lettres',)
    inlines   = [ExerciceInline]

    def niveau_label(self, obj):
        return get_level_label(get_language(), obj.niveau)
    niveau_label.short_description = 'Niveau'

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        lang = _ui_lang_from_request(request)
        if db_field.name == 'niveau':
            kwargs['choices'] = [
                (code, label if code in (None, '') else get_level_label(lang, code))
                for code, label in _iter_choices(db_field)
            ]
        return super().formfield_for_choice_field(db_field, request, **kwargs)


@admin.register(Exercice)
class ExerciceAdmin(admin.ModelAdmin):
    list_display  = ('__str__', 'type_label', 'niveau_label', 'lecon', 'ordre')
    list_filter   = (TypeExerciceListFilter, NiveauListFilter)
    search_fields = ('question',)
    list_editable = ('ordre',)

    def type_label(self, obj):
        return get_exercise_type_label(get_language(), obj.type_exercice)
    type_label.short_description = 'Type'

    def niveau_label(self, obj):
        return get_level_label(get_language(), obj.niveau)
    niveau_label.short_description = 'Niveau'

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        lang = _ui_lang_from_request(request)
        if db_field.name == 'niveau':
            kwargs['choices'] = [
                (code, label if code in (None, '') else get_level_label(lang, code))
                for code, label in _iter_choices(db_field)
            ]
        if db_field.name == 'type_exercice':
            kwargs['choices'] = [
                (code, label if code in (None, '') else get_exercise_type_label(lang, code))
                for code, label in _iter_choices(db_field)
            ]
        return super().formfield_for_choice_field(db_field, request, **kwargs)


@admin.register(Progression)
class ProgressionAdmin(admin.ModelAdmin):
    list_display        = ('utilisateur', 'points', 'nb_lecons_terminees', 'derniere_activite')
    readonly_fields     = ('derniere_activite',)
    filter_horizontal   = ('lecons_terminees', 'exercices_reussis')

    def nb_lecons_terminees(self, obj):
        return obj.nb_lecons_terminees
    nb_lecons_terminees.short_description = 'Leçons terminées'


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display  = ('titre', 'categorie', 'niveau', 'lecon', 'publie', 'ordre', 'date_ajout')
    list_filter   = ('categorie', NiveauListFilter, 'publie')
    list_editable = ('publie', 'ordre')
    search_fields = ('titre', 'description')
    raw_id_fields = ('lecon',)


@admin.register(Livre)
class LivreAdmin(admin.ModelAdmin):
    list_display = ('titre', 'niveau', 'lecon', 'source_label', 'publie', 'ordre', 'date_ajout')
    list_filter = (NiveauListFilter, 'publie')
    list_editable = ('publie', 'ordre')
    search_fields = ('titre', 'description', 'url')
    raw_id_fields = ('lecon',)


@admin.register(LivreVendre)
class LivreVendreAdmin(admin.ModelAdmin):
    list_display = ('titre', 'prix_affiche', 'niveau', 'lecon', 'source_label', 'publie', 'ordre', 'date_ajout')
    list_filter = (NiveauListFilter, 'publie', 'devise')
    list_editable = ('publie', 'ordre')
    search_fields = ('titre', 'description', 'url')
    raw_id_fields = ('lecon',)


@admin.register(Annonce)
class AnnonceAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type', 'active', 'date', 'date_fin')
    list_editable = ('active',)
    list_filter = ('type', 'active')


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'categorie', 'ordre', 'active')
    list_editable = ('ordre', 'active')
    search_fields = ('question', 'reponse')


@admin.register(Temoignage)
class TemoignageAdmin(admin.ModelAdmin):
    list_display = ('nom', 'pays', 'note', 'approuve', 'date')
    list_editable = ('approuve',)
    list_filter = ('approuve', 'note')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('nom', 'email', 'sujet', 'lu', 'date')
    list_editable = ('lu',)
    search_fields = ('nom', 'email', 'sujet', 'message')
    readonly_fields = ('nom', 'email', 'sujet', 'message', 'date')

