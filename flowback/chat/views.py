from rest_framework import serializers
from rest_framework.views import APIView

from flowback.chat.selectors import group_message_list, group_message_preview
from flowback.chat.models import GroupMessage
from flowback.common.mixins import ApiErrorsMixin
from flowback.common.pagination import get_paginated_response, LimitOffsetPagination


class GroupMessageListApi(ApiErrorsMixin, APIView):
    class Pagination(LimitOffsetPagination):
        default_limit = 1

    class FilterSerializer(serializers.Serializer):
        user = serializers.IntegerField(required=False)
        message = serializers.CharField(required=False)
        created_at = serializers.DateTimeField(required=False)

    class OutputSerializer(serializers.ModelSerializer):
        username = serializers.CharField(source='user__username')
        image = serializers.ImageField(source='user__image')

        class Meta:
            model = GroupMessage
            fields = 'username', 'image' 'message', 'created_at'

    def get(self, request, group: int):
        filter_serializer = self.FilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)

        messages = group_message_list(user=request.user.id,
                                      group=group,
                                      filters=filter_serializer.validated_data)

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.OutputSerializer,
            queryset=messages,
            request=request,
            view=self
        )


class GroupMessagePreviewApi(ApiErrorsMixin, APIView):
    class Pagination(LimitOffsetPagination):
        default_limit = 1

    class OutputSerializer(serializers.ModelSerializer):
        username = serializers.CharField(source='user__username')
        image = serializers.ImageField(source='user__image')

        class Meta:
            model = GroupMessage
            fields = 'username', 'image' 'message', 'created_at'

    def get(self, request):
        messages = group_message_preview(user=request.user.id)

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.OutputSerializer,
            queryset=messages,
            request=request,
            view=self
        )


class DirectMessageListApi(ApiErrorsMixin, APIView):
    class Pagination(LimitOffsetPagination):
        default_limit = 1

    class FilterSerializer(serializers.Serializer):
        user = serializers.IntegerField(required=False)
        message = serializers.CharField(required=False)
        created_at = serializers.DateTimeField(required=False)

    class OutputSerializer(serializers.ModelSerializer):
        username = serializers.CharField(source='user__username')
        image = serializers.ImageField(source='user__image')

        class Meta:
            model = GroupMessage
            fields = 'username', 'image' 'message', 'created_at'

    def get(self, request, group: int):
        filter_serializer = self.FilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)

        messages = group_message_list(user=request.user.id,
                                      group=group,
                                      filters=filter_serializer.validated_data)

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.OutputSerializer,
            queryset=messages,
            request=request,
            view=self
        )


class DirectMessagePreviewApi(ApiErrorsMixin, APIView):
    class Pagination(LimitOffsetPagination):
        default_limit = 1

    class OutputSerializer(serializers.ModelSerializer):
        username = serializers.CharField(source='user__username')
        image = serializers.ImageField(source='user__image')

        class Meta:
            model = GroupMessage
            fields = 'username', 'image' 'message', 'created_at'

    def get(self, request):
        messages = group_message_preview(user=request.user.id)

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.OutputSerializer,
            queryset=messages,
            request=request,
            view=self
        )