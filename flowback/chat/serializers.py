from rest_framework import serializers

from flowback.user.serializers import BasicUserSerializer


class _MessageSerializerTemplate(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    user = BasicUserSerializer()
    channel_id = serializers.IntegerField()
    message = serializers.CharField()
    attachments = serializers.ListField(child=serializers.CharField())


class BasicMessageSerializer(_MessageSerializerTemplate):
    parent_id = serializers.IntegerField(required=False)


class MessageSerializer(_MessageSerializerTemplate):
    parent = BasicMessageSerializer()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    active = serializers.BooleanField()
