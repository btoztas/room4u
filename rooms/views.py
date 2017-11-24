from django.contrib.auth import login, authenticate
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import View
import fenixedu
from fenixedu.authentication import users

config = fenixedu.FenixEduConfiguration\
    ('1977390058176548', 'http://127.0.0.1:8000/room4u/auth',
     'ivhTjk4+geVbJT1bh+KtZ0zrcBo0RuMw/SFsQIxShsRJX7VSntrKVw3U82Yz2WQb7075DbsnQX6+/uUO+LG7Kw==',
     'https://fenix.tecnico.ulisboa.pt/')

client = fenixedu.FenixEduClient(config)


class IndexView(View):
    template_name = 'index.html'

    def get(self, request, *args, **kwargs):
        context = {'auth_url': client.get_authentication_url()}
        return render(request, 'index.html', context)


class AuthView(View):

    def get(self, request, *args, **kwargs):

        code = request.GET.get('code', None)
        if code is not None and not request.user.is_authenticated():
            user = authenticate(request=request, client=client, code=code)
            if user is not None:
                login(request, user)

        user = client.get_user_by_code(code=code)
        person = client.get_person(user=user)
        return HttpResponse(person.__str__())


class DashboardView(View):

    def get(self, request, *args, **kwargs):
        current_user = request.user
        return HttpResponse(current_user.username.__str__())
