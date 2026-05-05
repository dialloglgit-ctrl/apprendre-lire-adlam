"""
Tableau de bord administration PROMET (style WordPress).
Accès : /tableau-bord/   –   Code : Di1425
"""
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ValidationError
from django.utils import timezone
import csv
import datetime
import json

from .models import LettrAdlam, Lecon, Exercice, Progression, NIVEAU_CHOICES, UserPresence, Video, Livre, LivreVendre, \
    Annonce, FAQ, Temoignage, ContactMessage

# ── Géolocalisation simple (sans lib externe) ────────────────────────────────
def _geo_label(ip: str) -> str:
    """Retourne une étiquette de localisation approximative depuis l'IP."""
    if not ip or ip in ('127.0.0.1', '::1', 'localhost'):
        return 'Serveur local'
    parts = ip.split('.')
    if len(parts) == 4:
        try:
            a, b = int(parts[0]), int(parts[1])
            if a == 10:
                return 'Réseau local'
            if a == 172 and 16 <= b <= 31:
                return 'Réseau local'
            if a == 192 and b == 168:
                return 'Réseau local'
        except ValueError:
            pass
    return 'Connexion externe'


# ── Identifiants fixes (tableau de bord privé) ────────────────────────────────
_TB_USERNAME = 'Garki'
_TB_PASSWORD = 'Di1425'

# ── Décorateur : accès réservé à la session tableau de bord ───────────────────
def _tb_required(view_fn):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('tb_auth'):
            return redirect('tb_login')
        return view_fn(request, *args, **kwargs)
    wrapper.__name__ = view_fn.__name__
    return wrapper


def _clean_querystring(request, remove_keys=None):
    remove_keys = set(remove_keys or [])
    q = request.GET.copy()
    for key in remove_keys:
        q.pop(key, None)
    return q.urlencode()


def _paginate(request, queryset, per_page=20):
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(request.GET.get('page') or 1)
    return page_obj


def _maybe_export_csv(request, filename, headers, rows):
    if request.GET.get('export') != 'csv':
        return None
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(headers)
    writer.writerows(rows)
    return response


# ══ LOGIN ══════════════════════════════════════════════════════════════════════
def tb_login(request):
    if request.session.get('tb_auth'):
        return redirect('tableau_bord')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if username == _TB_USERNAME and password == _TB_PASSWORD:
            request.session['tb_auth'] = True
            return redirect('tableau_bord')

        return render(request, 'tableau_bord/login.html', {'erreur': 'Nom d\'utilisateur ou mot de passe incorrect.'})

    return render(request, 'tableau_bord/login.html', {})


# ══ LOGOUT ═════════════════════════════════════════════════════════════════════
def tb_logout(request):
    request.session.pop('tb_auth', None)
    return redirect('tb_login')


# ══ DASHBOARD ══════════════════════════════════════════════════════════════════
@_tb_required
def tableau_bord(request):
    nb_lettres   = LettrAdlam.objects.count()
    nb_lecons    = Lecon.objects.count()
    nb_exercices = Exercice.objects.count()
    nb_users     = User.objects.count()
    nb_progressions = Progression.objects.count()
    nb_videos    = Video.objects.filter(publie=True).count()
    nb_livres        = Livre.objects.filter(publie=True).count()
    nb_livres_vendre = LivreVendre.objects.filter(publie=True).count()

    seven_days_ago = timezone.now() - datetime.timedelta(days=7)
    try:
        online_minutes = int(request.GET.get('online_min', 10))
        if online_minutes not in (5, 10, 30):
            online_minutes = 10
    except (TypeError, ValueError):
        online_minutes = 10
    online_threshold = timezone.now() - datetime.timedelta(minutes=online_minutes)
    users_7d = User.objects.filter(date_joined__gte=seven_days_ago).count()
    lecons_7d = Lecon.objects.filter(creee_le__gte=seven_days_ago).count()

    online_qs = UserPresence.objects.filter(last_seen__gte=online_threshold).select_related('utilisateur')
    online_count = online_qs.count()
    online_by_path_raw = (
        online_qs
        .values('current_path')
        .annotate(count=Count('id'))
        .order_by('-count')[:7]
    )
    online_max = max([r['count'] for r in online_by_path_raw], default=1)
    online_by_path = []
    for row in online_by_path_raw:
        path = row['current_path'] or '/'
        online_by_path.append({
            'path': path,
            'count': row['count'],
            'pct': max(8, int((row['count'] / online_max) * 100)) if online_max else 8,
        })

    online_users_qs = online_qs.order_by('-last_seen')[:10]
    online_users = []
    for p in online_users_qs:
        p.geo_label = _geo_label(p.ip_address)
        online_users.append(p)

    # Marqueurs carte (utilisateurs avec coordonnées connues)
    map_markers = []
    for p in online_qs:
        if p.latitude is not None and p.longitude is not None:
            map_markers.append({
                'lat': p.latitude,
                'lng': p.longitude,
                'label': p.utilisateur.username,
                'city': p.city or '',
                'country': p.country or '',
            })

    # Stats appareils (tous les utilisateurs présents cette semaine)
    week_qs = UserPresence.objects.filter(last_seen__gte=seven_days_ago)
    device_counts = {
        'mobile': week_qs.filter(device_type='mobile').count(),
        'tablet': week_qs.filter(device_type='tablet').count(),
        'desktop': week_qs.filter(device_type='desktop').count(),
    }
    device_total = max(sum(device_counts.values()), 1)
    device_stats = [
        {'label': 'Mobile 📱', 'key': 'mobile', 'count': device_counts['mobile'],
         'pct': round(device_counts['mobile'] / device_total * 100), 'color': '#2271b1'},
        {'label': 'Tablette 📟', 'key': 'tablet', 'count': device_counts['tablet'],
         'pct': round(device_counts['tablet'] / device_total * 100), 'color': '#dba617'},
        {'label': 'Desktop 💻', 'key': 'desktop', 'count': device_counts['desktop'],
         'pct': round(device_counts['desktop'] / device_total * 100), 'color': '#00a32a'},
    ]

    ex_par_niveau_raw = (
        Exercice.objects
        .values('niveau')
        .annotate(count=Count('id'))
        .order_by('niveau')
    )
    couleurs = {'debutant': '#00a32a', 'intermediaire': '#dba617', 'avance': '#d63638'}
    labels   = {'debutant': 'Débutant', 'intermediaire': 'Intermédiaire', 'avance': 'Avancé'}
    ex_par_niveau = [
        {
            'label': labels.get(r['niveau'], r['niveau']),
            'count': r['count'],
            'pct': round(r['count'] / nb_exercices * 100) if nb_exercices else 0,
            'color': couleurs.get(r['niveau'], '#2271b1'),
        }
        for r in ex_par_niveau_raw
    ]

    derniers_exercices = Exercice.objects.order_by('-pk')[:8]
    dernieres_lecons   = Lecon.objects.order_by('-pk')[:6]
    top_progressions   = Progression.objects.order_by('-points').select_related('utilisateur')[:8]

    lecons_sans_exercices = Lecon.objects.annotate(nb_ex=Count('exercices')).filter(nb_ex=0).count()
    exercices_sans_lecon = Exercice.objects.filter(lecon__isnull=True).count()
    lettres_sans_audio = LettrAdlam.objects.filter(audio__isnull=True).count()

    derniers_users_qs = User.objects.order_by('-date_joined')[:8]
    derniers_users = []
    for u in derniers_users_qs:
        try:
            xp = u.progression.points
        except Exception:
            xp = 0
        derniers_users.append({'pk': u.pk, 'username': u.username, 'date_joined': u.date_joined, 'xp': xp})

    recent_activity = []
    for u in User.objects.order_by('-date_joined')[:5]:
        recent_activity.append({
            'kind': 'user',
            'title': f"Nouveau compte: {u.username}",
            'time': u.date_joined,
            'dot': 'green',
        })
    for l in Lecon.objects.order_by('-creee_le')[:5]:
        recent_activity.append({
            'kind': 'lecon',
            'title': f"Leçon publiée: {l.titre}",
            'time': l.creee_le,
            'dot': 'orange',
        })
    for e in Exercice.objects.order_by('-pk')[:5]:
        recent_activity.append({
            'kind': 'exercice',
            'title': f"Exercice ajouté: {e.question[:42]}",
            'time': timezone.now(),
            'dot': 'blue',
        })
    recent_activity = sorted(recent_activity, key=lambda x: x['time'], reverse=True)[:10]

    day_labels = []
    users_series = []
    lecons_series = []
    for delta in range(6, -1, -1):
        day = timezone.localdate() - datetime.timedelta(days=delta)
        day_labels.append(day.strftime('%d/%m'))
        users_series.append(User.objects.filter(date_joined__date=day).count())
        lecons_series.append(Lecon.objects.filter(creee_le__date=day).count())

    users_max = max(users_series) if users_series else 1
    lecons_max = max(lecons_series) if lecons_series else 1
    users_series_pct = [max(8, int((v / users_max) * 100)) if users_max else 8 for v in users_series]
    lecons_series_pct = [max(8, int((v / lecons_max) * 100)) if lecons_max else 8 for v in lecons_series]

    return render(request, 'tableau_bord/dashboard.html', {
        'stats': {
            'nb_lettres': nb_lettres,
            'nb_lecons': nb_lecons,
            'nb_exercices': nb_exercices,
            'nb_users': nb_users,
            'nb_progressions': nb_progressions,
            'nb_videos': nb_videos,
            'nb_livres': nb_livres,
            'nb_livres_vendre': nb_livres_vendre,
            'users_7d': users_7d,
            'lecons_7d': lecons_7d,
            'online_count': online_count,
            'ex_par_niveau': ex_par_niveau,
        },
        'derniers_exercices': derniers_exercices,
        'dernieres_lecons': dernieres_lecons,
        'top_progressions': top_progressions,
        'derniers_users': derniers_users,
        'alerts': {
            'lecons_sans_exercices': lecons_sans_exercices,
            'exercices_sans_lecon': exercices_sans_lecon,
            'lettres_sans_audio': lettres_sans_audio,
        },
        'recent_activity': recent_activity,
        'trends': {
            'labels': day_labels,
            'users': users_series,
            'lecons': lecons_series,
            'users_pct': users_series_pct,
            'lecons_pct': lecons_series_pct,
        },
        'online_by_path': online_by_path,
        'online_users': online_users,
        'online_minutes': online_minutes,
        'online_filter_options': [
            {'value': 5,  'active': online_minutes == 5},
            {'value': 10, 'active': online_minutes == 10},
            {'value': 30, 'active': online_minutes == 30},
        ],
        'map_markers': map_markers,
        'device_stats': device_stats,
    })


# ══ LISTES ═════════════════════════════════════════════════════════════════════
@_tb_required
def tb_lettres(request):
    search = request.GET.get('q', '').strip()
    order = request.GET.get('order', 'ordre')

    lettres = LettrAdlam.objects.all()
    if search:
        lettres = lettres.filter(
            Q(nom__icontains=search)
            | Q(caractere__icontains=search)
            | Q(transliteration__icontains=search)
            | Q(prononciation__icontains=search)
        )

    order_map = {
        'ordre': 'ordre',
        'ordre_desc': '-ordre',
        'nom': 'nom',
        'recent': '-pk',
    }
    lettres = lettres.order_by(order_map.get(order, 'ordre'))

    export_response = _maybe_export_csv(
        request,
        'lettres_adlam.csv',
        ['ID', 'Caractere', 'Nom', 'Transliteration', 'Prononciation', 'Ordre'],
        [
            [l.pk, l.caractere, l.nom, l.transliteration, l.prononciation or '', l.ordre]
            for l in lettres
        ],
    )
    if export_response:
        return export_response

    page_obj = _paginate(request, lettres, 18)
    return render(request, 'tableau_bord/lettres.html', {
        'lettres': page_obj.object_list,
        'page_obj': page_obj,
        'total_count': lettres.count(),
        'q': search,
        'order': order,
        'order_choices': [
            ('ordre', 'Ordre (A→Z)'),
            ('ordre_desc', 'Ordre (Z→A)'),
            ('nom', 'Nom'),
            ('recent', 'Plus récents'),
        ],
        'show_search': True,
        'show_order': True,
        'query_string_no_page_export': _clean_querystring(request, {'page', 'export'}),
        'page_title': '🔤 Lettres Adlam',
        'active': 'lettres',
        'add_url': '/admin/learning/lettradlam/add/',
    })


@_tb_required
def tb_lecons(request):
    search = request.GET.get('q', '').strip()
    niveau = request.GET.get('niveau', '').strip()
    order = request.GET.get('order', 'recent')

    lecons = Lecon.objects.all().prefetch_related('exercices')
    if search:
        lecons = lecons.filter(Q(titre__icontains=search) | Q(description__icontains=search))
    if niveau:
        lecons = lecons.filter(niveau=niveau)

    order_map = {
        'recent': '-pk',
        'anciens': 'pk',
        'titre': 'titre',
        'niveau': 'niveau',
    }
    lecons = lecons.order_by(order_map.get(order, '-pk'))

    export_response = _maybe_export_csv(
        request,
        'lecons.csv',
        ['ID', 'Titre', 'Niveau', 'NombreExercices', 'CreeeLe'],
        [[l.pk, l.titre, l.get_niveau_display(), l.exercices.count(), l.creee_le] for l in lecons],
    )
    if export_response:
        return export_response

    page_obj = _paginate(request, lecons, 15)
    return render(request, 'tableau_bord/lecons.html', {
        'lecons': page_obj.object_list,
        'page_obj': page_obj,
        'total_count': lecons.count(),
        'q': search,
        'niveau': niveau,
        'order': order,
        'show_search': True,
        'show_level_filter': True,
        'show_order': True,
        'level_choices': NIVEAU_CHOICES,
        'order_choices': [
            ('recent', 'Plus récentes'),
            ('anciens', 'Plus anciennes'),
            ('titre', 'Titre A→Z'),
            ('niveau', 'Niveau'),
        ],
        'query_string_no_page_export': _clean_querystring(request, {'page', 'export'}),
        'page_title': '📘 Leçons',
        'active': 'lecons',
        'add_url': '/admin/learning/lecon/add/',
    })


@_tb_required
def tb_exercices(request):
    search = request.GET.get('q', '').strip()
    niveau = request.GET.get('niveau', '').strip()
    type_exercice = request.GET.get('type', '').strip()
    order = request.GET.get('order', 'recent')

    exercices = Exercice.objects.all().select_related('lecon')
    if search:
        exercices = exercices.filter(
            Q(question__icontains=search)
            | Q(reponse_correcte__icontains=search)
            | Q(lecon__titre__icontains=search)
        )
    if niveau:
        exercices = exercices.filter(niveau=niveau)
    if type_exercice:
        exercices = exercices.filter(type_exercice=type_exercice)

    order_map = {
        'recent': '-pk',
        'anciens': 'pk',
        'niveau': 'niveau',
        'type': 'type_exercice',
    }
    exercices = exercices.order_by(order_map.get(order, '-pk'))

    export_response = _maybe_export_csv(
        request,
        'exercices.csv',
        ['ID', 'Question', 'Type', 'Niveau', 'Lecon'],
        [
            [e.pk, e.question, e.get_type_exercice_display(), e.get_niveau_display(), e.lecon.titre if e.lecon else '']
            for e in exercices
        ],
    )
    if export_response:
        return export_response

    page_obj = _paginate(request, exercices, 18)
    return render(request, 'tableau_bord/exercices.html', {
        'exercices': page_obj.object_list,
        'page_obj': page_obj,
        'total_count': exercices.count(),
        'q': search,
        'niveau': niveau,
        'type_exercice': type_exercice,
        'order': order,
        'show_search': True,
        'show_level_filter': True,
        'show_type_filter': True,
        'show_order': True,
        'level_choices': NIVEAU_CHOICES,
        'type_choices': Exercice.TYPE_CHOICES,
        'order_choices': [
            ('recent', 'Plus récents'),
            ('anciens', 'Plus anciens'),
            ('niveau', 'Niveau'),
            ('type', 'Type'),
        ],
        'query_string_no_page_export': _clean_querystring(request, {'page', 'export'}),
        'page_title': '🎯 Exercices',
        'active': 'exercices',
        'add_url': '/admin/learning/exercice/add/',
    })


@_tb_required
def tb_utilisateurs(request):
    search = request.GET.get('q', '').strip()
    staff = request.GET.get('staff', '').strip()
    order = request.GET.get('order', 'recent')

    users = User.objects.all()
    if search:
        users = users.filter(Q(username__icontains=search) | Q(email__icontains=search))
    if staff == 'yes':
        users = users.filter(is_staff=True)
    elif staff == 'no':
        users = users.filter(is_staff=False)

    order_map = {
        'recent': '-date_joined',
        'anciens': 'date_joined',
        'az': 'username',
        'za': '-username',
    }
    users = users.order_by(order_map.get(order, '-date_joined'))

    export_response = _maybe_export_csv(
        request,
        'utilisateurs.csv',
        ['ID', 'Username', 'Email', 'IsStaff', 'DateJoined', 'Points', 'Serie'],
        [
            [
                u.pk,
                u.username,
                u.email,
                u.is_staff,
                u.date_joined,
                getattr(getattr(u, 'progression', None), 'points', 0),
                getattr(getattr(u, 'progression', None), 'serie_jours', 0),
            ]
            for u in users
        ],
    )
    if export_response:
        return export_response

    page_obj = _paginate(request, users, 18)
    rows = []
    for u in page_obj.object_list:
        try:
            xp = u.progression.points
            serie = u.progression.serie_jours
        except Exception:
            xp, serie = 0, 0
        rows.append({'obj': u, 'xp': xp, 'serie': serie})
    return render(request, 'tableau_bord/utilisateurs.html', {
        'rows': rows,
        'page_obj': page_obj,
        'total_count': users.count(),
        'q': search,
        'staff': staff,
        'order': order,
        'show_search': True,
        'show_staff_filter': True,
        'show_order': True,
        'order_choices': [
            ('recent', 'Inscrits récemment'),
            ('anciens', 'Plus anciens'),
            ('az', 'Nom A→Z'),
            ('za', 'Nom Z→A'),
        ],
        'query_string_no_page_export': _clean_querystring(request, {'page', 'export'}),
        'page_title': '👥 Utilisateurs',
        'active': 'users',
        'add_url': '/admin/auth/user/add/',
    })


@_tb_required
def tb_progressions(request):
    search = request.GET.get('q', '').strip()
    order = request.GET.get('order', 'points')

    progressions = (
        Progression.objects
        .select_related('utilisateur')
    )
    if search:
        progressions = progressions.filter(utilisateur__username__icontains=search)

    order_map = {
        'points': '-points',
        'serie': '-serie_jours',
        'recent': '-derniere_activite',
    }
    progressions = progressions.order_by(order_map.get(order, '-points'))

    export_response = _maybe_export_csv(
        request,
        'progressions.csv',
        ['Username', 'Points', 'SerieJours', 'LettresVues', 'Badges', 'DerniereActivite'],
        [
            [
                p.utilisateur.username,
                p.points,
                p.serie_jours,
                p.lettres_vues.count(),
                len(p.badges),
                p.derniere_activite,
            ]
            for p in progressions
        ],
    )
    if export_response:
        return export_response

    page_obj = _paginate(request, progressions, 18)
    return render(request, 'tableau_bord/progressions.html', {
        'progressions': page_obj.object_list,
        'page_obj': page_obj,
        'total_count': progressions.count(),
        'q': search,
        'order': order,
        'show_search': True,
        'show_order': True,
        'order_choices': [
            ('points', 'Points décroissants'),
            ('serie', 'Séries les plus hautes'),
            ('recent', 'Activité récente'),
        ],
        'query_string_no_page_export': _clean_querystring(request, {'page', 'export'}),
        'page_title': '📈 Progressions',
        'active': 'prog',
    })


# ══ ENDPOINT JSON : statistiques en ligne (auto-refresh) ══════════════════════
@_tb_required
def tb_online_stats(request):
    """Retourne les données 'en ligne' en JSON pour le widget auto-refresh."""
    try:
        minutes = int(request.GET.get('online_min', 10))
        if minutes not in (5, 10, 30):
            minutes = 10
    except (TypeError, ValueError):
        minutes = 10

    threshold = timezone.now() - datetime.timedelta(minutes=minutes)
    qs = UserPresence.objects.filter(last_seen__gte=threshold).select_related('utilisateur')

    count = qs.count()

    by_path_raw = (
        qs.values('current_path')
        .annotate(cnt=Count('id'))
        .order_by('-cnt')[:7]
    )
    max_cnt = max([r['cnt'] for r in by_path_raw], default=1)
    by_path = [
        {
            'path': r['current_path'] or '/',
            'count': r['cnt'],
            'pct': max(8, int((r['cnt'] / max_cnt) * 100)) if max_cnt else 8,
        }
        for r in by_path_raw
    ]

    now = timezone.now()
    users = []
    for p in qs.order_by('-last_seen')[:10]:
        diff = int((now - p.last_seen).total_seconds())
        if diff < 60:
            ago = f"{diff}s"
        else:
            ago = f"{diff // 60}min {diff % 60}s"
        users.append({
            'username': p.utilisateur.username,
            'path': p.current_path or '/',
            'ago': ago,
            'ip': p.ip_address or '—',
            'geo': _geo_label(p.ip_address),
            'city': p.city or '',
            'country': p.country or '',
            'device': p.device_type or 'desktop',
        })

    # Marqueurs carte
    markers = []
    for p in qs:
        if p.latitude is not None and p.longitude is not None:
            markers.append({
                'lat': p.latitude,
                'lng': p.longitude,
                'label': p.utilisateur.username,
                'city': p.city or '',
                'country': p.country or '',
            })

    return JsonResponse({'count': count, 'minutes': minutes, 'by_path': by_path, 'users': users, 'markers': markers})


# ══ VIDÉOS ════════════════════════════════════════════════════════════════════
@_tb_required
def tb_videos(request):
    search    = request.GET.get('q', '').strip()
    categorie = request.GET.get('categorie', '')
    publie    = request.GET.get('publie', '')

    qs = Video.objects.select_related('lecon').order_by('ordre', '-date_ajout')
    if search:
        qs = qs.filter(titre__icontains=search)
    if categorie:
        qs = qs.filter(categorie=categorie)
    if publie == '1':
        qs = qs.filter(publie=True)
    elif publie == '0':
        qs = qs.filter(publie=False)

    page_obj = _paginate(request, qs, 20)
    return render(request, 'tableau_bord/videos.html', {
        'videos':        page_obj.object_list,
        'page_obj':      page_obj,
        'total_count':   qs.count(),
        'q':             search,
        'categorie':     categorie,
        'publie':        publie,
        'cat_choices':   Video.CATEGORIE_CHOICES,
        'show_search':   True,
        'add_url':       '/tableau-bord/videos/ajouter/',
        'page_title':    '🎬 Vidéos',
        'active':        'videos',
    })


@_tb_required
def tb_video_ajouter(request):
    lecons = Lecon.objects.order_by('ordre', 'titre')
    erreur = None
    form   = {
        'titre': '', 'url': '', 'description': '', 'miniature': '',
        'categorie': 'alphabet', 'niveau': 'debutant',
        'lecon_id': None, 'ordre': '0', 'publie': True,
    }

    if request.method == 'POST':
        titre       = request.POST.get('titre', '').strip()
        url         = request.POST.get('url', '').strip()
        description = request.POST.get('description', '').strip()
        miniature   = request.POST.get('miniature', '').strip()
        categorie   = request.POST.get('categorie', 'alphabet')
        niveau      = request.POST.get('niveau', 'debutant')
        lecon_id    = request.POST.get('lecon', '') or None
        ordre       = request.POST.get('ordre', '0')
        publie      = request.POST.get('publie') == 'on'

        form = {
            'titre': titre, 'url': url, 'description': description,
            'miniature': miniature, 'categorie': categorie, 'niveau': niveau,
            'lecon_id': lecon_id, 'ordre': ordre, 'publie': publie,
        }

        if not titre:
            erreur = "Le titre est obligatoire."
        elif not url:
            erreur = "L'URL de la vidéo est obligatoire."
        else:
            try:
                ordre_int = int(ordre)
            except (ValueError, TypeError):
                ordre_int = 0
            lecon_obj = None
            if lecon_id:
                try:
                    lecon_obj = Lecon.objects.get(pk=lecon_id)
                except Lecon.DoesNotExist:
                    pass
            Video.objects.create(
                titre=titre, url=url, description=description,
                miniature=miniature, categorie=categorie, niveau=niveau,
                lecon=lecon_obj, ordre=ordre_int, publie=publie,
            )
            return redirect('tb_videos')

    return render(request, 'tableau_bord/video_form.html', {
        'lecons':      lecons,
        'cat_choices': Video.CATEGORIE_CHOICES,
        'form':        form,
        'erreur':      erreur,
        'page_title':  '🎬 Ajouter une vidéo',
        'active':      'videos',
    })


@_tb_required
def tb_video_modifier(request, pk):
    try:
        video = Video.objects.get(pk=pk)
    except Video.DoesNotExist:
        return redirect('tb_videos')

    lecons = Lecon.objects.order_by('ordre', 'titre')
    erreur = None

    if request.method == 'POST':
        video.titre       = request.POST.get('titre', '').strip()
        video.url         = request.POST.get('url', '').strip()
        video.description = request.POST.get('description', '').strip()
        video.miniature   = request.POST.get('miniature', '').strip()
        video.categorie   = request.POST.get('categorie', 'alphabet')
        video.niveau      = request.POST.get('niveau', 'debutant')
        video.publie      = request.POST.get('publie') == 'on'
        lecon_id          = request.POST.get('lecon', '') or None
        try:
            video.ordre = int(request.POST.get('ordre', '0'))
        except (ValueError, TypeError):
            video.ordre = 0

        if not video.titre:
            erreur = "Le titre est obligatoire."
        elif not video.url:
            erreur = "L'URL de la vidéo est obligatoire."
        else:
            video.lecon = Lecon.objects.filter(pk=lecon_id).first() if lecon_id else None
            video.save()
            return redirect('tb_videos')

    return render(request, 'tableau_bord/video_form.html', {
        'video':       video,
        'lecons':      lecons,
        'cat_choices': Video.CATEGORIE_CHOICES,
        'erreur':      erreur,
        'page_title':  '🎬 Modifier la vidéo',
        'active':      'videos',
    })


@_tb_required
def tb_video_supprimer(request, pk):
    if request.method == 'POST':
        Video.objects.filter(pk=pk).delete()
    return redirect('tb_videos')


@_tb_required
def tb_livres(request):
    search = request.GET.get('q', '').strip()
    publie = request.GET.get('publie', '')

    qs = Livre.objects.select_related('lecon').order_by('ordre', '-date_ajout')
    if search:
        qs = qs.filter(titre__icontains=search)
    if publie == '1':
        qs = qs.filter(publie=True)
    elif publie == '0':
        qs = qs.filter(publie=False)

    page_obj = _paginate(request, qs, 20)
    return render(request, 'tableau_bord/livres.html', {
        'livres': page_obj.object_list,
        'page_obj': page_obj,
        'total_count': qs.count(),
        'q': search,
        'publie': publie,
        'show_search': True,
        'add_url': '/tableau-bord/livres/ajouter/',
        'add_label': '➕ Ajouter un livre',
        'page_title': '📚 Livres',
        'active': 'livres',
    })


@_tb_required
def tb_livre_ajouter(request):
    lecons = Lecon.objects.order_by('ordre', 'titre')
    erreur = None
    form = {
        'titre': '', 'url': '', 'description': '',
        'niveau': 'debutant', 'lecon_id': None, 'ordre': '0', 'publie': True,
    }

    if request.method == 'POST':
        titre = request.POST.get('titre', '').strip()
        url = request.POST.get('url', '').strip()
        description = request.POST.get('description', '').strip()
        niveau = request.POST.get('niveau', 'debutant')
        lecon_id = request.POST.get('lecon', '') or None
        ordre = request.POST.get('ordre', '0')
        publie = request.POST.get('publie') == 'on'
        pdf = request.FILES.get('pdf')
        couverture = request.FILES.get('couverture')

        form = {
            'titre': titre, 'url': url, 'description': description,
            'niveau': niveau, 'lecon_id': lecon_id, 'ordre': ordre, 'publie': publie,
        }

        if not titre:
            erreur = 'Le titre est obligatoire.'
        elif not pdf and not url:
            erreur = 'Ajoutez un PDF ou un lien pour ce livre.'
        else:
            try:
                ordre_int = int(ordre)
            except (ValueError, TypeError):
                ordre_int = 0
            lecon_obj = Lecon.objects.filter(pk=lecon_id).first() if lecon_id else None
            livre = Livre(
                titre=titre,
                url=url,
                description=description,
                niveau=niveau,
                lecon=lecon_obj,
                ordre=ordre_int,
                publie=publie,
                couverture=couverture,
                pdf=pdf,
            )
            try:
                livre.full_clean()
                livre.save()
                return redirect('tb_livres')
            except ValidationError as exc:
                erreur = '; '.join(exc.messages)

    return render(request, 'tableau_bord/livre_form.html', {
        'lecons': lecons,
        'form': form,
        'erreur': erreur,
        'page_title': '📚 Ajouter un livre',
        'active': 'livres',
    })


@_tb_required
def tb_livre_modifier(request, pk):
    try:
        livre = Livre.objects.get(pk=pk)
    except Livre.DoesNotExist:
        return redirect('tb_livres')

    lecons = Lecon.objects.order_by('ordre', 'titre')
    erreur = None

    if request.method == 'POST':
        livre.titre = request.POST.get('titre', '').strip()
        livre.url = request.POST.get('url', '').strip()
        livre.description = request.POST.get('description', '').strip()
        livre.niveau = request.POST.get('niveau', 'debutant')
        livre.publie = request.POST.get('publie') == 'on'
        lecon_id = request.POST.get('lecon', '') or None
        pdf = request.FILES.get('pdf')
        couverture = request.FILES.get('couverture')
        if pdf:
            livre.pdf = pdf
        if couverture:
            livre.couverture = couverture
        try:
            livre.ordre = int(request.POST.get('ordre', '0'))
        except (ValueError, TypeError):
            livre.ordre = 0

        if not livre.titre:
            erreur = 'Le titre est obligatoire.'
        elif not livre.pdf and not livre.url:
            erreur = 'Ajoutez un PDF ou un lien pour ce livre.'
        else:
            livre.lecon = Lecon.objects.filter(pk=lecon_id).first() if lecon_id else None
            try:
                livre.full_clean()
                livre.save()
                return redirect('tb_livres')
            except ValidationError as exc:
                erreur = '; '.join(exc.messages)

    return render(request, 'tableau_bord/livre_form.html', {
        'livre': livre,
        'lecons': lecons,
        'erreur': erreur,
        'page_title': '📚 Modifier le livre',
        'active': 'livres',
    })


@_tb_required
def tb_livre_supprimer(request, pk):
    if request.method == 'POST':
        Livre.objects.filter(pk=pk).delete()
    return redirect('tb_livres')


# ══ LIVRES À VENDRE ══════════════════════════════════════════════════════════

@_tb_required
def tb_boutique(request):
    search = request.GET.get('q', '').strip()
    publie = request.GET.get('publie', '')

    qs = LivreVendre.objects.select_related('lecon').order_by('ordre', '-date_ajout')
    if search:
        qs = qs.filter(titre__icontains=search)
    if publie == '1':
        qs = qs.filter(publie=True)
    elif publie == '0':
        qs = qs.filter(publie=False)

    page_obj = _paginate(request, qs, 20)
    return render(request, 'tableau_bord/boutique.html', {
        'livres': page_obj.object_list,
        'page_obj': page_obj,
        'total_count': qs.count(),
        'q': search,
        'publie': publie,
        'show_search': True,
        'add_url': '/tableau-bord/boutique/ajouter/',
        'add_label': '➕ Ajouter un livre à vendre',
        'page_title': '🛒 Livres à vendre',
        'active': 'boutique',
    })


@_tb_required
def tb_boutique_ajouter(request):
    lecons = Lecon.objects.order_by('ordre', 'titre')
    erreur = None
    form = {
        'titre': '', 'url': '', 'description': '',
        'niveau': 'debutant', 'lecon_id': None, 'ordre': '0', 'publie': True,
        'prix': '', 'devise': 'EUR',
    }

    if request.method == 'POST':
        titre = request.POST.get('titre', '').strip()
        url = request.POST.get('url', '').strip()
        description = request.POST.get('description', '').strip()
        niveau = request.POST.get('niveau', 'debutant')
        lecon_id = request.POST.get('lecon', '') or None
        ordre = request.POST.get('ordre', '0')
        publie = request.POST.get('publie') == 'on'
        prix_str = request.POST.get('prix', '').strip()
        devise = request.POST.get('devise', 'EUR')
        pdf = request.FILES.get('pdf')
        couverture = request.FILES.get('couverture')

        form = {
            'titre': titre, 'url': url, 'description': description,
            'niveau': niveau, 'lecon_id': lecon_id, 'ordre': ordre, 'publie': publie,
            'prix': prix_str, 'devise': devise,
        }

        if not titre:
            erreur = 'Le titre est obligatoire.'
        elif not pdf and not url:
            erreur = 'Ajoutez un PDF ou un lien pour ce livre.'
        else:
            try:
                ordre_int = int(ordre)
            except (ValueError, TypeError):
                ordre_int = 0
            prix = None
            if prix_str:
                try:
                    prix = float(prix_str.replace(',', '.'))
                except ValueError:
                    erreur = 'Prix invalide.'
            if not erreur:
                lecon_obj = Lecon.objects.filter(pk=lecon_id).first() if lecon_id else None
                livre = LivreVendre(
                    titre=titre, url=url, description=description,
                    niveau=niveau, lecon=lecon_obj, ordre=ordre_int,
                    publie=publie, couverture=couverture, pdf=pdf,
                    prix=prix, devise=devise,
                )
                try:
                    livre.full_clean()
                    livre.save()
                    return redirect('tb_boutique')
                except ValidationError as exc:
                    erreur = '; '.join(exc.messages)

    return render(request, 'tableau_bord/livre_vendre_form.html', {
        'lecons': lecons,
        'form': form,
        'erreur': erreur,
        'page_title': '🛒 Ajouter un livre à vendre',
        'active': 'boutique',
    })


@_tb_required
def tb_boutique_modifier(request, pk):
    try:
        livre = LivreVendre.objects.get(pk=pk)
    except LivreVendre.DoesNotExist:
        return redirect('tb_boutique')

    lecons = Lecon.objects.order_by('ordre', 'titre')
    erreur = None

    if request.method == 'POST':
        livre.titre = request.POST.get('titre', '').strip()
        livre.url = request.POST.get('url', '').strip()
        livre.description = request.POST.get('description', '').strip()
        livre.niveau = request.POST.get('niveau', 'debutant')
        livre.publie = request.POST.get('publie') == 'on'
        livre.devise = request.POST.get('devise', 'EUR')
        lecon_id = request.POST.get('lecon', '') or None
        prix_str = request.POST.get('prix', '').strip()
        pdf = request.FILES.get('pdf')
        couverture = request.FILES.get('couverture')
        if pdf:
            livre.pdf = pdf
        if couverture:
            livre.couverture = couverture
        try:
            livre.ordre = int(request.POST.get('ordre', '0'))
        except (ValueError, TypeError):
            livre.ordre = 0
        if prix_str:
            try:
                livre.prix = float(prix_str.replace(',', '.'))
            except ValueError:
                erreur = 'Prix invalide.'
        else:
            livre.prix = None

        if not erreur:
            if not livre.titre:
                erreur = 'Le titre est obligatoire.'
            elif not livre.pdf and not livre.url:
                erreur = 'Ajoutez un PDF ou un lien pour ce livre.'
            else:
                livre.lecon = Lecon.objects.filter(pk=lecon_id).first() if lecon_id else None
                try:
                    livre.full_clean()
                    livre.save()
                    return redirect('tb_boutique')
                except ValidationError as exc:
                    erreur = '; '.join(exc.messages)

    return render(request, 'tableau_bord/livre_vendre_form.html', {
        'livre': livre,
        'lecons': lecons,
        'erreur': erreur,
        'page_title': '🛒 Modifier le livre à vendre',
        'active': 'boutique',
    })


@_tb_required
def tb_boutique_supprimer(request, pk):
    if request.method == 'POST':
        LivreVendre.objects.filter(pk=pk).delete()
    return redirect('tb_boutique')


# ── Export CSV ────────────────────────────────────────────────────────────────────
def tb_export_csv(request, type):
    """Export CSV des données du tableau de bord."""
    if not request.session.get('tb_auth'):
        return redirect('tb_login')
    import csv
    from django.contrib.auth.models import User
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="export_{type}.csv"'
    response.write('\ufeff')  # BOM UTF-8 pour Excel
    writer = csv.writer(response)
    if type == 'utilisateurs':
        writer.writerow(['ID', 'Nom d\'utilisateur', 'Email', 'Inscrit le', 'Actif', 'Staff'])
        for u in User.objects.all().order_by('-date_joined'):
            writer.writerow([u.pk, u.username, u.email, u.date_joined.strftime('%Y-%m-%d %H:%M'), u.is_active, u.is_staff])
    elif type == 'progressions':
        writer.writerow(['ID', 'Utilisateur', 'Leçons terminées', 'Score total', 'Badge actuel'])
        for p in Progression.objects.select_related('utilisateur').all():
            writer.writerow([p.pk, p.utilisateur.username, p.lecons_terminees, p.score_total, p.badge_actuel])
    elif type == 'messages':
        writer.writerow(['ID', 'Nom', 'Email', 'Sujet', 'Date', 'Lu'])
        for m in ContactMessage.objects.all().order_by('-date'):
            writer.writerow([m.pk, m.nom, m.email, m.sujet, m.date.strftime('%Y-%m-%d %H:%M'), 'Oui' if m.lu else 'Non'])
    else:
        writer.writerow(['Erreur'])
        writer.writerow([f'Type export inconnu : {type}'])
    return response


# ── Messages de contact ─────────────────────────────────────────────────────────
def tb_contact_messages(request):
    if not request.session.get('tb_auth'):
        return redirect('tb_login')
    if request.method == 'POST':
        action = request.POST.get('action')
        pk = request.POST.get('pk')
        if action == 'marquer_lu' and pk:
            ContactMessage.objects.filter(pk=pk).update(lu=True)
        elif action == 'supprimer' and pk:
            ContactMessage.objects.filter(pk=pk).delete()
        return redirect('tb_contact_messages')
    msgs = ContactMessage.objects.order_by('-date')
    non_lus = msgs.filter(lu=False).count()
    return render(request, 'tableau_bord/contact_messages.html', {'msgs': msgs, 'non_lus': non_lus})


# ── Annonces admin ───────────────────────────────────────────────────────────────
def tb_annonces(request):
    if not request.session.get('tb_auth'):
        return redirect('tb_login')
    if request.method == 'POST':
        action = request.POST.get('action')
        pk = request.POST.get('pk')
        if action == 'supprimer' and pk:
            Annonce.objects.filter(pk=pk).delete()
            return redirect('tb_annonces')
        if action == 'ajouter':
            Annonce.objects.create(
                titre=request.POST.get('titre', '').strip(),
                contenu=request.POST.get('contenu', '').strip(),
                type=request.POST.get('type', 'info'),
                active=request.POST.get('active') == '1',
            )
            return redirect('tb_annonces')
        if action == 'modifier' and pk:
            Annonce.objects.filter(pk=pk).update(
                titre=request.POST.get('titre', '').strip(),
                contenu=request.POST.get('contenu', '').strip(),
                type=request.POST.get('type', 'info'),
                active=request.POST.get('active') == '1',
            )
            return redirect('tb_annonces')
    annonces = Annonce.objects.order_by('-date')
    return render(request, 'tableau_bord/annonces.html', {'annonces': annonces})


# ── FAQ admin ────────────────────────────────────────────────────────────────────────
def tb_faq(request):
    if not request.session.get('tb_auth'):
        return redirect('tb_login')
    if request.method == 'POST':
        action = request.POST.get('action')
        pk = request.POST.get('pk')
        if action == 'supprimer' and pk:
            FAQ.objects.filter(pk=pk).delete()
            return redirect('tb_faq')
        if action == 'ajouter':
            FAQ.objects.create(
                question=request.POST.get('question', '').strip(),
                reponse=request.POST.get('reponse', '').strip(),
                categorie=request.POST.get('categorie', 'Général').strip(),
                ordre=int(request.POST.get('ordre', 0)),
                active=request.POST.get('active') == '1',
            )
            return redirect('tb_faq')
        if action == 'modifier' and pk:
            FAQ.objects.filter(pk=pk).update(
                question=request.POST.get('question', '').strip(),
                reponse=request.POST.get('reponse', '').strip(),
                categorie=request.POST.get('categorie', 'Général').strip(),
                ordre=int(request.POST.get('ordre', 0)),
                active=request.POST.get('active') == '1',
            )
            return redirect('tb_faq')
    faqs = FAQ.objects.order_by('ordre', 'pk')
    return render(request, 'tableau_bord/faq.html', {'faqs': faqs})


# ── Témoignages admin ───────────────────────────────────────────────────────────────
def tb_temoignages(request):
    if not request.session.get('tb_auth'):
        return redirect('tb_login')
    if request.method == 'POST':
        action = request.POST.get('action')
        pk = request.POST.get('pk')
        if action == 'approuver' and pk:
            Temoignage.objects.filter(pk=pk).update(approuve=True)
        elif action == 'supprimer' and pk:
            Temoignage.objects.filter(pk=pk).delete()
        return redirect('tb_temoignages')
    temoignages = Temoignage.objects.order_by('-date')
    nb_attente = temoignages.filter(approuve=False).count()
    return render(request, 'tableau_bord/temoignages.html', {'temoignages': temoignages, 'nb_attente': nb_attente})

