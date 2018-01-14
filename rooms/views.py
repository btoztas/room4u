import requests
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.conf import settings
import fenixedu
from .forms import MessageForm, SearchRoomFrom
from .models import Message, Room

config = fenixedu.FenixEduConfiguration\
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

        return redirect(settings.SITE_URL+'/room4u')


class IndexView(View):
    login_template = 'login.html'
    dashboard_template = 'main.html'

    def get(self, request, *args, **kwargs):

        if not request.user.is_authenticated():
            context = {'auth_url': client.get_authentication_url()}
            return render(request, self.login_template, context)
        else:
            context = {
                'username': request.user.username
            }
            return render(request, self.dashboard_template, context)


class NewMessageView(View):
    new_message_template = 'new_messages.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.new_message_template)


class NewMessageHandlerView(View):
    new_message_handler_template = 'new_message_handler.html'

    def post(self, request, *args, **kwargs):
        #message = request.POST.get("message", "")
        if request.method == 'POST':
            # create a form instance and populate it with data from the request:
            form = MessageForm(request.POST)
            # check whether it's valid:
            if form.is_valid():
                # process the data in form.cleaned_data as required
                # ...
                message = request.POST.get("message", "")
                # redirect to a new URL:
                instance = Message(title=str(request.POST.get("subject", "")), text=str(request.POST.get("message", "")), sender=request.user, receiver=request.user)
                instance.save()
                context = {'message': message}
                return render(request, self.new_message_handler_template, context)


class MessageView(View):
    message_template = 'messages.html'

    def get(self, request, *args, **kwargs):
        messages = Message.objects.all()
        context = {'messages': messages}
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
    form_class = SearchRoomFrom

    def get(self, request, *args, **kwargs):
        context = {
            'username': request.user.username,
            'is_admin': request.user.is_staff
        }
        return render(request, self.template, context)

    def post(self, request, *args, **kwargs):
        context = {
            'username': request.user.username,
            'is_admin': request.user.is_staff
        }

        form = self.form_class(request.POST)

        if form.is_valid():

            # Get search keywords
            keyword = request.POST['keyword']

            # Search for rooms in the db
            context['rooms'] = Room.objects.filter(name__contains=keyword)

        return render(request, self.template, context)



@method_decorator(login_required(login_url='/room4u/'), name='dispatch')
class CheckInHistoryView(View):
    template = 'check-in_history.html'

    def get(self, request, *args, **kwargs):
        context = {
            'username': request.user.username,
            'is_admin': request.user.is_staff
        }
        return render(request, self.template, context)

