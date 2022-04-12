
from rest_framework.routers import DefaultRouter
from django.urls import path
from django.conf.urls import url, include

from django_rest_passwordreset import views as reset_pass_view

from flowback.base.api.routers import SingletonRouter
from flowback.users.views import UserViewSet, UserLogin, CurrentUserViewSet, UserGroupViewSet, UserLogout, \
    LocationViewSet, FriendsViewSet, GroupChatViewSet
from flowback.polls.views import GroupPollViewSet
from flowback.notifications.urls import urlpatterns as notification_urls
from flowback.chat.urls import urlpatterns as chat_urls
from flowback.probability.urls import urlpatterns as probability_urls

default_router = DefaultRouter(trailing_slash=False)
singleton_router = SingletonRouter(trailing_slash=False)
default_router.register("user", UserViewSet, basename="user")
default_router.register("me", CurrentUserViewSet, basename="me")
default_router.register("user_group", UserGroupViewSet, basename="user_group")
default_router.register("group_poll", GroupPollViewSet, basename="group_poll")
default_router.register("location", LocationViewSet, basename="location")
default_router.register("friend", FriendsViewSet, basename="friend")
default_router.register('group_chat', GroupChatViewSet, basename='group_chat')

urlpatterns = default_router.urls + singleton_router.urls + notification_urls + chat_urls + probability_urls + [
    path("login", UserLogin.as_view(), name="user-login"),
    path("logout", UserLogout.as_view(), name="user-logout"),
    url(r'^password_reset/validate_token/',
        reset_pass_view.ResetPasswordValidateToken.as_view(authentication_classes=[], permission_classes=[]),
        name="reset-password-validate"),
    url(r'^password_reset/confirm/',
        reset_pass_view.ResetPasswordConfirm.as_view(authentication_classes=[], permission_classes=[]),
        name="reset-password-confirm"),
    url(r'^password_reset/',
        reset_pass_view.ResetPasswordRequestToken.as_view(authentication_classes=[], permission_classes=[]),
        name='reset-password-request')
]
