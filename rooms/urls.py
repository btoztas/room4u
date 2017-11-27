from django.conf.urls import url
from django.contrib.auth import views as auth_views
from rooms.views import IndexView, AuthView

urlpatterns = [

    # Web application urls
    url(r'^$', IndexView.as_view()),
    url(r'^auth/$', AuthView.as_view()),
    url(r'^admin-panel/$', auth_views.login, {'template_name': 'admin_login.html'}, name='admin_login'),
    url(r'^logout/$', auth_views.logout, {'next_page': '/room4u'}, name='logout'),

    # API urls
    url(r'^index/$', IndexView.as_view()),
]

