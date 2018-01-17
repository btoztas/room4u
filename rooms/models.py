from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Room(models.Model):
    id = models.CharField(primary_key=True, editable=False, max_length=15)
    parent_id = models.CharField(max_length=15)
    name = models.CharField(max_length=15)
    created_at = models.DateTimeField(editable=False)
    modified_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.modified_at:
            self.created_at = timezone.now()
        self.modified_at = timezone.now()
        return super(Room, self).save(*args, **kwargs)


class Message(models.Model):
    title = models.CharField(max_length=50)
    text = models.CharField(max_length=500)
    #room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='room')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sender')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='receiver')
    created_at = models.DateTimeField(editable=False)
    modified_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.modified_at:
            self.created_at = timezone.now()
        self.modified_at = timezone.now()
        return super(Message, self).save(*args, **kwargs)


class Visit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    start = models.DateTimeField()
    end = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(editable=False)
    modified_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.modified_at:
            self.created_at = timezone.now()
        self.modified_at = timezone.now()
        return super(Visit, self).save(*args, **kwargs)


class NewMessage(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='message')