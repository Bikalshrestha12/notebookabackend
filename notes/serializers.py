from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Note


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'password2']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    note_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'note_count', 'date_joined']

    def get_note_count(self, obj):
        return obj.notes.count()


class NoteSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Note
        fields = [
            'id', 'title', 'content', 'category',
            'is_pinned', 'owner', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class NoteListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing notes (no full content)"""
    owner = serializers.ReadOnlyField(source='user.username')
    content_preview = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = [
            'id', 'title', 'content_preview', 'category',
            'is_pinned', 'owner', 'created_at', 'updated_at'
        ]

    def get_content_preview(self, obj):
        return obj.content[:120] + '...' if len(obj.content) > 120 else obj.content