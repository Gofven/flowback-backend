from django.test import TestCase
from flowback.chat.services import (message_create,
                                    message_update,
                                    message_delete,
                                    message_channel_create,
                                    message_channel_delete,
                                    message_channel_join,
                                    message_channel_leave)

# Create your tests here.


class ChatTest(TestCase):
    reset_sequences = True

    def setUp(self):
        pass
