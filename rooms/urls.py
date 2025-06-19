from django.urls import path
from . import views

app_name = 'rooms'

urlpatterns = [
    path('', views.room_list, name='room_list'),
    path('<int:pk>/', views.room_detail, name='room_detail'),
    path('reserve/<int:pk>/', views.reserve_room, name='reserve_room'),
    path('cancel/<int:pk>/', views.cancel_reservation, name='cancel_reservation'),
    path('rate/<int:pk>/', views.rate_room, name='rate_room'),
    path('my-reservations/', views.my_reservations, name='my_reservations'),
    path('availability/', views.room_availability, name='room_availability'),
    path('availability/<int:pk>/', views.room_availability, name='room_availability'),
] 