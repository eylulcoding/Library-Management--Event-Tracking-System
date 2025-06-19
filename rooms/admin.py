from django.contrib import admin
from .models import Room, TimeSlot, RoomReservation, RoomRating

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'floor', 'capacity')
    list_filter = ('floor',)
    search_fields = ('name', 'description')

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('slot', 'get_slot_display')

@admin.register(RoomReservation)
class RoomReservationAdmin(admin.ModelAdmin):
    list_display = ('user', 'room', 'date', 'time_slot', 'number_of_people', 'is_cancelled')
    list_filter = ('is_cancelled', 'date', 'time_slot')
    search_fields = ('user__username', 'room__name')
    date_hierarchy = 'date'

@admin.register(RoomRating)
class RoomRatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'room', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'room__name', 'comment')
