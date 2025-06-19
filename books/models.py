from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    description = models.TextField()
    cover_image = models.ImageField(upload_to='book_covers/')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @property
    def is_available(self):
        return self.available_copies > 0

class BookBorrowing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    borrow_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    return_date = models.DateTimeField(null=True, blank=True)
    is_returned = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.book.title}"

    def save(self, *args, **kwargs):
        if not self.pk and not self.due_date:  # Only set due_date when creating new instance
            self.due_date = timezone.now() + timedelta(days=30)
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        if self.is_returned:
            return False
        return timezone.now() > self.due_date

    @property
    def days_remaining(self):
        if self.is_returned:
            return 0
        delta = self.due_date - timezone.now()
        return max(0, delta.days)

    @property
    def days_overdue(self):
        if not self.is_overdue:
            return 0
        delta = timezone.now() - self.due_date
        return delta.days

class BookRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'book')

    def __str__(self):
        return f"{self.user.username} - {self.book.title} - {self.rating}★"

class ReadingList(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} by {self.user.username}"

    @property
    def like_count(self):
        return self.readinglistlike_set.count()

    @property
    def save_count(self):
        return self.savedreadinglist_set.count()

    @property
    def is_liked_by_user(self):
        if not hasattr(self, '_is_liked_by_user'):
            # Get the user from the current request using middleware
            from django.core.cache import cache
            request = cache.get('_current_request')
            if request and request.user.is_authenticated:
                self._is_liked_by_user = self.readinglistlike_set.filter(user=request.user).exists()
            else:
                self._is_liked_by_user = False
        return self._is_liked_by_user

    @property
    def is_saved_by_user(self):
        if not hasattr(self, '_is_saved_by_user'):
            # Get the user from the current request using middleware
            from django.core.cache import cache
            request = cache.get('_current_request')
            if request and request.user.is_authenticated:
                self._is_saved_by_user = self.savedreadinglist_set.filter(user=request.user).exists()
            else:
                self._is_saved_by_user = False
        return self._is_saved_by_user

class ReadingListItem(models.Model):
    reading_list = models.ForeignKey(ReadingList, on_delete=models.CASCADE)
    book = models.ForeignKey('Book', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['added_at']
        unique_together = ['reading_list', 'book']

    def __str__(self):
        return f"{self.book.title} in {self.reading_list.name}"

    def clean(self):
        if self.reading_list.user != getattr(self, '_current_user', None):
            raise ValidationError('You can only add books to your own reading lists.')

    def save(self, *args, **kwargs):
        if not hasattr(self, '_current_user'):
            from django.core.cache import cache
            request = cache.get('_current_request')
            if request:
                self._current_user = request.user
        self.clean()
        super().save(*args, **kwargs)

class SavedReadingList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reading_list = models.ForeignKey(ReadingList, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'reading_list']
        ordering = ['-saved_at']

    def __str__(self):
        return f"{self.user.username} saved {self.reading_list.name}"

class ReadingListLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reading_list = models.ForeignKey(ReadingList, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'reading_list']

    def __str__(self):
        return f"{self.user.username} liked {self.reading_list.name}"
