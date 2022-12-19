from django.urls import path

from .views import (NotificationListAPI,
                    NotificationMarkReadAPI,
                    NotificationSubscriptionListAPI)


notification_patterns = [
    path('', NotificationListAPI.as_view(), name='notification_list'),
    path('subscriptions', NotificationSubscriptionListAPI.as_view(), name='notification_subscription_list'),
    path('read', NotificationMarkReadAPI.as_view(), name='notification_mark_read'),
]
