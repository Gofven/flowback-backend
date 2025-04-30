from django.shortcuts import render

# Create your views here.
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from flowback.common.pagination import LimitOffsetPagination, get_paginated_response
from flowback.notification.selectors import notification_list, notification_subscription_list


class NotificationListAPI(APIView):
    class Pagination(LimitOffsetPagination):
        max_limit = 100
        default_limit = 20

    class FilterSerializer(serializers.Serializer):
        id = serializers.IntegerField(required=False)
        read = serializers.BooleanField(required=False)
        object_id = serializers.IntegerField(required=False)
        message__icontains = serializers.CharField(required=False)
        action = serializers.CharField(required=False)
        timestamp__lt = serializers.DateTimeField(required=False)
        timestamp__gt = serializers.DateTimeField(required=False)

        channel_name = serializers.CharField(required=False)
        order_by = serializers.ChoiceField(required=False, choices=['timestamp_asc',
                                                                    'timestamp_desc'])

    class OutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        read = serializers.BooleanField()

        object_id = serializers.IntegerField(source='notification_object_id')
        message = serializers.CharField(source='notification_object.message')
        data = serializers.IntegerField(source='notification_object.data')
        timestamp = serializers.DateTimeField(source='notification_object.timestamp')
        action = serializers.CharField(source='notification_object.action')
        tag = serializers.CharField(source='notification_object.tag')

        channel_name = serializers.CharField(source='notification_object.channel.content_type.model')
        channel_data = serializers.CharField(source='notification_object.channel.data')

    def get(self, request):
        filter_serializer = self.FilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        notifications = notification_list(user=request.user, filters=filter_serializer.validated_data)

        return get_paginated_response(pagination_class=self.Pagination,
                                      serializer_class=self.OutputSerializer,
                                      queryset=notifications,
                                      request=request,
                                      view=self)


class NotificationSubscriptionListAPI(APIView):
    class Pagination(LimitOffsetPagination):
        default_limit = 25
        max_limit = 100

    class FilterSerializer(serializers.Serializer):
        channel_id = serializers.IntegerField(required=False)
        channel_name = serializers.CharField(required=False)

    class OutputSerializer(serializers.Serializer):
        channel_id = serializers.IntegerField()
        channel_name = serializers.CharField(source='channel.name')
        tags = serializers.CharField()

    def get(self, request):
        filter_serializer = self.FilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        subscriptions = notification_subscription_list(user=request.user, filters=filter_serializer.validated_data)

        return get_paginated_response(pagination_class=self.Pagination,
                                      serializer_class=self.OutputSerializer,
                                      queryset=subscriptions,
                                      request=request,
                                      view=self)
