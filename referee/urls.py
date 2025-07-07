from django.contrib import admin
from django.urls import path
from referee.views import MatchSetupView, AddPlayersView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', MatchSetupView.as_view(), name='match_setup'),
    path('match/<int:match_id>/players/', AddPlayersView.as_view(), name='add_players'),
]