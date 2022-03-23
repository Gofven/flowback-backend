import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from rest_framework import serializers

from flowback.users.models import User


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        if self.scope['user'].is_anonymous:
            self.close()

        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user': self.scope['user']
            }
        )

    # Receive message from room group
    def chat_message(self, event):
        class OutputSerializer(serializers.ModelSerializer):
            class Meta:
                model = User
                fields = 'username', 'image'

        message = event['message']
        user = event['user']
        data = OutputSerializer(user).data

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message,
            'user': data
        }))
