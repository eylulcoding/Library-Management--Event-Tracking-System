from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('toggle-dark-mode/', views.toggle_dark_mode, name='toggle_dark_mode'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('search/', views.search_users, name='search_users'),
    path('send-friend-request/<str:username>/', views.send_friend_request, name='send_friend_request'),
    path('accept-friend-request/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('reject-friend-request/<int:request_id>/', views.reject_friend_request, name='reject_friend_request'),
    path('remove-friend/<str:username>/', views.remove_friend, name='remove_friend'),
    path('friends/', views.friend_list, name='friend_list'),
    path('<str:username>/', views.user_profile, name='user_profile'),
] 