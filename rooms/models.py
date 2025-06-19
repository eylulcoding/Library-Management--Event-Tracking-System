from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model

User = get_user_model()

class Room(models.Model):
    name = models.CharField(max_length=100)
    floor = models.PositiveIntegerField()
    capacity = models.PositiveIntegerField()
    description = models.TextField()
    image = models.ImageField(upload_to='room_images/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} (Floor {self.floor})"

class TimeSlot(models.Model):
    SLOT_CHOICES = [
        ('morning', '9:00 - 12:00'),
        ('afternoon', '13:00 - 16:00'),
        ('evening', '17:00 - 20:00'),
    ]
    
    slot = models.CharField(max_length=20, choices=SLOT_CHOICES)
    
    def __str__(self):
        return self.get_slot_display()

class RoomReservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    date = models.DateField()
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    number_of_people = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_cancelled = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.room.name} - {self.date} - {self.time_slot}"

class RoomRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'room')
    
    def __str__(self):
        return f"{self.user.username} - {self.room.name} - {self.rating}★"
