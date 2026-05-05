from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.urls import reverse
from django.conf import settings
import json

from .models import LettrAdlam, Lecon, Exercice, Progression, NIVEAU_CHOICES, BADGES_DEF, Livre, LivreVendre, \
    Annonce, FAQ, Temoignage, ContactMessage, Video
from .i18n import get_text, normalize_lang
from .ai_corrector import evaluate_answer as ai_evaluate


# ── Accueil ────────────────────────────────────────────────────────────────────

def accueil(request):
    nb_lettres = LettrAdlam.objects.count()
    nb_lecons = Lecon.objects.count()
    lecons_recentes = Lecon.objects.order_by('ordre')[:3]
    progression = None
    if request.user.is_authenticated:
        progression, _ = Progression.objects.get_or_create(utilisateur=request.user)
    return render(request, 'learning/accueil.html', {
        'nb_lettres': nb_lettres,
        'nb_lecons': nb_lecons,
        'lecons_recentes': lecons_recentes,
        'progression': progression,
    })


# ── Alphabet ───────────────────────────────────────────────────────────────────

def alphabet(request):
    lettres = LettrAdlam.objects.all()
    return render(request, 'learning/alphabet.html', {'lettres': lettres})


def lettre_detail(request, pk):
    lettre = get_object_or_404(LettrAdlam, pk=pk)
    # Tracker la lettre vue + badge première lettre
    if request.user.is_authenticated:
        progression, _ = Progression.objects.get_or_create(utilisateur=request.user)
        progression.lettres_vues.add(lettre)
        progression.debloquer_badge('premiere_lettre')
        progression.evaluer_badges()
    return render(request, 'learning/lettre_detail.html', {'lettre': lettre})


# ── Leçons ─────────────────────────────────────────────────────────────────────

def lecons_liste(request):
    niveau = request.GET.get('niveau', '')
    lecons = Lecon.objects.all()
    if niveau:
        lecons = lecons.filter(niveau=niveau)
    progression = None
    terminees_ids = []
    if request.user.is_authenticated:
        progression, _ = Progression.objects.get_or_create(utilisateur=request.user)
        terminees_ids = list(progression.lecons_terminees.values_list('id', flat=True))
    return render(request, 'learning/lecons.html', {
        'lecons': lecons,
        'niveaux': NIVEAU_CHOICES,
        'niveau_actif': niveau,
        'terminees_ids': terminees_ids,
    })


def lecon_detail(request, pk):
    lecon = get_object_or_404(Lecon, pk=pk)
    exercices = lecon.exercices.all() # type: ignore
    terminee = False
    if request.user.is_authenticated:
        progression, _ = Progression.objects.get_or_create(utilisateur=request.user)
        terminee = progression.lecons_terminees.filter(pk=pk).exists()
    return render(request, 'learning/lecon_detail.html', {
        'lecon': lecon,
        'exercices': exercices,
        'terminee': terminee,
    })


@login_required
@require_POST
def marquer_lecon_terminee(request, pk):
    lecon = get_object_or_404(Lecon, pk=pk)
    progression, _ = Progression.objects.get_or_create(utilisateur=request.user)
    progression.lecons_terminees.add(lecon)
    progression.points += 10
    progression.save()
    messages.success(request, f'Leçon « {lecon.titre} » marquée comme terminée !')
    return redirect('lecon_detail', pk=pk)


# ── Exercices ──────────────────────────────────────────────────────────────────

def exercices_liste(request):
    niveau = request.GET.get('niveau', '')
    exercices = Exercice.objects.all()
    if niveau:
        exercices = exercices.filter(niveau=niveau)
    return render(request, 'learning/exercices.html', {
        'exercices': exercices,
        'niveaux': NIVEAU_CHOICES,
        'niveau_actif': niveau,
    })


def exercice_detail(request, pk):
    exercice = get_object_or_404(Exercice, pk=pk)
    next_exercice = Exercice.objects.filter(pk__gt=pk).order_by('pk').first()
    return render(request, 'learning/exercice_detail.html', {
        'exercice': exercice,
        'next_exercice': next_exercice,
    })


def _normalize_answer(value):
    """Compatibilité – délègue au moteur IA."""
    from .ai_corrector import normalize_answer
    return normalize_answer(value)


def _evaluate_answer(user_answer, expected_answer):
    """Compatibilité – délègue au moteur IA."""
    return ai_evaluate(user_answer, expected_answer)


@login_required
@require_POST
def soumettre_reponse(request, pk):
    exercice = get_object_or_404(Exercice, pk=pk)
    data = json.loads(request.body)
    reponse = data.get('reponse', '')
    eval_result = ai_evaluate(reponse, exercice.reponse_correcte)
    succes = eval_result['accepted']

    points_earned = 0
    nouveaux_badges = []
    if succes:
        progression, _ = Progression.objects.get_or_create(utilisateur=request.user)
        if not progression.exercices_reussis.filter(pk=pk).exists():
            progression.exercices_reussis.add(exercice)
            if eval_result['exact']:
                points_earned = 10
            elif eval_result.get('near_phonetic'):
                points_earned = 8
            else:
                points_earned = 6
            progression.points += points_earned
            progression.save()
        progression.update_serie()
        nouveaux_badges = progression.evaluer_badges()

    current_lang = normalize_lang(request.session.get('ui_lang') or request.LANGUAGE_CODE)
    return JsonResponse({
        'succes': succes,
        'reponse_correcte': exercice.reponse_correcte,
        'score': eval_result['score'],
        'exact': eval_result['exact'],
        'near_phonetic': eval_result.get('near_phonetic', False),
        'feedback_level': eval_result['feedback_level'],
        'diff_html': eval_result.get('diff_html', ''),
        'suggestion': '' if succes else eval_result['best_match'],
        'points_earned': points_earned,
        'feedback': eval_result['feedback_message'],
        'nouveaux_badges': nouveaux_badges if succes else [],
    })


# ── Clavier virtuel / Dictée ───────────────────────────────────────────────────

def dictee(request):
    exercices_dictee = Exercice.objects.filter(type_exercice='dictee')
    return render(request, 'learning/dictee.html', {'exercices': exercices_dictee})


def outils(request):
    return render(request, 'learning/outils.html')


def videos(request):
    """Bibliotheque videos : videos en DB + section YouTube statique."""
    from .models import Video
    from collections import defaultdict

    db_videos = Video.objects.filter(publie=True).select_related('lecon').order_by('ordre', '-date_ajout')

    cat_labels = dict(Video.CATEGORIE_CHOICES)
    cat_colors = {'alphabet': '#1e3a8a', 'lecon': '#166534', 'culture': '#7c3aed', 'autre': '#92400e'}
    cat_emojis = {'alphabet': '✍️', 'lecon': '📘', 'culture': '🌍', 'autre': '🎬'}

    grouped = defaultdict(list)
    for v in db_videos:
        grouped[v.categorie].append(v)

    db_sections = [
        {'id': cat, 'title': cat_labels.get(cat, cat),
         'color': cat_colors.get(cat, '#1e3a8a'),
         'emoji': cat_emojis.get(cat, '▶️'), 'videos': vids}
        for cat, vids in grouped.items()
    ]

    yt_section = {
        'id': 'yt-adlam', 'title': 'Leçons sur YouTube',
        'subtitle': "Cours progressifs pour lire et écrire l'alphabet Adlam.",
        'tag': 'YouTube', 'color': '#dc2626', 'emoji': '📺',
        'yt_search': 'alphabet+adlam+ecriture+lecon',
        'channel_url': 'https://www.youtube.com/@user-cg7vd7me7p',
        'channel_name': 'Chaîne Adlam',
        'channel_desc': "Des vidéos dédiées à l'apprentissage de l'écriture Adlam et du Pulaar.",
        'cards': [
            {'title': "Introduction à l'Adlam", 'desc': "Histoire et origine de l'alphabet",   'yt': 'introduction+alphabet+adlam'},
            {'title': 'Les 28 lettres Adlam',   'desc': 'Apprendre chaque lettre une par une', 'yt': 'lettres+adlam+alphabet'},
            {'title': 'Ecriture des voyelles',  'desc': 'Voyelles et diacritiques Adlam',      'yt': 'voyelles+adlam+ecriture'},
            {'title': 'Lire des mots simples',  'desc': 'Premiers mots en Adlam',              'yt': 'lire+mots+adlam+pulaar'},
            {'title': "Pratiquer l'ecriture",   'desc': 'Exercices de trace des lettres',      'yt': 'ecriture+adlam+exercice'},
            {'title': 'Adlam sur ordinateur',   'desc': 'Clavier et polices Adlam',            'yt': 'adlam+clavier+ordinateur'},
        ],
    }

    return render(request, 'learning/videos.html', {
        'db_sections':  db_sections,
        'yt_section':   yt_section,
        'total_videos': db_videos.count(),
    })


def livres(request):
    """Bibliothèque publique des livres PDF et liens externes."""
    livres_qs = (
        Livre.objects
        .filter(publie=True)
        .select_related('lecon')
        .order_by('ordre', '-date_ajout')
    )
    return render(request, 'learning/livres.html', {
        'livres': livres_qs,
        'total_livres': livres_qs.count(),
    })


def boutique(request):
    """Page publique des livres à vendre."""
    livres_qs = (
        LivreVendre.objects
        .filter(publie=True)
        .select_related('lecon')
        .order_by('ordre', '-date_ajout')
    )
    return render(request, 'learning/boutique.html', {
        'livres': livres_qs,
        'total_livres': livres_qs.count(),
    })

# ── Recherche globale ────────────────────────────────────────────────────────
def recherche(request):
    """Endpoint JSON pour la barre de recherche globale."""
    q = request.GET.get('q', '').strip()
    if not q or len(q) < 2:
        return JsonResponse({'total': 0, 'lecons': [], 'livres': [], 'videos': []})
    lecons_qs = Lecon.objects.filter(titre__icontains=q)[:6]
    livres_qs = Livre.objects.filter(titre__icontains=q, publie=True)[:6]
    videos_qs = Video.objects.filter(titre__icontains=q, publie=True)[:6]
    lecons = [{'titre': o.titre, 'url': f'/lecons/{o.slug}/', 'sub': ''} for o in lecons_qs]
    livres = [{'titre': o.titre, 'url': f'/livres/', 'sub': o.get_niveau_display() if hasattr(o, 'get_niveau_display') else ''} for o in livres_qs]
    videos = [{'titre': o.titre, 'url': f'/videos/', 'sub': ''} for o in videos_qs]
    return JsonResponse({'total': len(lecons) + len(livres) + len(videos), 'lecons': lecons, 'livres': livres, 'videos': videos})


# ── FAQ ───────────────────────────────────────────────────────────────────────
def faq(request):
    """Page FAQ publique."""
    categories = FAQ.objects.filter(active=True).values_list('categorie', flat=True).distinct()
    faqs_par_cat = {}
    for cat in categories:
        faqs_par_cat[cat] = FAQ.objects.filter(active=True, categorie=cat).order_by('ordre')
    return render(request, 'learning/faq.html', {'faqs_par_cat': faqs_par_cat})


# ── Contact ───────────────────────────────────────────────────────────────────
def contact(request):
    """Page de contact avec formulaire."""
    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        email = request.POST.get('email', '').strip()
        sujet = request.POST.get('sujet', '').strip()
        message = request.POST.get('message', '').strip()
        if nom and email and sujet and message:
            ContactMessage.objects.create(nom=nom, email=email, sujet=sujet, message=message)
            messages.success(request, 'Votre message a été envoyé avec succès !')
            return redirect('contact')
        else:
            messages.error(request, 'Tous les champs sont obligatoires.')
    return render(request, 'learning/contact.html')


# ── Annonces ─────────────────────────────────────────────────────────────────
def annonces(request):
    """Page fil d'actualités."""
    annonces_qs = Annonce.objects.filter(active=True)
    return render(request, 'learning/annonces.html', {'annonces': annonces_qs})


# ── Témoignages ───────────────────────────────────────────────────────────────
def temoignages(request):
    """Page témoignages avec formulaire de soumission."""
    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        msg = request.POST.get('message', '').strip()
        pays = request.POST.get('pays', '').strip()
        note = int(request.POST.get('note', 5))
        if nom and msg and 1 <= note <= 5:
            Temoignage.objects.create(nom=nom, message=msg, pays=pays, note=note, approuve=False)
            messages.success(request, 'Merci pour votre témoignage ! Il sera publié après modération.')
            return redirect('temoignages')
    temoignages_qs = Temoignage.objects.filter(approuve=True)
    return render(request, 'learning/temoignages.html', {'temoignages': temoignages_qs})


def apprendre_ia(request):
    """Page IA : Lire / Écrire / Converser en Pulaar Adlam."""
    from .transliterator import latin_to_adlam

    # Catalogue de phrases Pulaar progressives (latin → Adlam calculé)
    PHRASES = [
        # Niveau débutant — salutations
        {"fr": "Bonjour",           "latin": "Jam waali",         "cat": "salutation"},
        {"fr": "Bonsoir",           "latin": "Jam hiiri",         "cat": "salutation"},
        {"fr": "Comment vas-tu ?",  "latin": "No mbadaa ?",       "cat": "salutation"},
        {"fr": "Je vais bien.",     "latin": "Mi waawi.",         "cat": "salutation"},
        {"fr": "Merci",             "latin": "A jaaraama",        "cat": "salutation"},
        {"fr": "Au revoir",         "latin": "Seeɗa",             "cat": "salutation"},
        {"fr": "S'il te plaît",     "latin": "Tiiɗno",            "cat": "salutation"},
        {"fr": "Bienvenue",         "latin": "Jam joodii",        "cat": "salutation"},
        # Niveau débutant — école
        {"fr": "Je lis.",           "latin": "Mi janngii.",       "cat": "ecole"},
        {"fr": "J'écris.",          "latin": "Mi winndi.",        "cat": "ecole"},
        {"fr": "Je comprends.",     "latin": "Mi faamii.",        "cat": "ecole"},
        {"fr": "Recommence.",       "latin": "Etti.",             "cat": "ecole"},
        {"fr": "C'est correct.",    "latin": "Ɗum moƴƴi.",       "cat": "ecole"},
        {"fr": "Ce n'est pas correct.", "latin": "Ɗum moƴƴaani.","cat": "ecole"},
        {"fr": "Je ne sais pas.",   "latin": "Mi anndaa.",        "cat": "ecole"},
        {"fr": "J'apprends.",       "latin": "Mi janngoo.",       "cat": "ecole"},
        # Niveau intermédiaire — famille
        {"fr": "Ma mère",           "latin": "Neene am",         "cat": "famille"},
        {"fr": "Mon père",          "latin": "Baabiraawo am",    "cat": "famille"},
        {"fr": "Mon frère",         "latin": "Banndiraabe am",   "cat": "famille"},
        {"fr": "Ma maison",         "latin": "Suudu am",         "cat": "famille"},
        # Niveau intermédiaire — vie quotidienne
        {"fr": "Je mange.",         "latin": "Mi ñaamii.",       "cat": "vie"},
        {"fr": "Je bois de l'eau.", "latin": "Mi yarii ndiyam.", "cat": "vie"},
        {"fr": "Je dors.",          "latin": "Mi dummii.",       "cat": "vie"},
        {"fr": "Je veux apprendre.", "latin": "Mi yiɗi janngo.", "cat": "vie"},
        {"fr": "C'est beau.",       "latin": "Ɗum nafata.",      "cat": "vie"},
    ]

    # Calcul de la version Adlam pour chaque phrase
    for p in PHRASES:
        p["adlam"] = latin_to_adlam(p["latin"])

    # Lettres pour le quiz aléatoire (passées au template)
    lettres = list(LettrAdlam.objects.all().values('pk', 'nom', 'caractere', 'transliteration'))

    return render(request, 'learning/apprendre_ia.html', {
        'phrases': PHRASES,
        'lettres': lettres,
    })


# ── Compte utilisateur ─────────────────────────────────────────────────────────

def inscription(request):
    if request.user.is_authenticated:
        return redirect('accueil')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Progression.objects.create(utilisateur=user)
            login(request, user)
            messages.success(request, 'Compte créé avec succès ! Bienvenue.')
            return redirect('accueil')
    else:
        form = UserCreationForm()
    return render(request, 'learning/inscription.html', {'form': form})


def connexion(request):
    if request.user.is_authenticated:
        return redirect('accueil')
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Bon retour, {user.username} !')
            return redirect(request.GET.get('next', 'accueil'))
    else:
        form = AuthenticationForm()
    return render(request, 'learning/connexion.html', {'form': form})


def deconnexion(request):
    logout(request)
    messages.info(request, 'Vous avez été déconnecté.')
    return redirect('accueil')


@login_required
def profil(request):
    progression, _ = Progression.objects.get_or_create(utilisateur=request.user)
    # Enrichir les badges avec leurs infos affichables
    badges_def_map = {code: (emj, label, desc) for code, emj, label, desc in BADGES_DEF}
    badges_affiches = []
    for code in progression.badges:
        if code in badges_def_map:
            emj, label, desc = badges_def_map[code]
            badges_affiches.append({'code': code, 'emoji': emj, 'label': label, 'desc': desc})
    # Badges non encore débloqués
    badges_locked = []
    for code, emj, label, desc in BADGES_DEF:
        if code not in progression.badges:
            badges_locked.append({'code': code, 'emoji': '🔒', 'label': label, 'desc': desc})
    return render(request, 'learning/profil.html', {
        'progression': progression,
        'niveau_info': progression.niveau_info,
        'badges_affiches': badges_affiches,
        'badges_locked': badges_locked,
    })


def set_language(request, lang_code):
    lang = normalize_lang(lang_code)
    request.session['ui_lang'] = lang
    request.session['django_language'] = lang
    next_url = request.GET.get('next') or reverse('accueil')
    response = redirect(next_url)
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang)
    return response


@never_cache
def pwa_manifest(request):
        payload = {
                'name': 'PROMET Adlam',
                'short_name': 'PROMET',
                'description': 'Apprendre a lire et ecrire Adlam - par Ibrahima Garki Diallo',
                'author': 'Ibrahima Garki Diallo',
                'start_url': '/',
                'display': 'standalone',
                'background_color': '#fffbe6',
                'theme_color': '#58cc02',
                'orientation': 'portrait-primary',
                'icons': [],
        }
        return JsonResponse(payload)


@never_cache
def service_worker(request):
        js = """
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open('promet-v1').then((cache) => cache.addAll([
            '/',
            '/static/css/style.css',
            '/static/js/main.js'
        ]))
    );
});

self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request).then((response) => response || fetch(event.request))
    );
});
"""
        return HttpResponse(js, content_type='application/javascript')
