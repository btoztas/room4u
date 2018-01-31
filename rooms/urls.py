from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt

from rooms.views import IndexView, AuthView, CheckInView, MessageView, NewMessageView, NewMessageHandlerView, ApiView, \
    CheckInHistoryView, NewCheckInView, CheckOutView, IncomingMessageView, RoomsView, RoomView, UsersView, UserView, \
    VisitApiView, NewMessageApiView, UserApiView, RoomsApiView, MessagesApiView, RoomsReloadView

urlpatterns = [

    # Web application urls
    url(r'^$', csrf_exempt(IndexView.as_view())),
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
    url(r'^rooms/reload$', RoomsReloadView.as_view()),
    url(r'^rooms/(?P<room_id>\d+)/$', cache_page(60)(RoomView.as_view())),
    url(r'^users/$', UsersView.as_view()),
    url(r'^users/(?P<username>.*)/$', cache_page(15*60)(UserView.as_view())),
    url(r'^admin-panel/$', cache_page(15*60)(auth_views.login), {'template_name': 'admin_login.html'}, name='admin_login'),
    url(r'^logout/$', auth_views.logout, {'next_page': '/room4u'}, name='logout'),

    # API urls
    url(r'^api/$', ApiView.as_view()),
    url(r'^api/rooms/$',  cache_page(15*60)(RoomsApiView.as_view())),
    url(r'^api/rooms/(?P<room_id>\d+)/$', cache_page(15*60)(RoomsApiView.as_view())),
    url(r'^api/rooms/(?P<room_id>\d+)/(?P<search>.*)/$', RoomsApiView.as_view()),
    url(r'^api/messages/$', csrf_exempt(MessagesApiView.as_view())),
    url(r'^api/messages/(?P<message_id>\d+)/$', MessagesApiView.as_view()),
    url(r'^api/visits$', csrf_exempt(VisitApiView.as_view())),
    url(r'^api/visits/(?P<visit_id>\d+)$', csrf_exempt(VisitApiView.as_view())),
    url(r'^api/new_messages$', csrf_exempt(NewMessageApiView.as_view())),
    url(r'^api/new_messages/(?P<new_message_id>\d+)$', csrf_exempt(NewMessageApiView.as_view())),
    url(r'^api/users$', cache_page(15*60)(csrf_exempt(UserApiView.as_view()))),
    url(r'^api/users/(?P<user_id>\d+)$', cache_page(10)(csrf_exempt(UserApiView.as_view()))),
    url(r'^api/users/(?P<user_id>\d+)/(?P<resource>.*)$', csrf_exempt(UserApiView.as_view())),
]

