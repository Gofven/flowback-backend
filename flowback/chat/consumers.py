import json
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from flowback.users.models import User, Group
from flowback.users.services import group_user_permitted
from flowback.chat.models import GroupMessage, DirectMessage


class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.chat_id = f'group_{self.group_id}'

        if self.scope['user'].is_anonymous:
            await self.close()

        self.group = await self.group_channel_connect()

        # Join room group
        await self.channel_layer.group_add(
            self.chat_id,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.chat_id,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        class OutputSerializer(serializers.ModelSerializer):
            class Meta:
                model = User
                fields = 'username', 'image'

        await self.group_channel_message(message)

        # Send message to room group
        await self.channel_layer.group_send(
            self.chat_id,
            {
                'type': 'chat_message',
                'user': OutputSerializer(self.user).data,
                'message': message
            }
        )

    # Receive message from room group
    async def chat_message(self, content: dict):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': content.get('message'),
            'user': content.get('user')
        }))

    @database_sync_to_async
    def group_channel_connect(self):
        group = get_object_or_404(Group, pk=self.group_id)
        group_user_permitted(user=self.user.id,
                             group=self.group_id,
                             permission='member')

        return group

    @database_sync_to_async
    def group_channel_message(self, message):
        obj = GroupMessage(user=self.user,
                           group=self.group,
                           message=message)

        obj.full_clean()
        obj.save()


class DirectChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']

        if self.scope['user'].is_anonymous:
            await self.close()

        # chat_id: user_<id:int>
        self.group_name = f'user_{self.user.id}'

        # Join room group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        class FilterSerializer(serializers.Serializer):
            message = serializers.CharField()
            target = serializers.IntegerField()

        class OutputSerializer(serializers.ModelSerializer):
            class Meta:
                model = User
                fields = 'username', 'image'

        serializer = FilterSerializer(data=json.loads(text_data))
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        await self.direct_message(**data)

        # Send message to room group
        await self.channel_layer.group_send(
            await self.get_message_target(data.get('target')),
            {
                'type': 'chat_message',
                'user': OutputSerializer(self.user).data,
                'message': data.get('message'),
            }
        )

    # Receive message from room group
    async def chat_message(self, content: dict):

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': content.get('message'),
            'user': content.get('user')
        }))

    @database_sync_to_async
    def get_message_target(self, target: int):
        get_object_or_404(User, pk=target)

        return f'user_{target}'

    @database_sync_to_async
    def direct_message(self, *, message: str, target: int):
        obj = DirectMessage(user=self.user,
                            target_id=target,
                            message=message)

        obj.full_clean()
        obj.save()
