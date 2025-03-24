from rest_framework import serializers

from flowback.user.serializers import BasicUserSerializer
from flowback.files.serializers import FileSerializer


class _MessageSerializerTemplate(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    user = BasicUserSerializer()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    channel_id = serializers.IntegerField()
    channel_origin_name = serializers.CharField(source="channel.origin_name")
    channel_title = serializers.CharField(source="channel.title")
    topic_id = serializers.IntegerField(required=False)
    topic_name = serializers.CharField(required=False, source='topic.name')
    type = serializers.CharField(read_only=True)
    message = serializers.CharField()
    attachments = FileSerializer(many=True, source='attachments.file_collection.filesegment_set', allow_null=True)


class BasicMessageSerializer(_MessageSerializerTemplate):
    parent_id = serializers.IntegerField(required=False)


class MessageSerializer(_MessageSerializerTemplate):
    parent = BasicMessageSerializer()
    active = serializers.BooleanField()
