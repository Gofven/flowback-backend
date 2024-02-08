from django.test import TransactionTestCase

from ..models import (MessageChannel,
                      Message,
                      MessageChannelParticipant,
                      MessageChannelTopic,
                      MessageFileCollection)

from ..services import (message_create,
                        message_update,
                        message_delete,
                        message_channel_create,
                        message_channel_delete,
                        message_channel_join,
                        message_channel_leave)

from .factories import (MessageChannelFactory,
                        MessageFactory,
                        MessageChannelParticipantFactory,
                        MessageChannelTopicFactory,
                        MessageFileCollectionFactory)
from ...user.tests.factories import UserFactory


# Create your tests here.


class ChatTest(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.user_one = UserFactory()
        self.user_two = UserFactory()
        self.message_channel = MessageChannelFactory()
        self.message_channel_participant_one = MessageChannelParticipantFactory(channel=self.message_channel)
        self.message_channel_participant_two = MessageChannelParticipantFactory(channel=self.message_channel)
        self.message_channel_topic = MessageChannelTopicFactory(channel=self.message_channel)
        self.message_channel_file_collection = MessageFileCollectionFactory(channel=self.message_channel)

    def test_message_channel_create(self):
        channel = message_channel_create(origin_name="user", title="test")

        self.assertTrue(channel.id)

    def test_message_channel_delete(self):
        channel_id = self.message_channel.id
        message_channel_delete(channel_id=channel_id)

        self.assertFalse(MessageChannel.objects.filter(id=channel_id).exists())

    def test_message_channel_join(self):
        participant = message_channel_join(user_id=self.user_one.id, channel_id=self.message_channel.id)

        self.assertTrue(participant.id)
        self.assertTrue(isinstance(participant, MessageChannelParticipant))

    def test_message_channel_leave(self):
        participant_id = self.message_channel_participant_one.id
        message_channel_leave(user_id=self.message_channel_participant_one.user.id, channel_id=self.message_channel.id)

        self.assertFalse(MessageChannelParticipant.objects.filter(id=participant_id).exists())

    def test_message_create(self):
        message_one = message_create(user_id=self.message_channel_participant_one.user.id,
                                     channel_id=self.message_channel.id,
                                     message="test message",
                                     attachments_id=self.message_channel_file_collection.id)

        self.assertTrue(message_one.id)
        self.assertEqual(message_one.message, "test message")
        self.assertEqual(message_one.user.id, self.message_channel_participant_one.user.id)
        self.assertEqual(message_one.attachments_id, self.message_channel_file_collection.id)

    def test_message_update(self):
        message = MessageFactory()

        message_update(user_id=message.user_id, message_id=message.id, message="testify message")

        message.refresh_from_db()
        self.assertEqual(message.message, "testify message")

    def test_message_delete(self):
        message = MessageFactory()
        message_delete(user_id=message.user_id, message_id=message.id)
        message.refresh_from_db()

        self.assertFalse(message.active)
