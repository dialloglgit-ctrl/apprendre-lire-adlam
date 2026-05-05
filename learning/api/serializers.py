from rest_framework import serializers
from django.contrib.auth.models import User
from ..models import LettrAdlam, Lecon, Exercice, Progression


class LettrAdlamSerializer(serializers.ModelSerializer):
    class Meta:
        model = LettrAdlam
        fields = ['id', 'nom', 'caractere', 'transliteration', 'prononciation',
                  'exemple_mot', 'exemple_mot_latin', 'ordre']


class ExerciceSerializer(serializers.ModelSerializer):
    type_label = serializers.SerializerMethodField()

    class Meta:
        model = Exercice
        fields = ['id', 'type_exercice', 'type_label', 'question', 'choix',
                  'niveau', 'ordre', 'lecon']

    def get_type_label(self, obj):
        return obj.get_type_exercice_display()


class ExerciceDetailSerializer(ExerciceSerializer):
    """Inclut la réponse correcte (accès authentifié uniquement)."""
    class Meta(ExerciceSerializer.Meta):
        fields = ExerciceSerializer.Meta.fields + ['reponse_correcte']


class LeconSerializer(serializers.ModelSerializer):
    lettres = LettrAdlamSerializer(many=True, read_only=True)
    exercices_count = serializers.SerializerMethodField()
    niveau_label = serializers.SerializerMethodField()

    class Meta:
        model = Lecon
        fields = ['id', 'titre', 'description', 'niveau', 'niveau_label',
                  'contenu', 'ordre', 'lettres', 'exercices_count', 'creee_le']

    def get_exercices_count(self, obj):
        return obj.exercices.count()

    def get_niveau_label(self, obj):
        return obj.get_niveau_display()


class LeconDetailSerializer(LeconSerializer):
    exercices = ExerciceSerializer(many=True, read_only=True)

    class Meta(LeconSerializer.Meta):
        fields = LeconSerializer.Meta.fields + ['exercices']


class ProgressionSerializer(serializers.ModelSerializer):
    lecons_terminees_ids = serializers.SerializerMethodField()
    exercices_reussis_ids = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()

    class Meta:
        model = Progression
        fields = ['id', 'username', 'points', 'derniere_activite',
                  'lecons_terminees_ids', 'exercices_reussis_ids']

    def get_lecons_terminees_ids(self, obj):
        return list(obj.lecons_terminees.values_list('id', flat=True))

    def get_exercices_reussis_ids(self, obj):
        return list(obj.exercices_reussis.values_list('id', flat=True))

    def get_username(self, obj):
        return obj.utilisateur.username


class SoumettreReponseSerializer(serializers.Serializer):
    exercice_id = serializers.IntegerField()
    reponse = serializers.CharField(max_length=500)


class EvaluationResultSerializer(serializers.Serializer):
    accepted = serializers.BooleanField()
    score = serializers.FloatField()
    exact = serializers.BooleanField()
    near_phonetic = serializers.BooleanField()
    feedback_level = serializers.CharField()
    feedback_message = serializers.CharField()
    correct_answer = serializers.CharField()
    diff_html = serializers.CharField()
    points_earned = serializers.IntegerField()
    total_points = serializers.IntegerField()
