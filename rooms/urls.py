from django.conf.urls import url
from django.contrib.auth import views as auth_views
from rooms.views import IndexView, AuthView, DashboardView

urlpatterns = [
    url(r'^index/$', IndexView.as_view()),
    url(r'^auth/$', AuthView.as_view()),
    url(r'^dashboard/$', DashboardView.as_view()),
    url(r'^logout/$', auth_views.logout, {'next_page': '/room4u/index'}, name='logout'),
]
