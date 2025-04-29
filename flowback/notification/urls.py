from django.urls import path

from .views import (NotificationListAPI,
                    NotificationSubscriptionListAPI)


notification_patterns = [
    path('list', NotificationListAPI.as_view(), name='notification_list'),
    path('subscription', NotificationSubscriptionListAPI.as_view(), name='notification_subscription_list')
]
