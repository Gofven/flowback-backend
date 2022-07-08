from django.urls import path, include

from .views import GroupMessageListApi, GroupMessagePreviewApi, DirectMessageListApi, DirectMessagePreviewApi

chat_patterns = [
    path('group/<int:group>', GroupMessageListApi.as_view(), name='chat-group-list'),
    path('group/preview', GroupMessagePreviewApi.as_view(), name='chat-group-preview'),
    path('dm/<int:target>', DirectMessageListApi.as_view(), name='chat-dm-list'),
    path('dm/preview', DirectMessagePreviewApi.as_view(), name='chat-dm-preview')
]

urlpatterns = [
    path('chat/', include((chat_patterns, 'chat')))
]
