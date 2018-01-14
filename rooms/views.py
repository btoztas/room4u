from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.conf import settings
import fenixedu
from .forms import MessageForm, FilterForm
from fenixedu.authentication import users
from .models import Message

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
        context = {
            'messages': messages,
            'username': request.user.username,
            'is_admin': request.user.is_staff,
            'filter': "",
            'text': "",
            'date': "",
            'sdate': ""
        }
        #return HttpResponse('ola')
        return render(request, self.message_template, context)
    def post(self, request, *args, **kwargs):
        #message = request.POST.get("message", "")
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
                if str(filter)=="Search":
                    messages = Message.objects.filter(text__contains=str(text))
                    messages = messages | Message.objects.filter(title__contains=str(text))
                elif str(filter)=="Room":
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
                context = {'filter': filter, 'text': text, 'date': date, 'sdate': sdate, 'messages': messages}
                return render(request, self.message_template, context)


@method_decorator(login_required(login_url='/room4u/'), name='dispatch')
class CheckInView(View):
    template = 'check_in.html'

    def get(self, request, *args, **kwargs):
        context = {
            'username': request.user.username,
            'is_admin': request.user.is_staff
        }
        return render(request, self.template, context)

