"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from backend.settings import DEBUG, MEDIA_URL, MEDIA_ROOT, URL_SUBPATH
from flowback.kanban.urls import kanban_patterns
from flowback.poll.views import PollUserScheduleListAPI, PollListApi
from flowback.user.urls import user_patterns
from flowback.group.urls import group_patterns
from flowback.poll.urls import poll_patterns
from flowback.chat.urls import chat_patterns
from flowback.notification.urls import notification_patterns
from django.conf.urls.static import static

path_prefix = f'{URL_SUBPATH}/' if URL_SUBPATH else ''
path_prefix_noslash = f'{URL_SUBPATH}' if URL_SUBPATH else ''

urlpatterns = [
    path(path_prefix + 'admin/', admin.site.urls),
    path(path_prefix + '', include((user_patterns, 'user'))),
    path(path_prefix + 'group/', include((group_patterns, 'group'))),
    path(path_prefix + 'chat/', include((chat_patterns, 'chat'))),
    path(path_prefix + 'group/<int:group>/poll/', include((poll_patterns, 'poll'))),
    path(path_prefix + 'group/<int:group_id>/kanban/', include((kanban_patterns, 'kanban'))),
    path(path_prefix + 'home/kanban', include((kanban_patterns, 'home_kanban'))),
    path(path_prefix + 'notification/', include((notification_patterns, 'notification'))),
    path(path_prefix + 'home/polls', PollListApi.as_view(), name='home_polls'),
    path(path_prefix + 'poll/user/schedule', PollUserScheduleListAPI.as_view(), name='poll_user_schedule')
]

if DEBUG:
    urlpatterns += static(path_prefix_noslash + MEDIA_URL, document_root=MEDIA_ROOT)

