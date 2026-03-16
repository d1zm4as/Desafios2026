from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core import views


urlpatterns = [
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('movies/', views.MovieListView.as_view(), name='movie-list'),
    path('movies/<int:movie_id>/sessions/', views.SessionListView.as_view(), name='session-list'),
    path('sessions/<int:session_id>/seats/', views.SessionSeatMapView.as_view(), name='session-seats'),
    path('sessions/<int:session_id>/reserve/', views.ReserveSeatView.as_view(), name='session-reserve'),
    path('sessions/<int:session_id>/checkout/', views.CheckoutView.as_view(), name='session-checkout'),
    path('me/tickets/', views.MyTicketsView.as_view(), name='my-tickets'),
]
