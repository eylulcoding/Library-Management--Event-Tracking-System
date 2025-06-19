from django.contrib import admin
from .models import Book, Category, BookBorrowing, BookRating

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'available_copies', 'total_copies')
    list_filter = ('category',)
    search_fields = ('title', 'author')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 20

@admin.register(BookBorrowing)
class BookBorrowingAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'borrow_date', 'return_date', 'is_returned')
    list_filter = ('is_returned', 'borrow_date')
    search_fields = ('user__username', 'book__title')
    date_hierarchy = 'borrow_date'

@admin.register(BookRating)
class BookRatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'book__title', 'comment')
