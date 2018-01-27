from django.contrib import admin

from rooms.models import Room, Message, Visit

admin.site.register(Room)
admin.site.register(Message)
admin.site.register(Visit)
