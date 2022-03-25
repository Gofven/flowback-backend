from django.urls import path, include

from .views import GroupMessageListApi

chat_patterns = [
    path('group/<int:group>', GroupMessageListApi.as_view(), name='chat-group-list'),
]

urlpatterns = [
    path('chat/', include((chat_patterns, 'chat')))
]
