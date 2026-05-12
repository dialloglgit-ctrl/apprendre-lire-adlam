from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime


NIVEAU_CHOICES = [
    ('debutant', 'Débutant'),
    ('intermediaire', 'Intermédiaire'),
    ('avance', 'Avancé'),
]

# Seuils XP → niveau joueur
NIVEAUX_XP = [
    (0,    'Fuɗɗorde',   '🌱', 'debutant'),
    (50,   'Janngooɗo',  '📖', 'debutant'),
    (150,  'Jaɓɓiiɗo',   '⭐', 'intermediaire'),
    (300,  'Tiiɗɗo',     '🔥', 'intermediaire'),
    (500,  'Gonɗo',      '💎', 'avance'),
    (800,  'Mawɗo',      '🏆', 'avance'),
    (1200, 'Jaaɓi-hoolere', '👑', 'avance'),
]

BADGES_DEF = [
    ('premiere_lettre',  '🔤', 'Première lettre',   'Consulter une lettre de l\'alphabet'),
    ('premier_exercice', '🎯', 'Premier exercice',  'Réussir un premier exercice'),
    ('serie_3',          '🔥', 'Série de 3',        '3 jours consécutifs d\'activité'),
    ('serie_7',          '🔥🔥','Série de 7',       '7 jours consécutifs d\'activité'),
    ('premiere_lecon',   '📘', 'Première leçon',    'Terminer une première leçon'),
    ('dix_exercices',    '🏅', '10 exercices',      'Réussir 10 exercices'),
    ('vingt_exercices',  '🥈', '20 exercices',      'Réussir 20 exercices'),
    ('cent_points',      '⭐', '100 XP',            'Atteindre 100 points'),
    ('cinqcent_points',  '💎', '500 XP',            'Atteindre 500 points'),
    ('alphabet_complet', '👑', 'Alphabet complet',  'Consulter les 28 lettres'),
    ('explorateur_video', '🎬', 'Explorateur',       'Regarder une vidéo d\'apprentissage'),
    ('bibliophile',       '📚', 'Bibliophile',      'Consulter la bibliothèque de livres'),
]


class LettrAdlam(models.Model):
    nom = models.CharField(max_length=50)           # nom de la lettre ex: Alif
    caractere = models.CharField(max_length=10)     # le glyphe Adlam 𞤀
    transliteration = models.CharField(max_length=20)  # ex: A, B, C...
    prononciation = models.CharField(max_length=100, blank=True)
    exemple_mot = models.CharField(max_length=100, blank=True)
    exemple_mot_latin = models.CharField(max_length=100, blank=True)
    audio = models.FileField(upload_to='audio/lettres/', blank=True, null=True)
    ordre = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordre']
        verbose_name = 'Lettre Adlam'
        verbose_name_plural = 'Lettres Adlam'

    def __str__(self):
        return f"{self.caractere} ({self.nom})"


class Lecon(models.Model):
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    niveau = models.CharField(max_length=20, choices=NIVEAU_CHOICES, default='debutant')
    contenu = models.TextField()
    ordre = models.PositiveIntegerField(default=0)
    lettres = models.ManyToManyField(LettrAdlam, blank=True, related_name='lecons')
    creee_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordre']
        verbose_name = 'Leçon'
        verbose_name_plural = 'Leçons'

    def __str__(self):
        return self.titre


class Exercice(models.Model):
    TYPE_CHOICES = [
        ('qcm', 'QCM'),
        ('dictee', 'Dictée'),
        ('association', 'Association lettre/son'),
        ('ecriture', 'Écriture'),
    ]
    lecon = models.ForeignKey(Lecon, on_delete=models.CASCADE, related_name='exercices', null=True, blank=True)
    type_exercice = models.CharField(max_length=20, choices=TYPE_CHOICES)
    question = models.TextField()
    reponse_correcte = models.CharField(max_length=300)
    choix = models.JSONField(default=list, blank=True)  # pour QCM : liste de choix
    niveau = models.CharField(max_length=20, choices=NIVEAU_CHOICES, default='debutant')
    ordre = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordre']
        verbose_name = 'Exercice'
        verbose_name_plural = 'Exercices'

    def __str__(self):
        return f"[{self.get_type_exercice_display()}] {self.question[:60]}"


class Progression(models.Model):
    utilisateur = models.OneToOneField(User, on_delete=models.CASCADE, related_name='progression')
    lecons_terminees = models.ManyToManyField(Lecon, blank=True, related_name='terminees_par')
    exercices_reussis = models.ManyToManyField(Exercice, blank=True, related_name='reussis_par')
    points = models.PositiveIntegerField(default=0)
    derniere_activite = models.DateTimeField(auto_now=True)
    # Séries de jours consécutifs
    serie_jours = models.PositiveIntegerField(default=0)
    date_derniere_serie = models.DateField(null=True, blank=True)
    # Lettres consultées (pour badge alphabet complet)
    lettres_vues = models.ManyToManyField(LettrAdlam, blank=True, related_name='vues_par')
    # Badges débloqués (liste de codes)
    badges = models.JSONField(default=list)

    class Meta:
        verbose_name = 'Progression'
        verbose_name_plural = 'Progressions'

    def __str__(self):
        return f"Progression de {self.utilisateur.username}"

    @property
    def nb_lecons_terminees(self):
        return self.lecons_terminees.count()

    @property
    def pourcentage(self):
        total = Lecon.objects.count()
        if total == 0:
            return 0
        return int((self.nb_lecons_terminees / total) * 100)

    @property
    def niveau_info(self):
        """Retourne (label_pulaar, emoji, xp_actuel, xp_prochain, pct_vers_prochain)."""
        pts = self.points
        label, emoji = NIVEAUX_XP[0][1], NIVEAUX_XP[0][2]
        xp_actuel = 0
        xp_prochain = NIVEAUX_XP[1][0]
        for i, (seuil, lbl, emj, _) in enumerate(NIVEAUX_XP):
            if pts >= seuil:
                label, emoji = lbl, emj
                xp_actuel = seuil
                xp_prochain = NIVEAUX_XP[i + 1][0] if i + 1 < len(NIVEAUX_XP) else None
        if xp_prochain is None:
            pct = 100
        else:
            tranche = xp_prochain - xp_actuel
            pct = int((pts - xp_actuel) / tranche * 100) if tranche else 100
        return {'label': label, 'emoji': emoji, 'xp_prochain': xp_prochain, 'pct': pct}

    def update_serie(self):
        """Met à jour la série quotidienne. Appeler à chaque activité."""
        today = timezone.localdate()
        if self.date_derniere_serie == today:
            return  # déjà comptabilisé aujourd'hui
        if self.date_derniere_serie == today - datetime.timedelta(days=1):
            self.serie_jours += 1
        else:
            self.serie_jours = 1
        self.date_derniere_serie = today
        self.save(update_fields=['serie_jours', 'date_derniere_serie'])

    def debloquer_badge(self, code: str):
        """Ajoute un badge si pas encore débloqué. Retourne True si nouveau."""
        if code not in self.badges:
            self.badges.append(code)
            self.save(update_fields=['badges'])
            return True
        return False

    def evaluer_badges(self):
        """Vérifie et débloque automatiquement les badges mérités."""
        nouveaux = []
        ex_count = self.exercices_reussis.count()
        if ex_count >= 1 and self.debloquer_badge('premier_exercice'):
            nouveaux.append('premier_exercice')
        if ex_count >= 10 and self.debloquer_badge('dix_exercices'):
            nouveaux.append('dix_exercices')
        if ex_count >= 20 and self.debloquer_badge('vingt_exercices'):
            nouveaux.append('vingt_exercices')
        if self.nb_lecons_terminees >= 1 and self.debloquer_badge('premiere_lecon'):
            nouveaux.append('premiere_lecon')
        if self.points >= 100 and self.debloquer_badge('cent_points'):
            nouveaux.append('cent_points')
        if self.points >= 500 and self.debloquer_badge('cinqcent_points'):
            nouveaux.append('cinqcent_points')
        if self.serie_jours >= 3 and self.debloquer_badge('serie_3'):
            nouveaux.append('serie_3')
        if self.serie_jours >= 7 and self.debloquer_badge('serie_7'):
            nouveaux.append('serie_7')
        if self.lettres_vues.count() >= 28 and self.debloquer_badge('alphabet_complet'):
            nouveaux.append('alphabet_complet')
        return nouveaux


class Video(models.Model):
    """Vidéo pédagogique liée aux leçons Adlam."""
    CATEGORIE_CHOICES = [
        ('alphabet', 'Alphabet Adlam'),
        ('lecon',    'Leçon'),
        ('culture',  'Culture & Histoire'),
        ('autre',    'Autre'),
    ]
    titre       = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    url         = models.URLField(max_length=500, help_text="URL YouTube ou lien direct")
    miniature   = models.URLField(max_length=500, blank=True,
                                  help_text="Miniature personnalisée (optionnel, auto-détectée pour YouTube)")
    lecon       = models.ForeignKey(Lecon, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='videos')
    categorie   = models.CharField(max_length=20, choices=CATEGORIE_CHOICES, default='alphabet')
    niveau      = models.CharField(max_length=20, choices=NIVEAU_CHOICES, default='debutant')
    ordre       = models.PositiveIntegerField(default=0)
    publie      = models.BooleanField(default=True)
    date_ajout  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordre', '-date_ajout']
        verbose_name = 'Vidéo'
        verbose_name_plural = 'Vidéos'

    def __str__(self):
        return self.titre

    @property
    def youtube_id(self):
        import re
        m = re.search(
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
            self.url,
        )
        return m.group(1) if m else None

    @property
    def miniature_auto(self):
        if self.miniature:
            return self.miniature
        yt_id = self.youtube_id
        return f"https://img.youtube.com/vi/{yt_id}/mqdefault.jpg" if yt_id else ''

    @property
    def embed_url(self):
        yt_id = self.youtube_id
        return f"https://www.youtube.com/embed/{yt_id}" if yt_id else self.url


class Livre(models.Model):
    """Livre pédagogique disponible en PDF local ou via un lien externe."""
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    couverture = models.FileField(upload_to='livres/couvertures/', blank=True, null=True)
    pdf = models.FileField(upload_to='livres/', blank=True, null=True)
    url = models.URLField(max_length=500, blank=True)
    lecon = models.ForeignKey(
        Lecon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='livres',
    )
    niveau = models.CharField(max_length=20, choices=NIVEAU_CHOICES, default='debutant')
    ordre = models.PositiveIntegerField(default=0)
    publie = models.BooleanField(default=True)
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordre', '-date_ajout']
        verbose_name = 'Livre'
        verbose_name_plural = 'Livres'

    def __str__(self):
        return self.titre

    def clean(self):
        if not self.pdf and not self.url:
            raise ValidationError("Ajoutez un PDF ou un lien pour ce livre.")

    @property
    def access_url(self):
        if self.pdf:
            return self.pdf.url
        return self.url

    @property
    def source_label(self):
        if self.pdf:
            return 'PDF'
        if self.url:
            return 'Lien'
        return '—'


class LivreVendre(models.Model):
    """Livre disponible à l'achat : PDF téléchargeable ou lien externe."""
    DEVISE_CHOICES = [
        ('EUR', '€'),
        ('USD', '$'),
        ('XOF', 'FCFA'),
        ('GNF', 'GNF'),
    ]

    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    couverture = models.ImageField(upload_to='boutique/couvertures/', blank=True, null=True)
    pdf = models.FileField(upload_to='boutique/pdf/', blank=True, null=True)
    url = models.URLField(max_length=500, blank=True)
    prix = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    devise = models.CharField(max_length=4, choices=DEVISE_CHOICES, default='EUR')
    lecon = models.ForeignKey(
        Lecon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='livres_vendre',
    )
    niveau = models.CharField(max_length=20, choices=NIVEAU_CHOICES, default='debutant')
    ordre = models.PositiveIntegerField(default=0)
    publie = models.BooleanField(default=True)
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordre', '-date_ajout']
        verbose_name = 'Livre à vendre'
        verbose_name_plural = 'Livres à vendre'

    def __str__(self):
        return self.titre

    def clean(self):
        if not self.pdf and not self.url:
            raise ValidationError("Ajoutez un PDF ou un lien pour ce livre.")

    @property
    def access_url(self):
        if self.pdf:
            return self.pdf.url
        return self.url

    @property
    def source_label(self):
        if self.pdf:
            return 'PDF'
        if self.url:
            return 'Lien'
        return '—'

    @property
    def prix_affiche(self):
        if self.prix is None:
            return 'Gratuit'
        devise_symbol = dict(self.DEVISE_CHOICES).get(self.devise, self.devise)
        return f'{self.prix:,.0f} {devise_symbol}'


# ── Annonces ──────────────────────────────────────────────────────────────────
class Annonce(models.Model):
    TYPES = [
        ('info',    'Information'),
        ('success', 'Succès'),
        ('warning', 'Avertissement'),
        ('new',     'Nouveauté'),
    ]
    titre     = models.CharField(max_length=200)
    contenu   = models.TextField()
    type      = models.CharField(max_length=10, choices=TYPES, default='info')
    active    = models.BooleanField(default=True)
    date      = models.DateTimeField(auto_now_add=True)
    date_fin  = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Annonce'
        verbose_name_plural = 'Annonces'

    def __str__(self):
        return self.titre

    @property
    def is_active(self):
        if not self.active:
            return False
        if self.date_fin and timezone.now() > self.date_fin:
            return False
        return True


# ── FAQ ───────────────────────────────────────────────────────────────────────
class FAQ(models.Model):
    question = models.CharField(max_length=300)
    reponse  = models.TextField()
    categorie = models.CharField(max_length=80, blank=True, default='Général')
    ordre    = models.PositiveIntegerField(default=0)
    active   = models.BooleanField(default=True)

    class Meta:
        ordering = ['ordre', 'pk']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQ'

    def __str__(self):
        return self.question


# ── Témoignages ───────────────────────────────────────────────────────────────
class Temoignage(models.Model):
    nom      = models.CharField(max_length=100)
    message  = models.TextField()
    pays     = models.CharField(max_length=80, blank=True)
    note     = models.PositiveSmallIntegerField(default=5)  # 1-5
    approuve = models.BooleanField(default=False)
    date     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Témoignage'
        verbose_name_plural = 'Témoignages'

    def __str__(self):
        return f'{self.nom} – {self.note}★'


# ── Messages de contact ───────────────────────────────────────────────────────
class ContactMessage(models.Model):
    nom     = models.CharField(max_length=100)
    email   = models.EmailField()
    sujet   = models.CharField(max_length=200)
    message = models.TextField()
    lu      = models.BooleanField(default=False)
    date    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Message de contact'
        verbose_name_plural = 'Messages de contact'

    def __str__(self):
        return f'[{self.nom}] {self.sujet}'


# ── Notes (★) sur les livres ─────────────────────────────────────────────────
class NoteLivre(models.Model):
    livre    = models.ForeignKey(Livre, on_delete=models.CASCADE, related_name='notes')
    session  = models.CharField(max_length=64)    # clé de session anonyme
    note     = models.PositiveSmallIntegerField()  # 1-5
    date     = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('livre', 'session')
        verbose_name = 'Note livre'


# ── Compteurs de vues ─────────────────────────────────────────────────────────
class VueLivre(models.Model):
    livre = models.OneToOneField(Livre, on_delete=models.CASCADE, related_name='compteur')
    vues  = models.PositiveBigIntegerField(default=0)

    def __str__(self):
        return f'{self.livre.titre}: {self.vues} vues'


class VueVideo(models.Model):
    video = models.OneToOneField('Video', on_delete=models.CASCADE, related_name='compteur')
    vues  = models.PositiveBigIntegerField(default=0)

    def __str__(self):
        return f'{self.video.titre}: {self.vues} vues'


class UserPresence(models.Model):
    """Presence en ligne d'un utilisateur connecte (last seen + page + geo + device)."""
    utilisateur = models.OneToOneField(User, on_delete=models.CASCADE, related_name='presence')
    last_seen = models.DateTimeField(auto_now=True)
    current_path = models.CharField(max_length=255, blank=True, default='')
    ip_address = models.CharField(max_length=64, blank=True, default='')
    # Géolocalisation (remplie par le middleware via ip-api.com)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    city = models.CharField(max_length=100, blank=True, default='')
    country = models.CharField(max_length=100, blank=True, default='')
    country_code = models.CharField(max_length=4, blank=True, default='')
    # Appareil détecté depuis le User-Agent
    device_type = models.CharField(max_length=20, blank=True, default='')  # mobile/tablet/desktop

    class Meta:
        verbose_name = 'Presence utilisateur'
        verbose_name_plural = 'Presences utilisateurs'
        indexes = [
            models.Index(fields=['last_seen']),
            models.Index(fields=['current_path']),
        ]

    def __str__(self):
        return f"{self.utilisateur.username} - {self.current_path or '/'}"

