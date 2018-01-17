from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.views.decorators.csrf import csrf_exempt

from rooms.views import IndexView, AuthView, CheckInView, MessageView, NewMessageView, NewMessageHandlerView, ApiView, \
    CheckInHistoryView, NewCheckInView, CheckOutView, IncomingMessageView, RoomsView, RoomView, UsersView, UserView

urlpatterns = [

    # Web application urls
    url(r'^$', IndexView.as_view()),
    url(r'^auth/$', AuthView.as_view()),
    url(r'^logout/$', auth_views.logout, {'next_page': '/room4u'}, name='logout'),
    url(r'^messages/new$', NewMessageView.as_view()),
    url(r'^messages/incoming$', csrf_exempt(IncomingMessageView.as_view())),
    url(r'^messages/handler$', csrf_exempt(NewMessageHandlerView.as_view())),
    url(r'^messages/$', MessageView.as_view()),
    url(r'^check-in/$', CheckInView.as_view()),
    url(r'^check-in/new$', csrf_exempt(NewCheckInView.as_view())),
    url(r'^check-in/history$', CheckInHistoryView.as_view()),
    url(r'^check-out', csrf_exempt(CheckOutView.as_view())),
    url(r'^rooms/$', RoomsView.as_view()),
    url(r'^rooms/(?P<room_id>\d+)/$', RoomView.as_view()),
    url(r'^users/$', UsersView.as_view()),
    url(r'^users/(?P<username>.*)/$', UserView.as_view()),
    url(r'^admin-panel/$', auth_views.login, {'template_name': 'admin_login.html'}, name='admin_login'),
    url(r'^logout/$', auth_views.logout, {'next_page': '/room4u'}, name='logout'),

    # API urls
    url(r'^api/$', ApiView.as_view()),
]

