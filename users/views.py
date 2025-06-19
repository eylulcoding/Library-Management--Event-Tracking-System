from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from itertools import chain
from operator import attrgetter
from .models import UserProfile, CustomUser, FriendRequest
from books.models import BookBorrowing, BookRating
from rooms.models import RoomReservation, RoomRating

# Create your views here.

@login_required
def profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    today = timezone.now().date()

    # Get statistics
    total_borrows = BookBorrowing.objects.filter(user=request.user).count()
    total_reservations = RoomReservation.objects.filter(user=request.user).count()
    total_ratings = BookRating.objects.filter(user=request.user).count() + RoomRating.objects.filter(user=request.user).count()

    # Get all activities
    book_borrows = BookBorrowing.objects.filter(
        user=request.user
    ).select_related('book')
    
    room_reservations = RoomReservation.objects.filter(
        user=request.user
    ).select_related('room', 'time_slot')
    
    book_ratings = BookRating.objects.filter(
        user=request.user
    ).select_related('book')
    
    room_ratings = RoomRating.objects.filter(
        user=request.user
    ).select_related('room')

    # Convert activities to a common format
    activities = []
    
    # Add borrows and returns
    for borrow in book_borrows:
        activities.append({
            'type': 'borrow',
            'book': borrow.book,
            'created_at': borrow.borrow_date
        })
        if borrow.is_returned:
            activities.append({
                'type': 'return',
                'book': borrow.book,
                'return_date': borrow.return_date
            })
    
    # Add room reservations
    for reservation in room_reservations:
        activities.append({
            'type': 'reserve',
            'room': reservation.room,
            'date': reservation.date,
            'time_slot': reservation.time_slot,
            'created_at': reservation.created_at
        })
    
    # Add book ratings
    for rating in book_ratings:
        activities.append({
            'type': 'rate',
            'book': rating.book,
            'rating': rating.rating,
            'comment': rating.comment,
            'created_at': rating.created_at
        })
    
    # Add room ratings
    for rating in room_ratings:
        activities.append({
            'type': 'rate',
            'room': rating.room,
            'rating': rating.rating,
            'comment': rating.comment,
            'created_at': rating.created_at
        })
    
    # Sort activities by date, most recent first
    activities.sort(key=lambda x: x.get('created_at') or x.get('return_date') or x.get('date'), reverse=True)
    
    # Limit to last 10 activities
    activities = activities[:10]

    context = {
        'profile': profile,
        'total_borrows': total_borrows,
        'total_reservations': total_reservations,
        'total_ratings': total_ratings,
        'activities': activities,
        'today': today,
    }
    
    return render(request, 'users/profile.html', context)

@login_required
def edit_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
        
        # Update bio
        profile.bio = request.POST.get('bio', '')
        profile.save()
        
        # Update user information
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        
        # Handle password change
        new_password = request.POST.get('new_password')
        if new_password:
            user.set_password(new_password)
        
        user.save()
        messages.success(request, 'Profile updated successfully')
        return redirect('users:profile')
    
    return render(request, 'users/edit_profile.html', {'profile': profile})

@login_required
def toggle_dark_mode(request):
    user = request.user
    user.dark_mode = not user.dark_mode
    user.save()
    return JsonResponse({'dark_mode': user.dark_mode})

@login_required
def dashboard(request):
    today = timezone.now().date()
    
    # Get current borrowed books
    current_borrows = BookBorrowing.objects.filter(
        user=request.user,
        is_returned=False
    ).select_related('book')
    
    # Get past borrowed books
    past_borrows = BookBorrowing.objects.filter(
        user=request.user,
        is_returned=True
    ).select_related('book').order_by('-return_date')[:5]
    
    # Get active room reservations
    active_reservations = RoomReservation.objects.filter(
        user=request.user,
        date__gte=today,
        is_cancelled=False
    ).select_related('room', 'time_slot').order_by('date')
    
    # Get recent ratings
    recent_ratings = BookRating.objects.filter(
        user=request.user
    ).select_related('book').order_by('-created_at')[:5]
    
    # Get user statistics
    total_books_borrowed = BookBorrowing.objects.filter(user=request.user).count()
    total_books_returned = BookBorrowing.objects.filter(user=request.user, is_returned=True).count()
    total_active_borrows = current_borrows.count()
    total_room_reservations = RoomReservation.objects.filter(user=request.user).count()
    total_ratings_given = BookRating.objects.filter(user=request.user).count() + RoomRating.objects.filter(user=request.user).count()
    
    context = {
        'today': today,
        'current_borrows': current_borrows,
        'past_borrows': past_borrows,
        'active_reservations': active_reservations,
        'recent_ratings': recent_ratings,
        'total_books_borrowed': total_books_borrowed,
        'total_books_returned': total_books_returned,
        'total_active_borrows': total_active_borrows,
        'total_room_reservations': total_room_reservations,
        'total_ratings_given': total_ratings_given,
    }
    return render(request, 'users/dashboard.html', context)

@login_required
def friend_list(request):
    profile = request.user.userprofile
    friends = profile.friends.all()
    pending_requests = FriendRequest.objects.filter(
        to_user=profile,
        status='pending'
    ).select_related('from_user__user')
    
    context = {
        'friends': friends,
        'pending_requests': pending_requests,
    }
    return render(request, 'users/friend_list.html', context)

@login_required
def send_friend_request(request, username):
    if request.method == 'POST':
        from_user = request.user.userprofile
        to_user = get_object_or_404(CustomUser, username=username).userprofile
        
        if from_user != to_user:
            friend_request, created = FriendRequest.objects.get_or_create(
                from_user=from_user,
                to_user=to_user,
                defaults={'status': 'pending'}
            )
            
            if created:
                messages.success(request, f'Friend request sent to {username}')
            else:
                messages.info(request, f'Friend request already sent to {username}')
        
        return redirect('users:user_profile', username=username)
    return redirect('users:user_profile', username=username)

@login_required
def accept_friend_request(request, request_id):
    if request.method == 'POST':
        friend_request = get_object_or_404(
            FriendRequest,
            id=request_id,
            to_user=request.user.userprofile,
            status='pending'
        )
        
        friend_request.status = 'accepted'
        friend_request.save()
        
        # Add to friends list (both ways due to symmetrical=True)
        friend_request.from_user.friends.add(friend_request.to_user)
        
        messages.success(request, f'You are now friends with {friend_request.from_user.user.username}')
        return redirect('users:friend_list')
    return redirect('users:friend_list')

@login_required
def reject_friend_request(request, request_id):
    if request.method == 'POST':
        friend_request = get_object_or_404(
            FriendRequest,
            id=request_id,
            to_user=request.user.userprofile,
            status='pending'
        )
        
        friend_request.status = 'rejected'
        friend_request.save()
        
        messages.info(request, f'Friend request from {friend_request.from_user.user.username} rejected')
        return redirect('users:friend_list')
    return redirect('users:friend_list')

@login_required
def remove_friend(request, username):
    if request.method == 'POST':
        user_profile = request.user.userprofile
        friend_profile = get_object_or_404(CustomUser, username=username).userprofile
        
        user_profile.friends.remove(friend_profile)
        messages.info(request, f'{username} has been removed from your friends')
        
        return redirect('users:friend_list')
    return redirect('users:friend_list')

def user_profile(request, username):
    user = get_object_or_404(CustomUser, username=username)
    profile = get_object_or_404(UserProfile, user=user)
    
    # Get friendship status
    is_friend = False
    friend_request_sent = False
    friend_request_received = False
    friend_request = None
    
    if request.user.is_authenticated:
        is_friend = request.user.userprofile.friends.filter(id=profile.id).exists()
        friend_request_sent = FriendRequest.objects.filter(
            from_user=request.user.userprofile,
            to_user=profile,
            status='pending'
        ).exists()
        friend_request = FriendRequest.objects.filter(
            from_user=profile,
            to_user=request.user.userprofile,
            status='pending'
        ).first()
        friend_request_received = friend_request is not None
    
    # Get user's activity
    book_borrows = BookBorrowing.objects.filter(user=user).order_by('-borrow_date')[:5]
    room_reservations = RoomReservation.objects.filter(user=user).order_by('-date', '-time_slot')[:5]
    
    # Get user's statistics
    total_books_borrowed = BookBorrowing.objects.filter(user=user).count()
    total_rooms_reserved = RoomReservation.objects.filter(user=user).count()
    total_friends = profile.friends.count()
    
    context = {
        'profile_user': user,
        'profile': profile,
        'book_borrows': book_borrows,
        'room_reservations': room_reservations,
        'total_books_borrowed': total_books_borrowed,
        'total_rooms_reserved': total_rooms_reserved,
        'total_friends': total_friends,
        'is_friend': is_friend,
        'friend_request_sent': friend_request_sent,
        'friend_request_received': friend_request_received,
        'friend_request': friend_request,
    }
    
    return render(request, 'users/user_profile.html', context)

def search_users(request):
    query = request.GET.get('q', '')
    users = []
    
    if query:
        users = CustomUser.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).select_related('userprofile')[:20]  # Limit to 20 results
    
    context = {
        'query': query,
        'users': users
    }
    return render(request, 'users/search_users.html', context)
