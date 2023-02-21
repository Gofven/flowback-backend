from django.urls import path
from rest_framework.authtoken import views

from flowback.user.views.user import (UserCreateApi,
                                      UserCreateVerifyApi,
                                      UserListApi,
                                      UserGetApi,
                                      UserUpdateApi,
                                      UserForgotPasswordApi,
                                      UserForgotPasswordVerifyApi)
from flowback.user.views.schedule import (UserScheduleEventListAPI,
                                          UserScheduleEventCreateAPI,
                                          UserScheduleEventUpdateAPI,
                                          UserScheduleEventDeleteAPI, UserScheduleUnsubscribeAPI)

user_patterns = [
    path('register', UserCreateApi.as_view(), name='register'),
    path('register/verify', UserCreateVerifyApi.as_view(), name='register_verify'),
    path('login', views.obtain_auth_token, name='login'),
    path('forgot_password', UserForgotPasswordApi.as_view(), name='forgot_password'),
    path('forgot_password/verify', UserForgotPasswordVerifyApi.as_view(), name='forgot_password_verify'),
    path('users', UserListApi.as_view(), name='users'),
    path('user', UserGetApi.as_view(), name='user'),
    path('user/<int:user_id>', UserGetApi.as_view(), name='user'),
    path('user/update', UserUpdateApi.as_view(), name='user_update'),

    path('user/schedule', UserScheduleEventListAPI.as_view(), name='user_schedule'),
    path('user/schedule/create', UserScheduleEventCreateAPI.as_view(), name='user_schedule_create'),
    path('user/schedule/update', UserScheduleEventUpdateAPI.as_view(), name='user_schedule_update'),
    path('user/schedule/delete', UserScheduleEventDeleteAPI.as_view(), name='user_schedule_delete'),
    path('user/schedule/unsubscribe', UserScheduleUnsubscribeAPI.as_view(), name='user_schedule_unsubscribe'),
]
