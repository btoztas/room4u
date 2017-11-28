from django.conf.urls import url
from django.contrib.auth import views as auth_views
from rooms.views import IndexView, AuthView, DashboardView, MessageView, NewMessageView, NewMessageHandlerView

urlpatterns = [

    # Web application urls
    url(r'^$', IndexView.as_view()),
    url(r'^auth/$', AuthView.as_view()),
    #url(r'^admin-panel/$', AdminLoginView.as_view()),
    url(r'^logout/$', auth_views.logout, {'next_page': '/room4u'}, name='logout'),
    url(r'^messages/new$', NewMessageView.as_view()),
    url(r'^messages/handler$', NewMessageHandlerView.as_view()),
    url(r'^messages/$', MessageView.as_view()),

    # API urls
    url(r'^index/$', IndexView.as_view()),
]

