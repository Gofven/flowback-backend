from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .selectors import message_list, message_channel_preview_list
from .serializers import MessageSerializer
from .services import update_message_channel_userdata, leave_message_channel, upload_message_files
from flowback.common.pagination import get_paginated_response, LimitOffsetPagination


class MessageListAPI(APIView):
    class Pagination(LimitOffsetPagination):
        default_limit = 50
        max_limit = 50

    class FilterSerializer(serializers.Serializer):
        order_by = serializers.ChoiceField(required=False, choices=['created_at_asc', 'created_at_desc'])
        id = serializers.IntegerField(required=False)
        user_id = serializers.IntegerField(required=False)
        message__icontains = serializers.CharField(required=False)
        parent_id = serializers.IntegerField(required=False)
        created_at__gte = serializers.DateTimeField(required=False)
        created_at__lte = serializers.DateTimeField(required=False)

    OutputSerializer = MessageSerializer

    def get(self, request, channel_id: int):
        serializer = self.FilterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        messages = message_list(user=request.user, channel_id=channel_id, filters=serializer.validated_data)

        return get_paginated_response(pagination_class=self.Pagination,
                                      serializer_class=self.OutputSerializer,
                                      queryset=messages,
                                      request=request,
                                      view=self)


class MessageChannelPreviewAPI(APIView):
    class Pagination(LimitOffsetPagination):
        default_limit = 50
        max_limit = 50

    class FilterSerializer(serializers.Serializer):
        order_by = serializers.ChoiceField(required=False, choices=['timestamp_asc', 'timestamp_desc'])
        username__icontains = serializers.CharField(required=False)
        id = serializers.IntegerField(required=False)
        user_id = serializers.IntegerField(required=False)
        created_at__gte = serializers.DateTimeField(required=False)
        created_at__lte = serializers.DateTimeField(required=False)
        channel_id = serializers.IntegerField(required=False)

    class OutputSerializer(MessageSerializer):
        timestamp = serializers.DateTimeField()

    def get(self, request):
        serializer = self.FilterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        messages = message_channel_preview_list(user=request.user, origin_name='messages',
                                                filters=serializer.validated_data)

        return get_paginated_response(pagination_class=self.Pagination,
                                      serializer_class=self.OutputSerializer,
                                      queryset=messages,
                                      request=request,
                                      view=self)


class MessageFileCollectionUploadAPI(APIView):
    class InputSerializer(serializers.Serializer):
        channel_id = serializers.IntegerField()
        files = serializers.ListField(child=serializers.FileField())

    class OutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file_collection = upload_message_files(user_id=request.user.id, **serializer.validated_data)
        return Response(status=status.HTTP_201_CREATED, data=self.OutputSerializer(file_collection).data)


class MessageChannelUserDataUpdateAPI(APIView):
    class InputSerializer(serializers.Serializer):
        channel_id = serializers.IntegerField()
        timestamp = serializers.DateTimeField()

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        update_message_channel_userdata(user_id=request.user.id, **serializer.validated_data)

        return Response(status=status.HTTP_200_OK)


class MessageChannelLeave(APIView):
    class InputSerializer(serializers.Serializer):
        channel_id = serializers.IntegerField()

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        leave_message_channel(user_id=request.user.id, **serializer.validated_data)

        return Response(status=status.HTTP_200_OK)
