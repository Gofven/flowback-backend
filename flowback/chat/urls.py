from django.urls import path

from backend.settings import URL_SUBPATH
from .consumers import ChatConsumer
from .views import MessageChannelUserDataUpdateAPI

subpath = f'{URL_SUBPATH}/' if URL_SUBPATH else ''

chat_patterns = [
    path('message/channel/userdata/update', MessageChannelUserDataUpdateAPI.as_view(), name='message_channel_userdata_update')
]

chat_ws_patterns = [
    path(subpath + 'chat/ws', ChatConsumer.as_asgi(), name='ws_chat'),
]
