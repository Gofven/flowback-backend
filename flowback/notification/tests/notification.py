import datetime

from Scripts.activate_this import prev_length
from rest_framework.test import APITransactionTestCase

from flowback.common.tests import generate_request
from flowback.group.tests.factories import GroupFactory
from flowback.notification.models import NotificationObject
from flowback.notification.tests.factories import NotificationObjectFactory


# Create your tests here.
class GroupNotificationTest(APITransactionTestCase):
    def setUp(self):
        self.group = GroupFactory()
        self.group_user_creator = self.group.group_user_creator

    def test_group_notification_channel_exists(self):
        self.assertTrue(self.group.notification_channel)

    def test_group_notify_group(self):
        message = "Hello everyone"
        self.group.notify_group(message=message)

        self.assertTrue(NotificationObject.objects.filter(channel__content_type__model="group",
                                                          channel__object_id=self.group.id,
                                                          tag="group",
                                                          action=NotificationObject.Action.CREATED,
                                                          message=message).exists(),
                        NotificationObject.objects.first().__dict__)

    def test_group_notification_shift(self):
        NotificationObjectFactory.create_batch(size=10,
                                               channel=self.group.notification_channel,
                                               tag="group")

        # Test shifting all notifications 100 seconds forward
        prev_timestamps = list(NotificationObject.objects.all().order_by("id").values_list("timestamp",
                                                                                           flat=True))
        self.group.notification_channel.shift(delta=-200)
        self.group.notification_channel.shift(delta=300)  # Net total = 100 seconds

        for i, timestamp in enumerate(NotificationObject.objects.all().order_by("id").values_list("timestamp",
                                                                                                  flat=True)):
            self.assertEqual(timestamp, (prev_timestamps[i] + datetime.timedelta(seconds=100)))

        # Test shifting some notifications 100 seconds forward
        prev_timestamps = list(NotificationObject.objects.all().order_by("id").values_list("timestamp",
                                                                                           flat=True))
        self.group.notification_channel.shift(delta=200, timestamp__gt=prev_timestamps[5])

        for i, timestamp in enumerate(NotificationObject.objects.all().order_by("id").values_list("timestamp",
                                                                                                  flat=True)):
            if i <= 5:
                self.assertEqual(timestamp, prev_timestamps[i])
            else:
                self.assertEqual(timestamp, (prev_timestamps[i] + datetime.timedelta(seconds=200)))
