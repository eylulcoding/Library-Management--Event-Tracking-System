from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from .models import Book, Category, BookBorrowing, BookRating, ReadingList, ReadingListItem, SavedReadingList, ReadingListLike
from unidecode import unidecode

def home(request):
    return render(request, 'books/home.html')

def book_list(request):
    categories = Category.objects.all()
    category_id = request.GET.get('category')
    books = Book.objects.all()
    
    if category_id:
        books = books.filter(category_id=category_id)
    
    return render(request, 'books/book_list.html', {
        'books': books,
        'categories': categories,
        'selected_category': int(category_id) if category_id else None
    })

def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    user_rating = None
    if request.user.is_authenticated:
        user_rating = BookRating.objects.filter(book=book, user=request.user).first()
    return render(request, 'books/book_detail.html', {
        'book': book,
        'user_rating': user_rating
    })

@login_required
def borrow_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if book.available_copies > 0:
        # Check if user already has an active borrowing for this book
        existing_borrow = BookBorrowing.objects.filter(
            user=request.user,
            book=book,
            is_returned=False
        ).first()
        
        if existing_borrow:
            if existing_borrow.is_overdue:
                messages.error(
                    request, 
                    f'You already have this book and it is overdue by {existing_borrow.days_overdue} days. '
                    'Please return it first.'
                )
            else:
                messages.error(
                    request, 
                    f'You already have this book. It is due in {existing_borrow.days_remaining} days.'
                )
            return redirect('books:book_detail', pk=pk)
        
        # Create new borrowing
        borrowing = BookBorrowing.objects.create(
            user=request.user,
            book=book
        )
        book.available_copies -= 1
        book.save()
        
        messages.success(
            request, 
            f'You have successfully borrowed {book.title}. '
            f'Please return it by {borrowing.due_date.strftime("%B %d, %Y")}.'
        )
    else:
        messages.error(request, 'This book is not available for borrowing')
    return redirect('books:book_detail', pk=pk)

@login_required
def return_book(request, pk):
    borrowing = get_object_or_404(
        BookBorrowing,
        book_id=pk,
        user=request.user,
        is_returned=False
    )
    borrowing.is_returned = True
    borrowing.return_date = timezone.now()
    borrowing.save()
    
    book = borrowing.book
    book.available_copies += 1
    book.save()
    
    if borrowing.is_overdue:
        messages.warning(
            request, 
            f'Book returned {borrowing.days_overdue} days late. '
            'Please return books on time in the future.'
        )
    else:
        messages.success(
            request, 
            f'You have successfully returned {book.title}. Thank you for returning it on time!'
        )
    return redirect('books:book_detail', pk=pk)

@login_required
def rate_book(request, pk):
    if request.method == 'POST':
        book = get_object_or_404(Book, pk=pk)
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '')
        
        if rating:
            BookRating.objects.update_or_create(
                user=request.user,
                book=book,
                defaults={'rating': rating, 'comment': comment}
            )
            messages.success(request, 'Your rating has been saved')
        else:
            messages.error(request, 'Please provide a rating')
    return redirect('books:book_detail', pk=pk)

def category_books(request, pk):
    category = get_object_or_404(Category, pk=pk)
    books = Book.objects.filter(category=category)
    return render(request, 'books/category_books.html', {
        'category': category,
        'books': books
    })

def search_books(request):
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')
    
    print(f"Original search query: '{query}'")
    print(f"Search query encoded: {query.encode('utf-8')}")
    
    books = Book.objects.all()
    print(f"Total books before filter: {books.count()}")
    
    if query:
        # Get all books and filter in Python to debug the matching
        all_books = list(books)
        matched_books = []
        
        for book in all_books:
            print(f"\nChecking book: {book.title}")
            print(f"Book title encoded: {book.title.encode('utf-8')}")
            
            # Convert both to lowercase for case-insensitive comparison
            book_title_lower = book.title.lower()
            query_lower = query.lower()
            
            print(f"Lowercase comparison - Book: '{book_title_lower}', Query: '{query_lower}'")
            
            # Check if query is in book title
            if query_lower in book_title_lower:
                print(f"Match found! Query '{query_lower}' is in '{book_title_lower}'")
                matched_books.append(book)
                continue
            
            # Try with ASCII conversion
            ascii_title = unidecode(book_title_lower)
            ascii_query = unidecode(query_lower)
            
            print(f"ASCII comparison - Book: '{ascii_title}', Query: '{ascii_query}'")
            
            if ascii_query in ascii_title:
                print(f"ASCII match found! Query '{ascii_query}' is in '{ascii_title}'")
                matched_books.append(book)
        
        # Convert matched books back to queryset
        if matched_books:
            books = Book.objects.filter(id__in=[book.id for book in matched_books])
        else:
            books = Book.objects.none()
        
        print(f"\nTotal books after filter: {books.count()}")
        print(f"Found books: {[book.title for book in books]}")
    
    if category_id:
        books = books.filter(category_id=category_id)
    
    categories = Category.objects.all()
    
    return render(request, 'books/search_results.html', {
        'books': books,
        'query': query,
        'categories': categories,
        'selected_category': int(category_id) if category_id else None
    })

@login_required
def reading_list_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        is_public = request.POST.get('is_public') == 'on'  # Convert checkbox value to boolean
        
        if name:
            reading_list = ReadingList.objects.create(
                user=request.user,
                name=name,
                description=description,
                is_public=is_public
            )
            messages.success(request, 'Reading list created successfully!')
            return redirect('books:reading_list_detail', pk=reading_list.pk)
        else:
            messages.error(request, 'Please provide a name for the reading list.')
    
    return render(request, 'books/reading_list_form.html')

@login_required
def reading_list_detail(request, pk):
    reading_list = get_object_or_404(ReadingList, pk=pk)
    if not reading_list.is_public and reading_list.user != request.user:
        messages.error(request, 'This reading list is private.')
        return redirect('books:reading_lists')
    
    return render(request, 'books/reading_list_detail.html', {
        'reading_list': reading_list
    })

@login_required
def reading_lists(request):
    tab = request.GET.get('tab', 'all')
    
    if tab == 'saved' and request.user.is_authenticated:
        saved_lists = SavedReadingList.objects.filter(user=request.user).select_related('reading_list')
        return render(request, 'books/reading_lists.html', {
            'saved_lists': saved_lists,
        })
    elif tab == 'my' and request.user.is_authenticated:
        user_lists = ReadingList.objects.filter(user=request.user).annotate(
            book_count=Count('readinglistitem')
        )
        return render(request, 'books/reading_lists.html', {
            'user_lists': user_lists,
        })
    else:
        public_lists = ReadingList.objects.filter(is_public=True).annotate(
            book_count=Count('readinglistitem')
        )
        return render(request, 'books/reading_lists.html', {
            'public_lists': public_lists,
        })

@login_required
def add_to_reading_list(request, book_id):
    if request.method == 'POST':
        book = get_object_or_404(Book, pk=book_id)
        list_id = request.POST.get('reading_list')
        
        if list_id:
            # Get reading list and verify ownership
            reading_list = get_object_or_404(ReadingList, pk=list_id)
            if reading_list.user != request.user:
                messages.error(request, 'You can only add books to your own reading lists.')
                return redirect('books:book_detail', pk=book_id)
            
            ReadingListItem.objects.get_or_create(
                reading_list=reading_list,
                book=book
            )
            messages.success(request, f'Added "{book.title}" to "{reading_list.name}"')
        else:
            messages.error(request, 'Please select a reading list.')
        
        return redirect('books:book_detail', pk=book_id)
    
    book = get_object_or_404(Book, pk=book_id)
    reading_lists = ReadingList.objects.filter(user=request.user)
    
    return render(request, 'books/add_to_reading_list.html', {
        'book': book,
        'reading_lists': reading_lists
    })

@login_required
def toggle_reading_list_like(request, pk):
    if request.method == 'POST':
        reading_list = get_object_or_404(ReadingList, pk=pk)
        like, created = ReadingListLike.objects.get_or_create(
            user=request.user,
            reading_list=reading_list
        )
        
        if not created:
            like.delete()
            is_liked = False
        else:
            is_liked = True
        
        return JsonResponse({
            'is_liked': is_liked,
            'like_count': reading_list.like_count
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def toggle_reading_list_save(request, pk):
    if request.method == 'POST':
        reading_list = get_object_or_404(ReadingList, pk=pk)
        saved, created = SavedReadingList.objects.get_or_create(
            user=request.user,
            reading_list=reading_list
        )
        
        if not created:
            saved.delete()
            is_saved = False
        else:
            is_saved = True
        
        return JsonResponse({
            'is_saved': is_saved,
            'save_count': reading_list.save_count
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def saved_reading_lists(request):
    saved_lists = SavedReadingList.objects.filter(user=request.user).select_related('reading_list')
    
    return render(request, 'books/saved_reading_lists.html', {
        'saved_lists': saved_lists
    })

@login_required
def remove_from_list(request, list_id, book_id):
    reading_list = get_object_or_404(ReadingList, pk=list_id, user=request.user)
    ReadingListItem.objects.filter(reading_list=reading_list, book_id=book_id).delete()
    messages.success(request, 'Book removed from the list successfully.')
    return redirect('books:reading_list_detail', pk=list_id)
