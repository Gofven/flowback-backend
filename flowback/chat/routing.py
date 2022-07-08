from django.conf.urls import url

from . import consumers

websockets_urlpatterns = [
    url(r'ws/group_chat/(?P<group_id>\d+)/$', consumers.GroupChatConsumer.as_asgi()),
    url(r'ws/direct_chat/$', consumers.DirectChatConsumer.as_asgi())
]
