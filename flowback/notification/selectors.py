import django_filters
from django.utils import timezone

from .models import NotificationChannel, NotificationObject, Notification, NotificationSubscription
from ..user.models import User


class BaseNotificationFilter(django_filters.FilterSet):
    notification_id = django_filters.NumberFilter(field_name='notification_object_id')
    notification_title = django_filters.CharFilter(field_name='notification_object_title',
                                                   lookup_expr='iexact')
    notification_description = django_filters.CharFilter(field_name='notification_object__description',
                                                         lookup_expr='iexact')
    notification_title__icontains = django_filters.CharFilter(field_name='notification_object_title',
                                                              lookup_expr='icontains')
    notification_description__icontains = django_filters.CharFilter(field_name='notification_object__description',
                                                                    lookup_expr='icontains')
    notification_timestamp__lt = django_filters.DateFilter(field_name='notification_object__timestamp',
                                                           lookup_expr='lt')
    notification_timestamp__gt = django_filters.DateFilter(field_name='notification_object__timestamp',
                                                           lookup_expr='gt')

    notification_channel_type = django_filters.CharFilter(field_name='notification_object__channel__sender_type')
    notification_channel_id = django_filters.NumberFilter(field_name='notification_object__channel__sender_id')
    notification_channel_action = django_filters.CharFilter(field_name='notification_object__channel__action')

    class Meta:
        model = Notification
        fields = dict(id=['exact'],
                      read=['exact'])


def notification_list(*, user: User, filters=None):
    filters = filters or {}
    qs = Notification.objects.filter(user=user,
                                     notification_object__timestamp__lte=timezone.now()).order_by('timestamp').all()

    return BaseNotificationFilter(filters, qs)
