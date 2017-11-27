from django.contrib import admin

from rooms.models import Room, Profile, Message, Visit

admin.site.register(Room)
admin.site.register(Profile)
admin.site.register(Message)
admin.site.register(Visit)
