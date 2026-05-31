from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
# from . import views
from notes import views

urlpatterns = [
    # ── Auth ────────────────────────────────
    path("", views.HomeView.as_view(), name="home"), 
    # ── Auth ────────────────────────────────
    path('auth/register/',  views.RegisterView.as_view(),   name='register'),
    path('auth/login/',     views.LoginView.as_view(),      name='login'),
    path('auth/logout/',    views.LogoutView.as_view(),     name='logout'),
    path('auth/refresh/',   TokenRefreshView.as_view(),     name='token_refresh'),
    path('auth/profile/',   views.ProfileView.as_view(),    name='profile'),

    # ── Notes ───────────────────────────────
    path('notes/',              views.NoteListCreateView.as_view(), name='notes-list-create'),
    path('notes/stats/',        views.notes_stats,                  name='notes-stats'),
    path('notes/<int:pk>/',     views.NoteDetailView.as_view(),     name='note-detail'),
    path('notes/<int:pk>/pin/', views.PinNoteView.as_view(),        name='note-pin'),
]