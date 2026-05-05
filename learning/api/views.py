from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
import os, io

from ..models import LettrAdlam, Lecon, Exercice, Progression
from ..ai_corrector import evaluate_answer
from ..transliterator import latin_to_adlam, adlam_to_latin, auto_convert, detect_script
from ..translator import translate_text, translate_word, get_vocabulary
from .serializers import (
    LettrAdlamSerializer, LeconSerializer, LeconDetailSerializer,
    ExerciceSerializer, ExerciceDetailSerializer,
    ProgressionSerializer, SoumettreReponseSerializer,
)


# ── Auth ───────────────────────────────────────────────────────────────────────

class RegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')
        password2 = request.data.get('password2', '')
        if not username or not password:
            return Response({'error': 'Identifiants requis.'}, status=400)
        if password != password2:
            return Response({'error': 'Les mots de passe ne correspondent pas.'}, status=400)
        if User.objects.filter(username=username).exists():
            return Response({'error': "Ce nom d'utilisateur est déjà pris."}, status=400)
        user = User.objects.create_user(username=username, password=password)
        Progression.objects.create(utilisateur=user)
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'username': user.username,
        }, status=201)


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')
        user = authenticate(username=username, password=password)
        if not user:
            return Response({'error': 'Identifiants invalides.'}, status=401)
        refresh = RefreshToken.for_user(user)
        prog, _ = Progression.objects.get_or_create(utilisateur=user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'username': user.username,
            'points': prog.points,
        })


# ── Alphabet ───────────────────────────────────────────────────────────────────

class LettrAdlamListAPIView(generics.ListAPIView):
    queryset = LettrAdlam.objects.all()
    serializer_class = LettrAdlamSerializer
    permission_classes = [permissions.AllowAny]


class LettrAdlamDetailAPIView(generics.RetrieveAPIView):
    queryset = LettrAdlam.objects.all()
    serializer_class = LettrAdlamSerializer
    permission_classes = [permissions.AllowAny]


# ── Leçons ─────────────────────────────────────────────────────────────────────

class LeconListAPIView(generics.ListAPIView):
    serializer_class = LeconSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Lecon.objects.all()
        niveau = self.request.query_params.get('niveau')
        if niveau:
            qs = qs.filter(niveau=niveau)
        return qs


class LeconDetailAPIView(generics.RetrieveAPIView):
    queryset = Lecon.objects.all()
    serializer_class = LeconDetailSerializer
    permission_classes = [permissions.AllowAny]


# ── Exercices ──────────────────────────────────────────────────────────────────

class ExerciceListAPIView(generics.ListAPIView):
    serializer_class = ExerciceSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Exercice.objects.all()
        niveau = self.request.query_params.get('niveau')
        lecon = self.request.query_params.get('lecon')
        type_ex = self.request.query_params.get('type')
        if niveau:
            qs = qs.filter(niveau=niveau)
        if lecon:
            qs = qs.filter(lecon_id=lecon)
        if type_ex:
            qs = qs.filter(type_exercice=type_ex)
        return qs


class ExerciceDetailAPIView(generics.RetrieveAPIView):
    """Détail sans réponse correcte (public)."""
    queryset = Exercice.objects.all()
    serializer_class = ExerciceSerializer
    permission_classes = [permissions.AllowAny]


# ── Soumettre une réponse (IA) ─────────────────────────────────────────────────

class SoumettreReponseAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ser = SoumettreReponseSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=400)

        exercice_id = ser.validated_data['exercice_id']
        user_answer = ser.validated_data['reponse']
        exercice = get_object_or_404(Exercice, pk=exercice_id)

        result = evaluate_answer(user_answer, exercice.reponse_correcte)

        points_earned = 0
        prog, _ = Progression.objects.get_or_create(utilisateur=request.user)

        if result['accepted']:
            prog.exercices_reussis.add(exercice)
            if result['exact']:
                points_earned = 10
            elif result['near_phonetic']:
                points_earned = 8
            else:
                points_earned = 6
            prog.points += points_earned
            prog.save()

        return Response({
            'accepted': result['accepted'],
            'score': result['score'],
            'exact': result['exact'],
            'near_phonetic': result['near_phonetic'],
            'feedback_level': result['feedback_level'],
            'feedback_message': result['feedback_message'],
            'correct_answer': exercice.reponse_correcte,
            'diff_html': result['diff_html'],
            'points_earned': points_earned,
            'total_points': prog.points,
        })


# ── Progression ────────────────────────────────────────────────────────────────

class ProgressionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        prog, _ = Progression.objects.get_or_create(utilisateur=request.user)
        return Response(ProgressionSerializer(prog).data)


class TerminerLeconAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        lecon = get_object_or_404(Lecon, pk=pk)
        prog, _ = Progression.objects.get_or_create(utilisateur=request.user)
        already_done = prog.lecons_terminees.filter(pk=pk).exists()
        if not already_done:
            prog.lecons_terminees.add(lecon)
            prog.points += 10
            prog.save()
        return Response({
            'lecon_id': pk,
            'titre': lecon.titre,
            'already_done': already_done,
            'points': prog.points,
        })


# ── Évaluation rapide (sans auth, sans enregistrement) ────────────────────────

@api_view(['POST'])
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def evaluer_reponse_libre(request):
    """
    POST { "reponse": "...", "attendu": "..." }
    Retourne l'évaluation IA sans toucher à la progression.
    """
    user_answer = request.data.get('reponse', '')
    expected = request.data.get('attendu', '')
    if not expected:
        return Response({'error': 'Champ "attendu" requis.'}, status=400)
    result = evaluate_answer(user_answer, expected)
    return Response(result)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def transliterer(request):
    """
    POST { "texte": "...", "sens": "auto|latin_to_adlam|adlam_to_latin" }
    Convertit entre latin Pulaar et script Adlam.
    """
    texte = request.data.get('texte', '').strip()
    sens = request.data.get('sens', 'auto')
    pulaar_specials = bool(request.data.get('pulaar_specials', True))

    if not texte:
        return Response({'error': 'Champ "texte" requis.'}, status=400)

    if sens == 'latin_to_adlam':
        result = latin_to_adlam(texte)
        return Response({
            'input': texte,
            'input_script': 'latin',
            'output_script': 'adlam',
            'result': result,
        })
    elif sens == 'adlam_to_latin':
        result = adlam_to_latin(texte, pulaar_specials=pulaar_specials)
        return Response({
            'input': texte,
            'input_script': 'adlam',
            'output_script': 'latin',
            'result': result,
        })
    else:  # auto
        data = auto_convert(texte, pulaar_specials=pulaar_specials)
        data['input'] = texte
        return Response(data)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def traduire(request):
    """
    POST { "texte": "...", "depuis": "fr|en" }
    Traduit du français/anglais vers le Pulaar (latin + Adlam).
    """
    texte = request.data.get('texte', '').strip()
    depuis = request.data.get('depuis', 'fr')

    if not texte:
        return Response({'error': 'Champ "texte" requis.'}, status=400)
    if depuis not in ('fr', 'en'):
        return Response({'error': '"depuis" doit être "fr" ou "en".'}, status=400)

    result = translate_text(texte, from_lang=depuis)
    return Response(result)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def vocabulaire(request):
    """
    GET /api/v1/vocabulaire/?depuis=fr
    Retourne tout le vocabulaire disponible.
    """
    depuis = request.query_params.get('depuis', 'fr')
    if depuis not in ('fr', 'en'):
        depuis = 'fr'
    return Response({'vocabulaire': get_vocabulary(depuis), 'langue': depuis})


# ── Audio TTS ─────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def audio_lettre(request, pk):
    """
    GET /api/v1/audio/lettre/<pk>/
    Retourne un fichier MP3 pour la lettre demandée.
    - Si un fichier audio existe déjà (lettre.audio), le sert directement.
    - Sinon, génère avec gTTS (fr) et met en cache dans media/audio/lettres/lettre_<pk>.mp3.
    """
    lettre = get_object_or_404(LettrAdlam, pk=pk)

    # 1. Fichier audio uploadé manuellement → priorité maximale
    if lettre.audio:
        audio_path = lettre.audio.path
        if os.path.exists(audio_path):
            return FileResponse(
                open(audio_path, 'rb'),
                content_type='audio/mpeg',
                headers={'Cache-Control': 'public, max-age=86400'},
            )

    # 2. Cache gTTS déjà généré
    cache_dir = os.path.join(settings.MEDIA_ROOT, 'audio', 'lettres')
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f'lettre_{pk}.mp3')

    if not os.path.exists(cache_path):
        # Générer le fichier audio avec gTTS
        try:
            from gtts import gTTS
            # Texte à prononcer : nom pulaar + translittération pour une meilleure prononciation
            texte = lettre.nom
            if lettre.prononciation:
                texte = lettre.prononciation
            # gTTS ne supporte pas 'ff' (Fula) → on utilise 'fr' (phonétique proche)
            tts = gTTS(text=texte, lang='fr', slow=True)
            tts.save(cache_path)
        except Exception as e:
            raise Http404(f"Impossible de générer l'audio : {e}")

    return FileResponse(
        open(cache_path, 'rb'),
        content_type='audio/mpeg',
        headers={'Cache-Control': 'public, max-age=86400'},
    )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def audio_texte(request):
    """
    GET /api/v1/audio/texte/?texte=jam+waali&lang=fr
    Génère un MP3 pour n'importe quel texte Pulaar latin.
    Le texte est mis en cache via son hash SHA1.
    """
    import hashlib
    texte = (request.query_params.get('texte') or '').strip()
    lang  = (request.query_params.get('lang') or 'fr').strip()
    if not texte:
        raise Http404('Paramètre texte manquant.')
    if len(texte) > 300:
        raise Http404('Texte trop long (max 300 caractères).')
    if lang not in ('fr', 'en'):
        lang = 'fr'

    # Clé de cache = hash du texte + langue
    cache_key = hashlib.sha1(f'{lang}:{texte}'.encode()).hexdigest()
    cache_dir  = os.path.join(settings.MEDIA_ROOT, 'audio', 'textes')
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f'{cache_key}.mp3')

    if not os.path.exists(cache_path):
        try:
            from gtts import gTTS
            tts = gTTS(text=texte, lang=lang, slow=True)
            tts.save(cache_path)
        except Exception as e:
            raise Http404(f'Impossible de générer l\'audio : {e}')

    return FileResponse(
        open(cache_path, 'rb'),
        content_type='audio/mpeg',
        headers={'Cache-Control': 'public, max-age=86400'},
    )
