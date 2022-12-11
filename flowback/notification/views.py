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
        notification_id = serializers.IntegerField(required=False)
        notification_message = serializers.CharField(required=False)
        notification_message__icontains = serializers.CharField(required=False)
        notification_timestamp__lt = serializers.DateTimeField(required=False)
        notification_timestamp__gt = serializers.DateTimeField(required=False)
        notification_channel_type = serializers.CharField(required=False)
        notification_channel_id = serializers.IntegerField(required=False)
        notification_channel_action = serializers.CharField(required=False)
        notification_channel_category = serializers.CharField(required=False)

    class OutputSerializer(serializers.Serializer):
        id = serializers.IntegerField(),
        notification_id = serializers.IntegerField(source='notification_object_id')
        notification_message = serializers.CharField(source='notification_object.title')
        notification_timestamp = serializers.DateTimeField(source='notification_object.timestamp')
        notification_channel_type = serializers.CharField(source='notification_object.channel.type')
        notification_channel_id = serializers.IntegerField(source='notification_object.channel_id')
        notification_channel_action = serializers.CharField(source='notification_object.channel.action')
        notification_channel_category = serializers.CharField(source='notification_object.channel.category')
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
        channel_action = serializers.CharField(required=False)
        channel_category = serializers.CharField(required=False)

    class OutputSerializer(serializers.Serializer):
        channel_type = serializers.CharField(source='notification_object.channel.type')
        channel_id = serializers.IntegerField(source='notification_object.channel_id')
        channel_action = serializers.CharField(source='notification_object.channel.action')
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


class NotificationCreateAPI(APIView):
    class InputSerializer(serializers.Serializer):
        notification_id_list = serializers.ListField(child=serializers.IntegerField())

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        notification_mark_read(fetched_by=request.user.id, **serializer.validated_data)
        return Response(status=status.HTTP_200_OK)

