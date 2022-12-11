import django_filters
from django.utils import timezone

from .models import NotificationChannel, NotificationObject, Notification, NotificationSubscription
from ..user.models import User


class BaseNotificationFilter(django_filters.FilterSet):
    notification_id = django_filters.NumberFilter(field_name='notification_object_id')
    notification_message = django_filters.CharFilter(field_name='notification_object_message',
                                                     lookup_expr='iexact')
    notification_message__icontains = django_filters.CharFilter(field_name='notification_object_message',
                                                                lookup_expr='icontains')
    notification_timestamp__lt = django_filters.DateFilter(field_name='notification_object__timestamp',
                                                           lookup_expr='lt')
    notification_timestamp__gt = django_filters.DateFilter(field_name='notification_object__timestamp',
                                                           lookup_expr='gt')

    notification_channel_type = django_filters.CharFilter(field_name='notification_object__channel__sender_type')
    notification_channel_id = django_filters.NumberFilter(field_name='notification_object__channel__sender_id')
    notification_channel_action = django_filters.CharFilter(field_name='notification_object__channel__action')
    notification_channel_category = django_filters.CharFilter(field_name='notification_object__channel__category')

    class Meta:
        model = Notification
        fields = dict(id=['exact'],
                      read=['exact'])


class BaseNotificationSubscriptionFilter(django_filters.FilterSet):
    channel_type = django_filters.CharFilter(field_name='channel__sender_type')
    channel_id = django_filters.NumberFilter(field_name='channel__sender_id')
    channel_action = django_filters.CharFilter(field_name='channel__action')
    channel_category = django_filters.CharFilter(field_name='channel__category')

    class Meta:
        model = NotificationChannel


def notification_list(*, user: User, filters=None):
    filters = filters or {}
    qs = Notification.objects.filter(user=user,
                                     notification_object__timestamp__lte=timezone.now()).order_by('timestamp').all()

    return BaseNotificationFilter(filters, qs).qs


def notification_subscription_list(*, user: User, filters=None):
    filters = filters or {}
    qs = NotificationSubscription.objects.filter(user=user).all()
    return BaseNotificationSubscriptionFilter(filters, qs).qs
