from rest_framework.test import APITransactionTestCase

from flowback.user.tests.factories import UserFactory


class NotificationTest(APITransactionTestCase):
    def setUp(self):
        self.user = UserFactory()