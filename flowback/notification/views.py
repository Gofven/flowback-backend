from django.shortcuts import render

# Create your views here.
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from flowback.common.pagination import LimitOffsetPagination, get_paginated_response
from flowback.notification.selectors import notification_list, notification_subscription_list
from flowback.notification.services import notification_mark_read


class NotificationListAPI(APIView):
    class Pagination(LimitOffsetPagination):
        max_limit = 100
        default_limit = 20

    class FilterSerializer(serializers.Serializer):
        id = serializers.IntegerField(required=False)
        read = serializers.BooleanField(required=False)
        object_id = serializers.IntegerField(required=False, source='notification_object_id')
        message = serializers.CharField(required=False, source='notification_message')
        message__icontains = serializers.CharField(required=False, source='notification_message__icontains')
        action = serializers.CharField(required=False, source='notification_action')
        timestamp__lt = serializers.DateTimeField(required=False, source='notification_timestamp__lt')
        timestamp__gt = serializers.DateTimeField(required=False, source='notification_timestamp__gt')
        channel_type = serializers.CharField(required=False, source='notification_channel_type')
        channel_id = serializers.IntegerField(required=False, source='notification_channel_id')

        channel_category = serializers.CharField(required=False, source='notification_channel_category')

    class OutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        object_id = serializers.IntegerField(source='notification_object_id')
        message = serializers.CharField(source='notification_object.message')
        timestamp = serializers.DateTimeField(source='notification_object.timestamp')
        action = serializers.CharField(source='notification_object.action')
        channel_sender_id = serializers.IntegerField(source='notification_object.channel.sender_id')
        channel_sender_type = serializers.CharField(source='notification_object.channel.sender_type')
        channel_id = serializers.IntegerField(source='notification_object.channel_id')
        channel_category = serializers.CharField(source='notification_object.channel.category')
        read = serializers.BooleanField()

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
        channel_type = serializers.CharField(required=False)
        channel_id = serializers.IntegerField(required=False)
        action = serializers.CharField(required=False)
        channel_category = serializers.CharField(required=False)

    class OutputSerializer(serializers.Serializer):
        action = serializers.CharField(source='notification_object.action')
        channel_type = serializers.CharField(source='notification_object.channel.type')
        channel_id = serializers.IntegerField(source='notification_object.channel_id')
        channel_category = serializers.CharField(source='notification_object.channel.category')

    def get(self, request):
        filter_serializer = self.FilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        subscriptions = notification_subscription_list(user=request.user, filters=filter_serializer.validated_data)

        return get_paginated_response(pagination_class=self.Pagination,
                                      serializer_class=self.OutputSerializer,
                                      queryset=subscriptions,
                                      request=request,
                                      view=self)


class NotificationMarkReadAPI(APIView):
    class InputSerializer(serializers.Serializer):
        notification_id_list = serializers.ListField(child=serializers.IntegerField())

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        notification_mark_read(fetched_by=request.user.id, **serializer.validated_data)
        return Response(status=status.HTTP_200_OK)
