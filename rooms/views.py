from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from .models import Room, RoomReservation, RoomRating, TimeSlot
from django.db.utils import IntegrityError

def room_list(request):
    rooms = Room.objects.all()
    return render(request, 'rooms/room_list.html', {'rooms': rooms})

def room_detail(request, pk):
    room = get_object_or_404(Room, pk=pk)
    time_slots = TimeSlot.objects.all()
    user_rating = None
    if request.user.is_authenticated:
        user_rating = RoomRating.objects.filter(room=room, user=request.user).first()
    
    return render(request, 'rooms/room_detail.html', {
        'room': room,
        'time_slots': time_slots,
        'user_rating': user_rating
    })

@login_required
def reserve_room(request, pk):
    if request.method == 'POST':
        room = get_object_or_404(Room, pk=pk)
        date = request.POST.get('date')
        time_slot_id = request.POST.get('time_slot')
        number_of_people = request.POST.get('number_of_people')
        
        if not all([date, time_slot_id, number_of_people]):
            messages.error(request, 'Please fill all required fields')
            return redirect('rooms:room_detail', pk=pk)
        
        try:
            # Convert date string to datetime object
            reservation_date = datetime.strptime(date, '%Y-%m-%d').date()
            today = timezone.now().date()
            current_time = timezone.now().time()
            
            # Check if the date is in the past
            if reservation_date < today:
                messages.error(request, 'Cannot make reservations for past dates')
                return redirect('rooms:room_detail', pk=pk)
            
            # Get the time slot
            time_slot = get_object_or_404(TimeSlot, id=time_slot_id)
            
            # If reservation is for today, check if the time slot hasn't passed
            if reservation_date == today:
                slot_start_time = {
                    'morning': '09:00',
                    'afternoon': '13:00',
                    'evening': '17:00'
                }.get(time_slot.slot)
                
                slot_time = datetime.strptime(slot_start_time, '%H:%M').time()
                if current_time > slot_time:
                    messages.error(request, 'Cannot make reservations for past time slots')
                    return redirect('rooms:room_detail', pk=pk)
            
            # Check if room is already reserved for this time
            if RoomReservation.objects.filter(
                room=room,
                date=reservation_date,
                time_slot=time_slot,
                is_cancelled=False
            ).exists():
                messages.error(request, 'This room is already reserved for the selected time')
                return redirect('rooms:room_detail', pk=pk)
            
            # Check if number of people doesn't exceed room capacity
            if int(number_of_people) > room.capacity:
                messages.error(request, f'Maximum capacity for this room is {room.capacity} people')
                return redirect('rooms:room_detail', pk=pk)
            
            # Create the reservation
            RoomReservation.objects.create(
                user=request.user,
                room=room,
                date=reservation_date,
                time_slot=time_slot,
                number_of_people=number_of_people
            )
            messages.success(request, 'Room reserved successfully')
            return redirect('rooms:my_reservations')
            
        except ValueError:
            messages.error(request, 'Invalid date format')
            return redirect('rooms:room_detail', pk=pk)
        except IntegrityError:
            messages.error(request, 'This room is already reserved for the selected time')
            return redirect('rooms:room_detail', pk=pk)
    
    return redirect('rooms:room_detail', pk=pk)

@login_required
def cancel_reservation(request, pk):
    reservation = get_object_or_404(
        RoomReservation,
        pk=pk,
        user=request.user,
        is_cancelled=False
    )
    reservation.is_cancelled = True
    reservation.save()
    messages.success(request, 'Reservation cancelled successfully')
    return redirect('rooms:my_reservations')

@login_required
def rate_room(request, pk):
    if request.method == 'POST':
        room = get_object_or_404(Room, pk=pk)
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '')
        
        if rating:
            RoomRating.objects.update_or_create(
                user=request.user,
                room=room,
                defaults={'rating': rating, 'comment': comment}
            )
            messages.success(request, 'Your rating has been saved')
        else:
            messages.error(request, 'Please provide a rating')
    return redirect('rooms:room_detail', pk=pk)

@login_required
def my_reservations(request):
    active_reservations = RoomReservation.objects.filter(
        user=request.user,
        date__gte=timezone.now().date(),
        is_cancelled=False
    ).order_by('date', 'time_slot')
    
    return render(request, 'rooms/my_reservations.html', {
        'active_reservations': active_reservations,
    })

@login_required
def room_availability(request, pk=None):
    if pk:
        rooms = Room.objects.filter(pk=pk)
    else:
        rooms = Room.objects.all()
    
    time_slots = TimeSlot.objects.all()
    current_date = timezone.now().date()
    current_time = timezone.now().time()
    
    # Get selected date or use current date
    date = request.GET.get('date', current_date)
    if isinstance(date, str):
        try:
            date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            date = current_date
    
    # Get all reservations for the selected date
    reservations = RoomReservation.objects.filter(
        date=date,
        is_cancelled=False
    ).select_related('room', 'time_slot')
    
    # Create availability matrix
    availability_matrix = {}
    slot_times = {
        'morning': '09:00',
        'afternoon': '13:00',
        'evening': '17:00'
    }
    
    # Calculate which slots are in the past for today
    past_slots = []
    if date == current_date:
        for slot, time_str in slot_times.items():
            slot_time = datetime.strptime(time_str, '%H:%M').time()
            if current_time > slot_time:
                past_slots.append(slot)
    
    for room in rooms:
        availability_matrix[room] = {}
        for time_slot in time_slots:
            # Check if room is reserved
            is_reserved = reservations.filter(
                room=room,
                time_slot=time_slot
            ).exists()
            
            # Room is available only if it's not reserved AND not in the past
            is_past = (date < current_date) or (date == current_date and time_slot.slot in past_slots)
            availability_matrix[room][time_slot] = not (is_reserved or is_past)
    
    return render(request, 'rooms/room_availability.html', {
        'rooms': rooms,
        'time_slots': time_slots,
        'availability_matrix': availability_matrix,
        'selected_date': date,
        'selected_room': rooms.first() if pk else None,
        'today': current_date,
        'past_slots': past_slots,  # Add past slots for template
    })
