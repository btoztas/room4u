import json
import os
import string

import requests
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import View
from django.conf import settings
import fenixedu
from room4u.settings import SITE_URL
from rooms.management.commands import getrooms
from .forms import MessageForm, FilterForm, SearchRoomForm, AdminSearchForm
from .models import Message, Room, Visit, NewMessage
from django.utils import timezone
from django.core.serializers import serialize
from django.contrib.auth.models import User
import json

# import datetime

if 'ON_AWS' in os.environ:

    config = fenixedu.FenixEduConfiguration \
        ('1132965128044595', SITE_URL + '/room4u/auth',
         '3BjrjgA8DEYSQ545ozu/usJ4QjeTLTsWFOrDceUmNHprUVYGDnOHhfml2wI+W9CUwviQ5vP5OvKoFTbVtkdRgg==',
         'https://fenix.tecnico.ulisboa.pt/')

else:

    config = fenixedu.FenixEduConfiguration \
        ('1977390058176548', SITE_URL + '/room4u/auth',
         'ivhTjk4+geVbJT1bh+KtZ0zrcBo0RuMw/SFsQIxShsRJX7VSntrKVw3U82Yz2WQb7075DbsnQX6+/uUO+LG7Kw==',
         'https://fenix.tecnico.ulisboa.pt/')

client = fenixedu.FenixEduClient(config)


class AuthView(View):
    def get(self, request, *args, **kwargs):

        code = request.GET.get('code', None)
        if code is not None and not request.user.is_authenticated():
            user = authenticate(request=request, client=client, code=code)
            if user is not None:
                login(request, user)

        return redirect(settings.SITE_URL + '/room4u/')


class IndexView(View):
    login_template = 'login.html'
    dashboard_template = 'main.html'

    def get_context(self, request):

        context = {
            'username': request.user.username,
            'is_admin': request.user.is_staff
        }

        if not request.user.is_staff:

            current_check_in = Visit.objects.filter(user=request.user, end__isnull=True).first()

            if not current_check_in:
                context['checked_in'] = 0
            else:
                context['checked_in'] = 1
                context['checked_in_room'] = current_check_in.room.name
                context['user_id'] = request.user.id
                context['checked_in_room_id'] = current_check_in.room.id
                context['checked_in_time'] = current_check_in.start
                context['users_in_room'] = Visit.objects.filter(room=current_check_in.room, end__isnull=True).order_by(
                    '-start').all()

        return context

    def get(self, request, *args, **kwargs):

        if not request.user.is_authenticated():
            context = {'auth_url': client.get_authentication_url()}
            return render(request, self.login_template, context)
        else:
            context = self.get_context(request)

            return render(request, self.dashboard_template, context)


class NewMessageView(View):
    new_message_template = 'new_messages.html'

    def get(self, request, *args, **kwargs):
        if str(request.user) != "administrator":
            return redirect('/room4u')
        context = {
            'username': request.user.username,
            'is_admin': request.user.is_staff,
        }
        return render(request, self.new_message_template, context)


class IncomingMessageView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return redirect('/room4u')
        # check if any
        if not NewMessage.objects.filter(message__receiver=request.user.id):
            return HttpResponse("nothing")
        # filter
        message = NewMessage.objects.filter(message__receiver=request.user.id).first()
        NewMessage.objects.filter(id=message.id).delete()
        return HttpResponse(serialize('json', [message.message, ]))


class NewMessageHandlerView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return redirect('/room4u')
        if request.method == 'POST':
            # create a form instance and populate it with data from the request:
            form = MessageForm(request.POST)
            # check whether it's valid:
            if form.is_valid():
                # process the data in form.cleaned_data as required
                # ...
                print(request.POST.get("destination", ""))
                if request.POST.get("destflag", "") == "room":
                    destination = Room.objects.filter(id=request.POST.get("destination", ""))
                    users = Visit.objects.filter(room=destination, end__isnull=True)
                    nusers = len(users)
                    message = request.POST.get("message", "")
                    for user in users:
                        instance = Message(title=str(request.POST.get("subject", "")),
                                           text=str(request.POST.get("message", "")), sender=request.user,
                                           receiver=user.user, room=user.room)
                        instance.save()
                        instance2 = NewMessage(message=instance)
                        instance2.save()
                else:
                    user = request.POST.get("destination", "")
                    print(user)
                    users = Visit.objects.filter(user__username=user, end__isnull=True).first()
                    instance = Message(title=str(request.POST.get("subject", "")),
                                       text=str(request.POST.get("message", "")), sender=request.user,
                                       receiver=users.user, room=users.room)
                    instance.save()
                    instance2 = NewMessage(message=instance)
                    instance2.save()
                return HttpResponse(status=200)
            else:
                return HttpResponse("sm")

    def get(self, request, *args, **kwargs):
        return redirect('/room4u')


class MessageView(View):
    message_template = 'messages.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return redirect('/room4u')
        if request.user.is_staff:
            messages = Message.objects.all()
        else:
            messages = Message.objects.filter(receiver=request.user)
        context = {
            'messages': messages,
            'username': request.user.username,
            'is_admin': request.user.is_staff,
            'filter': "",
            'text': "",
            'date': "",
            'sdate': ""
        }
        return render(request, self.message_template, context)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return redirect('/room4u')
        if request.method == 'POST':
            # create a form instance and populate it with data from the request:
            form = FilterForm(request.POST)
            datee = (request.POST.get("sdate", "")).split("-")
            # check whether it's valid:
            if form.is_valid():
                # process the data in form.cleaned_data as required
                # ...
                filter = request.POST.get("filter", "")
                text = request.POST.get("text", "")
                date = request.POST.get("date", "")
                sdate = request.POST.get("sdate", "")
                if str(filter) == "Search":
                    if request.user.is_staff:
                        messages = Message.objects.filter(text__contains=str(text))
                        messages = messages | Message.objects.filter(title__contains=str(text))
                    else:
                        messages = Message.objects.filter(text__contains=str(text), receiver=request.user)
                        messages = messages | Message.objects.filter(title__contains=str(text))
                elif str(filter) == "Room":
                    if request.user.is_staff:
                        messages = Message.objects.filter(room__name__contains=str(text))
                    else:
                        messages = Message.objects.filter(room__name__contains=str(text), receiver=request.user)
                else:
                    if str(date) == "year":
                        startdate = timezone.now()
                        enddate = timezone.now() - timezone.timedelta(days=365)
                        if request.user.is_staff:
                            messages = Message.objects.filter(created_at__range=[enddate, startdate])
                        else:
                            messages = Message.objects.filter(created_at__range=[enddate, startdate],
                                                              receiver=request.user)
                    if str(date) == "6month":
                        startdate = timezone.now()
                        enddate = timezone.now() - timezone.timedelta(days=180)
                        if request.user.is_staff:
                            messages = Message.objects.filter(created_at__range=[enddate, startdate])
                        else:
                            messages = Message.objects.filter(created_at__range=[enddate, startdate],
                                                              receiver=request.user)
                    if str(date) == "month":
                        startdate = timezone.now()
                        enddate = timezone.now() - timezone.timedelta(days=30)
                        if request.user.is_staff:
                            messages = Message.objects.filter(created_at__range=[enddate, startdate])
                        else:
                            messages = Message.objects.filter(created_at__range=[enddate, startdate],
                                                              receiver=request.user)
                    if str(date) == "week":
                        startdate = timezone.now()
                        enddate = timezone.now() - timezone.timedelta(days=7)
                        if request.user.is_staff:
                            messages = Message.objects.filter(created_at__range=[enddate, startdate])
                        else:
                            messages = Message.objects.filter(created_at__range=[enddate, startdate],
                                                              receiver=request.user)
                    if str(date) == "today":
                        startdate = timezone.now()
                        enddate = timezone.now() - timezone.timedelta(hours=13)
                        print (enddate)
                        if request.user.is_staff:
                            messages = Message.objects.filter(created_at__range=[enddate, startdate])
                        else:
                            messages = Message.objects.filter(created_at__range=[enddate, startdate],
                                                              receiver=request.user)
                    if str(date) == "specific_date":
                        if request.user.is_staff:
                            messages = Message.objects.filter(created_at__year=datee[0], created_at__month=datee[1],
                                                              created_at__day=datee[2])
                        else:
                            messages = Message.objects.filter(created_at__year=datee[0], created_at__month=datee[1],
                                                              created_at__day=datee[2], receiver=request.user)
                context = {
                    'username': request.user.username,
                    'is_admin': request.user.is_staff,
                    'filter': filter,
                    'text': text,
                    'date': date,
                    'sdate': sdate,
                    'messages': messages
                }
                return render(request, self.message_template, context)
            else:
                return redirect('/room4u/messages')


class ApiView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("done")


class RoomsApiView(View):
    def get(self, request, **kwargs):
        if 'room_id' in kwargs:
            if not Room.objects.filter(id=kwargs['room_id']):
                response = dict()
                response['error'] = 'room not found'
                return HttpResponse(
                    json.dumps(response),
                    content_type='application/json',
                    status=404
                )
            else:
                if 'search' in kwargs:
                    if kwargs['search'] == "visits":
                        visits = Visit.objects.filter(room=kwargs['room_id'])
                        response = serialize("json", visits)
                        return HttpResponse(response, content_type='application/json')
                    elif kwargs['search'] == "messages":
                        messages = Message.objects.filter(room=kwargs['room_id'])
                        response = serialize("json", messages)
                        return HttpResponse(response, content_type='application/json')
                    else:
                        response = dict()
                        response['error'] = 'bad request, last parameter must be \'visits\' or \'messages\''
                        return HttpResponse(
                            json.dumps(response),
                            content_type='application/json',
                            status=400
                        )
                else:
                    rooms = Room.objects.filter(id=kwargs['room_id'])
                    response = serialize("json", rooms)
                    return HttpResponse(response, content_type='application/json')
        else:
            if request.method == 'GET':
                rooms = Room.objects.all()
                response = serialize("json", rooms)
                return HttpResponse(response, content_type='application/json')


class MessagesApiView(View):
    def get(self, request, **kwargs):
        if 'message_id' in kwargs:
            if not Message.objects.filter(id=kwargs['message_id']):
                response = dict()
                response['error'] = 'message not found'
                return HttpResponse(
                    json.dumps(response),
                    content_type='application/json',
                    status=404
                )
            else:
                messages = Message.objects.filter(id=kwargs['message_id'])
                response = serialize("json", messages)
                return HttpResponse(response, content_type='application/json')
        else:
            if request.method == 'GET':
                messages = Message.objects.all()
                response = serialize("json", messages)
                return HttpResponse(response, content_type='application/json')

    def post(self, request):
        body = json.loads(request.body)
        if 'subject' in body and 'message' in body and 'sender_id' in body:
            if body['subject'] == "" or body['message'] == "":
                response = dict()
                response['error'] = 'bad request, subject or body empty'
                return HttpResponse(
                    json.dumps(response),
                    content_type='application/json',
                    status=400
                )
            else:
                if 'room' in body:
                    destination = Room.objects.filter(id=body['room'])
                    if not destination:
                        response = dict()
                        response['error'] = 'room not found'
                        return HttpResponse(
                            json.dumps(response),
                            content_type='application/json',
                            status=404
                        )
                    else:
                        if body['sender_id'].isdigit():
                            if not User.objects.filter(id=body['sender_id']):
                                response = dict()
                                response['error'] = 'sender not found'
                                return HttpResponse(
                                    json.dumps(response),
                                    content_type='application/json',
                                    status=404
                                )
                            else:
                                users = Visit.objects.filter(room=destination, end__isnull=True)
                                for user in users:
                                    instance = Message(title=str(body['subject']),
                                                       text=str(body['message']),
                                                       sender=User.objects.filter(id=body['sender_id']).first(),
                                                       receiver=user.user, room=user.room)
                                    instance.save()
                                    instance2 = NewMessage(message=instance)
                                    instance2.save()
                                    response = serialize("json", [Message(title=str(body['subject']),
                                                                          text=str(body['message']),
                                                                          sender=User.objects.filter(
                                                                              id=body['sender_id']).first(),
                                                                          receiver=user.user, room=user.room)])
                                    return HttpResponse(response, content_type='application/json')
                        else:
                            response = dict()
                            response['error'] = 'sender not found'
                            return HttpResponse(
                                json.dumps(response),
                                content_type='application/json',
                                status=404
                            )
                elif 'user' in body:
                    user = body['user']
                    users = Visit.objects.filter(user__username=user, end__isnull=True).first()
                    if not users:
                        response = dict()
                        response['error'] = 'user not found'
                        return HttpResponse(
                            json.dumps(response),
                            content_type='application/json',
                            status=404
                        )
                    else:
                        if body['sender_id'].isdigit():
                            if not User.objects.filter(id=body['sender_id']).first():
                                response = dict()
                                response['error'] = 'sender not found'
                                return HttpResponse(
                                    json.dumps(response),
                                    content_type='application/json',
                                    status=404
                                )
                            else:
                                instance = Message(title=str(body['subject']),
                                                   text=str(body['message']),
                                                   sender=User.objects.filter(id=body['sender_id']).first(),
                                                   receiver=users.user, room=users.room)
                                instance.save()
                                instance2 = NewMessage(message=instance)
                                instance2.save()
                                response = serialize("json", [instance])
                                return HttpResponse(response, content_type='application/json')
                        else:
                            response = dict()
                            response['error'] = 'sender not found'
                            return HttpResponse(
                                json.dumps(response),
                                content_type='application/json',
                                status=404
                            )
                else:
                    response = dict()
                    response['error'] = 'bad request, room or user missing'
                    return HttpResponse(
                        json.dumps(response),
                        content_type='application/json',
                        status=400
                    )
        else:
            response = dict()
            response['error'] = 'bad request, text, title or sender_id missing'
            return HttpResponse(
                json.dumps(response),
                content_type='application/json',
                status=400
            )


@method_decorator(login_required(login_url='/room4u/'), name='dispatch')
class CheckInView(View):
    template = 'check-in.html'

    def get_context(self, request):

        context = {
            'username': request.user.username,
            'is_admin': request.user.is_staff,
            'user_id': request.user.id
        }

        if not request.user.is_staff:

            current_check_in = Visit.objects.filter(user=request.user, end__isnull=True).first()

            if not current_check_in:
                context['checked_in'] = 0
            else:
                context['checked_in'] = 1
                context['checked_in_room'] = current_check_in.room.name
                context['user_id'] = request.user.id
                context['checked_in_room_id'] = current_check_in.room.id
                context['checked_in_time'] = current_check_in.start
                context['users_in_room'] = Visit.objects.filter(room=current_check_in.room, end__isnull=True).order_by(
                    '-start').all()

        return context

    def get(self, request, *args, **kwargs):

        context = self.get_context(request)

        if request.user.is_staff:
            context['rooms'] = Visit.objects.filter(end__isnull=True).values('room').annotate(total=Count('room_id')). \
                order_by('-total')
            context['total'] = 0
            for room in context['rooms']:
                room['users'] = Visit.objects.filter(end__isnull=True, room=room['room']).order_by('-start').all()
                room['name'] = room['users'][0].room.name
                room['hierarchy'] = room['users'][0].room.hierarchy
                context['total'] += room['total']

        return render(request, self.template, context)

    def post(self, request, *args, **kwargs):

        context = self.get_context(request)

        if request.user.is_staff:

            form = AdminSearchForm(request.POST)

            if form.is_valid():
                # Get search keywords
                search_keyword = request.POST['search_keyword']
                search_type = request.POST['search_type']

                context['total'] = 0

                if search_type == 'room':

                    context['rooms'] = Visit.objects.filter(room__name__contains=search_keyword, end__isnull=True) \
                        .values('room').annotate(total=Count('room_id')).order_by('-total')

                    for room in context['rooms']:
                        room['users'] = Visit.objects \
                            .filter(room__name__contains=search_keyword, end__isnull=True, room=room['room']).order_by(
                            '-start').all()
                        room['name'] = room['users'][0].room.name
                        room['hierarchy'] = room['users'][0].room.hierarchy

                        context['total'] += room['total']

                elif search_type == 'username':
                    context['users'] = Visit.objects.filter(end__isnull=True, user__username__contains=search_keyword) \
                        .exclude(user__is_staff=True).all()
                    context['total'] = len(context['users'])

                elif search_type == 'name':

                    context['users'] = Visit.objects.filter(Q(end__isnull=True),
                                                            Q(user__first_name__contains=search_keyword) |
                                                            Q(user__last_name__contains=search_keyword)).exclude(
                        user__is_staff=True).all()

                    context['total'] = len(context['users'])

                context['search_keyword'] = search_keyword
                context['search_type'] = search_type

        else:
            form = SearchRoomForm(request.POST)
            if form.is_valid():
                # Get search keywords
                keyword = request.POST['keyword']

                # Search for rooms in the db
                context['rooms'] = Room.objects.filter(name__icontains=keyword)

        return render(request, self.template, context)


@method_decorator(login_required(login_url='/room4u/'), name='dispatch')
class NewCheckInView(View):
    def post(self, request, *args, **kwargs):
        # Visit parameters
        user = request.user
        room = Room.objects.get(id=request.POST['room'])
        start = timezone.now()

        # Checking if there is a pending visit
        current_check_in = Visit.objects.filter(user=request.user, end__isnull=True).first()

        if current_check_in:

            if current_check_in.room == room:
                return HttpResponse(status=409)

            current_check_in.end = start
            current_check_in.save()

        # Creating visit
        visit = Visit(user=user, room=room, start=start)
        visit.save()
        return HttpResponse(status=200)


@method_decorator(login_required(login_url='/room4u/'), name='dispatch')
class RoomsReloadView(View):
    base_url = 'https://fenix.tecnico.ulisboa.pt/api/fenix/v1/spaces/'

    def retrieve_space(self, space_parent, space_to_explore, hierarchy):

        # Request space's info
        r = requests.get(self.base_url + space_to_explore)
        space_info = r.json()

        # Create new space object with the info retrieved
        if space_parent == 0:
            new_space = Room(id=space_info['id'], name=space_info['name'], hierarchy=hierarchy)
        else:
            new_space = Room(id=space_info['id'], parent_id=space_parent,
                             name=space_info['name'], hierarchy=hierarchy)
        new_space.save()

        hierarchy = hierarchy + '/' + space_info['name']

        # Explore other contained spaces within this space
        for contained_space in space_info['containedSpaces']:
            self.retrieve_space(space_to_explore=contained_space['id'], space_parent=new_space, hierarchy=hierarchy)

    def handle(self, *args, **options):

        if not Room.objects.all().exists():

            # Request space's info - this will be the campuses (roots of the tree)
            r = requests.get(self.base_url)
            campuses = r.json()

            # Explore spaces contained within the campus
            for campus_index in range(0, len(campuses)):
                campus_id = campuses[campus_index]['id']
                print campuses[campus_index]['name']
                hierarchy = ''
                self.retrieve_space(space_to_explore=campus_id, space_parent=0, hierarchy=hierarchy)

    def get(self, request, *args, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS=0")
            cursor.execute("TRUNCATE rooms_room")
            cursor.execute("SET FOREIGN_KEY_CHECKS=1")

        self.handle()
        return HttpResponse(status=200)



@method_decorator(login_required(login_url='/room4u/'), name='dispatch')
class CheckOutView(View):
    def post(self, request, *args, **kwargs):
        current_check_in = Visit.objects.filter(user=request.user, end__isnull=True).first()
        if current_check_in:
            current_check_in.end = timezone.now()
            current_check_in.save()
            return HttpResponse(status=200)
        else:
            return HttpResponse(status=404)


@method_decorator(login_required(login_url='/room4u/'), name='dispatch')
class CheckInHistoryView(View):
    template = 'check-in_history.html'

    def get_context(self, request):

        context = {
            'username': request.user.username,
            'is_admin': request.user.is_staff
        }

        if not request.user.is_staff:

            current_check_in = Visit.objects.filter(user=request.user, end__isnull=True).first()

            if not current_check_in:
                context['checked_in'] = 0
            else:
                context['checked_in'] = 1
                context['checked_in_room'] = current_check_in.room.name
                context['user_id'] = request.user.id
                context['checked_in_room_id'] = current_check_in.room.id
                context['checked_in_time'] = current_check_in.start
                context['users_in_room'] = Visit.objects.filter(room=current_check_in.room, end__isnull=True).order_by(
                    '-start').all()

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context(request)

        if request.user.is_staff:

            context['rooms'] = Visit.objects.values('room').annotate(total=Count('room_id')). \
                order_by('-total')
            context['total'] = 0
            for room in context['rooms']:
                room['users'] = Visit.objects.filter(room=room['room']).order_by('-start').all()
                room['name'] = room['users'][0].room.name
                room['hierarchy'] = room['users'][0].room.hierarchy
                context['total'] += room['total']

        else:
            context['history'] = Visit.objects.filter(user=request.user).order_by('-start').all()

        return render(request, self.template, context)

    def post(self, request):

        context = self.get_context(request)

        if request.user.is_staff:

            form = AdminSearchForm(request.POST)

            if form.is_valid():
                # Get search keywords
                search_keyword = request.POST['search_keyword']
                search_type = request.POST['search_type']

                context['total'] = 0

                if search_type == 'room':

                    context['rooms'] = Visit.objects.filter(room__name__contains=search_keyword) \
                        .values('room').annotate(total=Count('room_id')).order_by('-total')

                    for room in context['rooms']:
                        room['users'] = Visit.objects \
                            .filter(room__name__contains=search_keyword, room=room['room']).order_by('-start').all()
                        room['name'] = room['users'][0].room.name
                        room['hierarchy'] = room['users'][0].room.hierarchy

                        context['total'] += room['total']

                elif search_type == 'username':

                    context['users'] = Visit.objects.filter(user__username__contains=search_keyword) \
                        .exclude(user__is_staff=True).values('user').annotate(total=Count('user_id')).order_by('-total')

                    for user in context['users']:
                        user['visits'] = Visit.objects.filter(user=user['user']).order_by('-start').all()[:5]
                        user['username'] = user['visits'][0].user.username
                        user['last_name'] = user['visits'][0].user.last_name
                        user['first_name'] = user['visits'][0].user.first_name

                    context['total'] = len(context['users'])

                elif search_type == 'name':

                    context['users'] = Visit.objects.filter(Q(user__first_name__contains=search_keyword) |
                                                            Q(user__last_name__contains=search_keyword)) \
                        .exclude(user__is_staff=True).values('user').annotate(total=Count('user_id')).order_by('-total')

                    for user in context['users']:
                        user['visits'] = Visit.objects.filter(user=user['user']).order_by('-start').all()[:5]
                        user['username'] = user['visits'][0].user.username
                        user['last_name'] = user['visits'][0].user.last_name
                        user['first_name'] = user['visits'][0].user.first_name

                    context['total'] = len(context['users'])

                context['search_keyword'] = search_keyword
                context['search_type'] = search_type

            return render(request, self.template, context)


@method_decorator(login_required(login_url='/room4u/'), name='dispatch')
class RoomsView(View):
    template = 'rooms.html'

    def get_context(self, request):
        context = {
            'username': request.user.username,
            'is_admin': request.user.is_staff
        }

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context(request)

        return render(request, self.template, context)

    def post(self, request, *args, **kwargs):
        context = self.get_context(request)

        form = SearchRoomForm(request.POST)
        if form.is_valid():
            # Get search keywords
            keyword = request.POST['keyword']

            # Search for rooms in the db
            context['rooms'] = Room.objects.filter(name__contains=keyword)

        return render(request, self.template, context)


@method_decorator(login_required(login_url='/room4u/'), name='dispatch')
class RoomView(View):
    template = 'room.html'

    def get_context(self, request):
        context = {
            'username': request.user.username,
            'is_admin': request.user.is_staff
        }

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context(request)

        room_id = kwargs['room_id']
        context['room_info'] = client.get_space(id=room_id)
        context['room'] = Room.objects.filter(id=room_id).first()

        # Getting room family
        context['room_family'] = []
        parent = context['room'].parent_id

        while parent:
            context['room_family'].append({
                'name': parent.name,
                'id': parent.id
            })
            parent = parent.parent_id
        context['room_family'].reverse()

        context['all_visits'] = Visit.objects.filter(room=context['room']).order_by('-start').all()
        context['all_visits_total'] = len(context['all_visits'])

        context['current_visits'] = Visit.objects.filter(room=context['room'], end__isnull=True).order_by(
            '-start').all()
        context['current_total'] = len(context['current_visits'])

        return render(request, self.template, context)


@method_decorator(login_required(login_url='/room4u/'), name='dispatch')
class UsersView(View):
    template = 'users.html'

    def get_context(self, request):
        context = {
            'username': request.user.username,
            'is_admin': request.user.is_staff
        }

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context(request)

        return render(request, self.template, context)

    def post(self, request, *args, **kwargs):
        context = self.get_context(request)

        form = SearchRoomForm(request.POST)
        if form.is_valid():
            # Get search keywords
            keyword = request.POST['keyword']

            # Search for rooms in the db
            context['users'] = User.objects.filter(Q(username__contains=keyword) |
                                                   Q(first_name__contains=keyword) |
                                                   Q(last_name__contains=keyword)) \
                .exclude(is_staff=True).all()

        return render(request, self.template, context)


@method_decorator(login_required(login_url='/room4u/'), name='dispatch')
class UserView(View):
    template = 'user.html'

    def get_context(self, request):
        context = {
            'username': request.user.username,
            'is_admin': request.user.is_staff
        }

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context(request)

        username = kwargs['username']

        context['user'] = User.objects.filter(username=username).first()

        context['checked_in'] = Visit.objects.filter(user=context['user'], end__isnull=True).first()

        context['all_visits'] = Visit.objects.filter(user=context['user']).order_by('-start').all()
        context['all_visits_total'] = len(context['all_visits'])

        return render(request, self.template, context)


class VisitApiView(View):
    def get(self, request, *args, **kwargs):

        if 'visit_id' in kwargs:
            visit_id = kwargs['visit_id']

            try:
                visit = Visit.objects.filter(id=visit_id).get()

            except Visit.DoesNotExist:
                response = dict()
                response['error'] = 'resource not found'
                return HttpResponse(
                    json.dumps(response),
                    content_type='application/json',
                    status=404
                )
            return HttpResponse(
                serialize("json", [visit]),
                content_type='application/json',
                status=200
            )
        else:
            visits = Visit.objects.all()

            return HttpResponse(
                serialize("json", visits),
                content_type='application/json',
                status=200
            )

    def post(self, request, *args, **kwargs):

        body = json.loads(request.body)

        if 'user' in body and 'room' in body:

            try:
                user = User.objects.get(id=body['user'])
                room = Room.objects.get(id=body['room'])
            except (User.DoesNotExist, Room.DoesNotExist, ValueError):

                response = dict()
                response['error'] = 'room or user not found'
                return HttpResponse(
                    json.dumps(response),
                    content_type='application/json',
                    status=404
                )

            # Checking if there is a pending visit
            current_check_in = Visit.objects.filter(user=user, end__isnull=True).first()

            if current_check_in:
                if current_check_in.room == room:
                    response = dict()
                    response['error'] = 'already checked-in in that room'
                    return HttpResponse(
                        json.dumps(response),
                        content_type='application/json',
                        status=409
                    )
                else:
                    current_check_in.end = timezone.now()
                    current_check_in.save()

            start = timezone.now()

            visit = Visit(user=user, room=room, start=start)
            visit.save()

            return HttpResponse(
                serialize("json", [visit]),
                status=200,
                content_type='application/json',
            )

        response = dict()
        response['error'] = 'bad request, room or user missing'
        return HttpResponse(
            json.dumps(response),
            content_type='application/json',
            status=400
        )

    def put(self, request, *args, **kwargs):

        body = json.loads(request.body)

        if 'user' in body and 'room' in body:

            try:
                user = User.objects.get(id=body['user'])
                room = Room.objects.get(id=body['room'])
            except (User.DoesNotExist, Room.DoesNotExist):

                response = dict()
                response['error'] = 'room or user not found'
                return HttpResponse(
                    json.dumps(response),
                    content_type='application/json',
                    status=404
                )

            # Checking if there is a pending visit
            current_check_in = Visit.objects.filter(user=user, end__isnull=True).first()

            if not current_check_in:
                response = dict()
                response['error'] = 'there is no pending visits'
                return HttpResponse(
                    json.dumps(response),
                    content_type='application/json',
                    status=409
                )

            current_check_in.end = timezone.now()
            current_check_in.save()

            return HttpResponse(
                serialize("json", [current_check_in]),
                status=200,
                content_type='application/json',
            )

        response = dict()
        response['error'] = 'bad request, room or user missing'
        return HttpResponse(
            json.dumps(response),
            content_type='application/json',
            status=400
        )

    def delete(self, request, *args, **kwargs):

        if 'visit_id' in kwargs:
            visit_id = kwargs['visit_id']

            try:
                visit = Visit.objects.filter(id=visit_id).get()
                visit.delete()
                return HttpResponse(
                    status=204
                )

            except Visit.DoesNotExist:
                response = dict()
                response['error'] = 'resource not found'
                return HttpResponse(
                    json.dumps(response),
                    content_type='application/json',
                    status=404
                )

        response = dict()
        response['error'] = 'not allowed'
        return HttpResponse(
            json.dumps(response),
            content_type='application/json',
            status=405
        )


class NewMessageApiView(View):
    def get(self, request, *args, **kwargs):

        if 'new_message_id' in kwargs:
            new_message_id = kwargs['new_message_id']

            try:
                new_message = NewMessage.objects.filter(id=new_message_id).get()

            except NewMessage.DoesNotExist:
                response = dict()
                response['error'] = 'resource not found'
                return HttpResponse(
                    json.dumps(response),
                    content_type='application/json',
                    status=404
                )

            return HttpResponse(
                serialize("json", [new_message.message]),
                content_type='application/json',
                status=200
            )
        else:
            messages = Message.objects.raw('select * from rooms_newmessage natural join rooms_message')
            return HttpResponse(
                serialize("json", messages),
                content_type='application/json',
                status=200
            )

    def delete(self, request, *args, **kwargs):

        if 'new_message_id' in kwargs:
            new_message_id = kwargs['new_message_id']

            try:
                new_message = NewMessage.objects.filter(id=new_message_id).get()
                new_message.delete()
                return HttpResponse(
                    status=204
                )

            except NewMessage.DoesNotExist:
                response = dict()
                response['error'] = 'resource not found'
                return HttpResponse(
                    json.dumps(response),
                    content_type='application/json',
                    status=404
                )

        response = dict()
        response['error'] = 'not allowed'
        return HttpResponse(
            json.dumps(response),
            content_type='application/json',
            status=405
        )


class UserApiView(View):
    def get(self, request, *args, **kwargs):

        if 'user_id' in kwargs:
            user_id = kwargs['user_id']

            try:
                user = User.objects.filter(id=user_id).get()

            except User.DoesNotExist:
                response = dict()
                response['error'] = 'resource not found'
                return HttpResponse(
                    json.dumps(response),
                    content_type='application/json',
                    status=404
                )

            if 'resource' in kwargs:
                resource = kwargs['resource']

                if resource == 'new_messages':
                    response = serialize("json", NewMessage.objects.filter(message__receiver=user).all())

                elif resource == 'messages':
                    response = serialize("json", Message.objects.filter(receiver=user).all())

                elif resource == 'visits':
                    response = serialize("json", Visit.objects.filter(user=user).all())

                else:
                    response = dict()
                    response['error'] = 'resource not found'
                    response = json.dumps(response)
                return HttpResponse(
                    response,
                    content_type='application/json',
                    status=404
                )

            return HttpResponse(
                serialize("json", [user]),
                content_type='application/json',
                status=200
            )

        else:
            users = User.objects.all()

            return HttpResponse(
                serialize("json", users),
                content_type='application/json',
                status=200
            )

    def delete(self, request, *args, **kwargs):
        if 'user_id' in kwargs and 'resource' in kwargs:
            if kwargs['resource'] == 'new_messages':
                if not NewMessage.objects.filter(message__receiver=kwargs['user_id']):
                    return HttpResponse(
                        json.dumps([]),
                        content_type='application/json',
                        status=200
                    )
                else:
                    # filter
                    message = NewMessage.objects.filter(message__receiver=kwargs['user_id']).first()
                    NewMessage.objects.filter(id=message.id).delete()
                    return HttpResponse(
                        serialize("json", [message.message, ]),
                        content_type='application/json',
                        status=200
                    )
            else:
                response = dict()
                response['error'] = 'bad request, resource must me \'new_messages\''
                return HttpResponse(
                    json.dumps(response),
                    content_type='application/json',
                    status=400
                )
        else:
            response = dict()
            response['error'] = 'bad request, user_id or resource missing'
            return HttpResponse(
                json.dumps(response),
                content_type='application/json',
                status=400
            )
