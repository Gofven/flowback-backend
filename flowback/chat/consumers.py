import json

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from flowback.chat.models import MessageChannelParticipant
from flowback.common.services import get_object
from flowback.user.models import User
from flowback.group.models import Group
from flowback.group.services import group_user_permissions

# create message
# update message
# delete message

# TODO Create websocket that only connects to one channel at a time.
#  In future create webhook for subscribing to notifications, in meantime use 10s
#  space between preview list api.
#  Additionally each module will have their own chat consumer to allow permission check

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if self.scope['user'].is_anonymous:
            await self.close()

        self.participating_channels = await self.get_participating_channels()
        for channel in self.participating_channels:
            await self.channel_layer.group_add(
                channel,
                self.channel_name
            )

        await self.accept()

    async def disconnect(self, close_code):
        for group in self.participating_channels:
            await self.channel_layer.group_discard(
                group,
                self.channel_name
            )

    # Receive message from WebSocket
    async def receive(self, text_data):
        class FilterSerializer(serializers.Serializer):
            target_channel = serializers.IntegerField()
            message = serializers.CharField()

        class OutputSerializer(serializers.ModelSerializer):
            class Meta:
                model = User
                fields = 'id', 'username', 'profile_image'

        serializer = FilterSerializer(data=json.loads(text_data or '{}'))
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        target_type = data.get('target_type')
        message = data.get('message')
        target = data.get('target')

        data = dict(user=OutputSerializer(self.user).data,
                    message=data.get('message'),
                    type='chat_message',
                    target_type=target_type)

        # Save message to database
        if target_type == 'direct':
            await self.direct_message(message=message, target=target)

        elif target_type == 'group':
            data['group'] = target
            await self.group_message(message=message, target=target)

        else:
            raise ValidationError('Unknown target type')

        # Send message to room group
        await self.channel_layer.group_send(
            await self.get_message_target(target=target, target_type=target_type),
            data
        )

    # Receive message from room group
    async def chat_message(self, content: dict):
        data = dict(message=content.get('message'),
                    user=content.get('user'),
                    target_type=content.get('target_type'))

        if data.get('target_type'):
            data['group'] = content.get('group')

        # Send message to WebSocket
        await self.send(text_data=json.dumps(data))

    @database_sync_to_async
    def get_message_target(self, target: int, target_type: str):
        return f'user_{target}' if target_type == 'direct' else f'group_{target}'

    @database_sync_to_async
    def get_participating_channels(self):
        return MessageChannelParticipant.objects.filter(user=self.user).values_list('channel_id', flat=True)

    @database_sync_to_async
    def direct_message(self, *, message: str, target: int):
        target = get_object(User, pk=target)

        obj = DirectMessage(user=self.user,
                            target_id=target.id,
                            message=message)

        obj.full_clean()
        obj.save()

    @database_sync_to_async
    def group_message(self, message: str, target: int):
        group_user = group_user_permissions(group=target, user=self.user.id)
        obj = GroupMessage(group_user=group_user,
                           message=message)

        obj.full_clean()
        obj.save()
