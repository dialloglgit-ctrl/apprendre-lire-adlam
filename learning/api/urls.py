from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    path('auth/register/', views.RegisterAPIView.as_view(), name='api_register'),
    path('auth/login/', views.LoginAPIView.as_view(), name='api_login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),

    # Alphabet
    path('lettres/', views.LettrAdlamListAPIView.as_view(), name='api_lettres'),
    path('lettres/<int:pk>/', views.LettrAdlamDetailAPIView.as_view(), name='api_lettre_detail'),

    # Leçons
    path('lecons/', views.LeconListAPIView.as_view(), name='api_lecons'),
    path('lecons/<int:pk>/', views.LeconDetailAPIView.as_view(), name='api_lecon_detail'),
    path('lecons/<int:pk>/terminer/', views.TerminerLeconAPIView.as_view(), name='api_terminer_lecon'),

    # Exercices
    path('exercices/', views.ExerciceListAPIView.as_view(), name='api_exercices'),
    path('exercices/<int:pk>/', views.ExerciceDetailAPIView.as_view(), name='api_exercice_detail'),

    # IA
    path('repondre/', views.SoumettreReponseAPIView.as_view(), name='api_repondre'),
    path('evaluer/', views.evaluer_reponse_libre, name='api_evaluer'),

    # Translittération & Traduction
    path('transliterer/', views.transliterer, name='api_transliterer'),
    path('traduire/', views.traduire, name='api_traduire'),
    path('vocabulaire/', views.vocabulaire, name='api_vocabulaire'),

    # Audio TTS
    path('audio/lettre/<int:pk>/', views.audio_lettre, name='api_audio_lettre'),
    path('audio/texte/', views.audio_texte, name='api_audio_texte'),

    # Progression
    path('progression/', views.ProgressionAPIView.as_view(), name='api_progression'),
    path('chat-ia/', views.api_chat_gemini, name='api_chat_ia_rest'),
]
