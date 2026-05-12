from django.urls import path
from . import views
from . import tb_views

urlpatterns = [

    # ── Tableau de bord admin (style WordPress) ──────────────────────────────
    path('tableau-bord/',               tb_views.tableau_bord,    name='tableau_bord'),
    path('tableau-bord/login/',         tb_views.tb_login,        name='tb_login'),
    path('tableau-bord/logout/',        tb_views.tb_logout,       name='tb_logout'),
    path('tableau-bord/lettres/',       tb_views.tb_lettres,      name='tb_lettres'),
    path('tableau-bord/lecons/',        tb_views.tb_lecons,       name='tb_lecons'),
    path('tableau-bord/exercices/',     tb_views.tb_exercices,    name='tb_exercices'),
    path('tableau-bord/utilisateurs/',  tb_views.tb_utilisateurs, name='tb_utilisateurs'),
    path('tableau-bord/progressions/',  tb_views.tb_progressions, name='tb_progressions'),
    path('tableau-bord/online-stats/',  tb_views.tb_online_stats, name='tb_online_stats'),
    path('tableau-bord/videos/',                    tb_views.tb_videos,          name='tb_videos'),
    path('tableau-bord/videos/ajouter/',            tb_views.tb_video_ajouter,   name='tb_video_ajouter'),
    path('tableau-bord/videos/<int:pk>/modifier/',  tb_views.tb_video_modifier,  name='tb_video_modifier'),
    path('tableau-bord/videos/<int:pk>/supprimer/', tb_views.tb_video_supprimer, name='tb_video_supprimer'),
    path('tableau-bord/livres/',                    tb_views.tb_livres,          name='tb_livres'),
    path('tableau-bord/livres/ajouter/',            tb_views.tb_livre_ajouter,   name='tb_livre_ajouter'),
    path('tableau-bord/livres/<int:pk>/modifier/',  tb_views.tb_livre_modifier,  name='tb_livre_modifier'),
    path('tableau-bord/livres/<int:pk>/supprimer/', tb_views.tb_livre_supprimer, name='tb_livre_supprimer'),
    path('tableau-bord/boutique/',                    tb_views.tb_boutique,          name='tb_boutique'),
    path('tableau-bord/boutique/ajouter/',            tb_views.tb_boutique_ajouter,  name='tb_boutique_ajouter'),
    path('tableau-bord/boutique/<int:pk>/modifier/',  tb_views.tb_boutique_modifier, name='tb_boutique_modifier'),
    path('tableau-bord/boutique/<int:pk>/supprimer/', tb_views.tb_boutique_supprimer,name='tb_boutique_supprimer'),
    path('tableau-bord/export/<str:type>/',           tb_views.tb_export_csv,        name='tb_export_csv'),
    path('tableau-bord/contact/',                     tb_views.tb_contact_messages,  name='tb_contact_messages'),
    path('tableau-bord/annonces/',                    tb_views.tb_annonces,          name='tb_annonces'),
    path('tableau-bord/faq/',                         tb_views.tb_faq,               name='tb_faq'),
    path('tableau-bord/temoignages/',                 tb_views.tb_temoignages,       name='tb_temoignages'),

    # Accueil
    path('', views.accueil, name='accueil'),
    path('lang/<str:lang_code>/', views.set_language, name='set_language'),
    path('manifest.webmanifest', views.pwa_manifest, name='pwa_manifest'),
    path('sw.js', views.service_worker, name='service_worker'),

    # Alphabet
    path('alphabet/', views.alphabet, name='alphabet'),
    path('alphabet/<int:pk>/', views.lettre_detail, name='lettre_detail'),

    # Leçons
    path('lecons/', views.lecons_liste, name='lecons'),
    path('lecons/<int:pk>/', views.lecon_detail, name='lecon_detail'),
    path('lecons/<int:pk>/terminer/', views.marquer_lecon_terminee, name='terminer_lecon'),

    # Exercices
    path('exercices/', views.exercices_liste, name='exercices'),
    path('exercices/<int:pk>/', views.exercice_detail, name='exercice_detail'),
    path('exercices/<int:pk>/repondre/', views.soumettre_reponse, name='soumettre_reponse'),

    # Dictée / clavier virtuel
    path('dictee/', views.dictee, name='dictee'),

    # Outils IA (traduction, translittération, correction)
    path('outils/', views.outils, name='outils'),

    # Videos d'apprentissage
    path('videos/', views.videos, name='videos'),
    path('livres/', views.livres, name='livres'),
    path('boutique/', views.boutique, name='boutique'),

    # Pages d'information
    path('recherche/', views.recherche, name='recherche'),
    path('faq/', views.faq, name='faq'),
    path('contact/', views.contact, name='contact'),
    path('annonces/', views.annonces, name='annonces'),
    path('temoignages/', views.temoignages, name='temoignages'),

    # Apprendre avec l'IA (lecture, écriture, conversation)
    path('apprendre-ia/', views.apprendre_ia, name='apprendre_ia'),
    path('classement/', views.classement, name='classement'),
    path('api/chat-ia/', views.api_chat_gemini, name='api_chat_ia'),

    # Compte
    path('compte/inscription/', views.inscription, name='inscription'),
    path('compte/connexion/', views.connexion, name='connexion'),
    path('compte/deconnexion/', views.deconnexion, name='deconnexion'),
    path('compte/profil/', views.profil, name='profil'),
]
