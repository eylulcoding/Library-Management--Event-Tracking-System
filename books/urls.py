from django.urls import path
from . import views

app_name = 'books'

urlpatterns = [
    path('', views.home, name='home'),
    path('books/', views.book_list, name='book_list'),
    path('books/<int:pk>/', views.book_detail, name='book_detail'),
    path('books/<int:pk>/borrow/', views.borrow_book, name='borrow_book'),
    path('books/<int:pk>/return/', views.return_book, name='return_book'),
    path('books/<int:pk>/rate/', views.rate_book, name='rate_book'),
    path('categories/<int:pk>/', views.category_books, name='category_books'),
    path('search/', views.search_books, name='search_books'),
    path('reading-lists/', views.reading_lists, name='reading_lists'),
    path('reading-lists/create/', views.reading_list_create, name='reading_list_create'),
    path('reading-lists/<int:pk>/', views.reading_list_detail, name='reading_list_detail'),
    path('reading-lists/<int:pk>/like/', views.toggle_reading_list_like, name='toggle_reading_list_like'),
    path('reading-lists/<int:pk>/save/', views.toggle_reading_list_save, name='toggle_reading_list_save'),
    path('books/<int:book_id>/add-to-list/', views.add_to_reading_list, name='add_to_reading_list'),
    path('reading-lists/<int:list_id>/remove/<int:book_id>/', views.remove_from_list, name='remove_from_list'),
] 