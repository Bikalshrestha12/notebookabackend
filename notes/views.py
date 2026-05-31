from rest_framework import status, generics, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Q
from django.views import View
from django.http import HttpResponse

from .models import Note
from .serializers import (
    NoteSerializer, NoteListSerializer,
    UserRegistrationSerializer, UserSerializer
)


# ─────────────────────────────────────────────
#  AUTH VIEWS
# ─────────────────────────────────────────────
class HomeView(View):
    def get(self, request):
        return HttpResponse("Welcome to SmartNotes API!")

# ─────────────────────────────────────────────
#  AUTH VIEWS
# ─────────────────────────────────────────────

class RegisterView(APIView):
    """POST /api/auth/register/"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "Registration successful.",
                "user": UserSerializer(user).data,
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """POST /api/auth/login/"""
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {"error": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)
        if not user:
            return Response(
                {"error": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "Login successful.",
            "user": UserSerializer(user).data,
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """POST /api/auth/logout/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    """GET/PUT /api/auth/profile/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def put(self, request):
        user = request.user
        email = request.data.get('email')
        if email:
            user.email = email
            user.save()
        return Response(UserSerializer(user).data)


# ─────────────────────────────────────────────
#  NOTES VIEWS
# ─────────────────────────────────────────────

class NoteListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/notes/          → list all notes for current user
    POST /api/notes/          → create a new note
    Supports ?search=, ?category=, ?pinned= query params
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at', 'title']

    def get_queryset(self):
        qs = Note.objects.filter(user=self.request.user)

        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)

        pinned = self.request.query_params.get('pinned')
        if pinned is not None:
            qs = qs.filter(is_pinned=(pinned.lower() == 'true'))

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(content__icontains=search))

        return qs

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return NoteListSerializer
        return NoteSerializer

    def create(self, request, *args, **kwargs):
        serializer = NoteSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            note = serializer.save()
            return Response(NoteSerializer(note, context={'request': request}).data,
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NoteDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/notes/<id>/   → retrieve single note
    PUT    /api/notes/<id>/   → full update
    PATCH  /api/notes/<id>/   → partial update (e.g. toggle pin)
    DELETE /api/notes/<id>/   → delete note
    """
    permission_classes = [IsAuthenticated]
    serializer_class = NoteSerializer

    def get_queryset(self):
        return Note.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "Note deleted successfully."}, status=status.HTTP_200_OK)


class PinNoteView(APIView):
    """PATCH /api/notes/<id>/pin/  → toggle pin status"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            note = Note.objects.get(pk=pk, user=request.user)
        except Note.DoesNotExist:
            return Response({"error": "Note not found."}, status=status.HTTP_404_NOT_FOUND)

        note.is_pinned = not note.is_pinned
        note.save()
        return Response({
            "message": f"Note {'pinned' if note.is_pinned else 'unpinned'}.",
            "is_pinned": note.is_pinned
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notes_stats(request):
    """GET /api/notes/stats/"""
    user = request.user
    notes = Note.objects.filter(user=user)
    stats = {
        "total": notes.count(),
        "pinned": notes.filter(is_pinned=True).count(),
        "by_category": {
            cat: notes.filter(category=cat).count()
            for cat, _ in Note.CATEGORY_CHOICES
        }
    }
    return Response(stats)