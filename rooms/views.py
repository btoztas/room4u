from django.contrib.auth import login, authenticate
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import View
from django.conf import settings
import fenixedu
from fenixedu.authentication import users

config = fenixedu.FenixEduConfiguration\
    ('1977390058176548', 'http://127.0.0.1:8000/room4u/auth',
     'ivhTjk4+geVbJT1bh+KtZ0zrcBo0RuMw/SFsQIxShsRJX7VSntrKVw3U82Yz2WQb7075DbsnQX6+/uUO+LG7Kw==',
     'https://fenix.tecnico.ulisboa.pt/')

client = fenixedu.FenixEduClient(config)


class IndexView(View):
    login_template = 'login.html'
    dashboard_template = 'main.html'

    def get(self, request, *args, **kwargs):

        if not request.user.is_authenticated():
            context = {'auth_url': client.get_authentication_url()}
            return render(request, self.login_template, context)
        else:
            return render(request, self.dashboard_template)


class AuthView(View):

    def get(self, request, *args, **kwargs):

        code = request.GET.get('code', None)
        if code is not None and not request.user.is_authenticated():
            user = authenticate(request=request, client=client, code=code)
            if user is not None:
                login(request, user)

        return redirect(settings.SITE_URL+'/room4u')


class DashboardView(View):

    def get(self, request, *args, **kwargs):
        current_user = request.user
        return HttpResponse(current_user.username.__str__())
