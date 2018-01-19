import json
import os
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.conf import settings
import fenixedu
from room4u.settings import SITE_URL
from .forms import MessageForm, FilterForm, SearchRoomForm, AdminSearchForm
from .models import Message, Room, Visit, NewMessage
from django.utils import timezone
from django.core.serializers import serialize
from django.contrib.auth.models import User

if 'RDS_DB_NAME' in os.environ:

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
        message = NewMessage.objects.filter(message__receiver=request.user.id).get()
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

    def get(self, request, *args, **kwargs):
        return redirect('/room4u')


class MessageView(View):
    message_template = 'messages.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return redirect('/room4u')
        if request.user.username == "administrator":
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
            print (request.POST.get("sdate", ""))
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
                    messages = Message.objects.filter(text__contains=str(text))
                    messages = messages | Message.objects.filter(title__contains=str(text))
                elif str(filter) == "Room":
                    messages = Message.objects.filter(room__contains=str(text))
                else:
                    if str(date) == "year":
                        startdate = timezone.today()
                        enddate = timezone.today().replace(year=timezone.today().year - 1)
                        messages = Message.objects.filter(created_at__range=[enddate, startdate])
                    if str(date) == "6month":
                        startdate = timezone.today()
                        enddate = timezone.today().replace(month=timezone.today().month - 6)
                        messages = Message.objects.filter(created_at__range=[enddate, startdate])
                    if str(date) == "month":
                        startdate = timezone.today()
                        enddate = timezone.today().replace(month=timezone.today().month - 1)
                        messages = Message.objects.filter(created_at__range=[enddate, startdate])
                    if str(date) == "week":
                        startdate = timezone.now().today()
                        enddate = timezone.now().today().replace(day=timezone.now().today().day - 7)
                        messages = Message.objects.filter(created_at__range=[enddate, startdate])
                    if str(date) == "today":
                        startdate = timezone.now().today()
                        enddate = timezone.now().today().replace(hour=0)
                        messages = Message.objects.filter(created_at__range=[enddate, startdate])
                    if str(date) == "specific_date":
                        messages = Message.objects.filter(created_at__year=datee[0], created_at__month=datee[1],
                                                          created_at__day=datee[2])
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


class ApiView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("done")


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
                context['rooms'] = Room.objects.filter(name__contains=keyword)

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
        else:
            visits = Visit.objects.all()

            if visits:
                return HttpResponse(
                    serialize("json", visits),
                    content_type='application/json',
                    status=200
                )

        response = dict()
        response['error'] = 'bad request'
        return HttpResponse(
            json.dumps(response),
            content_type='application/json',
            status=400
        )

    def post(self, request, *args, **kwargs):

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
