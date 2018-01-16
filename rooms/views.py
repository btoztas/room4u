import requests
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.conf import settings
import fenixedu
from .forms import MessageForm, FilterForm, SearchRoomForm, AdminSearchForm
from .models import Message, Room, Visit, NewMessage
from django.utils import timezone
from django.core.serializers import serialize


config = fenixedu.FenixEduConfiguration \
    ('1977390058176548', 'http://127.0.0.1:8000/room4u/auth',
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

    def get(self, request, *args, **kwargs):

        if not request.user.is_authenticated():
            context = {'auth_url': client.get_authentication_url()}
            return render(request, self.login_template, context)
        else:
            context = {
                'username': request.user.username,
                'is_admin': request.user.is_staff
            }
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
        #filter
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
                print (request.POST.get("destination", ""))
                if request.POST.get("destflag", "") == "room":
                    destination = Room.objects.filter(id=request.POST.get("destination", ""))
                    users = Visit.objects.filter(room=destination, end__isnull=True)
                    nusers = len(users)
                    message = request.POST.get("message", "")
                    for user in users:
                        instance = Message(title=str(request.POST.get("subject", "")),
                                           text=str(request.POST.get("message", "")), sender=request.user,
                                           receiver=user.user)
                        instance.save()
                        instance2 = NewMessage(message=instance)
                        instance2.save()
                else:
                    user = request.POST.get("destination", "")
                    print (user)
                    users = Visit.objects.filter(user__username=user, end__isnull=True).first()
                    instance = Message(title=str(request.POST.get("subject", "")),
                                       text=str(request.POST.get("message", "")), sender=request.user,
                                       receiver=users.user)
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
        if request.user.username=="administrator":
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
                        messages = Message.objects.raw('SELECT * FROM rooms_message')
                    if str(date) == "6month":
                        messages = Message.objects.raw('SELECT * FROM rooms_message')
                    if str(date) == "month":
                        messages = Message.objects.raw('SELECT * FROM rooms_message')
                    if str(date) == "week":
                        messages = Message.objects.raw('SELECT * FROM rooms_message')
                    if str(date) == "today":
                        messages = Message.objects.raw('SELECT * FROM rooms_message')
                    if str(date) == "specific_date":
                        messages = Message.objects.raw('SELECT * FROM rooms_message')
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
    base_url = 'https://fenix.tecnico.ulisboa.pt/api/fenix/v1/spaces/'

    def retrieve_space(self, space_parent, space_to_explore):

        # Request space's info
        r = requests.get(self.base_url + space_to_explore)
        space_info = r.json()

        # Create new space object with the info retrieved
        new_space = Room(id=space_info['id'], parent_id=space_parent, name=space_info['name'])
        new_space.save()

        # Explore other contained spaces within this space
        for contained_space in space_info['containedSpaces']:
            self.retrieve_space(space_to_explore=contained_space['id'], space_parent=space_info['id'])

    def get(self, request, *args, **kwargs):

        # Request space's info - this will be the campuses (roots of the tree)
        r = requests.get(self.base_url)
        campuses = r.json()

        # Explore spaces contained within the campus
        for campus_index in range(0, len(campuses)):
            campus_id = campuses[campus_index]['id']
            self.retrieve_space(space_to_explore=campus_id, space_parent=0)

        return HttpResponse("done")


@method_decorator(login_required(login_url='/room4u/'), name='dispatch')
class CheckInView(View):
    template = 'check-in.html'

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
                context['checked_in_time'] = current_check_in.start

        return context

    def get(self, request, *args, **kwargs):

        context = self.get_context(request)

        if request.user.is_staff:
            context['rooms'] = Visit.objects.filter(end__isnull=True).values('room').annotate(total=Count('room_id')).\
                order_by('-total')
            context['total'] = 0
            for room in context['rooms']:
                room['users'] = Visit.objects.filter(end__isnull=True, room=room['room']).all()
                room['name'] = room['users'][0].room.name
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

                    context['rooms'] = Visit.objects.filter(room__name__contains=search_keyword, end__isnull=True)\
                        .values('room').annotate(total=Count('room_id')).order_by('-total')

                    for room in context['rooms']:
                        room['users'] = Visit.objects\
                            .filter(room__name__contains=search_keyword, end__isnull=True, room=room['room']).all()
                        room['name'] = room['users'][0].room.name

                        context['total'] += room['total']

                elif search_type == 'username':
                    context['users'] = Visit.objects.filter(end__isnull=True, user__username__contains=search_keyword)\
                        .all()
                    context['total'] = len(context['users'])

                #elif type == 'name':
                    #TODO: implement name

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
                context['checked_in_time'] = current_check_in.start

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context(request)

        if request.user.is_staff:

            context['rooms'] = Visit.objects.values('room').annotate(total=Count('room_id')). \
                order_by('-total')
            context['total'] = 0
            for room in context['rooms']:
                room['users'] = Visit.objects.filter(room=room['room']).all()
                room['name'] = room['users'][0].room.name
                context['total'] += room['total']

        else:
            context['history'] = Visit.objects.filter(user=request.user).exclude(end__isnull=True).all()

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

                    context['rooms'] = Visit.objects.filter(room__name__contains=search_keyword)\
                        .values('room').annotate(total=Count('room_id')).order_by('-total')

                    for room in context['rooms']:
                        room['users'] = Visit.objects\
                            .filter(room__name__contains=search_keyword, room=room['room']).all()
                        room['name'] = room['users'][0].room.name

                        context['total'] += room['total']

                elif search_type == 'username':

                    context['users'] = Visit.objects.filter(user__username__contains=search_keyword) \
                        .values('user').annotate(total=Count('user_id')).order_by('-total')

                    for user in context['users']:
                        user['visits'] = Visit.objects.filter(user=user['user']).order_by('-start').all()[:5]
                        user['username'] = user['visits'][0].user.username

                    context['total'] = len(context['users'])


                #elif type == 'name':
                    #TODO: implement name

                context['search_keyword'] = search_keyword
                context['search_type'] = search_type

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
